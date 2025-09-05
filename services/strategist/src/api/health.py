"""Health check endpoints for STRATEGIST service."""

import time
from typing import Dict, Any
from fastapi import APIRouter
from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    service: str
    version: str
    timestamp: float
    uptime: float


router = APIRouter(prefix="/health", tags=["health"])

# Track service start time
_start_time = time.time()


@router.get("", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Basic health check endpoint."""
    current_time = time.time()
    return HealthResponse(
        status="healthy",
        service="strategist",
        version="1.0.0",
        timestamp=current_time,
        uptime=current_time - _start_time
    )


@router.get("/ready", response_model=Dict[str, Any])
async def readiness_check() -> Dict[str, Any]:
    """Readiness check with dependency validation."""
    # TODO: Add checks for embedding model, role taxonomy, etc.
    checks = {
        "embedding_model": True,  # Will implement in Task 2
        "role_taxonomy": True,    # Will implement in Task 3
        "memory": True,
        "disk": True
    }
    
    all_ready = all(checks.values())
    
    return {
        "status": "ready" if all_ready else "not_ready",
        "service": "strategist",
        "checks": checks,
        "timestamp": time.time()
    }