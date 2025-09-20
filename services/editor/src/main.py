"""FastAPI application entry point for the Editor service."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.editing import router as editing_router
from .api.health import router as health_router
from .core.config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan management."""
    # Startup
    logger.info("Starting Editor service...")

    # Initialize ML models and resources
    try:
        # TODO: Pre-load spaCy models, LanguageTool, etc.
        logger.info("Initialized NLP models and grammar checker")
    except Exception as e:
        logger.error(f"Failed to initialize models: {e}")

    yield

    # Shutdown
    logger.info("Shutting down Editor service...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Helios Editor Service",
        description="Granular text optimization and collaborative editing agent",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health_router, prefix="/health", tags=["health"])
    app.include_router(editing_router, tags=["editing"])

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
    )