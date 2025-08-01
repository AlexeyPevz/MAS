"""Logging helpers for AutoGen Studio integration.

This module records chat messages in a JSON Lines file. The log can then
be uploaded to AutoGen Studio to visualise the dialog graph.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterable

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    requests = None  # type: ignore

# AutoGen Studio configuration
STUDIO_URL = os.getenv("AUTOGEN_STUDIO_URL", "http://localhost:8081")
STUDIO_API_KEY = os.getenv("AUTOGEN_STUDIO_API_KEY", "")

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


def send_to_studio(url: str = None, log_file: Path | None = None) -> bool:
    """Send the Studio log file to AutoGen Studio.

    Returns ``True`` on success, otherwise ``False``.
    """

    if requests is None:
        raise RuntimeError("requests package is required for sending logs")

    upload_url = url or f"{STUDIO_URL}/api/v1/logs/upload"
    lf = log_file or LOG_PATH
    
    headers = {}
    if STUDIO_API_KEY:
        headers["Authorization"] = f"Bearer {STUDIO_API_KEY}"
    
    try:
        with lf.open("rb") as f:
            req_kwargs = {
                "files": {"file": (lf.name, f, "application/jsonl")},
                "timeout": 10,
            }
            if headers:
                req_kwargs["headers"] = headers
            response = requests.post(upload_url, **req_kwargs)
        response.raise_for_status()
        print(f"[studio_logger] ✅ Logs sent to AutoGen Studio: {upload_url}")
        return True
    except Exception as exc:  # pragma: no cover - network errors
        print(f"[studio_logger] ❌ Failed to send logs: {exc}")
        return False


def auto_upload_to_studio() -> bool:
    """Automatically upload logs to AutoGen Studio if configured."""
    if STUDIO_URL and STUDIO_API_KEY and LOG_PATH.exists():
        return send_to_studio()
    return False
