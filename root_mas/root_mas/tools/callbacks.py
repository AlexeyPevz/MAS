"""
callbacks.py
============

Заготовка для callback‑функций, используемых многоагентной системой.
Callbacks вызываются агентами в ответ на определённые события (например,
создание нового инстанса, генерация workflow, необходимость повысить
уровень LLM и т. п.). Реализация каждой callback зависит от
интеграционных механизмов и должна быть дополнена.
"""

from typing import Any, Dict, Optional
import logging

from .llm_selector import retry_with_higher_tier


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
    # TODO: вызвать Instance‑Factory и обновить config/instances.yaml
    print("[Instance‑Factory] Развертывание нового MAS инстанса... (заглушка)")


def route_workflow(params: Dict[str, Any]) -> None:
    """Обработать запрос на создание workflow.

    Args:
        params: словарь со спецификацией workflow
    """
    logging.info(f"[callback] route_workflow called with {params}")
    # TODO: вызов WF‑Builder, проверка Fact‑Checker и отправка в n8n via n8n_client
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
    # TODO: Агент Prompt‑Builder должен создать промпт, а затем Agent‑Builder создать инструмент
    print(f"[Prompt‑Builder] Требуется создать новый инструмент: {tool_name} (заглушка)")


def retry_with_higher_tier_callback(current_tier: str, attempt: int) -> None:
    """Обработать плохой результат LLM и повысить уровень модели.

    Args:
        current_tier: текущий уровень модели
        attempt: номер попытки
    """
    new_tier, model = retry_with_higher_tier(current_tier, attempt)
    logging.info(
        f"[callback] retry_with_higher_tier from {current_tier} attempt {attempt} -> {new_tier} model {model}"
    )
    print(f"[Model‑Selector] Повышаем уровень с {current_tier} до {new_tier}: {model}")


def outgoing_to_telegram(message: str) -> None:
    """Отправить сообщение пользователю через Telegram.

    Args:
        message: текст ответа

    Note:
        В рабочей системе здесь используется Telegram‑бот (см. telegram_voice.py),
        который пересылает ответы пользователю. В заглушке сообщение печатается в консоль.
    """
    logging.info(f"[callback] outgoing_to_telegram: {message}")
    # TODO: интеграция с Telegram через TelegramVoiceBot
    print(f"[TG] {message}")