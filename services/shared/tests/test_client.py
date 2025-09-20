"""
Tests for the main ResilientLLMClient implementation.
"""

import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_client.client import ResilientLLMClient
from llm_client.config import LLMConfig
from llm_client.exceptions import (
    LLMClientError,
    LLMConfigurationError,
    LLMProviderError,
)


class TestResilientLLMClient:
    """Test ResilientLLMClient class."""

    def test_initialization_success(self, test_llm_config):
        """Test successful client initialization."""
        with patch("llm_client.client.get_provider") as mock_get_provider:
            mock_provider = AsyncMock()
            mock_get_provider.return_value = mock_provider

            with patch("services.shared.llm_client.cache.LLMCache") as mock_cache_class:
                mock_cache = MagicMock()
                mock_cache_class.return_value = mock_cache

                client = ResilientLLMClient(test_llm_config)

                assert len(client.providers) == 2
                assert "test_openai" in client.providers
                assert "test_anthropic" in client.providers
                assert len(client.circuit_breakers) == 2

    def test_initialization_no_providers(self):
        """Test initialization fails with no providers."""
        config = LLMConfig(providers=[])

        with pytest.raises(LLMConfigurationError):
            ResilientLLMClient(config)

    @pytest.mark.asyncio
    async def test_successful_generation_primary_provider(self, test_llm_config):
        """Test successful generation using primary provider."""
        with patch("llm_client.client.get_provider") as mock_get_provider:
            mock_provider = AsyncMock()
            mock_provider.generate.return_value = {
                "content": "Test response",
                "model": "gpt-4",
                "usage": {"total_tokens": 15},
                "provider": "test_openai",
            }
            mock_get_provider.return_value = mock_provider

            with patch("services.shared.llm_client.cache.LLMCache") as mock_cache_class:
                mock_cache = AsyncMock()
                mock_cache.get.return_value = None  # Cache miss
                mock_cache.set.return_value = True
                mock_cache_class.return_value = mock_cache

                client = ResilientLLMClient(test_llm_config)
                result = await client.generate("Test prompt")

                assert result["content"] == "Test response"
                assert result["provider"] == "test_openai"
                assert result["cached"] is False
                assert result["attempts"] == 1

                # Verify caching was attempted
                mock_cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_hit(self, test_llm_config):
        """Test returning cached response."""
        with patch("llm_client.client.get_provider") as mock_get_provider:
            mock_provider = AsyncMock()
            mock_get_provider.return_value = mock_provider

            with patch("services.shared.llm_client.cache.LLMCache") as mock_cache_class:
                cached_response = {
                    "content": "Cached response",
                    "model": "gpt-4",
                    "usage": {"total_tokens": 10},
                }
                mock_cache = AsyncMock()
                mock_cache.get.return_value = cached_response
                mock_cache_class.return_value = mock_cache

                client = ResilientLLMClient(test_llm_config)
                result = await client.generate("Test prompt")

                assert result["content"] == "Cached response"
                assert result["cached"] is True
                assert result["attempts"] == 0

                # Verify provider was not called
                mock_provider.generate.assert_not_called()

    @pytest.mark.asyncio
    async def test_fallback_to_secondary_provider(self, test_llm_config):
        """Test fallback when primary provider fails."""
        with patch("llm_client.client.get_provider") as mock_get_provider:
            # Primary provider fails
            failing_provider = AsyncMock()
            failing_provider.generate.side_effect = LLMProviderError(
                "test_openai", "API error"
            )

            # Secondary provider succeeds
            success_provider = AsyncMock()
            success_provider.generate.return_value = {
                "content": "Fallback response",
                "model": "claude-3",
                "usage": {"total_tokens": 12},
                "provider": "test_anthropic",
            }

            # Map providers by name
            def provider_side_effect(config):
                if config.name == "test_openai":
                    return failing_provider
                elif config.name == "test_anthropic":
                    return success_provider
                else:
                    raise ValueError(f"Unknown provider: {config.name}")

            mock_get_provider.side_effect = provider_side_effect

            with patch("services.shared.llm_client.cache.LLMCache") as mock_cache_class:
                mock_cache = AsyncMock()
                mock_cache.get.return_value = None  # Cache miss
                mock_cache_class.return_value = mock_cache

                client = ResilientLLMClient(test_llm_config)
                result = await client.generate("Test prompt")

                assert result["content"] == "Fallback response"
                assert result["provider"] == "test_anthropic"
                assert result["attempts"] == 2

    @pytest.mark.asyncio
    async def test_all_providers_fail(self, test_llm_config):
        """Test behavior when all providers fail."""
        with patch("llm_client.client.get_provider") as mock_get_provider:
            failing_provider = AsyncMock()
            failing_provider.generate.side_effect = LLMProviderError(
                "provider", "API error"
            )
            mock_get_provider.return_value = failing_provider

            with patch("services.shared.llm_client.cache.LLMCache") as mock_cache_class:
                mock_cache = AsyncMock()
                mock_cache.get.return_value = None
                mock_cache_class.return_value = mock_cache

                client = ResilientLLMClient(test_llm_config)

                with pytest.raises(LLMClientError, match="All providers failed"):
                    await client.generate("Test prompt")

    @pytest.mark.asyncio
    async def test_circuit_breaker_prevents_calls(self, test_llm_config):
        """Test circuit breaker prevents calls to failing provider."""
        with patch("llm_client.client.get_provider") as mock_get_provider:
            mock_provider = AsyncMock()
            mock_get_provider.return_value = mock_provider

            with patch("services.shared.llm_client.cache.LLMCache") as mock_cache_class:
                mock_cache = AsyncMock()
                mock_cache.get.return_value = None
                mock_cache_class.return_value = mock_cache

                client = ResilientLLMClient(test_llm_config)

                # Manually open circuit breaker for primary provider
                client.circuit_breakers["test_openai"]._move_to_open()

                with pytest.raises(LLMClientError):
                    await client.generate(
                        "Test prompt", provider_preference=["test_openai"]
                    )

    @pytest.mark.asyncio
    async def test_disable_cache(self, test_llm_config):
        """Test generation with caching disabled."""
        with patch("llm_client.client.get_provider") as mock_get_provider:
            mock_provider = AsyncMock()
            mock_provider.generate.return_value = {
                "content": "Test response",
                "model": "gpt-4",
                "usage": {},
                "provider": "test_openai",
            }
            mock_get_provider.return_value = mock_provider

            with patch("services.shared.llm_client.cache.LLMCache") as mock_cache_class:
                mock_cache = AsyncMock()
                mock_cache_class.return_value = mock_cache

                client = ResilientLLMClient(test_llm_config)
                result = await client.generate("Test prompt", use_cache=False)

                assert result["content"] == "Test response"
                assert result["cached"] is False

                # Verify cache was not consulted
                mock_cache.get.assert_not_called()
                mock_cache.set.assert_not_called()

    @pytest.mark.asyncio
    async def test_custom_provider_preference(self, test_llm_config):
        """Test generation with custom provider preference."""
        with patch("llm_client.client.get_provider") as mock_get_provider:
            # Anthropic provider (preferred) succeeds
            anthropic_provider = AsyncMock()
            anthropic_provider.generate.return_value = {
                "content": "Anthropic response",
                "model": "claude-3",
                "usage": {},
                "provider": "test_anthropic",
            }

            # OpenAI provider should not be called
            openai_provider = AsyncMock()

            def provider_side_effect(config):
                if config.name == "test_openai":
                    return openai_provider
                elif config.name == "test_anthropic":
                    return anthropic_provider

            mock_get_provider.side_effect = provider_side_effect

            with patch("services.shared.llm_client.cache.LLMCache") as mock_cache_class:
                mock_cache = AsyncMock()
                mock_cache.get.return_value = None
                mock_cache_class.return_value = mock_cache

                client = ResilientLLMClient(test_llm_config)
                result = await client.generate(
                    "Test prompt", provider_preference=["test_anthropic"]
                )

                assert result["provider"] == "test_anthropic"
                openai_provider.generate.assert_not_called()

    def test_get_status(self, test_llm_config):
        """Test getting client status."""
        with patch("llm_client.client.get_provider") as mock_get_provider:
            mock_provider = AsyncMock()
            mock_get_provider.return_value = mock_provider

            with patch("services.shared.llm_client.cache.LLMCache") as mock_cache_class:
                mock_cache = MagicMock()
                mock_cache.get_stats.return_value = {"enabled": True, "cached_keys": 5}
                mock_cache_class.return_value = mock_cache

                client = ResilientLLMClient(test_llm_config)
                status = client.get_status()

                assert "providers" in status
                assert "cache" in status
                assert "config" in status
                assert len(status["providers"]) == 2
                assert status["config"]["primary_provider"] == "test_openai"

    def test_reset_circuit_breakers(self, test_llm_config):
        """Test resetting circuit breakers."""
        with patch("llm_client.client.get_provider") as mock_get_provider:
            mock_provider = AsyncMock()
            mock_get_provider.return_value = mock_provider

            with patch("services.shared.llm_client.cache.LLMCache") as mock_cache_class:
                mock_cache = MagicMock()
                mock_cache_class.return_value = mock_cache

                client = ResilientLLMClient(test_llm_config)

                # Reset specific provider
                client.reset_circuit_breakers("test_openai")

                # Reset all providers
                client.reset_circuit_breakers()

    @pytest.mark.asyncio
    async def test_clear_cache(self, test_llm_config):
        """Test clearing cache."""
        with patch("llm_client.client.get_provider") as mock_get_provider:
            mock_provider = AsyncMock()
            mock_get_provider.return_value = mock_provider

            with patch("services.shared.llm_client.cache.LLMCache") as mock_cache_class:
                mock_cache = AsyncMock()
                mock_cache.clear_all.return_value = 10
                mock_cache.invalidate_pattern.return_value = 5
                mock_cache_class.return_value = mock_cache

                client = ResilientLLMClient(test_llm_config)

                # Clear all
                count = await client.clear_cache()
                assert count == 10
                mock_cache.clear_all.assert_called_once()

                # Clear pattern
                count = await client.clear_cache("gpt-4*")
                assert count == 5
                mock_cache.invalidate_pattern.assert_called_once_with("gpt-4*")

    @pytest.mark.asyncio
    async def test_context_manager(self, test_llm_config):
        """Test using client as async context manager."""
        with patch("llm_client.client.get_provider") as mock_get_provider:
            mock_provider = AsyncMock()
            mock_get_provider.return_value = mock_provider

            with patch("services.shared.llm_client.cache.LLMCache") as mock_cache_class:
                mock_cache = MagicMock()
                mock_cache_class.return_value = mock_cache

                async with ResilientLLMClient(test_llm_config) as client:
                    assert isinstance(client, ResilientLLMClient)

                # close() should have been called
                mock_cache.close.assert_called_once()

    def test_provider_order_with_preference(self, test_llm_config):
        """Test provider ordering with custom preference."""
        with patch("llm_client.client.get_provider") as mock_get_provider:
            mock_provider = AsyncMock()
            mock_get_provider.return_value = mock_provider

            with patch("services.shared.llm_client.cache.LLMCache") as mock_cache_class:
                mock_cache = MagicMock()
                mock_cache_class.return_value = mock_cache

                client = ResilientLLMClient(test_llm_config)

                # Test default order
                order = client._get_provider_order()
                assert order[0] == "test_openai"  # Primary first

                # Test custom preference
                order = client._get_provider_order(["test_anthropic", "test_openai"])
                assert order[0] == "test_anthropic"

                # Test invalid preference
                order = client._get_provider_order(["nonexistent"])
                assert order[0] == "test_openai"  # Falls back to default
