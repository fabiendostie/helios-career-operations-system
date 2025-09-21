"""Integration client for STRATEGIST service."""

import logging
import aiohttp
from typing import Dict, Any, Optional
from ..core.config import settings

logger = logging.getLogger(__name__)


class StrategistClient:
    """HTTP client for communicating with STRATEGIST service."""

    def __init__(self):
        """Initialize strategist client."""
        self.base_url = getattr(settings, 'strategist_url', 'http://localhost:8002')
        self.timeout = aiohttp.ClientTimeout(total=30)

    async def generate_career_paths(
        self,
        profile_data: Dict[str, Any],
        session_id: str
    ) -> Dict[str, Any]:
        """Generate career paths based on profile data.

        Args:
            profile_data: Master career database from Profile Ingestor
            session_id: Session identifier

        Returns:
            Career path generation results
        """
        logger.info(f"Generating career paths for session {session_id}")

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                url = f"{self.base_url}/api/v1/discover"

                payload = {
                    "profile_data": profile_data,
                    "session_id": session_id,
                    "preferences": {
                        "max_paths": 5,
                        "include_analysis": True,
                        "difficulty_filter": "all"
                    }
                }

                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Successfully generated career paths for session {session_id}")
                        return {
                            "success": True,
                            "career_paths": result.get("paths", {}),
                            "analysis": result.get("analysis", {})
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"Strategist API error {response.status}: {error_text}")
                        return {
                            "success": False,
                            "error": f"API error {response.status}: {error_text}"
                        }

        except aiohttp.ClientError as e:
            logger.error(f"HTTP client error calling Strategist: {str(e)}")
            return {
                "success": False,
                "error": f"HTTP client error: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Unexpected error calling Strategist: {str(e)}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }

    async def health_check(self) -> Dict[str, Any]:
        """Check health of Strategist service.

        Returns:
            Health check results
        """
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                url = f"{self.base_url}/health"

                async with session.get(url) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "status": "healthy",
                            "service": "strategist",
                            "details": result
                        }
                    else:
                        return {
                            "status": "unhealthy",
                            "service": "strategist",
                            "error": f"HTTP {response.status}"
                        }

        except Exception as e:
            logger.error(f"Health check failed for Strategist: {str(e)}")
            return {
                "status": "unhealthy",
                "service": "strategist",
                "error": str(e)
            }

    async def get_service_info(self) -> Dict[str, Any]:
        """Get service information.

        Returns:
            Service information
        """
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                url = f"{self.base_url}/"

                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {
                            "error": f"HTTP {response.status}",
                            "service": "strategist"
                        }

        except Exception as e:
            return {
                "error": str(e),
                "service": "strategist"
            }
