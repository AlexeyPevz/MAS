from __future__ import annotations

from pathlib import Path
from typing import Any

from autogen.agentchat import ConversableAgent

from tools.prompt_io import read_prompt


PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts" / "agents"


class BaseAgent(ConversableAgent):
    """Base class for root MAS agents."""

    def __init__(self, name: str, model: str, *args: Any, **kwargs: Any) -> None:
        prompt_path = PROMPTS_DIR / name / "system.md"
        system_prompt = read_prompt(prompt_path)
        super().__init__(name=name, llm_config={"model": model}, system_message=system_prompt, *args, **kwargs)
