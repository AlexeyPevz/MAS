from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from autogen.agentchat import ConversableAgent
except Exception:  # pragma: no cover - optional dependency
    class ConversableAgent:  # type: ignore[too-few-public-methods]
        """Fallback stub when AutoGen is unavailable."""

        def __init__(self, name: str, llm_config: dict | None = None, system_message: str | None = None, *args: Any, **kwargs: Any) -> None:  # noqa: D401
            self.name = name
            self.llm_config = llm_config or {}
            self.system_message = system_message or ""

        def receive(self, message: dict, sender: str) -> None:  # pragma: no cover - stub
            pass

from prompt_io import read_prompt


# System prompts reside under the repository's ``prompts/agents`` directory.
PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts" / "agents"


class BaseAgent(ConversableAgent):
    """Base class for root MAS agents."""

    def __init__(self, name: str, model: str, *args: Any, **kwargs: Any) -> None:
        prompt_path = PROMPTS_DIR / name / "system.md"
        system_prompt = read_prompt(prompt_path)
        super().__init__(name=name, llm_config={"model": model}, system_message=system_prompt, *args, **kwargs)
