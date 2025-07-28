import tools.llm_selector as ls
from tools.budget_manager import BudgetManager


def test_pick_config_downgrades_with_budget(monkeypatch):
    data = {
        "tiers": {
            "cheap": [{"name": "c1"}],
            "standard": [{"name": "s1"}],
        }
    }
    monkeypatch.setattr(ls, "load_tiers", lambda config_path=None: data)
    manager = BudgetManager(daily_limit=10, spent_today=9)
    tier, model = ls.pick_config("standard", manager=manager)
    assert tier == "cheap"
    assert model["name"] == "c1"


def test_pick_config_no_downgrade(monkeypatch):
    data = {"tiers": {"cheap": [{"name": "c1"}], "standard": [{"name": "s1"}]}}
    monkeypatch.setattr(ls, "load_tiers", lambda config_path=None: data)
    manager = BudgetManager(daily_limit=10, spent_today=1)
    tier, model = ls.pick_config("standard", manager=manager)
    assert tier == "standard"
    assert model["name"] == "s1"

