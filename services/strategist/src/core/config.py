"""Configuration management for STRATEGIST service."""

import os
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class StrategistConfig:
    """Configuration for STRATEGIST service."""
    
    # Service configuration
    host: str = "0.0.0.0"
    port: int = 8002
    debug: bool = False
    
    # AI/ML configuration
    embedding_model: str = "all-MiniLM-L6-v2"
    max_career_paths: int = 3
    skill_weight: float = 0.65
    aspiration_weight: float = 0.35
    
    # Performance configuration
    max_response_time: float = 3.0
    cache_ttl: int = 300  # 5 minutes
    
    # Integration configuration
    orchestrator_url: str = "http://localhost:8001"
    orchestrator_timeout: float = 10.0
    
    # Redis cache configuration
    redis_enabled: bool = True
    redis_url: str = "redis://localhost:6379"
    redis_ttl: int = 3600  # 1 hour TTL for cached vectors
    
    @classmethod
    def from_env(cls) -> "StrategistConfig":
        """Load configuration from environment variables."""
        return cls(
            host=os.getenv("STRATEGIST_HOST", cls.host),
            port=int(os.getenv("STRATEGIST_PORT", str(cls.port))),
            debug=os.getenv("STRATEGIST_DEBUG", "false").lower() == "true",
            embedding_model=os.getenv("STRATEGIST_EMBEDDING_MODEL", cls.embedding_model),
            max_career_paths=int(os.getenv("STRATEGIST_MAX_PATHS", str(cls.max_career_paths))),
            skill_weight=float(os.getenv("STRATEGIST_SKILL_WEIGHT", str(cls.skill_weight))),
            aspiration_weight=float(os.getenv("STRATEGIST_ASPIRATION_WEIGHT", str(cls.aspiration_weight))),
            max_response_time=float(os.getenv("STRATEGIST_MAX_RESPONSE_TIME", str(cls.max_response_time))),
            cache_ttl=int(os.getenv("STRATEGIST_CACHE_TTL", str(cls.cache_ttl))),
            orchestrator_url=os.getenv("STRATEGIST_ORCHESTRATOR_URL", cls.orchestrator_url),
            orchestrator_timeout=float(os.getenv("STRATEGIST_ORCHESTRATOR_TIMEOUT", str(cls.orchestrator_timeout))),
            redis_enabled=os.getenv("STRATEGIST_REDIS_ENABLED", "true").lower() == "true",
            redis_url=os.getenv("STRATEGIST_REDIS_URL", cls.redis_url),
            redis_ttl=int(os.getenv("STRATEGIST_REDIS_TTL", str(cls.redis_ttl))),
        )


def get_config() -> StrategistConfig:
    """Get application configuration."""
    return StrategistConfig.from_env()