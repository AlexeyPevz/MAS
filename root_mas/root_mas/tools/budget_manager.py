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
from datetime import datetime, timedelta
from typing import Dict


@dataclass
class BudgetManager:
    daily_limit: float  # дневной лимит стоимости (например, в долларах)
    spent_today: float = 0.0
    last_reset: datetime = field(default_factory=datetime.utcnow)

    def add_expense(self, amount: float) -> None:
        """Добавить расход к сегодняшнему счёту."""
        self._reset_if_needed()
        self.spent_today += amount

    def _reset_if_needed(self) -> None:
        if datetime.utcnow() - self.last_reset >= timedelta(days=1):
            self.spent_today = 0.0
            self.last_reset = datetime.utcnow()

    def needs_downgrade(self) -> bool:
        """Проверить, достигнут ли порог 80 % от дневного лимита."""
        self._reset_if_needed()
        return self.spent_today >= 0.8 * self.daily_limit