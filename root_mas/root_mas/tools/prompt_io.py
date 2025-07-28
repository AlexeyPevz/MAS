"""
prompt_io.py
============

Вспомогательные функции для чтения и записи промптов. Они позволяют
агенту Prompt‑Builder создавать новые системные промпты, сохранять
изменения и производить версионирование (например, через git).
"""

from pathlib import Path
from typing import Iterable, List


def read_prompt(path: str) -> str:
    """Прочитать содержимое промпта из файла.

    Args:
        path: путь к файлу промпта

    Returns:
        Строка с содержимым файла.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Файл промпта не найден: {path}")
    return p.read_text(encoding="utf-8")


def write_prompt(path: str, lines: Iterable[str]) -> None:
    """Записать содержимое промпта в файл.

    Args:
        path: путь к файлу
        lines: коллекция строк для записи

    Note:
        В реальной реализации здесь можно добавить создание git‑коммита.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        for line in lines:
            f.write(line.rstrip("\n") + "\n")
