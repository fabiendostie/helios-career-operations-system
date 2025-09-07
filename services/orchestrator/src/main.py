"""HELIOS Orchestrator Service - Main FastAPI Application."""

import logging
import time
import uuid
from contextvars import ContextVar
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .core.config import settings
from .core.database import db_manager
from .core.background_tasks import background_tasks
from .integrations.profile_ingestor import close_profile_ingestor_client
from .api import health, sessions, commands, pipeline
from .utils.logging_config import get_logger, correlation_id_var


# Initialize logger
logger = get_logger("main")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title=settings.app_name,
        description="AI-powered Career Operations System - Central orchestration service",
        version=settings.app_version,
        openapi_url=settings.openapi_url,
        docs_url=settings.docs_url,
        redoc_url=settings.redoc_url,
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add correlation ID and logging middleware
    @app.middleware("http")
    async def add_correlation_id(request: Request, call_next):
        """Add correlation ID to all requests for tracing and logging."""
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        correlation_id_var.set(correlation_id)
        
        # Log incoming request
        logger.info(
            "Incoming request",
            extra={
                "method": request.method,
                "url": str(request.url),
                "client": request.client.host if request.client else "unknown"
            }
        )
        
        # Process request
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Log response
        logger.info(
            "Request completed",
            extra={
                "method": request.method,
                "url": str(request.url),
                "status_code": response.status_code,
                "process_time": round(process_time, 4)
            }
        )
        
        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id
        return response
    
    # Root endpoint - basic health check
    @app.get("/", tags=["root"])
    async def read_root():
        """Root endpoint - basic health check."""
        return {
            "service": settings.app_name,
            "version": settings.app_version,
            "status": "operational",
            "message": "HELIOS Orchestrator is running"
        }
    
    # Include API routers
    app.include_router(health.router, prefix="/health", tags=["health"])
    app.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
    app.include_router(commands.router, prefix="/commands", tags=["commands"])
    app.include_router(pipeline.router, tags=["pipeline"])
    
    # Application lifecycle events
    @app.on_event("startup")
    async def startup_event():
        """Initialize database and start background tasks on startup."""
        logger.info("Initializing database...")
        await db_manager.initialize()
        logger.info("Database initialized successfully")
        
        logger.info("Starting background tasks...")
        await background_tasks.start()
        logger.info("Background tasks started successfully")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Stop background tasks and close all connections on shutdown."""
        logger.info("Stopping background tasks...")
        await background_tasks.stop()
        logger.info("Background tasks stopped")
        
        logger.info("Closing Profile Ingestor client...")
        await close_profile_ingestor_client()
        logger.info("Profile Ingestor client closed")
        
        logger.info("Closing database connections...")
        await db_manager.close()
        logger.info("Database connections closed")
    
    return app


# Create the FastAPI application instance
app = create_app()


if __name__ == "__main__":
    # For development debugging
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        reload=settings.debug
    )