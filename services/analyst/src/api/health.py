"""Health check endpoints for the Analyst service."""

import logging
from typing import Dict, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


logger = logging.getLogger(__name__)
router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    service: str
    version: str
    timestamp: str
    details: Dict[str, Any]


@router.get("/", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Basic health check endpoint."""
    import datetime

    try:
        # Check critical dependencies
        health_details = {
            "database": "healthy",  # TODO: Add database check when implemented
            "ml_models": "healthy",  # TODO: Add spaCy model check
            "orchestrator": "unknown",  # TODO: Add orchestrator connectivity check
        }

        return HealthResponse(
            status="healthy",
            service="analyst",
            version="1.0.0",
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            details=health_details,
        )

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


@router.get("/ready", response_model=HealthResponse)
async def readiness_check() -> HealthResponse:
    """Readiness check for Kubernetes."""
    import datetime

    try:
        # More comprehensive checks for readiness
        readiness_details = {
            "spacy_models_loaded": False,  # TODO: Check if models are loaded
            "market_data_loaded": False,  # TODO: Check if market data is loaded
            "orchestrator_reachable": False,  # TODO: Check orchestrator connectivity
        }

        # For now, return ready status
        # TODO: Implement actual readiness checks

        return HealthResponse(
            status="ready",
            service="analyst",
            version="1.0.0",
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            details=readiness_details,
        )

    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service not ready")
