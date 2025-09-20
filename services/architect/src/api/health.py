"""Health check endpoints for ARCHITECT service."""

import time
import asyncio
from typing import Dict, Any

from fastapi import APIRouter, HTTPException
import psutil
import structlog

from ..core.config import get_settings

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.get("/")
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": "architect", 
        "version": "1.0.0",
        "timestamp": time.time()
    }


@router.get("/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """Detailed health check with system metrics."""
    settings = get_settings()
    
    # Get system metrics
    process = psutil.Process()
    memory_info = process.memory_info()
    memory_percent = process.memory_percent()
    cpu_percent = process.cpu_percent()
    
    # Check if system is healthy
    health_status = "healthy"
    issues = []
    
    if memory_percent > settings.memory_warning_threshold:
        health_status = "degraded" 
        issues.append(f"High memory usage: {memory_percent:.1f}%")
    
    if memory_percent > settings.memory_critical_threshold:
        health_status = "critical"
        issues.append(f"Critical memory usage: {memory_percent:.1f}%")
    
    # Check template engine status
    template_status = "unknown"
    template_cache_size = 0
    
    try:
        # This would normally check app.state.template_engine
        # For now, just return basic status
        template_status = "operational"
    except Exception as e:
        template_status = "error"
        issues.append(f"Template engine error: {str(e)}")
        if health_status == "healthy":
            health_status = "degraded"
    
    return {
        "status": health_status,
        "service": "architect",
        "version": "1.0.0",
        "timestamp": time.time(),
        "issues": issues,
        "system_metrics": {
            "memory_usage_mb": memory_info.rss / 1024 / 1024,
            "memory_percent": memory_percent,
            "cpu_percent": cpu_percent,
            "process_id": process.pid
        },
        "service_metrics": {
            "template_engine_status": template_status,
            "template_cache_size": template_cache_size,
        },
        "configuration": {
            "max_concurrent_generations": settings.max_concurrent_generations,
            "generation_timeout": settings.generation_timeout,
            "template_cache_size": settings.template_cache_size,
            "ats_compliance_strict": settings.ats_compliance_strict
        }
    }


@router.get("/dependencies")
async def check_dependencies() -> Dict[str, Any]:
    """Check external service dependencies."""
    settings = get_settings()
    dependencies = {}
    
    services_to_check = [
        ("orchestrator", settings.orchestrator_url, settings.orchestrator_timeout),
        ("analyst", settings.analyst_url, settings.analyst_timeout),
        ("strategist", settings.strategist_url, settings.strategist_timeout)
    ]
    
    for service_name, url, timeout in services_to_check:
        try:
            # Import here to avoid circular imports
            import aiohttp
            
            start_time = time.time()
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                async with session.get(f"{url}/health") as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        dependencies[service_name] = {
                            "status": "healthy",
                            "response_time": f"{response_time:.3f}s",
                            "url": url
                        }
                    else:
                        dependencies[service_name] = {
                            "status": "unhealthy",
                            "error": f"HTTP {response.status}",
                            "response_time": f"{response_time:.3f}s",
                            "url": url
                        }
                        
        except asyncio.TimeoutError:
            dependencies[service_name] = {
                "status": "timeout",
                "error": f"Timeout after {timeout}s",
                "url": url
            }
        except Exception as e:
            dependencies[service_name] = {
                "status": "error", 
                "error": str(e),
                "url": url
            }
    
    # Determine overall dependency status
    all_healthy = all(dep["status"] == "healthy" for dep in dependencies.values())
    has_critical_failures = any(dep["status"] in ["error", "timeout"] for dep in dependencies.values())
    
    overall_status = "healthy" if all_healthy else ("critical" if has_critical_failures else "degraded")
    
    return {
        "status": overall_status,
        "dependencies": dependencies,
        "timestamp": time.time()
    }


@router.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """Kubernetes readiness probe endpoint."""
    settings = get_settings()
    
    # Check critical components
    ready = True
    issues = []
    
    # Check memory usage
    memory_percent = psutil.Process().memory_percent()
    if memory_percent > settings.memory_critical_threshold:
        ready = False
        issues.append("Critical memory usage")
    
    # Check if we can handle new requests
    # This would normally check active request count
    # For now, just check basic system health
    
    if ready:
        return {"status": "ready", "timestamp": time.time()}
    else:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "issues": issues,
                "timestamp": time.time()
            }
        )


@router.get("/live") 
async def liveness_check() -> Dict[str, Any]:
    """Kubernetes liveness probe endpoint."""
    # Basic liveness check - if we can respond, we're alive
    return {"status": "alive", "timestamp": time.time()}