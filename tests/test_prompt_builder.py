import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / 'root_mas' / 'root_mas'))

from tools import prompt_builder


def test_create_agent_prompt(tmp_path, monkeypatch):
    monkeypatch.setattr(prompt_builder, 'REPO_ROOT', tmp_path)
    committed = {'flag': False}

    def fake_commit(paths, message):
        committed['flag'] = True

    monkeypatch.setattr(prompt_builder, 'git_commit', fake_commit)

    prompt_builder.create_agent_prompt('tester', 'hello')
    file_path = tmp_path / 'prompts' / 'agents' / 'tester' / 'system.md'
    assert file_path.read_text() == 'hello'
    assert committed['flag']


def test_audit_prompt(tmp_path, monkeypatch):
    monkeypatch.setattr(prompt_builder, 'REPO_ROOT', tmp_path)

    target = tmp_path / 'prompts' / 'agents' / 'tester' / 'system.md'
    target.parent.mkdir(parents=True)
    target.write_text('hello')

    class Dummy:
        stdout = 'diff output'

    def fake_run(cmd, cwd, capture_output=False, text=False):
        return Dummy()

    monkeypatch.setattr(prompt_builder.subprocess, 'run', fake_run)

    diff = prompt_builder.audit_prompt('tester')
    assert diff == 'diff output'
