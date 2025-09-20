"""
Configuration management for LLM client.
"""

import os
from dataclasses import dataclass, field
from enum import Enum


class LLMProvider(Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure_openai"


@dataclass
class ProviderConfig:
    """Configuration for a single LLM provider."""

    name: str
    api_key: str
    base_url: str
    model: str
    timeout: float = 30.0
    max_tokens: int = 4000
    temperature: float = 0.7
    headers: dict[str, str] = field(default_factory=dict)


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker pattern."""

    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    expected_exception: type = Exception


@dataclass
class RetryConfig:
    """Configuration for retry logic."""

    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True


@dataclass
class CacheConfig:
    """Configuration for Redis caching."""

    enabled: bool = True
    ttl: int = 3600  # 1 hour default
    redis_url: str = "redis://localhost:6379"
    key_prefix: str = "helios:llm_cache"


@dataclass
class LLMConfig:
    """Main configuration for the LLM client."""

    providers: list[ProviderConfig] = field(default_factory=list)
    primary_provider: str = "openai"
    fallback_providers: list[str] = field(default_factory=lambda: ["anthropic"])
    circuit_breaker: CircuitBreakerConfig = field(default_factory=CircuitBreakerConfig)
    retry: RetryConfig = field(default_factory=RetryConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)

    @classmethod
    def from_env(cls) -> "LLMConfig":
        """Create configuration from environment variables."""
        providers = []

        # OpenAI configuration
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key:
            providers.append(
                ProviderConfig(
                    name="openai",
                    api_key=openai_api_key,
                    base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
                    model=os.getenv("OPENAI_MODEL", "gpt-4"),
                    timeout=float(os.getenv("OPENAI_TIMEOUT", "30.0")),
                    max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "4000")),
                    temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
                    headers={"Content-Type": "application/json"},
                )
            )

        # Anthropic configuration
        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_api_key:
            providers.append(
                ProviderConfig(
                    name="anthropic",
                    api_key=anthropic_api_key,
                    base_url=os.getenv(
                        "ANTHROPIC_BASE_URL", "https://api.anthropic.com"
                    ),
                    model=os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229"),
                    timeout=float(os.getenv("ANTHROPIC_TIMEOUT", "30.0")),
                    max_tokens=int(os.getenv("ANTHROPIC_MAX_TOKENS", "4000")),
                    temperature=float(os.getenv("ANTHROPIC_TEMPERATURE", "0.7")),
                    headers={"Content-Type": "application/json"},
                )
            )

        # Azure OpenAI configuration
        azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        if azure_api_key and azure_endpoint:
            providers.append(
                ProviderConfig(
                    name="azure_openai",
                    api_key=azure_api_key,
                    base_url=azure_endpoint,
                    model=os.getenv("AZURE_OPENAI_MODEL", "gpt-4"),
                    timeout=float(os.getenv("AZURE_OPENAI_TIMEOUT", "30.0")),
                    max_tokens=int(os.getenv("AZURE_OPENAI_MAX_TOKENS", "4000")),
                    temperature=float(os.getenv("AZURE_OPENAI_TEMPERATURE", "0.7")),
                    headers={"Content-Type": "application/json"},
                )
            )

        # Circuit breaker configuration
        circuit_breaker = CircuitBreakerConfig(
            failure_threshold=int(os.getenv("CIRCUIT_BREAKER_FAILURE_THRESHOLD", "5")),
            recovery_timeout=float(
                os.getenv("CIRCUIT_BREAKER_RECOVERY_TIMEOUT", "60.0")
            ),
        )

        # Retry configuration
        retry = RetryConfig(
            max_retries=int(os.getenv("LLM_MAX_RETRIES", "3")),
            base_delay=float(os.getenv("LLM_BASE_DELAY", "1.0")),
            max_delay=float(os.getenv("LLM_MAX_DELAY", "60.0")),
            exponential_base=float(os.getenv("LLM_EXPONENTIAL_BASE", "2.0")),
            jitter=os.getenv("LLM_RETRY_JITTER", "true").lower() == "true",
        )

        # Cache configuration
        cache = CacheConfig(
            enabled=os.getenv("LLM_CACHE_ENABLED", "true").lower() == "true",
            ttl=int(os.getenv("LLM_CACHE_TTL", "3600")),
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
            key_prefix=os.getenv("LLM_CACHE_KEY_PREFIX", "helios:llm_cache"),
        )

        return cls(
            providers=providers,
            primary_provider=os.getenv("LLM_PRIMARY_PROVIDER", "openai"),
            fallback_providers=os.getenv("LLM_FALLBACK_PROVIDERS", "anthropic").split(
                ","
            ),
            circuit_breaker=circuit_breaker,
            retry=retry,
            cache=cache,
        )

    def get_provider(self, name: str) -> ProviderConfig | None:
        """Get provider configuration by name."""
        for provider in self.providers:
            if provider.name == name:
                return provider
        return None

    def validate(self) -> None:
        """Validate the configuration."""
        if not self.providers:
            raise ValueError("At least one provider must be configured")

        primary = self.get_provider(self.primary_provider)
        if not primary:
            raise ValueError(
                f"Primary provider '{self.primary_provider}' not found in providers"
            )

        for fallback in self.fallback_providers:
            if not self.get_provider(fallback):
                raise ValueError(
                    f"Fallback provider '{fallback}' not found in providers"
                )
