"""
Tests for LLM provider implementations.
"""

import os
import sys
from unittest.mock import AsyncMock, patch

import aiohttp
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_client.config import ProviderConfig
from llm_client.exceptions import LLMProviderError, LLMTimeoutError
from llm_client.providers import (
    AnthropicProvider,
    AzureOpenAIProvider,
    OpenAIProvider,
    get_provider,
)


class TestOpenAIProvider:
    """Test OpenAI provider implementation."""

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession")
    async def test_successful_generation(
        self, mock_session_class, test_provider_config
    ):
        """Test successful response generation."""
        # Setup mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}],
            "model": "gpt-4",
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        }

        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        mock_session_class.return_value.__aenter__.return_value = mock_session

        provider = OpenAIProvider(test_provider_config)
        result = await provider.generate("Test prompt")

        assert result["content"] == "Test response"
        assert result["model"] == "gpt-4"
        assert result["provider"] == "openai"
        assert result["usage"]["total_tokens"] == 15

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession")
    async def test_with_system_prompt(self, mock_session_class, test_provider_config):
        """Test generation with system prompt."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "System guided response"}}],
            "model": "gpt-4",
            "usage": {},
        }

        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        mock_session_class.return_value.__aenter__.return_value = mock_session

        provider = OpenAIProvider(test_provider_config)
        await provider.generate("User prompt", system_prompt="System prompt")

        # Verify the payload included both system and user messages
        call_args = mock_session.post.call_args
        payload = call_args[1]["json"]

        assert len(payload["messages"]) == 2
        assert payload["messages"][0]["role"] == "system"
        assert payload["messages"][0]["content"] == "System prompt"
        assert payload["messages"][1]["role"] == "user"
        assert payload["messages"][1]["content"] == "User prompt"

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession")
    async def test_api_error_response(self, mock_session_class, test_provider_config):
        """Test handling of API error responses."""
        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.text.return_value = "Bad Request: Invalid parameters"

        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        mock_session_class.return_value.__aenter__.return_value = mock_session

        provider = OpenAIProvider(test_provider_config)

        with pytest.raises(LLMProviderError) as exc_info:
            await provider.generate("Test prompt")

        assert exc_info.value.provider == "openai"
        assert exc_info.value.status_code == 400
        assert "Bad Request" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession")
    async def test_timeout_error(self, mock_session_class, test_provider_config):
        """Test handling of timeout errors."""
        mock_session = AsyncMock()
        mock_session.post.side_effect = TimeoutError()
        mock_session_class.return_value.__aenter__.return_value = mock_session

        provider = OpenAIProvider(test_provider_config)

        with pytest.raises(LLMTimeoutError) as exc_info:
            await provider.generate("Test prompt")

        assert exc_info.value.provider == "openai"
        assert exc_info.value.timeout == test_provider_config.timeout

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession")
    async def test_client_error(self, mock_session_class, test_provider_config):
        """Test handling of client errors."""
        mock_session = AsyncMock()
        mock_session.post.side_effect = aiohttp.ClientError("Connection failed")
        mock_session_class.return_value.__aenter__.return_value = mock_session

        provider = OpenAIProvider(test_provider_config)

        with pytest.raises(LLMProviderError) as exc_info:
            await provider.generate("Test prompt")

        assert exc_info.value.provider == "openai"
        assert "Client error" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession")
    async def test_custom_parameters(self, mock_session_class, test_provider_config):
        """Test generation with custom parameters."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Custom response"}}],
            "model": "gpt-3.5-turbo",
            "usage": {},
        }

        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        mock_session_class.return_value.__aenter__.return_value = mock_session

        provider = OpenAIProvider(test_provider_config)
        await provider.generate(
            "Test prompt",
            model="gpt-3.5-turbo",
            temperature=0.5,
            max_tokens=500,
            top_p=0.9,
        )

        # Verify custom parameters were included
        call_args = mock_session.post.call_args
        payload = call_args[1]["json"]

        assert payload["model"] == "gpt-3.5-turbo"
        assert payload["temperature"] == 0.5
        assert payload["max_tokens"] == 500
        assert payload["top_p"] == 0.9


