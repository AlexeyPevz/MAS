"""
n8n_client.py
==============

Простейший клиент для взаимодействия с платформой n8n по API. В реальной
реализации здесь могут использоваться HTTP‑запросы (например, через requests)
для создания, активации и управления workflow. Данные функции должны
использоваться агентом WF‑Builder и Instance‑Factory.
"""

import os
import json
from typing import Dict, Any, Optional

# В реальной реализации вам понадобятся requests или aiohttp
try:
    import requests  # type: ignore
except ImportError:
    requests = None  # type: ignore


class N8NClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        if requests is None:
            raise RuntimeError("Библиотека requests не установлена. Установите её для работы n8n_client.")

    def _headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def create_workflow(self, workflow_json: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Создать новый workflow в n8n.

        Args:
            workflow_json: описание workflow в формате n8n

        Returns:
            Ответ API n8n с информацией о созданном workflow или None при ошибке.
        """
        url = f"{self.base_url}/api/v1/workflows"
        try:
            response = requests.post(url, headers=self._headers(), json=workflow_json)
            response.raise_for_status()
            return response.json()
        except Exception as exc:
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
            response = requests.post(url, headers=self._headers())
            response.raise_for_status()
            return True
        except Exception as exc:
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
    if result:
        print("Создан workflow:", result.get("id"))