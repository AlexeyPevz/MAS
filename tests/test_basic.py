from tools.budget_manager import BudgetManager
from tools.llm_selector import pick_config
from tools.security import get_secret


def test_budget_manager_needs_downgrade() -> None:
    manager = BudgetManager(daily_limit=100.0)
    manager.add_expense(50)
    assert not manager.needs_downgrade()
    manager.add_expense(45)
    assert manager.needs_downgrade()


def test_llm_selector_pick_config() -> None:
    tier, model = pick_config("cheap", attempt=1)
    # В конфиге во втором слоте cheap → llama3-8b-instruct
    assert tier == "cheap"
    assert model["name"] in {"llama3-8b-instruct", "llama3-8b-instruct"}


def test_security_get_secret_env(monkeypatch) -> None:
    monkeypatch.setenv("MY_TEST_SECRET", "42")
    assert get_secret("MY_TEST_SECRET") == "42"
    # cleanup handled by monkeypatch