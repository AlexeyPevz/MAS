"""
fact_checker.py
===============

Заготовка для агента Fact‑Checker. Предоставляет функции для проверки
достоверности информации и источников. Реальная реализация может
использовать дополнительные API, библиотеки для детектирования фейков и
кросс‑проверку по нескольким источникам. Здесь реализована простая
валидация на наличие ключевых слов.
"""

from typing import List, Dict, Any


def validate_sources(sources: List[Dict[str, Any]]) -> bool:
    """Проверить достоверность списка источников.

    Args:
        sources: список словарей с ключами 'url' и 'title'

    Returns:
        True, если источники считаются надёжными, иначе False.

    Note:
        В этой заглушке мы считаем валидными источники, содержащие
        https:// в URL и не содержащие подозрительных доменов. Реальная
        проверка должна быть гораздо сложнее.
    """
    bad_keywords = ["clickbait", "fake", "suspicious"]
    for src in sources:
        url = src.get("url", "")
        title = src.get("title", "")
        if not url.startswith("https://"):
            return False
        for word in bad_keywords:
            if word in url.lower() or word in title.lower():
                return False
    return True