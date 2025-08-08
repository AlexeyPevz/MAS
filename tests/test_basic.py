from tools.budget_manager import BudgetManager
from tools.llm_selector import pick_config
from tools.security import get_secret
from tools.llm_selector import retry_with_higher_tier


def test_budget_manager_needs_downgrade() -> None:
    manager = BudgetManager(daily_limit=100.0)
    manager.add_expense(50)
    assert not manager.needs_downgrade()
    manager.add_expense(45)
    assert manager.needs_downgrade()


def test_budget_manager_add_usage() -> None:
    manager = BudgetManager(daily_limit=1.0)  # $1 daily limit
    cost = manager.add_usage("gpt-3.5-turbo", prompt_tokens=500, completion_tokens=500)
    # Для gpt-3.5-turbo это 0.25$ + 0.5$ = 0.75$
    assert round(cost, 3) == 0.75
    assert not manager.needs_downgrade()


def test_llm_selector_pick_config() -> None:
    tier, model = pick_config("cheap", attempt=1)
    # В конфиге во втором слоте cheap → llama3-8b-instruct
    assert tier == "cheap"
    assert model["name"] in {"llama3-8b-instruct", "llama3-8b-instruct"}


def test_retry_with_budget_guard() -> None:
    manager = BudgetManager(daily_limit=0.5)
    # расходуем бюджет, чтобы needs_downgrade=True
    manager.add_expense(0.5)
    tier, _m = retry_with_higher_tier("cheap", attempt=0, manager=manager)
    # Должно остаться на cheap из-за исчерпанного бюджета
    assert tier == "cheap"


def test_security_get_secret_env(monkeypatch) -> None:
    monkeypatch.setenv("MY_TEST_SECRET", "42")
    assert get_secret("MY_TEST_SECRET") == "42"
    # cleanup handled by monkeypatch