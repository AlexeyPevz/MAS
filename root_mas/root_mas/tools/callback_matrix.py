"""
callback_matrix.py
==================

Модуль определяет соответствие событий callback‑функциям. Агент
GroupChatManager может использовать этот словарь, чтобы маршрутизировать
запросы агентов. Матрица может быть расширена новыми событиями по
мере необходимости.
"""

from typing import Callable, Dict
from .callbacks import (
    route_instance_creation,
    route_workflow,
    route_missing_tool,
    retry_with_higher_tier_callback,
    budget_guard_callback,
    outgoing_to_telegram,
)


# Сопоставление имени события и соответствующей callback‑функции
CALLBACK_MATRIX: Dict[str, Callable[..., None]] = {
    "CREATE_INTERNAL": route_instance_creation,
    "CREATE_CLIENT": route_instance_creation,
    "CREATE_WORKFLOW": route_workflow,
    "MISSING_TOOL": route_missing_tool,
    "RETRY_WITH_HIGHER_TIER": retry_with_higher_tier_callback,
    "BUDGET_GUARD": budget_guard_callback,
    "OUTGOING_TO_TELEGRAM": outgoing_to_telegram,
}


def handle_event(event_name: str, *args, **kwargs) -> None:
    """Вызвать callback, ассоциированный с событием.

    Args:
        event_name: имя события
        *args: позиционные аргументы для callback
        **kwargs: именованные аргументы
    """
    callback = CALLBACK_MATRIX.get(event_name)
    if callback is None:
        raise ValueError(f"Неизвестный callback для события: {event_name}")
    callback(*args, **kwargs)
