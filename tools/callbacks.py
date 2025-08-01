"""
callbacks.py
============

Заготовка для callback‑функций, используемых многоагентной системой.
Callbacks вызываются агентами в ответ на определённые события (например,
создание нового инстанса, генерация workflow, необходимость повысить
уровень LLM и т. п.). Реализация каждой callback зависит от
интеграционных механизмов и должна быть дополнена.
"""

from typing import Any, Dict, Optional, Callable
import logging

from .budget_manager import BudgetManager
from .llm_selector import retry_with_higher_tier, downgrade_with_budget

# Простой экземпляр менеджера бюджета
budget_manager = BudgetManager(daily_limit=100.0)

# Хранилище функции отправки сообщений в Telegram.
_telegram_sender: Optional[Callable[[str], None]] = None


def register_telegram_sender(func: Callable[[str], None]) -> None:
    """Register a callable used to send messages to Telegram."""

    global _telegram_sender
    _telegram_sender = func


def route_instance_creation(params: Dict[str, Any]) -> None:
    """Обработать запрос на создание нового инстанса MAS.

    Args:
        params: параметры, необходимые для развертывания (тип, директория, env).

    Note:
        Здесь следует вызвать агент Instance‑Factory (deploy_instance) для
        развёртывания внутреннего или клиентского инстанса. После успешного
        развертывания информация должна быть добавлена в config/instances.yaml.
    """
    logging.info(f"[callback] route_instance_creation called with {params}")
    instance_type = params.get("type", "internal")
    env: Dict[str, str] = params.get("env", {})
    auto = params.get("auto", True)
    try:
        from .instance_factory import auto_deploy_instance, deploy_instance

        if auto:
            name = auto_deploy_instance(instance_type, env)
        else:
            directory = params.get("directory", f"deploy/{instance_type}")
            name = params.get("name", instance_type)
            deploy_instance(directory, env, name, instance_type)

        print(f"[Instance-Factory] Инстанс {name} запущен")
    except Exception as exc:  # pragma: no cover - optional integration
        logging.error("[callback] instance creation failed: %s", exc)
        print(f"[Instance-Factory] Ошибка развёртывания: {exc}")


def route_workflow(params: Dict[str, Any]) -> None:
    """Обработать запрос на создание workflow.

    Args:
        params: словарь со спецификацией workflow
    """
    logging.info(f"[callback] route_workflow called with {params}")
    spec = params.get("spec", "")
    n8n_url = params.get("n8n_url") or "http://localhost:5678"
    api_key = params.get("api_key") or ""
    try:
        from .wf_builder import create_workflow
        result = create_workflow(spec, n8n_url, api_key)
        print(f"[WF‑Builder] Workflow создан: {result}")
    except Exception as exc:
        print(f"[WF‑Builder] Ошибка генерации workflow: {exc}")


def route_missing_tool(tool_name: str) -> None:
    """Обработать отсутствие требуемого инструмента.

    Args:
        tool_name: имя инструмента, который отсутствует
    """
    logging.info(f"[callback] route_missing_tool called for tool: {tool_name}")
    try:
        from .prompt_builder import create_agent_prompt
        # Временно отключаем использование autogen.agentchat
        # TODO: Мигрировать на новый API v0.4
        # from autogen import agentchat

        prompt_text = f"Placeholder prompt for tool {tool_name}"
        create_agent_prompt(tool_name, prompt_text)
        # agentchat.build_from_spec({"name": tool_name})  # type: ignore[arg-type]
        print(f"[Agent-Builder] Инструмент {tool_name} создан")
    except Exception as exc:  # pragma: no cover - optional integration
        logging.error("[callback] tool generation failed: %s", exc)
        print(f"[Prompt-Builder] Не удалось создать инструмент {tool_name}: {exc}")


def retry_with_higher_tier_callback(current_tier: str, attempt: int) -> None:
    """Обработать плохой результат LLM и повысить уровень модели.

    Args:
        current_tier: текущий уровень модели
        attempt: номер попытки
    """
    new_tier, model = retry_with_higher_tier(current_tier, attempt, budget_manager)
    logging.info(
        f"[callback] retry_with_higher_tier from {current_tier} attempt {attempt} -> {new_tier} model {model}"
    )
    print(f"[Model‑Selector] Повышаем уровень с {current_tier} до {new_tier}: {model}")


def budget_guard_callback(current_tier: str, attempt: int = 0) -> None:
    """Проверить бюджет и при необходимости понизить уровень модели."""
    new_tier, model = downgrade_with_budget(current_tier, budget_manager, attempt)
    if new_tier != current_tier:
        logging.info(
            f"[callback] budget_guard downgrade {current_tier} -> {new_tier} model {model}"
        )
        print(f"[BudgetGuard] Лимит бюджета достигнут, переходим на {new_tier}: {model}")
    else:
        logging.info("[callback] budget_guard budget within limits")


def outgoing_to_telegram(message: str) -> None:
    """Отправить сообщение пользователю через Telegram.

    Args:
        message: текст ответа

    Note:
        В рабочей системе здесь используется Telegram‑бот (см. modern_telegram_bot.py),
        который пересылает ответы пользователю. В заглушке сообщение печатается в консоль.
    """
    logging.info(f"[callback] outgoing_to_telegram: {message}")
    if _telegram_sender is not None:
        _telegram_sender(message)
    else:
        print(f"[TG] {message}")


def research_validation_cycle(query: str) -> None:
    """Выполнить цикл исследование → валидация."""

    logging.info("[callback] research_validation_cycle: %s", query)
    from .researcher import search_and_store

    results = search_and_store(query)
    if results:
        print(f"[ResearchFlow] сохранено {len(results)} результатов по запросу '{query}'")
    else:
        print(f"[ResearchFlow] не удалось подтвердить источники для '{query}'")
