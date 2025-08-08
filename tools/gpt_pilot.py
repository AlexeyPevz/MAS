"""
gpt_pilot.py
============

Интерфейс для взаимодействия с GPT‑Pilot — сервисом, который позволяет
генерировать приложения из текстового описания. Агент WebApp‑Builder
использует этот модуль для создания приложений и отслеживания статуса.
"""

import os
from typing import Dict, Any, Optional

try:
    import requests  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    from types import SimpleNamespace
    def _not_installed(*_args, **_kwargs):  # pragma: no cover
        raise RuntimeError("requests is required for this operation")
    requests = SimpleNamespace(post=_not_installed, get=_not_installed)  # type: ignore


BASE_URL = os.getenv("GPT_PILOT_URL", "http://localhost:8000")
API_KEY = os.getenv("GPT_PILOT_API_KEY", "")


def _headers() -> Dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"
    return headers


def create_app(spec_json: Dict[str, Any]) -> str:
    """Отправить спецификацию в GPT‑Pilot и вернуть ID задачи."""
    if requests is None:
        raise RuntimeError("Для работы gpt_pilot требуется библиотека requests")
    try:
        resp = requests.post(
            f"{BASE_URL}/api/v1/tasks",
            json=spec_json,
            headers=_headers(),
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("id", "")
    except Exception as exc:  # pragma: no cover - network errors
        print(f"[gpt_pilot] Ошибка создания приложения: {exc}")
        return ""


def status(task_id: str) -> Optional[Dict[str, Any]]:
    """Получить статус выполнения задачи GPT‑Pilot."""
    if requests is None:
        raise RuntimeError("Для работы gpt_pilot требуется библиотека requests")
    try:
        resp = requests.get(
            f"{BASE_URL}/api/v1/tasks/{task_id}",
            headers=_headers(),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:  # pragma: no cover - network errors
        print(f"[gpt_pilot] Ошибка получения статуса: {exc}")
        return None

