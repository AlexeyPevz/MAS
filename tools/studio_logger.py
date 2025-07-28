"""Logging helpers for AutoGen Studio integration.

This module records chat messages in a JSON Lines file. The log can then
be uploaded to AutoGen Studio to visualise the dialog graph.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    requests = None  # type: ignore

# Default log file used by the helpers
LOG_PATH = Path("logs") / "studio.jsonl"


def log_interaction(sender: str, receivers: Iterable[str], message: dict) -> None:
    """Append a chat message to the Studio log."""

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {"sender": sender, "receivers": list(receivers), "message": message}
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def export_logs(dest: str | Path) -> Path:
    """Copy the Studio log to ``dest`` and return the new path."""

    dest_path = Path(dest)
    dest_path.write_text(LOG_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    return dest_path


def send_to_studio(url: str, log_file: Path | None = None) -> bool:
    """Send the Studio log file to the given URL.

    Returns ``True`` on success, otherwise ``False``.
    """

    if requests is None:
        raise RuntimeError("requests package is required for sending logs")

    lf = log_file or LOG_PATH
    try:
        with lf.open("rb") as f:
            response = requests.post(
                url,
                files={"file": (lf.name, f, "text/plain")},
                timeout=10,
            )
        response.raise_for_status()
        return True
    except Exception as exc:  # pragma: no cover - network errors
        print(f"[studio_logger] failed to send logs: {exc}")
        return False
