"""Configuration for the Architect service."""

import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Settings for the Architect service."""

    # Service configuration
    SERVICE_NAME: str = "architect"
    HOST: str = "0.0.0.0"
    PORT: int = 8005
    DEBUG: bool = False

    # CORS settings
    ALLOWED_ORIGINS: List[str] = ["*"]

    # Document generation settings
    MAX_DOCUMENT_SIZE_MB: int = 10
    GENERATION_TIMEOUT: int = 30  # seconds
    TEMPLATES_DIR: str = "src/templates"

    # ATS compliance settings
    ATS_COMPLIANCE_THRESHOLD: float = 85.0  # Minimum compliance score
    ENABLE_2025_OPTIMIZATIONS: bool = True

    # Integration settings
    ORCHESTRATOR_URL: str = "http://localhost:8001"
    ANALYST_URL: str = "http://localhost:8004"

    # Redis settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_prefix = "ARCHITECT_"


settings = Settings()