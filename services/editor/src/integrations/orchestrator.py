"""Integration with the Helios Orchestrator service."""

import logging
from typing import Any

import httpx

from ..core.config import settings

logger = logging.getLogger(__name__)


class OrchestratorClient:
    """Client for communicating with the Helios Orchestrator."""

    def __init__(self):
        """Initialize the orchestrator client."""
        self.base_url = settings.ORCHESTRATOR_URL
        self.timeout = 30.0

    async def register_service(self) -> bool:
        """Register this editor service with the orchestrator."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/services/register",
                    json={
                        "service_name": "editor",
                        "service_type": "text_editing",
                        "version": "1.0.0",
                        "endpoints": {
                            "edit": "/edit",
                            "analyze": "/analyze",
                            "batch_edit": "/edit/batch",
                            "suggestions": "/edit/suggestions",
                            "apply_suggestions": "/edit/apply",
                            "version_history": "/versions/{session_id}",
                            "compare_versions": "/versions/{session_id}/compare",
                            "revert": "/versions/{session_id}/revert",
                            "health": "/health",
                        },
                        "capabilities": [
                            "grammar_checking",
                            "style_analysis",
                            "content_enhancement",
                            "version_control",
                            "collaborative_editing",
                        ],
                    },
                )
                response.raise_for_status()
                logger.info("Successfully registered with orchestrator")
                return True

        except Exception as e:
            logger.error(f"Failed to register with orchestrator: {e}")
            return False

    async def send_status_update(
        self, status: str, details: dict[str, Any] | None = None
    ) -> bool:
        """Send status update to orchestrator."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload = {
                    "service_name": "editor",
                    "status": status,
                    "timestamp": details.get("timestamp") if details else None,
                }

                if details:
                    payload.update(details)

                response = await client.post(
                    f"{self.base_url}/services/status", json=payload
                )
                response.raise_for_status()
                return True

        except Exception as e:
            logger.error(f"Failed to send status update: {e}")
            return False

    async def get_session_context(self, session_id: str) -> dict[str, Any] | None:
        """Get session context from orchestrator."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/sessions/{session_id}/context"
                )
                response.raise_for_status()
                return response.json()

        except Exception as e:
            logger.error(f"Failed to get session context: {e}")
            return None

    async def notify_edit_completion(
        self, session_id: str, edit_summary: dict[str, Any]
    ) -> bool:
        """Notify orchestrator of completed edit."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/sessions/{session_id}/events",
                    json={
                        "event_type": "edit_completed",
                        "service": "editor",
                        "data": edit_summary,
                    },
                )
                response.raise_for_status()
                return True

        except Exception as e:
            logger.error(f"Failed to notify edit completion: {e}")
            return False

    async def request_ai_assistance(
        self, request_type: str, context: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Request AI assistance from orchestrator's LLM client."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/ai/assist",
                    json={
                        "service": "editor",
                        "request_type": request_type,
                        "context": context,
                    },
                )
                response.raise_for_status()
                return response.json()

        except Exception as e:
            logger.error(f"Failed to request AI assistance: {e}")
            return None
