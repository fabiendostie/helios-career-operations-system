"""Configuration management for HELIOS Orchestrator."""

import logging
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application metadata
    app_name: str = "HELIOS Orchestrator"
    app_version: str = "1.0.0"
    debug: bool = Field(False, description="Enable debug mode")
    
    # Server configuration
    host: str = Field("0.0.0.0", description="Server host")
    port: int = Field(8000, description="Server port")
    
    # Database configuration  
    database_url: str = Field(
        "sqlite+aiosqlite:///./sessions.db",
        description="Database connection URL"
    )
    
    # Session management
    session_timeout_minutes: int = Field(60, description="Session timeout in minutes")
    session_cleanup_interval_minutes: int = Field(15, description="Cleanup interval in minutes")
    
    # API configuration
    openapi_url: str = Field("/openapi.json", description="OpenAPI schema URL")
    docs_url: str = Field("/docs", description="Swagger UI URL") 
    redoc_url: str = Field("/redoc", description="ReDoc UI URL")
    
    # External service URLs
    profile_ingestor_url: str = Field(
        "http://localhost:8001",
        description="Profile Ingestor service URL"
    )
    
    # Request timeouts
    http_timeout_seconds: int = Field(30, description="HTTP request timeout")
    
    # Logging configuration
    log_level: str = Field("INFO", description="Logging level")
    log_format: str = Field(
        "%(asctime)s - %(name)s - %(levelname)s - [%(correlation_id)s] - %(message)s",
        description="Log message format"
    )
    
    # CORS settings
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()