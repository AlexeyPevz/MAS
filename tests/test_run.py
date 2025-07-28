from config_loader import LlmTiers
from run import pick_model


def test_pick_model_prefers_cheapest():
    tiers = LlmTiers(cheap=["c1"], standard=["s1"], premium=["p1"])
    assert pick_model(tiers) == "c1"


def test_pick_model_fallback():
    tiers = LlmTiers(cheap=[], standard=["s1"], premium=["p1"])
    assert pick_model(tiers) == "s1"


def test_pick_model_empty():
    tiers = LlmTiers(cheap=[], standard=[], premium=[])
    assert pick_model(tiers) == ""

