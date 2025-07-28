"""
wf_builder.py
==============

Модуль для генерации JSON‑описаний workflow n8n на основе текстовой
спецификации. Агент WF‑Builder использует функцию `generate_n8n_json`
для преобразования спецификации в структуру, понятную n8n, а затем
передаёт её клиенту через `n8n_client`.
"""

import json
import os
from typing import Any, Dict

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    yaml = None  # type: ignore

from .security import get_secret


def generate_n8n_json(spec: str) -> Dict[str, Any]:
    """Сгенерировать JSON‑workflow из текстовой спецификации.

    Сначала предпринимается попытка разобрать ``spec`` как JSON или YAML.
    Это позволяет передавать готовое описание workflow. Если разбор
    не удался, создаётся минимальный workflow с единственной нодой,
    содержащей исходный текст спецификации.

    Args:
        spec: текстовое описание задачи

    Returns:
        Словарь, который может быть отправлен в n8n API для создания workflow.
    """

    # Попытаться интерпретировать спецификацию как JSON/YAML
    for loader in (json.loads, getattr(yaml, "safe_load", None)):
        if not loader:
            continue
        try:
            data = loader(spec)
            if isinstance(data, dict) and "nodes" in data:
                return data
        except Exception:  # pragma: no cover - invalid spec
            continue

    # Fallback: минимальный workflow
    return {
        "name": f"Generated workflow for: {spec[:40]}",
        "nodes": [
            {
                "parameters": {"chatInput": spec},
                "name": "Start",
                "type": "n8n-nodes-base.start",
                "typeVersion": 1,
                "position": [0, 0],
            }
        ],
        "connections": {},
    }


def create_workflow(spec: Any, n8n_base_url: str | None = None, api_key: str | None = None) -> Any:
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
    key = api_key or get_secret("N8N_API_KEY") or os.getenv("N8N_API_KEY", "")
    if isinstance(spec, dict):
        workflow_json = spec
    else:
        workflow_json = generate_n8n_json(str(spec))
    client = N8NClient(base_url, key)
    result = client.create_workflow(workflow_json)
    if result and result.get("id"):
        workflow_id = result["id"]
        client.activate_workflow(workflow_id)
    return result
