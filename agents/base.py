from __future__ import annotations

from pathlib import Path
from typing import Any

# Требуемый импорт AutoGen. При отсутствии библиотеки завершится ImportError,
# что позволит CI выявить проблему на этапе установки зависимостей.
from autogen.agentchat import ConversableAgent

from prompt_io import read_prompt


# System prompts reside under the repository's ``prompts/agents`` directory.
PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts" / "agents"


class BaseAgent(ConversableAgent):
    """Base class for root MAS agents."""

    def __init__(self, name: str, model: str, *args: Any, **kwargs: Any) -> None:
        prompt_path = PROMPTS_DIR / name / "system.md"
        system_prompt = read_prompt(prompt_path)
        super().__init__(name=name, llm_config={"model": model}, system_message=system_prompt, *args, **kwargs)
