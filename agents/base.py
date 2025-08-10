from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import asyncio

# Импорт AutoGen v0.4+ с поддержкой новых API
try:
    from autogen_agentchat.agents import AssistantAgent
    from autogen_ext.models.openai import OpenAIChatCompletionClient
    from autogen_core import CancellationToken
except ImportError:
    # Полностью изолированный fallback без внешних импортов
    class AssistantAgent:  # type: ignore
        def __init__(self, name, model_client=None, system_message="", *args, **kwargs):
            self.name = name
            self.model_client = model_client
            self.system_message = system_message

        async def on_messages(self, messages, cancellation_token=None):
            class _Resp:
                def __init__(self, content: str) -> None:
                    class _Msg:
                        def __init__(self, c: str) -> None:
                            self.content = c
                    self.chat_message = _Msg(content)
            # Простой мок-контент без зависимостей
            return _Resp(content=f"[{self.name}] Mock response")

from tools.prompt_io import read_prompt

# New: helper to get task-specific prompt path


def _task_prompt_path(agent_name: str, task: str) -> Path:
    """Return the path to a task-specific prompt file.

    Expected file layout::

        prompts/agents/<agent_name>/task_<task>.md

    where *task* is an arbitrary slug (e.g. "research", "summarize").
    """

    filename = f"task_{task}.md"
    return PROMPTS_DIR / agent_name / filename


# System prompts reside under the repository's ``prompts/agents`` directory.
PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts" / "agents"


