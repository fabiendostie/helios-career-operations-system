"""
Circuit breaker implementation for LLM client resilience.
"""

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .config import CircuitBreakerConfig
from .exceptions import CircuitBreakerOpenError

logger = logging.getLogger(__name__)


class CircuitBreakerState(Enum):
    """States of the circuit breaker."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreakerStats:
    """Statistics for circuit breaker monitoring."""

    failure_count: int = 0
    success_count: int = 0
    last_failure_time: float | None = None
    state_change_time: float = 0


class CircuitBreaker:
    """
    Circuit breaker implementation to prevent cascading failures.

    The circuit breaker has three states:
    - CLOSED: Normal operation, requests are allowed
    - OPEN: Requests are rejected immediately due to failures
    - HALF_OPEN: Testing state, limited requests allowed
    """

    def __init__(self, config: CircuitBreakerConfig, name: str = "default"):
        self.config = config
        self.name = name
        self.state = CircuitBreakerState.CLOSED
        self.stats = CircuitBreakerStats()
        self.stats.state_change_time = time.time()

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function through the circuit breaker.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerOpenError: When circuit is open
        """
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self._move_to_half_open()
            else:
                raise CircuitBreakerOpenError(self.name, self.stats.failure_count)

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure(e)
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt a reset."""
        if self.stats.last_failure_time is None:
            return False

        time_since_failure = time.time() - self.stats.last_failure_time
        return time_since_failure >= self.config.recovery_timeout

    def _move_to_half_open(self) -> None:
        """Move circuit breaker to half-open state."""
        logger.info(f"Circuit breaker {self.name} moving to HALF_OPEN state")
        self.state = CircuitBreakerState.HALF_OPEN
        self.stats.state_change_time = time.time()

    def _on_success(self) -> None:
        """Handle successful operation."""
        self.stats.success_count += 1

        if self.state == CircuitBreakerState.HALF_OPEN:
            self._move_to_closed()

    def _on_failure(self, exception: Exception) -> None:
        """Handle failed operation."""
        if not isinstance(exception, self.config.expected_exception):
            return

        self.stats.failure_count += 1
        self.stats.last_failure_time = time.time()

        if self.state == CircuitBreakerState.CLOSED:
            if self.stats.failure_count >= self.config.failure_threshold:
                self._move_to_open()
        elif self.state == CircuitBreakerState.HALF_OPEN:
            self._move_to_open()

        logger.warning(
            f"Circuit breaker {self.name} recorded failure {self.stats.failure_count}. "
            f"Exception: {type(exception).__name__}: {exception}"
        )

    def _move_to_open(self) -> None:
        """Move circuit breaker to open state."""
        logger.error(
            f"Circuit breaker {self.name} moving to OPEN state after "
            f"{self.stats.failure_count} failures"
        )
        self.state = CircuitBreakerState.OPEN
        self.stats.state_change_time = time.time()

    def _move_to_closed(self) -> None:
        """Move circuit breaker to closed state."""
        logger.info(f"Circuit breaker {self.name} moving to CLOSED state")
        self.state = CircuitBreakerState.CLOSED
        self.stats.failure_count = 0
        self.stats.state_change_time = time.time()

    def reset(self) -> None:
        """Manually reset the circuit breaker to closed state."""
        logger.info(f"Manually resetting circuit breaker {self.name}")
        self._move_to_closed()

    def get_stats(self) -> dict:
        """Get current circuit breaker statistics."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.stats.failure_count,
            "success_count": self.stats.success_count,
            "last_failure_time": self.stats.last_failure_time,
            "state_change_time": self.stats.state_change_time,
            "failure_threshold": self.config.failure_threshold,
            "recovery_timeout": self.config.recovery_timeout,
        }
