from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, List
import asyncio

# Импорт AutoGen v0.4+ с поддержкой новых API
# Fallback для случаев, если модули еще не установлены
try:
    from autogen_agentchat.agents import AssistantAgent
    from autogen_ext.models.openai import OpenAIChatCompletionClient
except ImportError:
    print("Warning: autogen modules not found, using mock fallback")
    # Mock классы для тестирования
    class AssistantAgent:
        def __init__(self, *args, **kwargs):
            pass
    
    class OpenAIChatCompletionClient:
        def __init__(self, *args, **kwargs):
            self.api_key = kwargs.get('api_key', 'mock-key')

# Import new systems with fallback
try:
    from tools.learning_loop import learning_loop
    from tools.knowledge_graph import add_knowledge, query_knowledge
    from tools.ab_testing import ab_testing
    ADVANCED_FEATURES = True
except ImportError:
    print("Warning: Advanced features not available")
    ADVANCED_FEATURES = False

# Import semantic cache
try:
    from tools.semantic_llm_cache import semantic_cache, cached_llm_call
    SEMANTIC_CACHE_AVAILABLE = True
except ImportError:
    print("Warning: Semantic cache not available")
    SEMANTIC_CACHE_AVAILABLE = False

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
    """Базовый класс для всех агентов Root-MAS"""
    
    def __init__(self, name: str, model: str = "gpt-4o-mini", tier: str = "standard", *args, **kwargs):
        # Не присваиваем name напрямую, так как это property в AssistantAgent
        self.tier = tier
        self.model = model
        self._task_prompts = {}  # Для хранения task-specific промптов в памяти
        self._reflection_mode = False
        self._experiment_id = None
        self._current_task_type = None
        
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
        
        # Cache for task-specific prompts: slug -> text
        self._task_prompts: dict[str, str] = {}
        self._current_tier = tier
        self._current_model = model
        
        # Auto-connect memory based on agent configuration
        self.memory = None
        self._setup_memory()

    async def generate_reply_async(self, messages=None, sender=None, config=None):
        """Асинхронная версия generate_reply для совместимости с семантическим кэшированием"""
        if messages is None:
            messages = []
        
        try:
            # Конвертируем старый формат сообщений в новый
            new_messages = []
            last_content = ""
            for msg in messages:
                if isinstance(msg, dict):
                    content = msg.get("content", "")
                    source = msg.get("name", "user")
                else:
                    content = str(msg)
                    source = "user"
                # Простейшая модель новых сообщений: список словарей
                new_messages.append({"content": content, "source": source})
                last_content = content
            
            # Если есть семантический кэш и сообщения
            if SEMANTIC_CACHE_AVAILABLE and last_content:
                # Функция для вычисления ответа
                async def compute_response():
                    # Используем новый API, если он есть у родительского класса
                    if hasattr(super(), 'on_messages'):
                        cancellation_token = None
                        try:
                            from autogen_core import CancellationToken
                            cancellation_token = CancellationToken()
                        except Exception:
                            cancellation_token = None
                        response = await super().on_messages(new_messages, cancellation_token)
                        return getattr(getattr(response, 'chat_message', None), 'content', None) or ""
                    # Полностью fallback
                    return f"[{self.name}] Processed {len(new_messages)} messages"
                
                # Используем семантический кэш
                response_content, from_cache, similarity = await semantic_cache.get_or_compute(
                    query=last_content,
                    compute_func=compute_response,
                    agent_name=self.name,
                    ttl=86400 * 7,  # Неделя для персонального использования
                    model=getattr(self, 'model', 'gpt-4o-mini'),
                    estimated_tokens=len(last_content.split()) * 3
                )
                
                # Добавляем интеллектуальные функции если доступны
                if ADVANCED_FEATURES and not from_cache:
                    # Обучение с подкреплением
                    if hasattr(self, 'learning_enabled') and self.learning_enabled:
                        response_content = await learning_loop(self, last_content, response_content)
                    
                    # Добавление в граф знаний
                    if hasattr(self, 'knowledge_enabled') and self.knowledge_enabled:
                        await add_knowledge(self.name, last_content, response_content)
                
                return response_content
            else:
                # Без кэша - старая логика
                if hasattr(super(), 'on_messages'):
                    cancellation_token = None
                    try:
                        from autogen_core import CancellationToken
                        cancellation_token = CancellationToken()
                    except Exception:
                        cancellation_token = None
                    response = await super().on_messages(new_messages, cancellation_token)
                    return getattr(getattr(response, 'chat_message', None), 'content', None) or ""
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

    def _load_task_prompts(self):
        """Загрузить все task-specific промпты для агента"""
        base_path = Path(__file__).parents[1] / "prompts" / "agents" / self.name
        
        if base_path.exists():
            for task_file in base_path.glob("task_*.md"):
                task_name = task_file.stem.replace("task_", "")
                self._task_prompts[task_name] = task_file.read_text(encoding="utf-8")
        
        # Load A/B test variants if available
        if ADVANCED_FEATURES and ab_testing:
            # Check for A/B test prompt
            variant = ab_testing.get_variant_for_task(self.name, self._current_task_type)
            if variant:
                self._experiment_id = variant.id.split('_')[0]
                self.system_message = variant.content
                return
        
        # Check for winning prompts from completed experiments
        if ADVANCED_FEATURES and ab_testing:
            winning_prompt = ab_testing.get_winning_prompt(self.name, self._current_task_type)
            if winning_prompt:
                self.system_message = winning_prompt

    async def activate_task_mode(self, task: str):
        """Активировать task-specific режим для агента"""
        self._current_task_type = task
        
        if task == "reflection":
            self._reflection_mode = True
            if task in self._task_prompts:
                # Добавляем рефлексивный промпт к системному
                reflection_prompt = self._task_prompts[task]
                self.system_message = f"{self.system_message}\n\n{reflection_prompt}"
        elif task in self._task_prompts:
            # Заменяем системный промпт на task-specific
            self.system_message = self._task_prompts[task]
        
        # Re-check for A/B test variants
        self._load_task_prompts()

    async def learn_from_experience(self, state: Dict[str, Any], action: str, result: Any):
        """Обучиться на основе опыта выполнения задачи"""
        if not ADVANCED_FEATURES:
            return
        
        from tools.quality_metrics import TaskResult
        
        # Convert result to TaskResult if needed
        if isinstance(result, TaskResult):
            task_result = result
        else:
            # Create TaskResult from response
            task_result = TaskResult(
                task_id=f"{self.name}_{int(asyncio.get_event_loop().time())}",
                agent_name=self.name,
                task_type=self._current_task_type or "general",
                status="success" if result else "failure",
                confidence=0.7,  # Default
                response_time=1.0,  # Placeholder
                model_used=self.model,
                tier_used=self.tier,
                token_cost=0.001  # Placeholder
            )
        
        # Record experience for learning
        await learning_loop.record_experience(
            agent_name=self.name,
            task_type=self._current_task_type or "general",
            state=state,
            action=action,
            result=task_result
        )
        
        # Record A/B test result if in experiment
        if self._experiment_id and ab_testing:
            ab_testing.record_result(
                self._experiment_id,
                f"{self._experiment_id}_{self.name}",
                task_result
            )

    async def add_to_knowledge_graph(
        self, 
        concept: str, 
        concept_type: str = "entity",
        properties: Optional[Dict[str, Any]] = None,
        relations: Optional[List[tuple]] = None
    ):
        """Добавить концепцию в граф знаний"""
        if not ADVANCED_FEATURES:
            return
        
        await add_knowledge(
            concept_name=concept,
            concept_type=concept_type,
            properties=properties,
            relations=relations
        )

    async def query_knowledge_graph(self, query: str, max_depth: int = 3) -> List[Dict[str, Any]]:
        """Запросить информацию из графа знаний"""
        if not ADVANCED_FEATURES:
            return []
        
        results = await query_knowledge(
            query=query,
            concept_type=None,
            max_depth=max_depth
        )
        
        # Also search in traditional memory
        memory_results = self.search_memory(query)
        
        # Combine results
        combined = {
            "graph_results": results,
            "memory_results": memory_results
        }
        
        return combined

    async def get_action_suggestion(self, state: Dict[str, Any], available_actions: List[str]) -> str:
        """Получить предложение действия на основе обучения"""
        if not ADVANCED_FEATURES:
            return available_actions[0] if available_actions else ""
        
        return await learning_loop.suggest_action(
            agent_name=self.name,
            state=state,
            available_actions=available_actions
        )

    async def reflect_on_performance(self) -> Dict[str, Any]:
        """Выполнить саморефлексию производительности"""
        if not ADVANCED_FEATURES:
            return {"status": "reflection not available"}
        
        # Activate reflection mode
        await self.activate_task_mode("reflection")
        
        # Get performance data
        from tools.quality_metrics import quality_metrics
        performance = quality_metrics.get_agent_performance(self.name)
        
        # Get learning report
        learning_report = learning_loop.get_learning_report(self.name)
        
        # Build reflection context
        reflection_context = {
            "performance_metrics": performance,
            "learning_insights": learning_report,
            "recent_errors": performance.get("common_errors", {}),
            "improvement_trend": performance.get("recent_trend", "unknown")
        }
        
        # Generate reflection using LLM
        reflection_prompt = f"""
        Based on the following performance data, provide a detailed self-reflection:
        
        Performance: {json.dumps(performance, indent=2)}
        Learning: {json.dumps(learning_report, indent=2)}
        
        Follow the reflection format specified in your system prompt.
        """
        
        # Get reflection from LLM
        if hasattr(self, 'on_messages'):
            from autogen_core import CancellationToken
            messages = [{"role": "user", "content": reflection_prompt}]
            response = await self.on_messages(messages, CancellationToken())
            reflection = response.chat_message.content
        else:
            reflection = "Reflection capability not available"
        
        # Deactivate reflection mode
        self._reflection_mode = False
        self._load_task_prompts()  # Reload normal prompt
        
        return {
            "reflection": reflection,
            "context": reflection_context
        }
