from types import SimpleNamespace
from pathlib import Path
import yaml
from tools import instance_factory as ifac


def test_deploy_instance_writes_env_and_config(tmp_path, monkeypatch):
    deploy_dir = tmp_path / "deploy" / "internal"
    deploy_dir.mkdir(parents=True)
    (deploy_dir / "compose.yml").write_text("version: '3.8'\n")

    monkeypatch.setattr(ifac, "REPO_ROOT", tmp_path)
    (tmp_path / "config").mkdir()

    calls = []

    def fake_run(cmd, cwd=None):
        calls.append((cmd, cwd))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(ifac.subprocess, "run", fake_run)

    env = {"TEST": "42", "MAS_ENDPOINT": "http://x"}
    ifac.deploy_instance("deploy/internal", env, "demo", "internal")

    assert (deploy_dir / ".env").read_text() == "TEST=42\nMAS_ENDPOINT=http://x\n"

    cfg = yaml.safe_load((tmp_path / "config" / "instances.yaml").read_text())
    assert cfg["instances"]["demo"]["endpoint"] == "http://x"
    assert calls and calls[0][0][:2] == ["docker", "compose"]


def test_auto_deploy_instance(monkeypatch):
    captured = {}

    def fake_deploy(directory, env, name, itype):
        captured.update({"dir": directory, "env": env, "name": name, "type": itype})

    def fake_secret(key: str) -> str:
        return f"val-{key}"

    monkeypatch.setattr(ifac, "deploy_instance", fake_deploy)
    monkeypatch.setattr(ifac, "get_secret", fake_secret)

    name = ifac.auto_deploy_instance("client", {"A": "1"})

    assert name.startswith("client_")
    assert captured["dir"] == "deploy/client"
    assert captured["env"]["A"] == "1"
    assert captured["env"]["OPENROUTER_API_KEY"] == "val-OPENROUTER_API_KEY"
    assert captured["type"] == "client"

