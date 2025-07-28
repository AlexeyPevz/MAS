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
from typing import Dict, Any
from tools.logging_setup import configure_logging


def load_agents_config(config_path: str = "config/agents.yaml") -> Dict[str, Any]:
    """Загрузить конфигурацию агентов из YAML.

    Args:
        config_path: путь к файлу YAML

    Returns:
        Словарь с настройками агентов.
    """
    try:
        import yaml  # type: ignore
    except ImportError:
        raise RuntimeError("Для чтения YAML требуется библиотека PyYAML. Установите её: pip install pyyaml")
    path = Path(__file__).parent / config_path
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def echo_test(goal: str) -> None:
    """Вывести приветственное сообщение и заданную цель."""
    print("[Root GroupChat] Запуск MAS...")
    print(f"Цель: {goal}")
    agents_config = load_agents_config()
    print("Настроенные агенты:")
    for agent_name, data in agents_config.get("agents", {}).items():
        role = data.get("role")
        model = data.get("model")
        print(f"  - {agent_name}: {role} (model tier: {model})")
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