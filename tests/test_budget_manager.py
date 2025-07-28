import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / 'root_mas' / 'root_mas'))

from tools.budget_manager import BudgetManager


def test_budget_manager_threshold():
    mgr = BudgetManager(daily_limit=100)
    mgr.add_expense(50)
    assert not mgr.needs_downgrade()
    mgr.add_expense(35)
    assert mgr.needs_downgrade()
