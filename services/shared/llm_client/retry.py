"""
Retry logic with exponential backoff for LLM client.
"""

import asyncio
import logging
import random
from collections.abc import Callable
from typing import TypeVar

from .config import RetryConfig

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RetryHandler:
    """
    Handles retry logic with exponential backoff and jitter.
    """

    def __init__(self, config: RetryConfig):
        self.config = config

    async def execute_with_retry(
        self,
        func: Callable[..., T],
        *args,
        retryable_exceptions: tuple[type[Exception], ...] = (Exception,),
        **kwargs,
    ) -> T:
        """
        Execute a function with retry logic.

        Args:
            func: Function to execute
            *args: Function arguments
            retryable_exceptions: Tuple of exception types that should trigger retries
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            Last exception encountered if all retries are exhausted
        """
        last_exception = None

        for attempt in range(self.config.max_retries + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)

            except Exception as e:
                last_exception = e

                # Don't retry if this exception type is not retryable
                if not isinstance(e, retryable_exceptions):
                    logger.debug(f"Non-retryable exception: {type(e).__name__}: {e}")
                    raise

                # Don't retry on the last attempt
                if attempt == self.config.max_retries:
                    logger.error(
                        f"All {self.config.max_retries} retry attempts exhausted. "
                        f"Final error: {type(e).__name__}: {e}"
                    )
                    raise

                # Calculate delay for next attempt
                delay = self._calculate_delay(attempt)

                logger.warning(
                    f"Attempt {attempt + 1}/{self.config.max_retries + 1} failed: "
                    f"{type(e).__name__}: {e}. Retrying in {delay:.2f}s"
                )

                await asyncio.sleep(delay)

        # This should never be reached, but just in case
        if last_exception:
            raise last_exception
        else:
            raise RuntimeError("Unexpected error in retry logic")

    def _calculate_delay(self, attempt: int) -> float:
        """
        Calculate the delay for the next retry attempt.

        Args:
            attempt: Current attempt number (0-based)

        Returns:
            Delay in seconds
        """
        # Exponential backoff: base_delay * (exponential_base ^ attempt)
        delay = self.config.base_delay * (self.config.exponential_base**attempt)

        # Cap at max_delay
        delay = min(delay, self.config.max_delay)

        # Add jitter to prevent thundering herd
        if self.config.jitter:
            # Add random jitter up to 25% of the delay
            jitter_amount = delay * 0.25
            jitter = random.uniform(-jitter_amount, jitter_amount)
            delay = max(0, delay + jitter)

        return delay

    def get_retry_info(self, attempt: int) -> dict:
        """
        Get information about retry attempts.

        Args:
            attempt: Current attempt number (0-based)

        Returns:
            Dictionary with retry information
        """
        return {
            "attempt": attempt + 1,
            "max_attempts": self.config.max_retries + 1,
            "next_delay": (
                self._calculate_delay(attempt)
                if attempt < self.config.max_retries
                else None
            ),
            "config": {
                "max_retries": self.config.max_retries,
                "base_delay": self.config.base_delay,
                "max_delay": self.config.max_delay,
                "exponential_base": self.config.exponential_base,
                "jitter": self.config.jitter,
            },
        }
