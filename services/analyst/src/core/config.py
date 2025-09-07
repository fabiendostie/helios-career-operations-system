"""Configuration management for the Analyst service."""

import logging
from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Server configuration
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8003, description="Server port")
    DEBUG: bool = Field(default=False, description="Debug mode")

    # CORS configuration
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins",
    )

    # Orchestrator integration
    ORCHESTRATOR_URL: str = Field(
        default="http://localhost:8001", description="Orchestrator service URL"
    )

    # Analysis configuration
    ANALYSIS_TIMEOUT: int = Field(default=5, description="Analysis timeout in seconds")

    # NLP configuration
    SPACY_MODEL_EN: str = Field(
        default="en_core_web_sm", description="English spaCy model"
    )
    SPACY_MODEL_FR: str = Field(
        default="fr_core_news_sm", description="French spaCy model"
    )

    # Logging configuration
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")

    class Config:
        env_prefix = "ANALYST_"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
