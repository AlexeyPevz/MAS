from __future__ import annotations

from pathlib import Path
from typing import Any

# Импорт AutoGen с поддержкой разных версий
try:
    from autogen.agentchat import ConversableAgent
except ImportError:
    try:
        from autogen_agentchat import ConversableAgent
    except ImportError:
        # Fallback для случая отсутствия autogen
        class ConversableAgent:
            def __init__(self, name, llm_config, system_message="", *args, **kwargs):
                self.name = name
                self.llm_config = llm_config
                self.system_message = system_message
            
            def generate_reply(self, messages=None, sender=None, config=None):
                return f"[{self.name}] Mock response"

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


class BaseAgent(ConversableAgent):
    """Base class for root MAS agents."""

    def __init__(self, name: str, model: str = "gpt-4o-mini", tier: str = "cheap", *args: Any, **kwargs: Any) -> None:
        # Загружаем системный промпт
        prompt_path = PROMPTS_DIR / name / "system.md"
        system_prompt = read_prompt(prompt_path)
        
        # Создаем LLM конфигурацию
        from tools.llm_config import get_model_by_tier, create_llm_config
        
        # Используем tier для автоматического выбора модели или конкретную модель
        if tier and tier in ["cheap", "standard", "premium"]:
            llm_config = get_model_by_tier(tier, 0)
        else:
            llm_config = create_llm_config(model, "openrouter")
        
        super().__init__(
            name=name, 
            llm_config=llm_config, 
            system_message=system_prompt, 
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
