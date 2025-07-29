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

    def __init__(self, name: str, model: str, *args: Any, **kwargs: Any) -> None:
        prompt_path = PROMPTS_DIR / name / "system.md"
        system_prompt = read_prompt(prompt_path)
        super().__init__(name=name, llm_config={"model": model}, system_message=system_prompt, *args, **kwargs)

        # Cache for task-specific prompts: slug -> text
        self._task_prompts: dict[str, str] = {}

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
