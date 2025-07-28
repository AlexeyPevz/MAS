from __future__ import annotations

from typing import Dict, List

from autogen.agentchat import GroupChat, GroupChatManager, ConversableAgent

from tools.callback_matrix import handle_event


class RootGroupChatManager(GroupChatManager):
    """GroupChatManager with simple routing and callback integration."""

    def __init__(self, agents: Dict[str, ConversableAgent], routing: Dict[str, List[str]]):
        self.routing = routing
        chat = GroupChat(
            agents=list(agents.values()),
            messages=[],
            speaker_selection_method="manual",
        )
        super().__init__(groupchat=chat, llm_config={"model": "gpt-4o"})
        self._agents = agents

    def receive(self, message: Dict, sender: str) -> None:  # type: ignore[override]
        event = message.get("event")
        if event:
            handle_event(event, *message.get("args", []), **message.get("kwargs", {}))
            return
        receivers = self.routing.get(sender, [])
        for name in receivers:
            agent = self._agents.get(name)
            if agent is not None:
                agent.receive(message, sender=sender)  # type: ignore[arg-type]

