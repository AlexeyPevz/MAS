"""
callback_matrix.py
==================

Модуль определяет соответствие событий callback‑функциям. Агент
GroupChatManager может использовать этот словарь, чтобы маршрутизировать
запросы агентов. Матрица может быть расширена новыми событиями по
мере необходимости.
"""

from typing import Callable, Dict

# Сопоставление имени события и имени callback‑функции в tools.callbacks
CALLBACK_NAMES: Dict[str, str] = {
    "CREATE_INTERNAL": "route_instance_creation",
    "CREATE_CLIENT": "route_instance_creation",
    "CREATE_WORKFLOW": "route_workflow",
    "MISSING_TOOL": "route_missing_tool",
    "RETRY_WITH_HIGHER_TIER": "retry_with_higher_tier_callback",
    "BUDGET_GUARD": "budget_guard_callback",
    "OUTGOING_TO_TELEGRAM": "outgoing_to_telegram",
    "RESEARCH_TASK": "research_validation_cycle",
    # Новые события для динамического расширения системы
    "CREATE_AGENT": "create_agent_callback",
    "REGISTER_TOOL": "register_tool_callback",
}


def handle_event(event_name: str, *args, **kwargs) -> None:
    """Вызвать callback, ассоциированный с событием.

    Динамически извлекает функцию из модуля tools.callbacks, чтобы
    поддерживать monkeypatch в тестах.
    """
    from tools import callbacks  # импорт внутри для актуальных ссылок

    func_name = CALLBACK_NAMES.get(event_name)
    if not func_name:
        raise ValueError(f"Неизвестный callback для события: {event_name}")

    callback: Callable[..., None] | None = getattr(callbacks, func_name, None)
    if callback is None:
        raise ValueError(f"Callback '{func_name}' не найден в tools.callbacks")

    callback(*args, **kwargs)
