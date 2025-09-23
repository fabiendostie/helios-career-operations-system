"""Configuration for the Editor service."""

import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Settings for the Editor service."""

    # Service configuration
    SERVICE_NAME: str = "editor"
    HOST: str = "0.0.0.0"
    PORT: int = 8006
    DEBUG: bool = False

    # CORS settings
    ALLOWED_ORIGINS: List[str] = ["*"]

    # Text optimization settings
    MAX_TEXT_LENGTH: int = 10000  # Maximum characters per optimization
    OPTIMIZATION_TIMEOUT: int = 10  # seconds
    DEFAULT_OPTIMIZATION_LEVEL: str = "standard"

    # Performance settings
    ENABLE_2025_OPTIMIZATIONS: bool = True
    TARGET_IMPACT_SCORE: float = 85.0  # Minimum impact score target
    TARGET_READABILITY_SCORE: float = 80.0  # Minimum readability target

    # Integration settings
    ORCHESTRATOR_URL: str = "http://localhost:8001"
    ARCHITECT_URL: str = "http://localhost:8005"

    # Redis settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_prefix = "EDITOR_"


settings = Settings()