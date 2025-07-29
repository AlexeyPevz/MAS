from dataclasses import dataclass

import config.config_loader as cl


def test_load_dataclass(tmp_path):
    @dataclass
    class Dummy:
        a: int
        b: str

    p = tmp_path / "dummy.yaml"
    p.write_text("a: 1\nb: test")

    obj = cl.load_dataclass(p, Dummy)
    assert obj == Dummy(a=1, b="test")


def test_agents_config_from_yaml(tmp_path):
    content = """
agents:
  alice:
    role: tester
    model: gpt-3
  bob:
    role: helper
    model: gpt-4
"""
    p = tmp_path / "agents.yaml"
    p.write_text(content)

    cfg = cl.AgentsConfig.from_yaml(p)
    assert cfg.agents["alice"].role == "tester"
    assert cfg.agents["bob"].model == "gpt-4"


