"""Health check endpoints for the Editor service."""

import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    try:
        return {
            "status": "healthy",
            "service": "editor",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Service unhealthy")


@router.get("/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """Detailed health check with component status."""
    try:
        # Check individual components
        components = {
            "text_optimizer": "healthy",
            "grammar_checker": "healthy",
            "style_analyzer": "healthy",
            "content_enhancer": "healthy",
            "version_control": "healthy"
        }

        # TODO: Add actual component health checks
        # For now, assume all components are healthy

        all_healthy = all(status == "healthy" for status in components.values())

        return {
            "status": "healthy" if all_healthy else "degraded",
            "service": "editor",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "components": components
        }

    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        raise HTTPException(status_code=500, detail="Service unhealthy")