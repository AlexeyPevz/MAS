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
import logging


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


def check_facts(results: List[Dict[str, Any]]) -> bool:
    """Проверить факты на основе сниппетов."""

    snippets = [r.get("snippet", "") for r in results if r.get("snippet")]
    if len(snippets) < 2:
        logging.info("[FactChecker] недостаточно данных для кросс-проверки")
        return False
    return cross_reference(snippets)


def cross_reference(snippets: List[str]) -> bool:
    """Проверить совпадения фраз в нескольких источниках."""

    seen = set()
    for text in snippets:
        key = text.strip().lower()[:50]
        if key in seen:
            return True
        seen.add(key)
    return False