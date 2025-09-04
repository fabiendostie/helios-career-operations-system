"""Health check endpoints for HELIOS Orchestrator."""

import time
from typing import Dict, Any
from fastapi import APIRouter, status
from pydantic import BaseModel

from ..core.config import settings


router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""
    
    status: str
    timestamp: float
    service: str
    version: str
    uptime_seconds: float
    

class DetailedHealthResponse(HealthResponse):
    """Detailed health check with system information."""
    
    database: str
    external_services: Dict[str, str]
    configuration: Dict[str, Any]


# Store application start time for uptime calculation
_start_time = time.time()


@router.get("/", response_model=HealthResponse, tags=["health"])
async def health_check():
    """Basic health check endpoint.
    
    Returns:
        HealthResponse: Basic service health information
    """
    current_time = time.time()
    
    return HealthResponse(
        status="healthy",
        timestamp=current_time,
        service=settings.app_name,
        version=settings.app_version,
        uptime_seconds=current_time - _start_time
    )


@router.get("/detailed", response_model=DetailedHealthResponse, tags=["health"])
async def detailed_health_check():
    """Detailed health check with system information.
    
    Returns:
        DetailedHealthResponse: Comprehensive system health information
    """
    current_time = time.time()
    
    return DetailedHealthResponse(
        status="healthy",
        timestamp=current_time,
        service=settings.app_name,
        version=settings.app_version,
        uptime_seconds=current_time - _start_time,
        database="sqlite" if "sqlite" in settings.database_url else "postgresql",
        external_services={
            "profile_ingestor": settings.profile_ingestor_url,
        },
        configuration={
            "session_timeout_minutes": settings.session_timeout_minutes,
            "cors_enabled": len(settings.cors_origins) > 0,
            "debug_mode": settings.debug,
        }
    )


@router.get("/ready", tags=["health"])
async def readiness_check():
    """Kubernetes readiness probe endpoint.
    
    Returns:
        Dict: Simple readiness confirmation
    """
    return {"status": "ready"}


@router.get("/live", tags=["health"]) 
async def liveness_check():
    """Kubernetes liveness probe endpoint.
    
    Returns:
        Dict: Simple liveness confirmation
    """
    return {"status": "alive"}