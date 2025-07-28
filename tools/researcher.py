"""
researcher.py
=============

Заготовка для агента Researcher. Содержит функции для выполнения web‑поиска
и API‑запросов. В реальной системе функция `web_search` должна
использовать модуль browser или сторонние API (например, DuckDuckGo,
Google Custom Search). Здесь приведена базовая реализация с использованием
HTTP‑запроса к DuckDuckGo Instant Answer API.
"""

from typing import List, Dict, Any
import logging
import json

from memory.chroma_store import ChromaStore
from .fact_checker import validate_sources

try:
    import requests  # type: ignore
except ImportError:
    requests = None  # type: ignore


def web_search(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """Выполнить web‑поиск и вернуть список результатов.

    Args:
        query: поисковый запрос
        max_results: максимальное число результатов

    Returns:
        Список словарей с результатами (title, url, snippet).

    Note:
        Используется DuckDuckGo Instant Answer API, который ограничен и не
        требует ключа. В некоторых регионах может быть недоступен. Для
        полноценных RAG‑сценариев рекомендуется использовать платные API.
    """
    if requests is None:
        raise RuntimeError("Библиотека requests не установлена. Установите её: pip install requests")
    url = "https://api.duckduckgo.com/"
    params = {
        "q": query,
        "format": "json",
        "pretty": 1,
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        results = []
        # Instant Answer API возвращает раздел 'RelatedTopics'
        topics = data.get("RelatedTopics", [])
        count = 0
        for topic in topics:
            if count >= max_results:
                break
            if "Text" in topic and "FirstURL" in topic:
                results.append({
                    "title": topic["Text"],
                    "url": topic["FirstURL"],
                    "snippet": topic.get("Result", ""),
                })
                count += 1
        return results
    except Exception as exc:
        logging.warning("[Researcher] Ошибка web‑поиска: %s", exc)
        return []


def store_results(query: str, results: List[Dict[str, Any]], collection: str = "research_mem") -> None:
    """Сохранить результаты в коллекции ChromaDB."""

    if not results:
        return
    try:
        store = ChromaStore()
        ids = [res["url"] for res in results]
        docs = [json.dumps(res, ensure_ascii=False) for res in results]
        metadatas = [{"query": query}] * len(results)
        store.add(collection, ids=ids, documents=docs, metadatas=metadatas)
        logging.info("[Researcher] сохранено %d документов в %s", len(results), collection)
    except Exception as exc:  # pragma: no cover - optional dependency
        logging.warning("[Researcher] ошибка сохранения: %s", exc)


def search_and_store(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """Выполнить поиск, проверить факты и сохранить результаты."""

    results = web_search(query, max_results)
    if not results:
        return []
    if not validate_sources(results):
        logging.info("[Researcher] источники не прошли валидацию")
        return []
    store_results(query, results)
    return results