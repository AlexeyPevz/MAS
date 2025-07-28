"""
multitool.py
============

Интерфейс для вызова внешних API от имени MultiTool‑агента. В
конфигурации указано, что MultiTool использует фиксированную модель
LLM (например, Kimi K2) для обработки запросов. В этой заглушке
показано, как можно организовать вызов стороннего API с передачей
описания задачи и возвратом результата.
"""

from typing import Any, Dict, List
import os

try:
    import requests  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    requests = None  # type: ignore

BASE_URL = os.getenv("MULTITOOL_URL", "http://localhost:8080")
API_KEY = os.getenv("MULTITOOL_API_KEY", "")

# Предопределённые цепочки замены инструментов.
# Если основной API недоступен, используется следующий из списка.
FALLBACK_TOOLS: Dict[str, List[str]] = {
    "kimi_k2": ["kimi_k1"],
}


def _headers() -> Dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"
    return headers


def call_api(api_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Вызвать сторонний API и вернуть результат.

    Если API отсутствует (например, 404), генерируется событие
    ``MISSING_TOOL`` через callback_matrix.
    """
    if requests is None:
        raise RuntimeError("Для работы multitool требуется библиотека requests")
    url = f"{BASE_URL}/api/{api_name}"
    try:
        resp = requests.post(url, json=params, headers=_headers(), timeout=10)
        if resp.status_code == 404:
            from .callback_matrix import handle_event

            handle_event("MISSING_TOOL", api_name)
            return {"error": "missing_tool", "tool": api_name}
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:  # pragma: no cover - network errors
        print(f"[multitool] Ошибка вызова {api_name}: {exc}")
        return {"error": str(exc)}


def call(
    api_name: str,
    params: Dict[str, Any],
    fallbacks: Dict[str, List[str]] | None = None,
) -> Dict[str, Any]:
    """Вызвать API с автоматической заменой инструмента при ошибке.

    Args:
        api_name: имя основного инструмента
        params: параметры запроса
        fallbacks: карта подмены инструментов. Если ``None``,
            используются ``FALLBACK_TOOLS``.

    Returns:
        Ответ успешного запроса либо последняя ошибка.
    """

    chain = [api_name]
    mapping = fallbacks or FALLBACK_TOOLS
    chain.extend(mapping.get(api_name, []))

    result: Dict[str, Any] = {"error": "unavailable"}
    for tool in chain:
        result = call_api(tool, params)
        if "error" not in result:
            return result
    return result
