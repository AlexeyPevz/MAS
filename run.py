"""Entry point for launching the Root‑MAS platform.

This script demonstrates the tiered language model cascade by selecting an
appropriate model based on the cheapest tier available.  In a full
implementation this would instantiate a root group chat and run agents.  For
sprint 0 the script simply prints which model would be used to handle the
user's goal.
"""

import argparse
import sys
import yaml
from pathlib import Path
from typing import Dict, List


def load_llm_tiers(config_path: Path) -> Dict[str, List[str]]:
    """Load the LLM tier configuration from YAML.

    Args:
        config_path: Path to the `llm_tiers.yaml` file.

    Returns:
        A dictionary mapping tier names (cheap, standard, premium) to lists of
        model identifiers.
    """
    with config_path.open('r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    # configuration may either provide tiers at the top level or under the
    # ``tiers`` key; support both for compatibility
    tiers = data.get('tiers', data)
    return {
        'cheap': tiers.get('cheap', []),
        'standard': tiers.get('standard', []),
        'premium': tiers.get('premium', []),
    }


def pick_model(tiers: Dict[str, List[str]]) -> str:
    """Pick the first available model from the lowest tier.

    The selection logic iterates through the tiers in order of increasing
    cost (cheap → standard → premium) and returns the first model found.

    Args:
        tiers: A dictionary as returned by `load_llm_tiers`.

    Returns:
        The identifier of the chosen model, or an empty string if no models
        are configured.
    """
    for tier in ['cheap', 'standard', 'premium']:
        models = tiers.get(tier, [])
        if models:
            return models[0]
    return ""


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Root‑MAS echo test")
    parser.add_argument(
        '--goal', type=str, default="echo", help="High‑level goal for the test"
    )
    args = parser.parse_args()

    # Load the central configuration shipped under ``root_mas/root_mas``.  All
    # YAML files live in that directory so we keep the lookup path explicit
    # relative to this script.
    config_path = (
        Path(__file__).parent
        / 'root_mas'
        / 'root_mas'
        / 'config'
        / 'llm_tiers.yaml'
    )
    tiers = load_llm_tiers(config_path)
    model = pick_model(tiers)
    if not model:
        print("No models configured in llm_tiers.yaml", file=sys.stderr)
        sys.exit(1)

    print(f"Goal: {args.goal}")
    print(f"Selected model: {model}")
    print(
        "This is a stub execution.  In a full implementation the selected model would be used "
        "to execute the task via a ConversableAgent."
    )


if __name__ == '__main__':
    main()