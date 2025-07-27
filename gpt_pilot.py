"""Integration stubs for GPT‑Pilot.

GPT‑Pilot is used to generate full‑stack web applications from high‑level
specifications.  This module provides placeholder functions for sending a
request to GPT‑Pilot and checking the status of a generation job.
"""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def create_app(spec_json: Dict[str, Any]) -> str:
    """Request the creation of a new web application.

    Args:
        spec_json: A JSON‑serialisable object describing the desired web app.

    Returns:
        A string representing a job ID or URL for tracking the generation
        status.
    """
    logger.debug("Sending spec to GPT‑Pilot: %s", spec_json)
    raise NotImplementedError("GPT‑Pilot integration not implemented")


def status(job_id: str) -> Dict[str, Any]:
    """Check the status of a previously submitted GPT‑Pilot job."""
    logger.debug("Checking status for job %s", job_id)
    raise NotImplementedError("GPT‑Pilot integration not implemented")