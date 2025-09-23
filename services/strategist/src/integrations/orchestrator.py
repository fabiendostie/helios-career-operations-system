"""Integration client for HELIOS Orchestrator service."""

import logging
import asyncio
from typing import Dict, Any, Optional, Tuple
import aiohttp
import json

from ..core.config import StrategistConfig

logger = logging.getLogger(__name__)


class OrchestratorClient:
    """HTTP client for communicating with HELIOS Orchestrator."""

    def __init__(self, config: Optional[StrategistConfig] = None):
        """Initialize orchestrator client."""
        self.config = config or StrategistConfig()
        self.base_url = self.config.orchestrator_url.rstrip('/')
        self.timeout = self.config.orchestrator_timeout
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def register_with_orchestrator(self) -> bool:
        """Register STRATEGIST service with the Orchestrator."""
        try:
            registration_data = {
                "service_name": "STRATEGIST",
                "service_url": f"http://localhost:{self.config.port}",
                "capabilities": [
                    "career_path_generation",
                    "skill_analysis",
                    "role_matching",
                    "transition_planning"
                ],
                "commands": ["discover"],
                "status": "active",
                "version": "1.0.0"
            }

            async with self.session.post(
                f"{self.base_url}/services/register",
                json=registration_data,
                headers={"Content-Type": "application/json"}
            ) as response:

                if response.status == 200:
                    logger.info("Successfully registered with HELIOS Orchestrator")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to register with Orchestrator: {response.status} - {error_text}")
                    return False

        except asyncio.TimeoutError:
            logger.error("Timeout registering with Orchestrator")
            return False
        except Exception as e:
            logger.error(f"Error registering with Orchestrator: {e}")
            return False

    async def send_heartbeat(self) -> bool:
        """Send heartbeat to Orchestrator to maintain service status."""
        try:
            heartbeat_data = {
                "service_name": "STRATEGIST",
                "status": "active",
                "timestamp": asyncio.get_event_loop().time(),
                "health_check": {
                    "status": "healthy",
                    "components": {
                        "vectorizer": "ready",
                        "taxonomy": "loaded",
                        "fit_scorer": "active"
                    }
                }
            }

            async with self.session.post(
                f"{self.base_url}/services/heartbeat",
                json=heartbeat_data,
                headers={"Content-Type": "application/json"}
            ) as response:

                return response.status == 200

        except Exception as e:
            logger.warning(f"Heartbeat failed: {e}")
            return False

    async def get_session_data(self, user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session data from Orchestrator for a user."""
        try:
            async with self.session.get(
                f"{self.base_url}/sessions/{session_id}/data",
                params={"user_id": user_id}
            ) as response:

                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to get session data: {response.status}")
                    return None

        except Exception as e:
            logger.error(f"Error getting session data: {e}")
            return None

    async def update_session_data(self, session_id: str,
                                 strategist_data: Dict[str, Any]) -> bool:
        """Update session with STRATEGIST results."""
        try:
            update_data = {
                "service": "STRATEGIST",
                "data": strategist_data,
                "timestamp": asyncio.get_event_loop().time()
            }

            async with self.session.patch(
                f"{self.base_url}/sessions/{session_id}/data",
                json=update_data,
                headers={"Content-Type": "application/json"}
            ) as response:

                return response.status == 200

        except Exception as e:
            logger.error(f"Error updating session data: {e}")
            return False

    async def notify_completion(self, user_id: str, session_id: str,
                               processing_time_ms: float) -> bool:
        """Notify Orchestrator that STRATEGIST processing is complete."""
        try:
            completion_data = {
                "service": "STRATEGIST",
                "user_id": user_id,
                "session_id": session_id,
                "status": "completed",
                "processing_time_ms": processing_time_ms,
                "timestamp": asyncio.get_event_loop().time()
            }

            async with self.session.post(
                f"{self.base_url}/services/completion",
                json=completion_data,
                headers={"Content-Type": "application/json"}
            ) as response:

                return response.status == 200

        except Exception as e:
            logger.error(f"Error notifying completion: {e}")
            return False

    async def get_orchestrator_health(self) -> Dict[str, Any]:
        """Check Orchestrator health status."""
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"status": "unhealthy", "status_code": response.status}

        except Exception as e:
            logger.error(f"Error checking Orchestrator health: {e}")
            return {"status": "error", "error": str(e)}


class HeartbeatManager:
    """Manages periodic heartbeats to the Orchestrator."""

    def __init__(self, client: OrchestratorClient, interval: float = 30.0):
        """Initialize heartbeat manager."""
        self.client = client
        self.interval = interval
        self.running = False
        self.task: Optional[asyncio.Task] = None

    async def start(self):
        """Start periodic heartbeats."""
        if self.running:
            return

        self.running = True
        self.task = asyncio.create_task(self._heartbeat_loop())
        logger.info(f"Started heartbeat manager with {self.interval}s interval")

    async def stop(self):
        """Stop periodic heartbeats."""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped heartbeat manager")

    async def _heartbeat_loop(self):
        """Main heartbeat loop."""
        while self.running:
            try:
                success = await self.client.send_heartbeat()
                if not success:
                    logger.warning("Heartbeat failed")

                await asyncio.sleep(self.interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
                await asyncio.sleep(self.interval)


async def initialize_orchestrator_integration(config: StrategistConfig) -> Tuple[OrchestratorClient, HeartbeatManager]:
    """Initialize integration with HELIOS Orchestrator."""

    async with OrchestratorClient(config) as client:
        # Register with Orchestrator
        registration_success = await client.register_with_orchestrator()

        if not registration_success:
            logger.warning("Failed to register with Orchestrator - continuing anyway")

        # Create heartbeat manager
        heartbeat_manager = HeartbeatManager(client)

        return client, heartbeat_manager
