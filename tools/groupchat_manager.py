from __future__ import annotations

from pathlib import Path
from typing import Dict, List

try:
    from autogen.agentchat import GroupChat, GroupChatManager, ConversableAgent
except Exception:  # pragma: no cover - optional dependency
    class ConversableAgent:  # type: ignore[too-few-public-methods]
        def __init__(self, name: str, llm_config: dict | None = None, system_message: str | None = None) -> None:
            self.name = name
            self.llm_config = llm_config or {}
            self.system_message = system_message or ""

        def receive(self, message: Dict, sender: str) -> None:  # pragma: no cover - stub
            pass

    class GroupChat:  # type: ignore[too-few-public-methods]
        def __init__(self, agents: List[ConversableAgent], messages: List[Dict] | None = None, speaker_selection_method: str | None = None) -> None:
            self.agents = agents
            self.messages = messages or []

    class GroupChatManager:  # type: ignore[too-few-public-methods]
        def __init__(self, groupchat: GroupChat, llm_config: dict | None = None, system_message: str | None = None) -> None:
            self.groupchat = groupchat
            self.llm_config = llm_config or {}
            self.system_message = system_message or ""

        def receive(self, message: Dict, sender: str) -> None:  # pragma: no cover - stub
            pass

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
        super().__init__(groupchat=chat, llm_config={"model": "gpt-4o"}, system_message=system_prompt)
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

