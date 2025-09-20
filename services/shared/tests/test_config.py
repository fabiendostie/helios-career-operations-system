"""
Tests for LLM client configuration.
"""

import os
import sys
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_client.config import (
    CacheConfig,
    CircuitBreakerConfig,
    LLMConfig,
    ProviderConfig,
    RetryConfig,
)


class TestProviderConfig:
    """Test ProviderConfig class."""

    def test_provider_config_creation(self):
        """Test creating a provider configuration."""
        config = ProviderConfig(
            name="openai",
            api_key="test-key",
            base_url="https://api.openai.com/v1",
            model="gpt-4",
        )

        assert config.name == "openai"
        assert config.api_key == "test-key"
        assert config.base_url == "https://api.openai.com/v1"
        assert config.model == "gpt-4"
        assert config.timeout == 30.0  # default
        assert config.max_tokens == 4000  # default
        assert config.temperature == 0.7  # default


class TestLLMConfig:
    """Test LLMConfig class."""

    def test_basic_config_creation(self, test_provider_config):
        """Test creating a basic LLM configuration."""
        config = LLMConfig(
            providers=[test_provider_config], primary_provider="test_openai"
        )

        assert len(config.providers) == 1
        assert config.primary_provider == "test_openai"
        assert config.fallback_providers == ["anthropic"]  # default

    def test_get_provider(self, test_llm_config):
        """Test getting a provider by name."""
        provider = test_llm_config.get_provider("test_openai")
        assert provider is not None
        assert provider.name == "test_openai"

        provider = test_llm_config.get_provider("nonexistent")
        assert provider is None

    def test_validate_valid_config(self, test_llm_config):
        """Test validating a valid configuration."""
        test_llm_config.validate()  # Should not raise

    def test_validate_no_providers(self):
        """Test validation fails with no providers."""
        config = LLMConfig(providers=[])

        with pytest.raises(
            ValueError, match="At least one provider must be configured"
        ):
            config.validate()

    def test_validate_missing_primary_provider(self, test_provider_config):
        """Test validation fails with missing primary provider."""
        config = LLMConfig(
            providers=[test_provider_config], primary_provider="nonexistent"
        )

        with pytest.raises(
            ValueError, match="Primary provider 'nonexistent' not found"
        ):
            config.validate()

    def test_validate_missing_fallback_provider(self, test_provider_config):
        """Test validation fails with missing fallback provider."""
        config = LLMConfig(
            providers=[test_provider_config],
            primary_provider="test_openai",
            fallback_providers=["nonexistent"],
        )

        with pytest.raises(
            ValueError, match="Fallback provider 'nonexistent' not found"
        ):
            config.validate()

    @patch.dict(
        os.environ,
        {
            "OPENAI_API_KEY": "test-openai-key",
            "OPENAI_MODEL": "gpt-3.5-turbo",
            "ANTHROPIC_API_KEY": "test-anthropic-key",
            "LLM_PRIMARY_PROVIDER": "anthropic",
            "LLM_CACHE_ENABLED": "false",
            "LLM_MAX_RETRIES": "5",
        },
    )
    def test_from_env(self):
        """Test creating configuration from environment variables."""
        config = LLMConfig.from_env()

        # Check providers
        assert len(config.providers) == 2

        openai_provider = config.get_provider("openai")
        assert openai_provider is not None
        assert openai_provider.api_key == "test-openai-key"
        assert openai_provider.model == "gpt-3.5-turbo"

        anthropic_provider = config.get_provider("anthropic")
        assert anthropic_provider is not None
        assert anthropic_provider.api_key == "test-anthropic-key"

        # Check main config
        assert config.primary_provider == "anthropic"

        # Check cache config
        assert config.cache.enabled is False

        # Check retry config
        assert config.retry.max_retries == 5

    @patch.dict(
        os.environ,
        {
            "AZURE_OPENAI_API_KEY": "test-azure-key",
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
            "AZURE_OPENAI_MODEL": "gpt-4-32k",
        },
    )
    def test_from_env_azure(self):
        """Test creating Azure OpenAI configuration from environment."""
        config = LLMConfig.from_env()

        azure_provider = config.get_provider("azure_openai")
        assert azure_provider is not None
        assert azure_provider.api_key == "test-azure-key"
        assert azure_provider.base_url == "https://test.openai.azure.com/"
        assert azure_provider.model == "gpt-4-32k"

    @patch.dict(os.environ, {}, clear=True)
    def test_from_env_no_providers(self):
        """Test handling no providers in environment."""
        config = LLMConfig.from_env()
        assert len(config.providers) == 0


class TestCacheConfig:
    """Test CacheConfig class."""

    def test_default_cache_config(self):
        """Test default cache configuration."""
        config = CacheConfig()

        assert config.enabled is True
        assert config.ttl == 3600
        assert config.redis_url == "redis://localhost:6379"
        assert config.key_prefix == "helios:llm_cache"


class TestRetryConfig:
    """Test RetryConfig class."""

    def test_default_retry_config(self):
        """Test default retry configuration."""
        config = RetryConfig()

        assert config.max_retries == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0
        assert config.jitter is True


class TestCircuitBreakerConfig:
    """Test CircuitBreakerConfig class."""

    def test_default_circuit_breaker_config(self):
        """Test default circuit breaker configuration."""
        config = CircuitBreakerConfig()

        assert config.failure_threshold == 5
        assert config.recovery_timeout == 60.0
        assert config.expected_exception == Exception
