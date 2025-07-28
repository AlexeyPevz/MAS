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
        print(f"[Researcher] Ошибка web‑поиска: {exc}")
        return []