import pytest
from pathlib import Path

import run
from config.config_loader import AgentsConfig, AgentDefinition
from tools.callback_matrix import handle_event


def test_load_agents_config(tmp_path):
    content = """
agents:
  meta:
    role: Meta
    model: gpt
"""
    path = tmp_path / "agents.yaml"
    path.write_text(content)

    cfg = AgentsConfig.from_yaml(path)
    assert "meta" in cfg.agents


def test_load_llm_tiers(tmp_path):
    content = """
cheap: [a]
standard: [b]
premium: [c]
"""
    p = tmp_path / "tiers.yaml"
    p.write_text(content)
    tiers = run.load_llm_tiers(p)
    assert tiers.cheap == ["a"]


def test_create_agents_basic():
    import sys
    import types

    dummy = types.ModuleType("prompt_io")
    dummy.read_prompt = lambda p: ""
    sys.modules.setdefault("prompt_io", dummy)

    from agents.core_agents import create_agents

    cfg = AgentsConfig(
        agents={
            "meta": AgentDefinition(role="Meta", model="gpt-4"),
            "communicator": AgentDefinition(role="Comm", model="gpt-3"),
        }
    )
    agents = create_agents(cfg)
    assert set(agents.keys()) == {"meta", "communicator"}


def test_callback_matrix_known_event(capsys):
    handle_event("OUTGOING_TO_TELEGRAM", "ping")
    captured = capsys.readouterr()
    assert "ping" in captured.out


def test_callback_matrix_unknown_event():
    with pytest.raises(ValueError):
        handle_event("UNKNOWN_EVENT")
