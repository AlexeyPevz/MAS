"""
repo_validator.py
=================

Проверка корректности развернутых репозиториев. Используется Instance‑Factory и другими инструментами для валидации созданных проектов.
"""

from __future__ import annotations

from pathlib import Path


def is_git_repo(path: str | Path) -> bool:
    """Return True if ``path`` looks like a git repository."""
    p = Path(path)
    return p.is_dir() and (p / ".git").exists()


def validate_repository(path: str | Path) -> bool:
    """Validate that ``path`` contains a deployable project."""
    repo = Path(path)
    if not is_git_repo(repo):
        return False
    readme = repo / "README.md"
    compose1 = repo / "compose.yml"
    compose2 = repo / "docker-compose.yml"
    if not readme.exists():
        return False
    if not (compose1.exists() or compose2.exists()):
        return False
    return True
