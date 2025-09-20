"""Configuration management for the Editor service."""

import logging
from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Server configuration
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8006, description="Server port")
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

    # Editor configuration
    EDIT_TIMEOUT: int = Field(default=10, description="Edit timeout in seconds")
    MAX_TEXT_LENGTH: int = Field(default=50000, description="Maximum text length for editing")

    # Grammar and style checking
    GRAMMAR_CHECK_ENABLED: bool = Field(default=True, description="Enable grammar checking")
    STYLE_CHECK_ENABLED: bool = Field(default=True, description="Enable style checking")
    LANGUAGE_TOOL_LANGUAGE: str = Field(default="en-US", description="LanguageTool language")

    # Content enhancement
    ENHANCEMENT_ENABLED: bool = Field(default=True, description="Enable content enhancement")
    QUANTIFICATION_ENABLED: bool = Field(default=True, description="Enable achievement quantification")

    # Version control
    VERSION_TRACKING_ENABLED: bool = Field(default=True, description="Enable version tracking")
    MAX_VERSIONS: int = Field(default=10, description="Maximum number of versions to keep")

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
        env_prefix = "EDITOR_"
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