class BaseAgent(AssistantAgent):
    """Base class for root MAS agents."""

    def __init__(self, name: str, model: str = "gpt-4o-mini", tier: str = "cheap", *args: Any, **kwargs: Any) -> None:
        # Загружаем системный промпт
        if "system_message" not in kwargs:
            prompt_path = PROMPTS_DIR / name / "system.md"
            kwargs["system_message"] = read_prompt(prompt_path)

        # Создаем model_client вместо llm_config
        from tools.llm_config import get_model_by_tier, create_llm_config
        
        if tier:
            llm_config = get_model_by_tier(tier, 0)
        else:
            llm_config = create_llm_config(model, "openrouter")
        
        # Конвертируем старый llm_config в новый model_client
        config_list = llm_config.get("config_list", [{}])[0]
        api_key = config_list.get("api_key", "mock-key")
        base_url = config_list.get("base_url")
        
        try:
            # Создаем OpenAI клиент для v0.4
            model_client = OpenAIChatCompletionClient(
                model=config_list.get("model", model),
                api_key=api_key,
                base_url=base_url,
                temperature=config_list.get("temperature", 0.7),
                max_tokens=config_list.get("max_tokens", 2000)
            )
        except Exception:
            # Fallback на mock клиент
            model_client = None

        super().__init__(
            name=name,
            model_client=model_client,
            *args,
            **kwargs
        )
        self.tier = tier
        self.model = model
        
        # Cache for task-specific prompts: slug -> text
        self._task_prompts: dict[str, str] = {}
        self._current_tier = tier
        self._current_model = model
        
        # Auto-connect memory based on agent configuration
        self.memory = None
        self._setup_memory()

    async def generate_reply_async(self, messages=None, sender=None, config=None):
        """Асинхронная версия generate_reply для совместимости"""
        if messages is None:
            messages = []
        
        try:
            # Конвертируем старый формат сообщений в новый
            new_messages = []
            for msg in messages:
                if isinstance(msg, dict):
                    content = msg.get("content", "")
                    source = msg.get("name", "user")
                else:
                    content = str(msg)
                    source = "user"
                # Простейшая модель новых сообщений: список словарей
                new_messages.append({"content": content, "source": source})
            
            # Используем новый API, если он есть у родительского класса
            if hasattr(super(), 'on_messages'):
                cancellation_token = None
                try:
                    cancellation_token = CancellationToken()
                except Exception:
                    cancellation_token = None
                response = await super().on_messages(new_messages, cancellation_token)
                return getattr(getattr(response, 'chat_message', None), 'content', None) or ""
            # Полностью fallback
            return f"[{self.name}] Processed {len(new_messages)} messages"
        except Exception as e:
            print(f"Error in generate_reply_async: {e}")
            return f"[{self.name}] Error processing message"

    def generate_reply(self, messages=None, sender=None, config=None):
        """Безопасная синхронная обертка: не вызывает asyncio.run внутри event loop"""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        
        if loop and loop.is_running():
            # Внутри уже запущенного цикла — выполняем через executor блокирующий вызов
            future = asyncio.run_coroutine_threadsafe(self.generate_reply_async(messages, sender, config), loop)
            return future.result()
        else:
            return asyncio.run(self.generate_reply_async(messages, sender, config))

    # ------------------------------------------------------------------
    # Prompt helpers
    # ------------------------------------------------------------------

    def load_task_prompt(self, task: str) -> str:
        """Load and cache a task-specific prompt for this agent.

        Parameters
        ----------
        task:
            Slug of the task (without prefix). Example: "research" loads
            ``task_research.md`` from the agent's prompt directory.
        """

        if task in self._task_prompts:
            return self._task_prompts[task]

        path = _task_prompt_path(self.name, task)
        prompt = read_prompt(path)
        self._task_prompts[task] = prompt
        return prompt

    def set_task_prompt(self, task: str) -> None:
        """Replace current system prompt with a task prompt."""

        prompt = self.load_task_prompt(task)
        # ConversableAgent exposes attribute ``system_message``; we update it
        self.system_message = prompt

    def __hash__(self) -> int:
        """Make BaseAgent hashable for GroupChat compatibility."""
        return hash(self.name)

    def __eq__(self, other: object) -> bool:
        """Equality comparison for BaseAgent."""
        if not isinstance(other, BaseAgent):
            return False
        return self.name == other.name

    def _setup_memory(self):
        """Setup memory connection based on agent configuration"""
        try:
            # Пытаемся определить тип памяти по имени агента или конфигурации
            memory_config = self._get_memory_config()
            
            if memory_config == "global":
                from memory.redis_store import RedisStore
                self.memory = RedisStore()
            elif memory_config == "vector":
                from memory.chroma_store import ChromaStore
                self.memory = ChromaStore()
            elif memory_config == "persistent":
                from memory.postgres_store import PostgresStore
                self.memory = PostgresStore()
            # else: memory остается None (без памяти)
            
        except Exception as e:
            # Если не удалось подключить память - продолжаем без неё
            pass
    
    def _get_memory_config(self) -> str:
        """Determine memory type for this agent"""
        # Mapping agent names to memory types
        memory_map = {
            "meta": "global",
            "coordination": "global", 
            "researcher": "vector",
            "fact_checker": "vector",
            "prompt_builder": "persistent",
            "multi_tool": "global",
            "workflow_builder": "persistent",
            "webapp_builder": "persistent",
            "communicator": "global"
        }
        
        return memory_map.get(self.name, "none")
    
    def remember(self, key: str, value: str):
        """Store information in memory"""
        if self.memory:
            try:
                self.memory.store(key, value)
            except Exception:
                pass  # Тихо игнорируем ошибки памяти
    
    def recall(self, key: str) -> str:
        """Retrieve information from memory"""
        if self.memory:
            try:
                return self.memory.retrieve(key)
            except Exception:
                pass
        return ""
    
    def search_memory(self, query: str, limit: int = 5):
        """Search in memory (for vector stores)"""
        if self.memory and hasattr(self.memory, 'search'):
            try:
                return self.memory.search(query, limit)
            except Exception:
                pass
        return []
    
    async def ensure_knowledge(self, topic: str, confidence_threshold: float = 0.7) -> bool:
        """Ensure agent has sufficient knowledge on topic before proceeding"""
        # Check existing knowledge
        knowledge_check = self.assess_knowledge(topic)
        
        if knowledge_check['confidence'] >= confidence_threshold:
            return True
        
        # Request research if knowledge insufficient
        print(f"[{self.name}] Insufficient knowledge on '{topic}' (confidence: {knowledge_check['confidence']:.2f})")
        print(f"[{self.name}] Requesting research from Researcher agent...")
        
        # Create research request
        research_request = await self.request_research(topic)
        
        # Wait for research completion with timeout
        timeout = 30  # seconds
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            if await self.check_research_complete(research_request['id']):
                # Re-assess knowledge after research
                new_check = self.assess_knowledge(topic)
                if new_check['confidence'] >= confidence_threshold:
                    print(f"[{self.name}] Knowledge updated successfully (new confidence: {new_check['confidence']:.2f})")
                    return True
            
            await asyncio.sleep(1)
        
        print(f"[{self.name}] Research timeout - proceeding with limited knowledge")
        return False
    
    def assess_knowledge(self, topic: str) -> Dict[str, Any]:
        """Assess agent's knowledge level on a topic"""
        if not self.memory:
            return {'confidence': 0.0, 'sources': []}
        
        # Search relevant information
        results = self.search_memory(topic, limit=10)
        
        if not results:
            return {'confidence': 0.0, 'sources': []}
        
        # Calculate confidence based on:
        # - Number of relevant results
        # - Recency of information
        # - Source quality
        confidence = min(len(results) / 10.0, 0.9)  # Max 0.9 from search alone
        
        # Boost confidence if we have task-specific prompts
        if topic.lower() in self._task_prompts:
            confidence = min(confidence + 0.2, 1.0)
        
        return {
            'confidence': confidence,
            'sources': results[:5],
            'source_count': len(results)
        }
    
    async def request_research(self, topic: str) -> Dict[str, str]:
        """Request research from Researcher agent"""
        from tools.smart_groupchat import Message
        from datetime import datetime, timezone
        
        request_id = f"research_{self.name}_{int(datetime.now(timezone.utc).timestamp())}"
        
        # Store request for tracking
        if not hasattr(self, '_research_requests'):
            self._research_requests = {}
        
        self._research_requests[request_id] = {
            'topic': topic,
            'status': 'pending',
            'requested_at': datetime.now(timezone.utc)
        }
        
        # Send research request through callback or direct message
        try:
            from tools.callbacks import research_validation_cycle
            research_validation_cycle(topic)
            self._research_requests[request_id]['status'] = 'in_progress'
        except Exception as e:
            print(f"[{self.name}] Failed to request research: {e}")
            self._research_requests[request_id]['status'] = 'failed'
        
        return {'id': request_id, 'topic': topic}
    
    async def check_research_complete(self, request_id: str) -> bool:
        """Check if research request is complete"""
        if not hasattr(self, '_research_requests'):
            return False
        
        request = self._research_requests.get(request_id)
        if not request:
            return False
        
        # Check if new knowledge available
        if request['status'] == 'pending':
            # Re-check memory for new information
            new_results = self.search_memory(request['topic'])
            if new_results and len(new_results) > 0:
                request['status'] = 'completed'
                return True
        
        return request['status'] == 'completed'
