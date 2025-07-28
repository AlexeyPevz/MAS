"""
webapp_builder.py
=================

Обёртка для работы агента WebApp‑Builder. Позволяет создавать
приложения через GPT‑Pilot и отслеживать их статус. Предполагается,
что перед отправкой запроса агент Fact‑Checker валидирует URL
репозитория и спецификацию.
"""

from typing import Dict, Any, Optional
from .gpt_pilot import create_app as pilot_create_app, status as pilot_status


def create_app(spec_json: Dict[str, Any]) -> str:
    """Создать приложение через GPT‑Pilot.

    Args:
        spec_json: JSON‑описание приложения (структура определяется GPT‑Pilot)

    Returns:
        ID задачи GPT‑Pilot.
    """
    return pilot_create_app(spec_json)


def check_status(task_id: str) -> Optional[Dict[str, Any]]:
    """Получить статус задачи GPT‑Pilot."""
    return pilot_status(task_id)