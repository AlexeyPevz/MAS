"""Minimal client for the n8n REST API."""

from typing import Any, Dict, Optional
import logging
import os
import requests

logger = logging.getLogger(__name__)


class N8nClient:
    """Wrapper around the n8n HTTP API."""

    def __init__(self, base_url: str, api_key: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def _headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "X-N8n-Api-Key": self.api_key,
        }

    def create_workflow(self, workflow_json: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new workflow."""
        url = f"{self.base_url}/api/v1/workflows"
        logger.debug("Creating workflow at %s", url)
        try:
            resp = requests.post(url, headers=self._headers(), json=workflow_json, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:  # pragma: no cover - network
            logger.error("create_workflow failed: %s", exc)
            return None

    def activate_workflow(self, workflow_id: str) -> bool:
        """Activate an existing workflow by id."""
        url = f"{self.base_url}/api/v1/workflows/{workflow_id}/activate"
        logger.debug("Activating workflow %s", workflow_id)
        try:
            resp = requests.post(url, headers=self._headers(), timeout=15)
            resp.raise_for_status()
            return True
        except Exception as exc:  # pragma: no cover - network
            logger.error("activate_workflow failed: %s", exc)
            return False
