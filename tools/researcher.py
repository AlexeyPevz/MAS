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
import os
import time

from memory.chroma_store import ChromaStore
from .fact_checker import validate_sources

# Optional backends
try:
    import requests  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    requests = None  # type: ignore

try:
    from memory.redis_store import RedisStore

    _REDIS = RedisStore()
except Exception:  # pragma: no cover - redis optional
    _REDIS = None  # type: ignore


# ---------------------------------------------------------------------------
# Backends
# ---------------------------------------------------------------------------


def _cache_get(key: str) -> list[Dict[str, Any]] | None:  # noqa: D401
    if _REDIS is None:
        return None
    try:
        data = _REDIS.get(key)
        if data:
            return json.loads(data)
    except Exception:
        pass
    return None


def _cache_set(key: str, value: list[Dict[str, Any]], ttl: int = 86400) -> None:  # 1 day
    if _REDIS is None:
        return
    try:
        _REDIS.set(key, json.dumps(value, ensure_ascii=False), ttl)
    except Exception:
        pass


def _serpapi_search(query: str, max_results: int) -> list[Dict[str, Any]]:
    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key:
        raise RuntimeError("SERPAPI_API_KEY not set")
    params = {
        "q": query,
        "api_key": api_key,
        "num": max_results,
        "engine": "google",
        "hl": "en",
    }
    resp = requests.get("https://serpapi.com/search", params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    organic = data.get("organic_results", [])
    results = []
    for item in organic[:max_results]:
        results.append({
            "title": item.get("title"),
            "url": item.get("link"),
            "snippet": item.get("snippet", ""),
        })
    return results


def _duck_search(query: str, max_results: int) -> list[Dict[str, Any]]:
    url = "https://api.duckduckgo.com/"
    params = {"q": query, "format": "json", "pretty": 1}
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    topics = data.get("RelatedTopics", [])
    results: list[Dict[str, Any]] = []
    for topic in topics:
        if len(results) >= max_results:
            break
        if "Text" in topic and "FirstURL" in topic:
            results.append({
                "title": topic["Text"],
                "url": topic["FirstURL"],
                "snippet": topic.get("Result", ""),
            })
    return results


def web_search(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """Выполнить web-поиск (SerpAPI → DuckDuckGo fallback) с кешированием."""

    if requests is None:
        raise RuntimeError("Библиотека requests не установлена (researcher)")

    cache_key = f"research:{query}:{max_results}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    backends = [
        lambda: _serpapi_search(query, max_results),
        lambda: _duck_search(query, max_results),
    ]
    for backend in backends:
        try:
            results = backend()
            if results:
                _cache_set(cache_key, results)
                return results
        except Exception as exc:
            logging.warning("[Researcher] backend error: %s", exc)

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