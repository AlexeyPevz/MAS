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
            if not isinstance(data, dict):
                continue
            # Full n8n JSON already
            if "nodes" in data:
                return data

            # High-level DSL: {name, steps: [{name, type, parameters}]}
            if "steps" in data and isinstance(data["steps"], list):
                return _steps_to_workflow(data)
        except Exception:
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
    key = api_key or os.getenv("N8N_API_KEY", "")
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _steps_to_workflow(spec: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a simple *steps* DSL into n8n workflow JSON."""

    steps = spec.get("steps", [])
    name = spec.get("name", "Generated Workflow")

    nodes: list[Dict[str, Any]] = []
    connections: Dict[str, Dict[str, list[dict]]] = {}

    x, y = 0, 0
    for idx, step in enumerate(steps):
        node_name = step.get("name", f"Step {idx+1}")
        node_type = step.get("type", "n8n-nodes-base.noOp")
        params = step.get("parameters", {})

        node = {
            "parameters": params,
            "name": node_name,
            "type": node_type,
            "typeVersion": 1,
            "position": [x, y],
        }
        nodes.append(node)

        # simple vertical layout
        y += 200

        # create sequential connection
        if idx > 0:
            prev_name = steps[idx - 1].get("name", f"Step {idx}")
            connections.setdefault(prev_name, {}).setdefault("main", [[]]).append({"node": node_name, "type": "main", "index": 0})

    return {
        "name": name,
        "nodes": nodes,
        "connections": connections,
    }
