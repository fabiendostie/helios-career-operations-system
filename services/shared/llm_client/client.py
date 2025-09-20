"""
Main resilient LLM client implementation.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any

from .cache import LLMCache
from .circuit_breaker import CircuitBreaker
from .config import LLMConfig
from .exceptions import (
    CircuitBreakerOpenError,
    LLMClientError,
    LLMConfigurationError,
    LLMProviderError,
    LLMTimeoutError,
)
from .providers import BaseLLMProvider, get_provider
from .retry import RetryHandler

logger = logging.getLogger(__name__)


class ResilientLLMClient:
    """
    Resilient LLM client with caching, retries, fallbacks, and circuit breakers.

    This client provides a robust interface to LLM services with:
    - Redis caching for identical prompts
    - Automatic retries with exponential backoff
    - Fallback between multiple providers
    - Circuit breaker pattern to prevent cascading failures
    - Comprehensive logging and monitoring
    """

    def __init__(self, config: LLMConfig | None = None):
        self.config = config or LLMConfig.from_env()
        self.config.validate()

        # Initialize components
        self.cache = LLMCache(self.config.cache)
        self.retry_handler = RetryHandler(self.config.retry)
        self.circuit_breakers: dict[str, CircuitBreaker] = {}
        self.providers: dict[str, BaseLLMProvider] = {}

        # Initialize providers and circuit breakers
        self._init_providers()
        self._init_circuit_breakers()

        logger.info(
            f"ResilientLLMClient initialized with {len(self.providers)} providers"
        )

    def _init_providers(self) -> None:
        """Initialize all configured providers."""
        for provider_config in self.config.providers:
            try:
                provider = get_provider(provider_config)
                self.providers[provider_config.name] = provider
                logger.info(f"Initialized provider: {provider_config.name}")
            except Exception as e:
                logger.error(
                    f"Failed to initialize provider {provider_config.name}: {e}"
                )

        if not self.providers:
            raise LLMConfigurationError("No providers could be initialized")

    def _init_circuit_breakers(self) -> None:
        """Initialize circuit breakers for each provider."""
        for provider_name in self.providers.keys():
            self.circuit_breakers[provider_name] = CircuitBreaker(
                self.config.circuit_breaker, name=provider_name
            )

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        use_cache: bool = True,
        provider_preference: list[str] | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Generate a response from an LLM with full resilience features.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            use_cache: Whether to use caching (default: True)
            provider_preference: Optional list of preferred providers to try
            **kwargs: Additional parameters passed to the provider

        Returns:
            Dictionary containing:
                - content: The generated text
                - model: Model used
                - provider: Provider used
                - usage: Token usage information
                - cached: Whether response was cached
                - attempts: Number of attempts made

        Raises:
            LLMClientError: When all providers fail or configuration is invalid
        """
        # Check cache first
        if use_cache:
            cached_response = await self._get_cached_response(
                prompt, system_prompt, **kwargs
            )
            if cached_response:
                cached_response["cached"] = True
                cached_response["attempts"] = 0
                logger.info("Returning cached response")
                return cached_response

        # Determine provider order
        provider_order = self._get_provider_order(provider_preference)

        attempts = 0
        last_error = None

        for provider_name in provider_order:
            attempts += 1

            try:
                response = await self._generate_with_provider(
                    provider_name, prompt, system_prompt, **kwargs
                )

                # Cache successful response
                if use_cache:
                    await self._cache_response(
                        prompt, system_prompt, response, **kwargs
                    )

                response["cached"] = False
                response["attempts"] = attempts
                logger.info(
                    f"Successfully generated response using {provider_name} after {attempts} attempts"
                )
                return response

            except CircuitBreakerOpenError as e:
                logger.warning(f"Circuit breaker open for {provider_name}: {e}")
                last_error = e
                continue

            except (LLMProviderError, LLMTimeoutError) as e:
                logger.warning(f"Provider {provider_name} failed: {e}")
                last_error = e
                continue

            except Exception as e:
                logger.error(f"Unexpected error with provider {provider_name}: {e}")
                last_error = e
                continue

        # All providers failed
        error_msg = (
            f"All providers failed after {attempts} attempts. Last error: {last_error}"
        )
        logger.error(error_msg)
        raise LLMClientError(error_msg)

    async def _generate_with_provider(
        self, provider_name: str, prompt: str, system_prompt: str | None, **kwargs
    ) -> dict[str, Any]:
        """Generate response using a specific provider with retries and circuit breaker."""
        provider = self.providers[provider_name]
        circuit_breaker = self.circuit_breakers[provider_name]

        async def _call_provider():
            return await provider.generate(prompt, system_prompt, **kwargs)

        # Execute with circuit breaker and retry logic
        return await circuit_breaker.call(
            self.retry_handler.execute_with_retry,
            _call_provider,
            retryable_exceptions=(
                LLMProviderError,
                LLMTimeoutError,
                asyncio.TimeoutError,
            ),
        )

    def _get_provider_order(self, preference: list[str] | None = None) -> list[str]:
        """
        Determine the order in which to try providers.

        Args:
            preference: Optional list of preferred providers

        Returns:
            Ordered list of provider names to try
        """
        if preference:
            # Filter to only available providers
            available_preference = [p for p in preference if p in self.providers]
            if available_preference:
                # Add remaining providers not in preference
                remaining = [p for p in self.providers if p not in available_preference]
                return available_preference + remaining

        # Default order: primary first, then fallbacks, then any remaining
        order = []

        if self.config.primary_provider in self.providers:
            order.append(self.config.primary_provider)

        for fallback in self.config.fallback_providers:
            if fallback in self.providers and fallback not in order:
                order.append(fallback)

        # Add any remaining providers
        for provider_name in self.providers:
            if provider_name not in order:
                order.append(provider_name)

        return order

    async def _get_cached_response(
        self, prompt: str, system_prompt: str | None, **kwargs
    ) -> dict[str, Any] | None:
        """Attempt to get a cached response."""
        # Use primary provider model for cache key consistency
        model = kwargs.get("model")
        if not model and self.config.primary_provider in self.providers:
            primary_config = self.config.get_provider(self.config.primary_provider)
            model = primary_config.model if primary_config else "unknown"

        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        return await self.cache.get(full_prompt, model or "unknown", **kwargs)

    async def _cache_response(
        self,
        prompt: str,
        system_prompt: str | None,
        response: dict[str, Any],
        **kwargs,
    ) -> None:
        """Cache a successful response."""
        model = response.get("model", "unknown")
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt

        # Don't cache provider-specific metadata
        cache_response = {
            "content": response["content"],
            "model": model,
            "usage": response.get("usage", {}),
        }

        await self.cache.set(full_prompt, model, cache_response, **kwargs)

    def get_status(self) -> dict[str, Any]:
        """
        Get comprehensive status of the client and all components.

        Returns:
            Dictionary with status information
        """
        provider_status = {}
        for name, provider in self.providers.items():
            circuit_breaker = self.circuit_breakers.get(name)
            provider_status[name] = {
                "available": True,
                "circuit_breaker": (
                    circuit_breaker.get_stats() if circuit_breaker else None
                ),
            }

        return {
            "providers": provider_status,
            "cache": self.cache.get_stats(),
            "config": {
                "primary_provider": self.config.primary_provider,
                "fallback_providers": self.config.fallback_providers,
                "retry_config": {
                    "max_retries": self.config.retry.max_retries,
                    "base_delay": self.config.retry.base_delay,
                },
            },
        }

    def reset_circuit_breakers(self, provider_name: str | None = None) -> None:
        """
        Reset circuit breakers.

        Args:
            provider_name: Specific provider to reset, or None for all
        """
        if provider_name:
            if provider_name in self.circuit_breakers:
                self.circuit_breakers[provider_name].reset()
                logger.info(f"Reset circuit breaker for {provider_name}")
            else:
                logger.warning(f"No circuit breaker found for {provider_name}")
        else:
            for name, cb in self.circuit_breakers.items():
                cb.reset()
            logger.info("Reset all circuit breakers")

    async def clear_cache(self, pattern: str | None = None) -> int:
        """
        Clear cache entries.

        Args:
            pattern: Optional pattern to match (None clears all)

        Returns:
            Number of entries cleared
        """
        if pattern:
            return self.cache.invalidate_pattern(pattern)
        else:
            return self.cache.clear_all()

    async def close(self) -> None:
        """Close the client and clean up resources."""
        self.cache.close()
        logger.info("ResilientLLMClient closed")

    @asynccontextmanager
    async def _context_manager(self):
        """Context manager for automatic cleanup."""
        try:
            yield self
        finally:
            await self.close()

    def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
