"""
llm_selector.py
===============

Реализация функций выбора LLM на основе каскада, определённого в
config/llm_tiers.yaml. Агент Model‑Selector использует `pick_config` для
получения следующей модели, а callback `retry_with_higher_tier` повышает
уровень модели при ошибке или недостаточном качестве.
"""

from pathlib import Path
from typing import Any, Dict, List, Tuple
import logging

try:
    import yaml  # type: ignore
except ImportError:
    raise RuntimeError("Для работы llm_selector требуется библиотека PyYAML. Установите её: pip install pyyaml")


def load_tiers(config_path: str = "config/llm_tiers.yaml") -> Dict[str, Any]:
    """Загрузить YAML‑конфигурацию уровней LLM.

    Returns:
        Словарь с данными конфигурации.
    """
    path = Path(__file__).parent.parent / config_path
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data


def pick_config(tier: str, attempt: int = 0) -> Tuple[str, Dict[str, str]]:
    """Получить конфигурацию модели из указанного уровня.

    Args:
        tier: уровень (cheap, standard, premium)
        attempt: номер попытки (0 — первая, 1 — вторая и т.д.), влияет на индекс в списке моделей

    Returns:
        Кортеж (tier_name, model_dict), где `model_dict` содержит имя модели и провайдера.

    Note:
        Если количество попыток превышает список моделей, возвращается последняя модель уровня.
    """
    data = load_tiers()
    tiers = data.get("tiers", {})
    models: List[Dict[str, str]] = tiers.get(tier, [])
    if not models:
        raise ValueError(f"Неизвестный tier: {tier}")
    index = min(attempt, len(models) - 1)
    return tier, models[index]


def next_tier(current_tier: str) -> str:
    """Получить следующий уровень после текущего для повышения каскада."""
    order = ["cheap", "standard", "premium"]
    if current_tier not in order:
        raise ValueError(f"Неизвестный tier: {current_tier}")
    idx = order.index(current_tier)
    return order[min(idx + 1, len(order) - 1)]


def retry_with_higher_tier(current_tier: str, attempt: int) -> Tuple[str, Dict[str, str]]:
    """Повысить уровень модели при ошибке и вернуть новую конфигурацию.

    Args:
        current_tier: текущий уровень модели
        attempt: номер попытки (увеличивается при каждом вызове)

    Returns:
        Кортеж (tier_name, model_dict) для следующей попытки.

    Note:
        Если достигнут максимальный уровень, возвращается последняя модель premium.
    """
    config = load_tiers()
    max_retries = config.get("max_retries", 3)
    # Если количество попыток превышает max_retries, остаёмся на текущем уровне
    if attempt >= max_retries:
        logging.warning("Достигнут лимит повторных попыток; остаёмся на текущем уровне.")
        return pick_config(current_tier, attempt=attempt)
    # Иначе повышаем уровень
    next_level = next_tier(current_tier)
    return pick_config(next_level, attempt=0)


if __name__ == "__main__":
    # Демонстрация работы каскада
    tier, model = pick_config("cheap", attempt=0)
    print(f"Выбрана модель для cheap: {model}")
    # Повышаем до следующего уровня
    next_t, next_model = retry_with_higher_tier(tier, 0)
    print(f"Повышение до {next_t}, модель: {next_model}")