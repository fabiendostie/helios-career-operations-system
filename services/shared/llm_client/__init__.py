"""
LLM Client module for resilient AI service communication.

This module provides a robust HTTP client wrapper for LLM services with:
- Redis caching for identical prompts
- Automatic retries with exponential backoff
- Fallback logic between providers
- Circuit breaker pattern
- Comprehensive logging
"""

from .client import ResilientLLMClient
from .config import LLMConfig
from .exceptions import (
    CircuitBreakerOpenError,
    LLMClientError,
    LLMProviderError,
    LLMTimeoutError,
)

__all__ = [
    "ResilientLLMClient",
    "LLMConfig",
    "LLMClientError",
    "LLMProviderError",
    "LLMTimeoutError",
    "CircuitBreakerOpenError",
]