class TestAnthropicProvider:
    """Test Anthropic provider implementation."""

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession")
    async def test_successful_generation(
        self, mock_session_class, test_anthropic_config
    ):
        """Test successful response generation."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "content": [{"text": "Anthropic response"}],
            "model": "claude-3-sonnet-20240229",
            "usage": {"input_tokens": 10, "output_tokens": 5},
        }

        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        mock_session_class.return_value.__aenter__.return_value = mock_session

        provider = AnthropicProvider(test_anthropic_config)
        result = await provider.generate("Test prompt")

        assert result["content"] == "Anthropic response"
        assert result["model"] == "claude-3-sonnet-20240229"
        assert result["provider"] == "anthropic"

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession")
    async def test_with_system_prompt(self, mock_session_class, test_anthropic_config):
        """Test generation with system prompt."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "content": [{"text": "System guided response"}],
            "model": "claude-3-sonnet-20240229",
            "usage": {},
        }

        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        mock_session_class.return_value.__aenter__.return_value = mock_session

        provider = AnthropicProvider(test_anthropic_config)
        await provider.generate("User prompt", system_prompt="System prompt")

        # Verify the payload included system prompt separately
        call_args = mock_session.post.call_args
        payload = call_args[1]["json"]

        assert payload["system"] == "System prompt"
        assert len(payload["messages"]) == 1
        assert payload["messages"][0]["role"] == "user"

    def test_header_preparation(self, test_anthropic_config):
        """Test Anthropic-specific header preparation."""
        provider = AnthropicProvider(test_anthropic_config)
        headers = provider._prepare_headers()

        assert headers["x-api-key"] == test_anthropic_config.api_key
        assert headers["anthropic-version"] == "2023-06-01"
        assert headers["Content-Type"] == "application/json"


class TestAzureOpenAIProvider:
    """Test Azure OpenAI provider implementation."""

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession")
    async def test_successful_generation(self, mock_session_class):
        """Test successful response generation."""
        config = ProviderConfig(
            name="azure_openai",
            api_key="test-azure-key",
            base_url="https://test.openai.azure.com",
            model="gpt-4-32k",
        )

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Azure response"}}],
            "model": "gpt-4-32k",
            "usage": {},
        }

        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        mock_session_class.return_value.__aenter__.return_value = mock_session

        provider = AzureOpenAIProvider(config)
        result = await provider.generate("Test prompt")

        assert result["content"] == "Azure response"
        assert result["provider"] == "azure_openai"

        # Verify Azure-specific URL format
        call_args = mock_session.post.call_args
        url = call_args[0][0]
        assert "/openai/deployments/" in url
        assert "api-version=" in url

    def test_header_preparation(self):
        """Test Azure-specific header preparation."""
        config = ProviderConfig(
            name="azure_openai",
            api_key="test-azure-key",
            base_url="https://test.openai.azure.com",
            model="gpt-4",
        )

        provider = AzureOpenAIProvider(config)
        headers = provider._prepare_headers()

        assert headers["api-key"] == "test-azure-key"
        assert headers["Content-Type"] == "application/json"


class TestProviderFactory:
    """Test provider factory function."""

    def test_get_openai_provider(self, test_provider_config):
        """Test getting OpenAI provider."""
        provider = get_provider(test_provider_config)
        assert isinstance(provider, OpenAIProvider)

    def test_get_anthropic_provider(self, test_anthropic_config):
        """Test getting Anthropic provider."""
        provider = get_provider(test_anthropic_config)
        assert isinstance(provider, AnthropicProvider)

    def test_get_azure_provider(self):
        """Test getting Azure OpenAI provider."""
        config = ProviderConfig(
            name="azure_openai",
            api_key="test-key",
            base_url="https://test.openai.azure.com",
            model="gpt-4",
        )

        provider = get_provider(config)
        assert isinstance(provider, AzureOpenAIProvider)

    def test_unsupported_provider(self):
        """Test error for unsupported provider."""
        config = ProviderConfig(
            name="unsupported",
            api_key="test-key",
            base_url="https://example.com",
            model="test-model",
        )

        with pytest.raises(ValueError, match="Unsupported provider: unsupported"):
            get_provider(config)
