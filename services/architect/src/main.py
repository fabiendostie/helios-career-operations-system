"""FastAPI application entry point for ARCHITECT service."""

import logging
import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from prometheus_client import make_asgi_app, Counter, Histogram
import structlog

from .api import generation, health, validation, integrated_generation
from .core.config import get_settings


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter('architect_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('architect_request_duration_seconds', 'Request duration', ['method', 'endpoint'])


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    logger.info("Starting ARCHITECT service", service="architect", version="1.0.0")

    # Startup tasks
    settings = get_settings()

    # Initialize template cache
    from .core.template_engine import TemplateEngine
    template_engine = TemplateEngine()
    app.state.template_engine = template_engine

    # Warm up template cache with common templates
    await template_engine.warm_cache()

    logger.info("ARCHITECT service startup complete")

    yield

    # Cleanup tasks
    logger.info("Shutting down ARCHITECT service")

    # Clear template cache
    if hasattr(app.state, 'template_engine'):
        await app.state.template_engine.clear_cache()

    logger.info("ARCHITECT service shutdown complete")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Helios ARCHITECT Service",
        description="AI-powered document generation with ATS compliance",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add request logging middleware
    @app.middleware("http")
    async def logging_middleware(request: Request, call_next):
        """Log requests with correlation IDs."""
        correlation_id = request.headers.get("X-Correlation-ID", "unknown")

        with structlog.contextvars.bind_contextvars(
            correlation_id=correlation_id,
            method=request.method,
            url=str(request.url),
            client_ip=request.client.host if request.client else "unknown"
        ):
            logger.info("Request started")

            start_time = asyncio.get_event_loop().time()

            try:
                response = await call_next(request)
                duration = asyncio.get_event_loop().time() - start_time

                # Record metrics
                REQUEST_COUNT.labels(
                    method=request.method,
                    endpoint=request.url.path,
                    status=response.status_code
                ).inc()

                REQUEST_DURATION.labels(
                    method=request.method,
                    endpoint=request.url.path
                ).observe(duration)

                logger.info(
                    "Request completed",
                    status_code=response.status_code,
                    duration=duration
                )

                # Add correlation ID to response headers
                response.headers["X-Correlation-ID"] = correlation_id

                return response

            except Exception as e:
                duration = asyncio.get_event_loop().time() - start_time

                REQUEST_COUNT.labels(
                    method=request.method,
                    endpoint=request.url.path,
                    status=500
                ).inc()

                logger.error(
                    "Request failed",
                    error=str(e),
                    duration=duration,
                    exc_info=True
                )

                raise

    # Include routers
    app.include_router(health.router, prefix="/health", tags=["health"])
    app.include_router(generation.router, prefix="/generate", tags=["generation"])
    app.include_router(validation.router, tags=["validation"])
    app.include_router(integrated_generation.router, tags=["integrated-generation"])

    # Add Prometheus metrics endpoint
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Global exception handler with structured logging."""
        correlation_id = request.headers.get("X-Correlation-ID", "unknown")

        logger.error(
            "Unhandled exception",
            correlation_id=correlation_id,
            error=str(exc),
            exc_info=True
        )

        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "correlation_id": correlation_id
            }
        )

    return app


# Create the FastAPI app instance
app = create_app()


if __name__ == "__main__":
    settings = get_settings()

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info" if settings.debug else "warning"
    )
