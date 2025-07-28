"""Integration with GPT-Pilot service."""

from typing import Dict, Any
import logging
import os
import requests

logger = logging.getLogger(__name__)


def create_app(spec_json: Dict[str, Any]) -> str:
    """Request creation of a web application via GPT-Pilot.

    The GPT_PILOT_URL environment variable should contain the base URL of
    the GPT‑Pilot service.
    """
    base_url = os.getenv("GPT_PILOT_URL", "http://localhost:8001")
    logger.debug("Sending spec to GPT-Pilot: %s", spec_json)
    try:
        response = requests.post(f"{base_url}/api/v1/apps", json=spec_json, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get("id", "")
    except Exception as exc:
        logger.error("create_app request failed: %s", exc)
        return ""


def status(job_id: str) -> Dict[str, Any]:
    """Check the status of a previously created GPT‑Pilot job."""
    base_url = os.getenv("GPT_PILOT_URL", "http://localhost:8001")
    logger.debug("Checking status for job %s", job_id)
    try:
        response = requests.get(f"{base_url}/api/v1/apps/{job_id}", timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as exc:
        logger.error("status request failed: %s", exc)
        return {"status": "error", "detail": str(exc)}
