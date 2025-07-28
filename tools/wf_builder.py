"""
wf_builder.py
==============

Модуль для генерации JSON‑описаний workflow n8n на основе текстовой
спецификации. Агент WF‑Builder использует функцию `generate_n8n_json`
для преобразования спецификации в структуру, понятную n8n, а затем
передаёт её клиенту через `n8n_client`.
"""

import os
from typing import Dict, Any


def generate_n8n_json(spec: str) -> Dict[str, Any]:
    """Сгенерировать JSON‑workflow из текстовой спецификации.

    Args:
        spec: текстовое описание задачи (например, "собирать RSS‑ленты и
        отправлять обновления в Telegram")

    Returns:
        Словарь, который может быть отправлен в n8n API для создания workflow.

    Note:
        В этой заготовке создаётся минимальный workflow с одной нодой
        комментария. Для реальной генерации необходимо использовать LLM
        (например, через AutoGen) и шаблоны рецептов.
    """
    workflow = {
        "name": f"Generated workflow for: {spec[:40]}",
        "nodes": [
            {
                "parameters": {
                    "chatInput": spec
                },
                "name": "Start",
                "type": "n8n-nodes-base.start",
                "typeVersion": 1,
                "position": [0, 0],
            }
        ],
        "connections": {},
    }
    return workflow


def create_workflow(spec: str, n8n_base_url: str | None = None, api_key: str | None = None) -> Any:
    """Создать и активировать workflow в n8n.

    Args:
        spec: текстовое описание
        n8n_base_url: URL сервера n8n
        api_key: ключ API для доступа к n8n

    Returns:
        Ответ сервера n8n или None при ошибке.
    """
    from .n8n_client import N8NClient

    base_url = n8n_base_url or os.getenv("N8N_URL", "http://localhost:5678")
    key = api_key or os.getenv("N8N_API_KEY", "")
    workflow_json = generate_n8n_json(spec)
    client = N8NClient(base_url, key)
    result = client.create_workflow(workflow_json)
    if result and result.get("id"):
        workflow_id = result["id"]
        client.activate_workflow(workflow_id)
    return result
