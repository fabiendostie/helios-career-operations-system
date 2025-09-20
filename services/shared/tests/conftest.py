"""
Pytest configuration and fixtures for shared services tests.
"""

import os
import sys
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
import redis

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_client.config import (
    CacheConfig,
    CircuitBreakerConfig,
    LLMConfig,
    ProviderConfig,
    RetryConfig,
)


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    mock_client = MagicMock(spec=redis.Redis)
    mock_client.ping.return_value = True
    mock_client.get.return_value = None
    mock_client.setex.return_value = True
    mock_client.delete.return_value = 1
    mock_client.keys.return_value = []
    mock_client.info.return_value = {
        "used_memory_human": "1.5M",
        "connected_clients": 3,
    }
    return mock_client


@pytest.fixture
def test_provider_config():
    """Test provider configuration."""
    return ProviderConfig(
        name="test_openai",
        api_key="test-key",
        base_url="https://api.openai.com/v1",
        model="gpt-4",
        timeout=30.0,
        max_tokens=1000,
        temperature=0.7,
        headers={"Content-Type": "application/json"},
    )


@pytest.fixture
def test_anthropic_config():
    """Test Anthropic provider configuration."""
    return ProviderConfig(
        name="test_anthropic",
        api_key="test-anthropic-key",
        base_url="https://api.anthropic.com",
        model="claude-3-sonnet-20240229",
        timeout=30.0,
        max_tokens=1000,
        temperature=0.7,
        headers={"Content-Type": "application/json"},
    )


@pytest.fixture
def test_cache_config():
    """Test cache configuration."""
    return CacheConfig(
        enabled=True,
        ttl=3600,
        redis_url="redis://localhost:6379",
        key_prefix="test:llm_cache",
    )


@pytest.fixture
def test_retry_config():
    """Test retry configuration."""
    return RetryConfig(
        max_retries=3,
        base_delay=0.1,  # Shorter delay for tests
        max_delay=1.0,
        exponential_base=2.0,
        jitter=False,  # Disable jitter for predictable tests
    )


@pytest.fixture
def test_circuit_breaker_config():
    """Test circuit breaker configuration."""
    return CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=1.0,  # Shorter timeout for tests
        expected_exception=Exception,
    )


@pytest.fixture
def test_llm_config(
    test_provider_config,
    test_anthropic_config,
    test_cache_config,
    test_retry_config,
    test_circuit_breaker_config,
):
    """Complete test LLM configuration."""
    return LLMConfig(
        providers=[test_provider_config, test_anthropic_config],
        primary_provider="test_openai",
        fallback_providers=["test_anthropic"],
        cache=test_cache_config,
        retry=test_retry_config,
        circuit_breaker=test_circuit_breaker_config,
    )


@pytest.fixture
def mock_aiohttp_response():
    """Mock aiohttp response."""
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(
        return_value={
            "choices": [{"message": {"content": "Test response"}}],
            "model": "gpt-4",
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        }
    )
    return mock_response


@pytest.fixture
def mock_aiohttp_session(mock_aiohttp_response):
    """Mock aiohttp session."""
    mock_session = AsyncMock()
    mock_session.post.return_value.__aenter__.return_value = mock_aiohttp_response
    return mock_session


@pytest_asyncio.fixture
async def mock_successful_provider():
    """Mock LLM provider that always succeeds."""
    provider = AsyncMock()
    provider.generate.return_value = {
        "content": "Test response",
        "model": "test-model",
        "usage": {"total_tokens": 15},
        "provider": "test",
    }
    return provider


@pytest_asyncio.fixture
async def mock_failing_provider():
    """Mock LLM provider that always fails."""
    from llm_client.exceptions import LLMProviderError

    provider = AsyncMock()
    provider.generate.side_effect = LLMProviderError("test", "Provider failure")
    return provider
