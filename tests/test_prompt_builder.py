import subprocess
from pathlib import Path
import pytest

import tools.prompt_builder as pb


def test_update_prompt_creates_file(monkeypatch, tmp_path):
    monkeypatch.setattr(pb, "REPO_ROOT", tmp_path)
    called = []
    monkeypatch.setattr(pb, "git_commit", lambda paths, message: called.append((list(paths), message)))

    pb.update_agent_prompt("demo", "hello")

    file_path = tmp_path / "prompts" / "agents" / "demo" / "system.md"
    assert file_path.read_text() == "hello\n"
    assert called[0][0] == [str(file_path.relative_to(tmp_path))]
    assert "demo" in called[0][1]


def test_update_global_permission(monkeypatch, tmp_path):
    monkeypatch.setattr(pb, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(pb, "git_commit", lambda *a, **k: None)

    with pytest.raises(PermissionError):
        pb.update_agent_prompt("global", "hi")

    pb.update_agent_prompt("global", "hi", allow_global=True)
    file_path = tmp_path / "prompts" / "global" / "system.md"
    assert file_path.read_text() == "hi\n"


def test_get_prompt_history(monkeypatch, tmp_path):
    monkeypatch.setattr(pb, "REPO_ROOT", tmp_path)
    def fake_run(cmd, cwd=None, capture_output=False, text=False):
        return subprocess.CompletedProcess(cmd, 0, stdout="LOG", stderr="")
    monkeypatch.setattr(subprocess, "run", fake_run)
    result = pb.get_prompt_history("demo", limit=2)
    assert result == "LOG"


def test_update_creates_version(monkeypatch, tmp_path):
    monkeypatch.setattr(pb, "REPO_ROOT", tmp_path)
    commits = []
    monkeypatch.setattr(pb, "git_commit", lambda paths, message: commits.append((list(paths), message)))

    pb.create_agent_prompt("demo", "v1")
    pb.update_agent_prompt("demo", "v2")

    version_file = tmp_path / "prompts" / "agents" / "demo" / "versions" / "v1.md"
    assert version_file.exists()
    assert version_file.read_text() == "v1\n"
    assert any("Snapshot" in msg for _, msg in commits)
