"""
Custom exceptions for the LLM client module.
"""


class LLMClientError(Exception):
    """Base exception for LLM client errors."""

    pass


class LLMProviderError(LLMClientError):
    """Exception raised when an LLM provider fails."""

    def __init__(self, provider: str, message: str, status_code: int = None):
        self.provider = provider
        self.status_code = status_code
        super().__init__(f"Provider {provider} failed: {message}")


class LLMTimeoutError(LLMClientError):
    """Exception raised when an LLM request times out."""

    def __init__(self, provider: str, timeout: float):
        self.provider = provider
        self.timeout = timeout
        super().__init__(f"Request to {provider} timed out after {timeout}s")


class CircuitBreakerOpenError(LLMClientError):
    """Exception raised when the circuit breaker is open."""

    def __init__(self, provider: str, failure_count: int):
        self.provider = provider
        self.failure_count = failure_count
        super().__init__(
            f"Circuit breaker open for {provider} after {failure_count} failures"
        )


class LLMConfigurationError(LLMClientError):
    """Exception raised when LLM configuration is invalid."""

    pass


class CacheError(LLMClientError):
    """Exception raised when cache operations fail."""

    pass
