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
import json
from pathlib import Path
import sys
from tools.logging_setup import configure_logging
sys.path.append(str(Path(__file__).resolve().parents[2]))
from config_loader import AgentsConfig


def load_agents_config(config_path: str = "config/agents.yaml") -> AgentsConfig:
    """Загрузить конфигурацию агентов из YAML."""

    path = Path(__file__).parent / config_path
    return AgentsConfig.from_yaml(path)


def echo_test(goal: str) -> None:
    """Вывести приветственное сообщение и заданную цель."""
    print("[Root GroupChat] Запуск MAS...")
    print(f"Цель: {goal}")
    agents_config = load_agents_config()
    print("Настроенные агенты:")
    for agent_name, data in agents_config.agents.items():
        print(f"  - {agent_name}: {data.role} (model: {data.model})")
    print("Система готова к работе. Реализуйте агентов с использованием AutoGen.")


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
    echo_test(args.goal)


if __name__ == "__main__":
    main()