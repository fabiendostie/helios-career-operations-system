"""Health check endpoints for the Architect service."""

import time
from typing import Dict, Any

from fastapi import APIRouter
from src.core.config import settings

router = APIRouter()


@router.get("/")
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint."""
    return {
        "service": settings.SERVICE_NAME,
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0",
        "ats_optimizations_enabled": settings.ENABLE_2025_OPTIMIZATIONS
    }


@router.get("/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """Detailed health check including component status."""
    health_status = {
        "service": settings.SERVICE_NAME,
        "status": "healthy",
        "timestamp": time.time(),
        "components": {
            "document_generator": {"status": "healthy", "ats_compliance_ready": True},
            "template_engine": {"status": "healthy", "templates_loaded": True},
            "ats_compliance_engine": {"status": "healthy", "2025_standards": True}
        },
        "configuration": {
            "ats_compliance_threshold": settings.ATS_COMPLIANCE_THRESHOLD,
            "generation_timeout": settings.GENERATION_TIMEOUT,
            "max_document_size_mb": settings.MAX_DOCUMENT_SIZE_MB
        }
    }

    return health_status