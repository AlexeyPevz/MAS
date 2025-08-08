"""
budget_manager.py
=================

Модуль для отслеживания расхода бюджета на LLM и регулирования уровня
моделей. Функция `check_budget` проверяет, достигнут ли порог
использования (например, 80 % дневного лимита), и может сигнализировать
о необходимости понизить tier. Реализация расхода средств должна
основываться на фактической стоимости запросов.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict

# cost estimation
from .pricing import estimate_cost
from .budget_storage import record_expense


@dataclass
class BudgetManager:
    daily_limit: float  # дневной лимит стоимости (например, в долларах)
    spent_today: float = 0.0
    last_reset: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def add_expense(self, amount: float) -> None:
        """Добавить расход к сегодняшнему счёту."""
        self._reset_if_needed()
        self.spent_today += amount
        record_expense(datetime.now(timezone.utc), amount)

    # ------------------------------------------------------------------
    # High-level helper
    # ------------------------------------------------------------------

    def add_usage(self, model: str, prompt_tokens: int, completion_tokens: int = 0) -> float:
        """Учитыть использование токенов и вернуть рассчитанную стоимость.

        Это обёртка над :func:`estimate_cost`.  Возвращённое значение (USD)
        автоматически добавляется к ежедневному счётчику.
        """

        cost = estimate_cost(model, prompt_tokens, completion_tokens)
        self.add_expense(cost)
        return cost

    def _reset_if_needed(self) -> None:
        if datetime.now(timezone.utc) - self.last_reset >= timedelta(days=1):
            self.spent_today = 0.0
            self.last_reset = datetime.now(timezone.utc)

    def needs_downgrade(self) -> bool:
        """Проверить, достигнут ли порог 80 % от дневного лимита."""
        self._reset_if_needed()
        return self.spent_today >= 0.8 * self.daily_limit
