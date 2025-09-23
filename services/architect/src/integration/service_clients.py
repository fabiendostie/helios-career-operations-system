"""
Service Clients for Helios Integration

HTTP clients for communicating with other Helios services:
- Orchestrator: Session management and coordination
- ANALYST: Market analysis and resume optimization
- STRATEGIST: Career path and skill adjacency insights
"""

import asyncio
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from urllib.parse import urljoin
import structlog

import httpx
from pydantic import BaseModel

from .data_contracts import (
    AnalystRecommendations,
    StrategistInsights,
    OrchestratorSession,
    ServiceHealthStatus,
    IntegrationHealthReport
)
from ..core.config import get_settings

logger = structlog.get_logger(__name__)

class ServiceClient:
    """Base class for Helios service clients."""

    def __init__(self, service_name: str, base_url: str, timeout: int = 30):
        self.service_name = service_name
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
        self._health_cache: Optional[ServiceHealthStatus] = None
        self._health_cache_expires: Optional[datetime] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with connection pooling."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                limits=httpx.Limits(max_keepalive_connections=10, max_connections=20)
            )
        return self._client

    async def close(self):
        """Close HTTP client and cleanup resources."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> httpx.Response:
        """Make HTTP request with error handling and logging."""

        url = urljoin(self.base_url, endpoint)
        client = await self._get_client()

        logger.info(f"Making {method} request to {self.service_name}",
                   url=url, service=self.service_name)

        try:
            response = await client.request(method, url, **kwargs)

            logger.info(f"{self.service_name} response received",
                       status_code=response.status_code,
                       response_time=response.elapsed.total_seconds())

            return response

        except httpx.TimeoutException:
            logger.error(f"{self.service_name} request timeout", url=url)
            raise
        except httpx.NetworkError as e:
            logger.error(f"{self.service_name} network error", url=url, error=str(e))
            raise
        except Exception as e:
            logger.error(f"{self.service_name} request failed", url=url, error=str(e))
            raise

    async def health_check(self) -> ServiceHealthStatus:
        """Check service health with caching."""

        # Return cached result if still valid
        if (self._health_cache and self._health_cache_expires
            and datetime.utcnow() < self._health_cache_expires):
            return self._health_cache

        start_time = datetime.utcnow()

        try:
            response = await self._make_request('GET', '/health')
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            is_healthy = response.status_code == 200

            status = ServiceHealthStatus(
                service_name=self.service_name,
                is_healthy=is_healthy,
                response_time_ms=response_time,
                error_message=None if is_healthy else f"HTTP {response.status_code}"
            )

        except Exception as e:
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            status = ServiceHealthStatus(
                service_name=self.service_name,
                is_healthy=False,
                response_time_ms=response_time,
                error_message=str(e)
            )

        # Cache result for 1 minute
        self._health_cache = status
        self._health_cache_expires = datetime.utcnow() + timedelta(minutes=1)

        return status

class OrchestratorClient(ServiceClient):
    """Client for communicating with the Orchestrator service."""

    def __init__(self, base_url: str):
        super().__init__("orchestrator", base_url)

    async def get_session(self, session_id: str) -> Optional[OrchestratorSession]:
        """Get session information from Orchestrator."""

        try:
            response = await self._make_request('GET', f'/sessions/{session_id}')

            if response.status_code == 200:
                data = response.json()
                return OrchestratorSession(**data)
            elif response.status_code == 404:
                logger.warning("Session not found", session_id=session_id)
                return None
            else:
                response.raise_for_status()

        except Exception as e:
            logger.error("Failed to get session from orchestrator",
                        session_id=session_id, error=str(e))
            raise

    async def update_session_status(
        self,
        session_id: str,
        status: str,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """Update session status in Orchestrator."""

        payload = {
            "architect_status": status,
            "updated_at": datetime.utcnow().isoformat()
        }

        if metadata:
            payload["metadata"] = metadata

        try:
            response = await self._make_request(
                'PATCH',
                f'/sessions/{session_id}',
                json=payload
            )

            if response.status_code == 200:
                logger.info("Session status updated", session_id=session_id, status=status)
                return True
            else:
                logger.warning("Failed to update session status",
                             session_id=session_id, status_code=response.status_code)
                return False

        except Exception as e:
            logger.error("Failed to update session status",
                        session_id=session_id, error=str(e))
            return False

    async def register_document_completion(
        self,
        session_id: str,
        document_type: str,
        document_url: str,
        quality_metrics: Dict[str, Any] = None
    ) -> bool:
        """Register completed document with Orchestrator."""

        payload = {
            "document_type": document_type,
            "document_url": document_url,
            "generated_at": datetime.utcnow().isoformat(),
            "service": "architect"
        }

        if quality_metrics:
            payload["quality_metrics"] = quality_metrics

        try:
            response = await self._make_request(
                'POST',
                f'/sessions/{session_id}/documents',
                json=payload
            )

            return response.status_code in [200, 201]

        except Exception as e:
            logger.error("Failed to register document completion",
                        session_id=session_id, error=str(e))
            return False

class AnalystClient(ServiceClient):
    """Client for communicating with the ANALYST service."""

    def __init__(self, base_url: str):
        super().__init__("analyst", base_url)

    async def get_recommendations(
        self,
        session_id: str,
        target_role: Optional[str] = None,
        target_company: Optional[str] = None
    ) -> Optional[AnalystRecommendations]:
        """Get optimization recommendations from ANALYST."""

        params = {"session_id": session_id}
        if target_role:
            params["target_role"] = target_role
        if target_company:
            params["target_company"] = target_company

        try:
            response = await self._make_request(
                'GET',
                '/recommendations',
                params=params
            )

            if response.status_code == 200:
                data = response.json()
                return AnalystRecommendations(**data)
            elif response.status_code == 404:
                logger.info("No recommendations available",
                           session_id=session_id)
                return None
            else:
                response.raise_for_status()

        except Exception as e:
            logger.error("Failed to get recommendations from analyst",
                        session_id=session_id, error=str(e))
            # Return empty recommendations to allow graceful degradation
            return AnalystRecommendations(
                session_id=session_id,
                user_profile_id="unknown",
                content_optimization={},
                priority_keywords=[],
                keyword_density_targets={},
                critical_skills=[],
                emerging_skills=[],
                market_insights={},
                ats_recommendations={},
                optimization_score=0.0
            )

    async def request_analysis(
        self,
        session_id: str,
        user_profile: Dict[str, Any],
        target_role: Optional[str] = None,
        target_company: Optional[str] = None
    ) -> bool:
        """Request new analysis from ANALYST service."""

        payload = {
            "session_id": session_id,
            "user_profile": user_profile,
            "target_role": target_role,
            "target_company": target_company,
            "requested_by": "architect",
            "requested_at": datetime.utcnow().isoformat()
        }

        try:
            response = await self._make_request(
                'POST',
                '/analyze',
                json=payload
            )

            return response.status_code in [200, 202]  # 202 for async processing

        except Exception as e:
            logger.error("Failed to request analysis from analyst",
                        session_id=session_id, error=str(e))
            return False

class StrategistClient(ServiceClient):
    """Client for communicating with the STRATEGIST service."""

    def __init__(self, base_url: str):
        super().__init__("strategist", base_url)

    async def get_insights(
        self,
        session_id: str,
        user_profile_id: Optional[str] = None
    ) -> Optional[StrategistInsights]:
        """Get career strategy insights from STRATEGIST."""

        params = {"session_id": session_id}
        if user_profile_id:
            params["user_profile_id"] = user_profile_id

        try:
            response = await self._make_request(
                'GET',
                '/insights',
                params=params
            )

            if response.status_code == 200:
                data = response.json()
                return StrategistInsights(**data)
            elif response.status_code == 404:
                logger.info("No strategic insights available",
                           session_id=session_id)
                return None
            else:
                response.raise_for_status()

        except Exception as e:
            logger.error("Failed to get insights from strategist",
                        session_id=session_id, error=str(e))
            # Return empty insights for graceful degradation
            return StrategistInsights(
                session_id=session_id,
                user_profile_id=user_profile_id or "unknown",
                recommended_career_paths=[],
                skill_adjacency={},
                skill_progression={},
                target_roles=[],
                role_gap_analysis={},
                industry_trends={},
                positioning_strategy={},
                confidence_score=0.0
            )

    async def request_strategy_analysis(
        self,
        session_id: str,
        user_profile: Dict[str, Any],
        career_goals: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Request new strategy analysis from STRATEGIST service."""

        payload = {
            "session_id": session_id,
            "user_profile": user_profile,
            "career_goals": career_goals,
            "requested_by": "architect",
            "requested_at": datetime.utcnow().isoformat()
        }

        try:
            response = await self._make_request(
                'POST',
                '/analyze',
                json=payload
            )

            return response.status_code in [200, 202]  # 202 for async processing

        except Exception as e:
            logger.error("Failed to request analysis from strategist",
                        session_id=session_id, error=str(e))
            return False

