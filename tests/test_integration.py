import tools.callback_matrix as cbm
from agents.core_agents import create_agents
from tools.groupchat_manager import RootGroupChatManager
from config_loader import AgentsConfig


def test_goal_groupchat_callback(monkeypatch):
    """Full-stack integration: Meta -> callback -> outgoing_to_telegram."""

    # Load default agents config
    cfg = AgentsConfig.from_yaml("config/agents.yaml")
    agents = create_agents(cfg)

    # Capture outgoing telegram messages
    sent: list[str] = []

    def fake_sender(msg: str) -> None:  # pragma: no cover
        sent.append(msg)

    monkeypatch.setattr("tools.callbacks.outgoing_to_telegram", fake_sender)

    routing = {
        "communicator": ["meta"],
        "meta": [],  # meta can escalate directly
    }

    manager = RootGroupChatManager(agents, routing)

    # Ask Meta to escalate a question -> should hit callback matrix -> sender
    evt = agents["meta"].escalate("test ping")
    manager.receive(evt, sender="meta")

    assert sent and "test ping" in sent[0]