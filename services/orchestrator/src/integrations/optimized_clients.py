"""Optimized HTTP clients using connection pooling for all service integrations."""

import asyncio
import logging
from typing import Dict, Any, Optional
import json

from ..core.connection_pool import (
    get_connection_pool_manager, ConnectionPoolConfig, http_request
)
from ..core.config import settings

logger = logging.getLogger(__name__)


class OptimizedServiceClient:
    """Base class for optimized service clients with connection pooling."""
    
    def __init__(self, 
                 service_name: str, 
                 base_url: str, 
                 pool_config: Optional[ConnectionPoolConfig] = None):
        """Initialize optimized service client.
        
        Args:
            service_name: Name of the service
            base_url: Base URL for the service
            pool_config: Custom pool configuration
        """
        self.service_name = service_name
        self.base_url = base_url
        self.pool_name = f"{service_name}_pool"
        self.pool_manager = get_connection_pool_manager()
        self.pool_config = pool_config or ConnectionPoolConfig(
            max_connections=50,
            max_connections_per_host=20,
            timeout_seconds=60,
            retry_attempts=3
        )
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the client and create connection pool."""
        if self._initialized:
            return
        
        await self.pool_manager.create_pool(
            pool_name=self.pool_name,
            base_url=self.base_url,
            config=self.pool_config
        )
        
        self._initialized = True
        logger.info(f"OptimizedServiceClient for {self.service_name} initialized")
    
    async def _make_request(self, 
                          method: str, 
                          endpoint: str, 
                          data: Optional[Dict[str, Any]] = None,
                          headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Make HTTP request using connection pool."""
        if not self._initialized:
            await self.initialize()
        
        # Prepare request parameters
        request_kwargs = {}
        if data:
            request_kwargs['json'] = data
        
        if headers:
            request_kwargs['headers'] = headers
        
        try:
            async with http_request(self.pool_name, method, endpoint, **request_kwargs) as response:
                response_data = await response.json()
                
                if response.status >= 400:
                    logger.error(f"{self.service_name} API error {response.status}: {response_data}")
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}: {response_data.get('detail', 'Unknown error')}"
                    }
                
                return response_data
                
        except asyncio.TimeoutError:
            logger.error(f"{self.service_name} request timeout")
            return {
                "success": False,
                "error": "Request timeout"
            }
        except Exception as e:
            logger.error(f"{self.service_name} request error: {str(e)}")
            return {
                "success": False,
                "error": f"Request failed: {str(e)}"
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the service."""
        try:
            response = await self._make_request("GET", "/health")
            
            # Add connection pool metrics to health check
            pool_metrics = await self.pool_manager.get_all_metrics()
            pool_info = pool_metrics.get(self.pool_name, {})
            
            return {
                "status": "healthy" if response.get("status") == "healthy" else "unhealthy",
                "service": self.service_name,
                "details": response,
                "connection_pool": {
                    "utilization": pool_info.get("pool_utilization_percent", 0),
                    "success_rate": pool_info.get("success_rate", 0),
                    "avg_response_time": pool_info.get("avg_response_time_ms", 0)
                }
            }
        except Exception as e:
            logger.error(f"Health check failed for {self.service_name}: {str(e)}")
            return {
                "status": "unhealthy",
                "service": self.service_name,
                "error": str(e)
            }


class OptimizedProfileIngestorClient(OptimizedServiceClient):
    """Optimized client for Profile Ingestor service."""
    
    def __init__(self):
        """Initialize Profile Ingestor client."""
        super().__init__(
            service_name="profile_ingestor",
            base_url=getattr(settings, 'profile_ingestor_url', 'http://localhost:8001'),
            pool_config=ConnectionPoolConfig(
                max_connections=30,  # Profile ingestion can be resource intensive
                max_connections_per_host=10,
                timeout_seconds=120,  # Longer timeout for document processing
                retry_attempts=2
            )
        )
    
    async def ingest_resume(self, 
                           resume_path: str, 
                           session_id: str,
                           options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Ingest resume using optimized connection."""
        payload = {
            "resume_path": resume_path,
            "session_id": session_id,
            "options": options or {}
        }
        
        logger.info(f"Starting resume ingestion for session {session_id}")
        response = await self._make_request("POST", "/api/v1/ingest", data=payload)
        
        if response.get("success"):
            logger.info(f"Resume ingestion completed for session {session_id}")
        
        return response


class OptimizedStrategistClient(OptimizedServiceClient):
    """Optimized client for Strategist service."""
    
    def __init__(self):
        """Initialize Strategist client."""
        super().__init__(
            service_name="strategist",
            base_url=getattr(settings, 'strategist_url', 'http://localhost:8002'),
            pool_config=ConnectionPoolConfig(
                max_connections=40,  # ML inference benefits from more connections
                max_connections_per_host=15,
                timeout_seconds=90,  # ML processing can take time
                retry_attempts=3
            )
        )
    
    async def generate_career_paths(self, 
                                  profile_data: Dict[str, Any], 
                                  session_id: str,
                                  preferences: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate career paths using optimized connection."""
        payload = {
            "profile_data": profile_data,
            "session_id": session_id,
            "preferences": preferences or {
                "max_paths": 5,
                "include_analysis": True,
                "difficulty_filter": "all"
            }
        }
        
        logger.info(f"Starting career path generation for session {session_id}")
        response = await self._make_request("POST", "/api/v1/discover", data=payload)
        
        if response.get("success"):
            paths_count = len(response.get("career_paths", {}).get("recommended_paths", []))
            logger.info(f"Generated {paths_count} career paths for session {session_id}")
        
        return response


class OptimizedAnalystClient(OptimizedServiceClient):
    """Optimized client for Analyst service."""
    
    def __init__(self):
        """Initialize Analyst client."""
        super().__init__(
            service_name="analyst",
            base_url=getattr(settings, 'analyst_url', 'http://localhost:8003'),
            pool_config=ConnectionPoolConfig(
                max_connections=35,  # Market analysis involves external API calls
                max_connections_per_host=12,
                timeout_seconds=75,  # Market analysis can be time consuming
                retry_attempts=3
            )
        )
    
    async def analyze_market_position(self, 
                                    profile_data: Dict[str, Any], 
                                    career_paths: Dict[str, Any], 
                                    session_id: str,
                                    analysis_options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze market position using optimized connection."""
        payload = {
            "profile_data": profile_data,
            "career_paths": career_paths,
            "session_id": session_id,
            "analysis_options": analysis_options or {
                "include_market_demand": True,
                "include_skill_gaps": True,
                "include_resume_optimization": True,
                "include_salary_analysis": True,
                "geographic_scope": "national"
            }
        }
        
        logger.info(f"Starting market analysis for session {session_id}")
        response = await self._make_request("POST", "/api/v1/analyze", data=payload)
        
        if response.get("success"):
            logger.info(f"Market analysis completed for session {session_id}")
        
        return response
    
    async def analyze_resume(self, 
                           profile_data: Dict[str, Any], 
                           session_id: str,
                           options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze resume for ATS optimization using optimized connection."""
        payload = {
            "profile_data": profile_data,
            "session_id": session_id,
            "options": options or {
                "ats_simulation": True,
                "keyword_optimization": True,
                "format_analysis": True
            }
        }
        
        logger.info(f"Starting resume analysis for session {session_id}")
        response = await self._make_request("POST", "/api/v1/analyze/resume", data=payload)
        
        return response


class OptimizedClientManager:
    """Manager for all optimized service clients."""
    
    def __init__(self):
        """Initialize client manager."""
        self.profile_ingestor = OptimizedProfileIngestorClient()
        self.strategist = OptimizedStrategistClient()
        self.analyst = OptimizedAnalystClient()
        self._initialized = False
    
    async def initialize_all(self) -> None:
        """Initialize all service clients."""
        if self._initialized:
            return
        
        initialization_tasks = [
            self.profile_ingestor.initialize(),
            self.strategist.initialize(),
            self.analyst.initialize()
        ]
        
        await asyncio.gather(*initialization_tasks)
        self._initialized = True
        
        logger.info("All optimized service clients initialized")
    
    async def health_check_all(self) -> Dict[str, Any]:
        """Perform health checks on all services."""
        health_tasks = [
            self.profile_ingestor.health_check(),
            self.strategist.health_check(),
            self.analyst.health_check()
        ]
        
        health_results = await asyncio.gather(*health_tasks, return_exceptions=True)
        
        # Process results
        services_health = {}
        overall_healthy = True
        
        for client, result in zip(
            [self.profile_ingestor, self.strategist, self.analyst], 
            health_results
        ):
            if isinstance(result, Exception):
                services_health[client.service_name] = {
                    "status": "unhealthy",
                    "error": str(result)
                }
                overall_healthy = False
            else:
                services_health[client.service_name] = result
                if result.get("status") != "healthy":
                    overall_healthy = False
        
        # Get connection pool metrics
        pool_manager = get_connection_pool_manager()
        pool_metrics = await pool_manager.get_all_metrics()
        
        return {
            "overall_status": "healthy" if overall_healthy else "degraded",
            "services": services_health,
            "connection_pools": pool_metrics,
            "timestamp": asyncio.get_event_loop().time()
        }
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics for all clients."""
        pool_manager = get_connection_pool_manager()
        pool_metrics = await pool_manager.get_all_metrics()
        
        return {
            "connection_pools": pool_metrics,
            "clients_initialized": self._initialized,
            "total_pools": len(pool_metrics) - 1,  # Exclude summary
            "optimization_enabled": True
        }
    
    async def cleanup(self) -> None:
        """Cleanup all client resources."""
        logger.info("Cleaning up optimized service clients")
        
        # Close all connection pools
        pool_manager = get_connection_pool_manager()
        await pool_manager.close_all_pools()
        
        self._initialized = False
        logger.info("Optimized service clients cleanup complete")


# Global client manager instance
_global_client_manager: Optional[OptimizedClientManager] = None


def get_optimized_client_manager() -> OptimizedClientManager:
    """Get global optimized client manager instance."""
    global _global_client_manager
    
    if _global_client_manager is None:
        _global_client_manager = OptimizedClientManager()
    
    return _global_client_manager