class ServiceClientsManager:
    """Manager for all service clients with health monitoring."""

    def __init__(self):
        settings = get_settings()

        # Initialize service clients from configuration
        self.orchestrator = OrchestratorClient(
            base_url=getattr(settings, 'orchestrator_url', 'http://localhost:8000')
        )
        self.analyst = AnalystClient(
            base_url=getattr(settings, 'analyst_url', 'http://localhost:8001')
        )
        self.strategist = StrategistClient(
            base_url=getattr(settings, 'strategist_url', 'http://localhost:8002')
        )

        self.clients = [self.orchestrator, self.analyst, self.strategist]

    async def health_check_all(self) -> IntegrationHealthReport:
        """Perform health check on all integrated services."""

        logger.info("Performing health check on all integrated services")

        # Run health checks concurrently
        health_tasks = [
            self.orchestrator.health_check(),
            self.analyst.health_check(),
            self.strategist.health_check()
        ]

        orchestrator_health, analyst_health, strategist_health = await asyncio.gather(
            *health_tasks, return_exceptions=True
        )

        # Handle any exceptions in health checks
        if isinstance(orchestrator_health, Exception):
            orchestrator_health = ServiceHealthStatus(
                service_name="orchestrator",
                is_healthy=False,
                error_message=str(orchestrator_health)
            )

        if isinstance(analyst_health, Exception):
            analyst_health = ServiceHealthStatus(
                service_name="analyst",
                is_healthy=False,
                error_message=str(analyst_health)
            )

        if isinstance(strategist_health, Exception):
            strategist_health = ServiceHealthStatus(
                service_name="strategist",
                is_healthy=False,
                error_message=str(strategist_health)
            )

        # Determine overall health
        all_healthy = all([
            orchestrator_health.is_healthy,
            analyst_health.is_healthy,
            strategist_health.is_healthy
        ])

        degraded_services = []
        if not orchestrator_health.is_healthy:
            degraded_services.append("orchestrator")
        if not analyst_health.is_healthy:
            degraded_services.append("analyst")
        if not strategist_health.is_healthy:
            degraded_services.append("strategist")

        report = IntegrationHealthReport(
            orchestrator=orchestrator_health,
            analyst=analyst_health,
            strategist=strategist_health,
            overall_health=all_healthy,
            degraded_services=degraded_services
        )

        logger.info("Integration health check completed",
                   overall_health=all_healthy,
                   degraded_services=degraded_services)

        return report

    async def close_all(self):
        """Close all service clients."""
        await asyncio.gather(
            *[client.close() for client in self.clients],
            return_exceptions=True
        )

# Global instance for dependency injection
_service_clients_manager: Optional[ServiceClientsManager] = None

async def get_service_clients() -> ServiceClientsManager:
    """Get service clients manager instance."""
    global _service_clients_manager

    if _service_clients_manager is None:
        _service_clients_manager = ServiceClientsManager()

    return _service_clients_manager
