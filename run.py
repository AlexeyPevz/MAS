"""
run.py
======

Точка входа для запуска Root GroupChat. Этот скрипт анализирует аргументы
командной строки, инициализирует агентов и запускает эхо‑тест.

Для полноценной работы требуется установленная библиотека AutoGen и
реализация агентов согласно конфигурации. В данной версии реализован
упрощённый механизм, выводящий в консоль цель и демонстрирующий
структуру агентов.
"""

import argparse
from pathlib import Path


from tools.logging_setup import configure_logging

from config_loader import AgentsConfig, LlmTiers, load_dataclass


def load_agents_config(config_path: str = "config/agents.yaml") -> AgentsConfig:
    """Загрузить конфигурацию агентов из YAML."""

    path = Path(__file__).parent / config_path
    return AgentsConfig.from_yaml(path)


def load_llm_tiers(config_path: Path) -> LlmTiers:
    """Load the LLM tier configuration from YAML into a dataclass."""

    return load_dataclass(config_path, LlmTiers)


def pick_model(tiers: LlmTiers) -> str:
    """Select the first available model from the cheapest tier."""

    for tier in ["cheap", "standard", "premium"]:
        models = getattr(tiers, tier)
        if models:
            return models[0]
    return ""


def start_groupchat(goal: str) -> None:
    """Инициализировать агентов и запустить корневой GroupChat."""

    from agents.core_agents import create_agents
    from tools.groupchat_manager import RootGroupChatManager

    print("[Root GroupChat] Запуск MAS...")
    print(f"Цель: {goal}")

    agents_cfg = load_agents_config()
    agents = create_agents(agents_cfg)

    routing = {
        "communicator": ["meta"],
        "meta": ["coordination"],
    }

    RootGroupChatManager(agents, routing)  # инициализация чата

    print("Настроенные агенты:")
    for name, data in agents_cfg.agents.items():
        print(f"  - {name}: {data.role} (model: {data.model})")
    print("Группа и агенты инициализированы. Реализуйте бизнес-логику в следующих спринтах.")


def main() -> None:
    # Настроить логирование
    configure_logging()
    parser = argparse.ArgumentParser(description="Запуск Root MAS GroupChat")
    parser.add_argument(
        "--goal",
        type=str,
        default="echo",
        help="Цель для корневого агента (например, 'echo' для тестирования)",
    )
    args = parser.parse_args()
    start_groupchat(args.goal)


if __name__ == "__main__":
    main()