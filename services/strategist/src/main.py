"""STRATEGIST Agent Service - FastAPI application entry point."""

import logging
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from .core.config import get_config
from .api.health import router as health_router
from .api.career_paths import router as career_paths_router, initialize_career_generator


# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("strategist.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan management."""
    logger.info("STRATEGIST service starting up...")
    
    # Initialize career generator with all components
    await initialize_career_generator()
    
    logger.info("STRATEGIST service startup complete")
    
    yield
    
    logger.info("STRATEGIST service shutting down...")
    # Cleanup resources if needed
    logger.info("STRATEGIST service shutdown complete")


# Initialize FastAPI application
config = get_config()

app = FastAPI(
    title="STRATEGIST Agent Service",
    description="Career Path Generation with Skill Adjacency Modeling",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    """Add correlation ID to all requests."""
    correlation_id = request.headers.get("x-correlation-id") or str(uuid.uuid4())
    
    # Add to logger context
    logger.info(f"Request started - {request.method} {request.url}", 
                extra={"correlation_id": correlation_id})
    
    response = await call_next(request)
    
    # Add correlation ID to response headers
    response.headers["x-correlation-id"] = correlation_id
    
    logger.info(f"Request completed - Status: {response.status_code}", 
                extra={"correlation_id": correlation_id})
    
    return response


# Register routers
app.include_router(health_router)
app.include_router(career_paths_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "STRATEGIST",
        "description": "Career Path Generation with Skill Adjacency Modeling",
        "version": "1.0.0",
        "status": "active"
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting STRATEGIST service on {config.host}:{config.port}")
    
    uvicorn.run(
        "src.main:app",
        host=config.host,
        port=config.port,
        reload=config.debug,
        log_level="info" if not config.debug else "debug"
    )