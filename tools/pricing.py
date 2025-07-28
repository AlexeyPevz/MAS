"""LLM pricing utilities.

This module loads model pricing from ``config/pricing.yaml`` and exposes helpers
for cost calculation.  Prices are defined *per 1 000 tokens* separately for
prompt (input) and completion (output).
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict
import functools

import yaml  # type: ignore

# ---------------------------------------------------------------------------
# Loading pricing config
# ---------------------------------------------------------------------------

_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "pricing.yaml"


@functools.lru_cache(maxsize=1)
def _load() -> Dict[str, Dict[str, float]]:
    with _CONFIG_PATH.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("models", {})


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def price_per_token(model: str, kind: str = "prompt") -> float:
    """Return price in USD *per single token*.

    Parameters
    ----------
    model: str
        Model name, e.g. ``"gpt-3.5-turbo"``
    kind: str
        Either ``"prompt"`` or ``"completion"``
    """
    models = _load()
    info = models.get(model)
    if not info or kind not in info:
        raise ValueError(f"No pricing info for {model}::{kind}")
    # convert price per 1K tokens to price per token
    return float(info[kind]) / 1000.0


def estimate_cost(model: str, prompt_tokens: int = 0, completion_tokens: int = 0) -> float:
    """Estimate cost for a single request in USD."""

    p_price = price_per_token(model, "prompt")
    c_price = price_per_token(model, "completion")
    return prompt_tokens * p_price + completion_tokens * c_price


def estimate_by_total(model: str, total_tokens: int) -> float:
    """If breakdown unknown assume half/half between prompt & completion."""

    half = total_tokens // 2
    return estimate_cost(model, prompt_tokens=half, completion_tokens=total_tokens - half)