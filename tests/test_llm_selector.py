import sys
from pathlib import Path

# add root_mas package to sys.path
sys.path.append(str(Path(__file__).resolve().parents[1] / 'root_mas' / 'root_mas'))

from tools.llm_selector import pick_config, retry_with_higher_tier


def test_pick_config_first_model():
    tier, model = pick_config('cheap', attempt=0)
    assert tier == 'cheap'
    assert model['name'] == 'gpt-3.5-turbo'


def test_pick_config_second_attempt():
    tier, model = pick_config('cheap', attempt=1)
    assert model['name'] == 'llama3-8b-instruct'


def test_retry_with_higher_tier():
    tier, model = retry_with_higher_tier('cheap', 0)
    assert tier == 'standard'
    assert model['name'] == 'gpt-4o'


def test_retry_max_retries():
    tier, model = retry_with_higher_tier('cheap', 3)
    assert tier == 'cheap'
    assert model['name'] == 'llama3-8b-instruct'
