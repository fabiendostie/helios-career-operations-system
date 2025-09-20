"""
LLM provider implementations for different APIs.
"""

import logging
from typing import Any

import aiohttp

from .config import ProviderConfig
from .exceptions import LLMProviderError, LLMTimeoutError

logger = logging.getLogger(__name__)


class BaseLLMProvider:
    """Base class for LLM providers."""

    def __init__(self, config: ProviderConfig):
        self.config = config

    async def generate(
        self, prompt: str, system_prompt: str | None = None, **kwargs
    ) -> dict[str, Any]:
        """
        Generate a response from the LLM.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            **kwargs: Additional parameters

        Returns:
            Response dictionary with 'content' and metadata

        Raises:
            LLMProviderError: When the provider fails
            LLMTimeoutError: When the request times out
        """
        raise NotImplementedError("Subclasses must implement generate()")

    def _prepare_headers(self) -> dict[str, str]:
        """Prepare headers for the API request."""
        headers = self.config.headers.copy()
        headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API provider."""

    async def generate(
        self, prompt: str, system_prompt: str | None = None, **kwargs
    ) -> dict[str, Any]:
        """Generate response using OpenAI API."""
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": kwargs.get("model", self.config.model),
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "temperature": kwargs.get("temperature", self.config.temperature),
        }

        # Add any additional parameters
        for key in ["top_p", "frequency_penalty", "presence_penalty", "stop"]:
            if key in kwargs:
                payload[key] = kwargs[key]

        url = f"{self.config.base_url}/chat/completions"
        headers = self._prepare_headers()

        try:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)

            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "content": data["choices"][0]["message"]["content"],
                            "model": data["model"],
                            "usage": data.get("usage", {}),
                            "provider": "openai",
                        }
                    else:
                        error_text = await response.text()
                        raise LLMProviderError(
                            provider="openai",
                            message=f"API error: {error_text}",
                            status_code=response.status,
                        )

        except TimeoutError:
            raise LLMTimeoutError("openai", self.config.timeout)
        except aiohttp.ClientError as e:
            raise LLMProviderError("openai", f"Client error: {e}")
        except Exception as e:
            raise LLMProviderError("openai", f"Unexpected error: {e}")


class AnthropicProvider(BaseLLMProvider):
    """Anthropic API provider."""

    def _prepare_headers(self) -> dict[str, str]:
        """Prepare headers for Anthropic API."""
        headers = self.config.headers.copy()
        headers["x-api-key"] = self.config.api_key
        headers["anthropic-version"] = "2023-06-01"
        return headers

    async def generate(
        self, prompt: str, system_prompt: str | None = None, **kwargs
    ) -> dict[str, Any]:
        """Generate response using Anthropic API."""
        messages = [{"role": "user", "content": prompt}]

        payload = {
            "model": kwargs.get("model", self.config.model),
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "temperature": kwargs.get("temperature", self.config.temperature),
        }

        if system_prompt:
            payload["system"] = system_prompt

        # Add any additional parameters
        for key in ["top_p", "top_k", "stop_sequences"]:
            if key in kwargs:
                payload[key] = kwargs[key]

        url = f"{self.config.base_url}/v1/messages"
        headers = self._prepare_headers()

        try:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)

            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "content": data["content"][0]["text"],
                            "model": data["model"],
                            "usage": data.get("usage", {}),
                            "provider": "anthropic",
                        }
                    else:
                        error_text = await response.text()
                        raise LLMProviderError(
                            provider="anthropic",
                            message=f"API error: {error_text}",
                            status_code=response.status,
                        )

        except TimeoutError:
            raise LLMTimeoutError("anthropic", self.config.timeout)
        except aiohttp.ClientError as e:
            raise LLMProviderError("anthropic", f"Client error: {e}")
        except Exception as e:
            raise LLMProviderError("anthropic", f"Unexpected error: {e}")


class AzureOpenAIProvider(BaseLLMProvider):
    """Azure OpenAI API provider."""

    def _prepare_headers(self) -> dict[str, str]:
        """Prepare headers for Azure OpenAI API."""
        headers = self.config.headers.copy()
        headers["api-key"] = self.config.api_key
        return headers

    async def generate(
        self, prompt: str, system_prompt: str | None = None, **kwargs
    ) -> dict[str, Any]:
        """Generate response using Azure OpenAI API."""
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        payload = {
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "temperature": kwargs.get("temperature", self.config.temperature),
        }

        # Add any additional parameters
        for key in ["top_p", "frequency_penalty", "presence_penalty", "stop"]:
            if key in kwargs:
                payload[key] = kwargs[key]

        # Azure OpenAI uses deployment name in URL
        deployment_name = kwargs.get("deployment_name", self.config.model)
        url = f"{self.config.base_url}/openai/deployments/{deployment_name}/chat/completions?api-version=2023-12-01-preview"
        headers = self._prepare_headers()

        try:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)

            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "content": data["choices"][0]["message"]["content"],
                            "model": data["model"],
                            "usage": data.get("usage", {}),
                            "provider": "azure_openai",
                        }
                    else:
                        error_text = await response.text()
                        raise LLMProviderError(
                            provider="azure_openai",
                            message=f"API error: {error_text}",
                            status_code=response.status,
                        )

        except TimeoutError:
            raise LLMTimeoutError("azure_openai", self.config.timeout)
        except aiohttp.ClientError as e:
            raise LLMProviderError("azure_openai", f"Client error: {e}")
        except Exception as e:
            raise LLMProviderError("azure_openai", f"Unexpected error: {e}")


def get_provider(config: ProviderConfig) -> BaseLLMProvider:
    """
    Factory function to get the appropriate provider instance.

    Args:
        config: Provider configuration

    Returns:
        Provider instance

    Raises:
        ValueError: If provider type is not supported
    """
    provider_map = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "azure_openai": AzureOpenAIProvider,
    }

    provider_class = provider_map.get(config.name)
    if not provider_class:
        raise ValueError(f"Unsupported provider: {config.name}")

    return provider_class(config)
