from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Any

# Прямой импорт AutoGen – в продакшне библиотека присутствует, иначе CI упадёт.
from autogen.agentchat import GroupChat, GroupChatManager, ConversableAgent

from .callback_matrix import handle_event
from .studio_logger import log_interaction


class RootGroupChatManager(GroupChatManager):
    """Simple manager that routes messages between core agents."""

    def __init__(self, agents: Dict[str, ConversableAgent], routing: Dict[str, List[str]]):
        self.routing = routing
        chat = GroupChat(
            agents=list(agents.values()),
            messages=[],
            speaker_selection_method="manual",
        )
        system_prompt_path = (
            Path(__file__).resolve().parent.parent / "prompts" / "global" / "system.md"
        )
        try:
            system_prompt = system_prompt_path.read_text(encoding="utf-8")
        except Exception:
            system_prompt = ""
        try:
            import openai  # noqa: F401
            llm_cfg: Any = {"model": "gpt-4o"}
        except ImportError:  # pragma: no cover - optional dependency
            llm_cfg = False
        super().__init__(groupchat=chat, llm_config=llm_cfg, system_message=system_prompt)
        self._agents = agents
        self.groupchat.messages = []

    def send_user_message(self, text: str) -> None:
        """Entry point for user messages coming from Communicator."""
        self.receive({"role": "user", "content": text}, sender="communicator")

    def receive(self, message: Dict, sender: str) -> None:  # type: ignore[override]
        event = message.get("event")
        if event:
            handle_event(event, *message.get("args", []), **message.get("kwargs", {}))
            return
        self.groupchat.messages.append({"sender": sender, "message": message})
        receivers = self.routing.get(sender, [])
        log_interaction(sender, receivers, message)
        for name in receivers:
            agent = self._agents.get(name)
            if agent is not None:
                agent.receive(message, sender=sender)  # type: ignore[arg-type]

