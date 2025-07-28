"""
prompt_builder.py
=================

Модуль для работы агента Prompt‑Builder. Позволяет создавать новые
системные промпты для агентов, проводить аудит существующих и
сохранять изменения в системе управления версиями (git). Функция
`create_agent_prompt` создаёт файл system.md для нового агента.
`audit_prompt` показывает разницу между текущей версией файла и
последним коммитом. Попытка редактировать глобальный промпт
(`prompts/global/system.md`) приводит к PermissionError.
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
    result = subprocess.run([
        "git",
        "diff",
        "HEAD",
        "--",
        str(rel_path),
    ], cwd=REPO_ROOT, capture_output=True, text=True)
    return result.stdout