"""Utilities for managing system prompts used by the agents.

The module is primarily used by the Prompt‑Builder agent.  It provides
helpers for creating and updating prompt files under ``prompts/`` and
keeps them under version control using git.  Direct modifications of the
global prompt (``prompts/global/system.md``) are forbidden unless the
caller explicitly allows it.

Functions
~~~~~~~~~
``create_agent_prompt`` -- create a new system prompt for an agent.
``update_agent_prompt`` -- update an existing prompt with optional global
permission check.
``audit_prompt`` -- show the diff between the working tree and HEAD.
``get_prompt_history`` -- show git log for a prompt file.
"""

import subprocess
from pathlib import Path
from typing import Iterable

from .prompt_io import write_prompt, read_prompt


REPO_ROOT = Path(__file__).resolve().parents[1]


def git_commit(file_paths: Iterable[str], message: str) -> None:
    """Сделать git‑коммит указанных файлов."""
    paths = [str(REPO_ROOT / p) for p in file_paths]
    # Добавляем файлы
    subprocess.run(["git", "add", *paths], cwd=REPO_ROOT)
    # Коммит
    subprocess.run(["git", "commit", "-m", message], cwd=REPO_ROOT)


def create_agent_prompt(agent_name: str, content: str) -> None:
    """Создать системный промпт для нового агента.

    Args:
        agent_name: имя агента
        content: текст промпта
    """
    if agent_name.lower() == "global":
        raise PermissionError("Редактирование глобального промпта запрещено.")
    path = REPO_ROOT / "prompts" / "agents" / agent_name / "system.md"
    write_prompt(str(path), [content])
    git_commit([str(path.relative_to(REPO_ROOT))], f"Add system prompt for agent {agent_name}")


def update_agent_prompt(agent_name: str, content: str, *, allow_global: bool = False) -> None:
    """Update an existing system prompt and commit the change.

    Parameters
    ----------
    agent_name:
        Target agent. Use ``"global"`` for the global system prompt.
    content:
        New prompt text.
    allow_global:
        Explicitly allow editing of the global prompt.
    """

    if agent_name.lower() == "global" and not allow_global:
        raise PermissionError("Редактирование глобального промпта запрещено.")

    if agent_name.lower() == "global":
        path = REPO_ROOT / "prompts" / "global" / "system.md"
    else:
        path = REPO_ROOT / "prompts" / "agents" / agent_name / "system.md"

    write_prompt(str(path), [content])
    git_commit([str(path.relative_to(REPO_ROOT))], f"Update system prompt for {agent_name}")


def audit_prompt(agent_name: str) -> str:
    """Вернуть diff промпта с последним коммитом.

    Args:
        agent_name: имя агента

    Returns:
        Строка с результатом diff.
    """
    path = REPO_ROOT / "prompts"
    if agent_name.lower() == "global":
        target = path / "global" / "system.md"
    else:
        target = path / "agents" / agent_name / "system.md"
    rel_path = target.relative_to(REPO_ROOT)
    # Используем git diff для сравнения последней версии с HEAD
    result = subprocess.run(
        ["git", "diff", "HEAD", "--", str(rel_path)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    return result.stdout


def get_prompt_history(agent_name: str, limit: int = 5) -> str:
    """Return git log output for a prompt file."""

    path = REPO_ROOT / "prompts"
    if agent_name.lower() == "global":
        target = path / "global" / "system.md"
    else:
        target = path / "agents" / agent_name / "system.md"
    rel_path = target.relative_to(REPO_ROOT)
    result = subprocess.run(
        ["git", "log", f"-n{limit}", "--", str(rel_path)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    return result.stdout