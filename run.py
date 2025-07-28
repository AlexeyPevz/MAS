"""Entry point for launching the Root‑MAS platform.

This script demonstrates the tiered language model cascade by selecting an
appropriate model based on the cheapest tier available.  In a full
implementation this would instantiate a root group chat and run agents.  For
sprint 0 the script simply prints which model would be used to handle the
user's goal.
"""

import argparse
import sys
from pathlib import Path


from config_loader import LlmTiers, load_dataclass


def load_llm_tiers(config_path: Path) -> LlmTiers:
    """Load the LLM tier configuration from YAML into a dataclass."""

    return load_dataclass(config_path, LlmTiers)


def pick_model(tiers: LlmTiers) -> str:
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
        models = getattr(tiers, tier)
        if models:
            return models[0]
    return ""


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Root‑MAS echo test")
    parser.add_argument(
        '--goal', type=str, default="echo", help="High‑level goal for the test"
    )
    args = parser.parse_args()

    config_path = Path(__file__).parent / 'llm_tiers.yaml'
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