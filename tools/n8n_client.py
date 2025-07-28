"""
n8n_client.py
==============

Простейший клиент для взаимодействия с платформой n8n по API. В реальной
реализации здесь могут использоваться HTTP‑запросы (например, через requests)
для создания, активации и управления workflow. Данные функции должны
использоваться агентом WF‑Builder и Instance‑Factory.
"""

import os
import time
import logging
from typing import Dict, Any, Optional

# В реальной реализации вам понадобятся requests или aiohttp
try:
    import requests  # type: ignore
except ImportError:
    requests = None  # type: ignore


TIMEOUT = 10

# Retry/back-off settings
MAX_RETRIES = int(os.getenv("N8N_RETRIES", "3"))
BACKOFF_BASE = float(os.getenv("N8N_BACKOFF", "1.5"))  # seconds


class N8NClient:
    """Минималистичный клиент для работы с API n8n."""

    def __init__(self, base_url: str | None = None, api_key: str | None = None) -> None:
        if requests is None:
            raise RuntimeError(
                "Библиотека requests не установлена. Установите её для работы n8n_client."
            )
        self.base_url = (base_url or os.getenv("N8N_URL", "http://localhost:5678")).rstrip("/")
        self.api_key = api_key or os.getenv("N8N_API_KEY", "")

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    # ------------------------------------------------------------------
    # Internal helper with retry / back-off
    # ------------------------------------------------------------------

    def _request(self, method: str, url: str, **kwargs: Any) -> "requests.Response":  # type: ignore[name-defined]
        backoff = BACKOFF_BASE
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = requests.request(method, url, timeout=TIMEOUT, **kwargs)  # type: ignore[arg-type]
                if resp.status_code >= 500:
                    raise RuntimeError(f"{resp.status_code} server error")
                return resp
            except Exception as exc:  # pragma: no cover - network errors
                if attempt == MAX_RETRIES:
                    raise
                logging.warning("[n8n_client] %s %s failed (%s), retry %d/%d", method, url, exc, attempt, MAX_RETRIES)
                time.sleep(backoff)
                backoff *= 2

    def create_workflow(self, workflow_json: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Создать новый workflow в n8n.

        Args:
            workflow_json: описание workflow в формате n8n

        Returns:
            Ответ API n8n с информацией о созданном workflow или None при ошибке.
        """
        url = f"{self.base_url}/api/v1/workflows"
        try:
            resp = self._request("POST", url, headers=self._headers(), json=workflow_json)
            return resp.json()
        except Exception as exc:  # pragma: no cover - network errors
            print(f"[n8n_client] Ошибка при создании workflow: {exc}")
            return None

    def activate_workflow(self, workflow_id: str) -> bool:
        """Активировать существующий workflow.

        Args:
            workflow_id: идентификатор workflow

        Returns:
            True при успешной активации, иначе False.
        """
        url = f"{self.base_url}/api/v1/workflows/{workflow_id}/activate"
        try:
            resp = self._request("POST", url, headers=self._headers())
            resp.raise_for_status()
            return True
        except Exception as exc:  # pragma: no cover - network errors
            print(f"[n8n_client] Ошибка при активации workflow: {exc}")
            return False


if __name__ == "__main__":
    # Пример использования клиента
    base = os.getenv("N8N_URL", "http://localhost:5678")
    key = os.getenv("N8N_API_KEY", "changeme")
    client = N8NClient(base, key)
    workflow = {
        "name": "Echo Workflow",
        "nodes": [],
        "connections": {},
    }
    result = client.create_workflow(workflow)
    if result and result.get("id"):
        print("Создан workflow:", result.get("id"))
        client.activate_workflow(result["id"])
