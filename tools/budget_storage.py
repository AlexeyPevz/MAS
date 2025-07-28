"""Budget persistence helpers.

This module provides a thin abstraction for storing cost usage events.  The
primary implementation uses Redis (fast, simple aggregation).  If Redis is not
available, events are appended to a local CSV file under ``data/budget.csv``.

Only *aggregated* spent-per-day values are stored; it is not intended for
per-request logs.
"""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Optional

from memory.redis_store import RedisStore

# ---------------------------------------------------------------------------
# Backend selection
# ---------------------------------------------------------------------------

_REDIS: Optional[RedisStore]
try:
    _REDIS = RedisStore()
except Exception:  # pragma: no cover – redis not installed or connection error
    _REDIS = None

_CSV_PATH = Path("data") / "budget.csv"
_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def _key_for(date: datetime) -> str:
    return f"budget:{date.strftime('%Y%m%d')}"


def record_expense(date: datetime, amount: float) -> None:
    """Add *amount* (USD) to the aggregated value for the given date."""

    if _REDIS is not None:
        key = _key_for(date)
        try:
            _REDIS.client.incrbyfloat(key, amount)
            # set TTL = 90 days to prevent unbounded growth
            _REDIS.client.expire(key, 90 * 24 * 3600)
            return
        except Exception:  # pragma: no cover – network errors
            pass  # fallback to CSV

    # CSV fallback (append-only, one line per update)
    with _CSV_PATH.open("a", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([date.isoformat(), f"{amount:.6f}"])