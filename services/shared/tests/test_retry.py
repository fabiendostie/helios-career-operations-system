"""
Tests for retry logic implementation.
"""

import os
import sys
import time

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_client.config import RetryConfig
from llm_client.retry import RetryHandler


class TestRetryHandler:
    """Test RetryHandler class."""

    @pytest.mark.asyncio
    async def test_successful_execution_no_retry(self, test_retry_config):
        """Test successful execution on first try."""
        handler = RetryHandler(test_retry_config)

        async def success_func():
            return "success"

        result = await handler.execute_with_retry(success_func)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_sync_function_support(self, test_retry_config):
        """Test retry handler works with sync functions."""
        handler = RetryHandler(test_retry_config)

        def sync_success_func():
            return "sync success"

        result = await handler.execute_with_retry(sync_success_func)
        assert result == "sync success"

    @pytest.mark.asyncio
    async def test_eventual_success_after_retries(self, test_retry_config):
        """Test eventual success after some failures."""
        handler = RetryHandler(test_retry_config)
        call_count = 0

        async def eventually_succeeds():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError(f"Attempt {call_count} failed")
            return f"success on attempt {call_count}"

        result = await handler.execute_with_retry(eventually_succeeds)
        assert result == "success on attempt 3"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_all_retries_exhausted(self, test_retry_config):
        """Test behavior when all retries are exhausted."""
        test_retry_config.max_retries = 2
        handler = RetryHandler(test_retry_config)
        call_count = 0

        async def always_fails():
            nonlocal call_count
            call_count += 1
            raise ValueError(f"Attempt {call_count} failed")

        with pytest.raises(ValueError, match="Attempt 3 failed"):
            await handler.execute_with_retry(always_fails)

        assert call_count == 3  # Initial call + 2 retries

    @pytest.mark.asyncio
    async def test_non_retryable_exception(self, test_retry_config):
        """Test that non-retryable exceptions are not retried."""
        handler = RetryHandler(test_retry_config)
        call_count = 0

        async def raises_non_retryable():
            nonlocal call_count
            call_count += 1
            raise KeyboardInterrupt("Should not be retried")

        with pytest.raises(KeyboardInterrupt):
            await handler.execute_with_retry(
                raises_non_retryable, retryable_exceptions=(ValueError, ConnectionError)
            )

        assert call_count == 1  # Should not have retried

    @pytest.mark.asyncio
    async def test_specific_retryable_exceptions(self, test_retry_config):
        """Test retrying only specific exception types."""
        handler = RetryHandler(test_retry_config)
        call_count = 0

        async def raises_retryable():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError(f"Connection failed on attempt {call_count}")
            return "success"

        result = await handler.execute_with_retry(
            raises_retryable, retryable_exceptions=(ConnectionError, TimeoutError)
        )

        assert result == "success"
        assert call_count == 3

    def test_delay_calculation_exponential(self):
        """Test exponential backoff delay calculation."""
        config = RetryConfig(
            base_delay=1.0, exponential_base=2.0, max_delay=10.0, jitter=False
        )
        handler = RetryHandler(config)

        # Test exponential growth
        assert handler._calculate_delay(0) == 1.0  # 1.0 * 2^0
        assert handler._calculate_delay(1) == 2.0  # 1.0 * 2^1
        assert handler._calculate_delay(2) == 4.0  # 1.0 * 2^2
        assert handler._calculate_delay(3) == 8.0  # 1.0 * 2^3

    def test_delay_calculation_max_cap(self):
        """Test delay is capped at max_delay."""
        config = RetryConfig(
            base_delay=1.0, exponential_base=2.0, max_delay=5.0, jitter=False
        )
        handler = RetryHandler(config)

        # Should be capped at max_delay
        assert handler._calculate_delay(10) == 5.0

    def test_delay_calculation_with_jitter(self):
        """Test delay calculation includes jitter."""
        config = RetryConfig(
            base_delay=4.0,
            exponential_base=1.0,  # No exponential growth
            max_delay=10.0,
            jitter=True,
        )
        handler = RetryHandler(config)

        # With jitter, delays should vary but be around base_delay
        delays = [handler._calculate_delay(0) for _ in range(100)]

        # All delays should be positive
        assert all(d >= 0 for d in delays)

        # Should have some variation (not all the same)
        assert len(set(delays)) > 10

        # Should generally be around base_delay (within jitter range)
        avg_delay = sum(delays) / len(delays)
        assert 3.0 < avg_delay < 5.0  # 4.0 ± 25% jitter range

    def test_get_retry_info(self):
        """Test retry information generation."""
        config = RetryConfig(max_retries=3, base_delay=1.0)
        handler = RetryHandler(config)

        info = handler.get_retry_info(0)
        assert info["attempt"] == 1
        assert info["max_attempts"] == 4  # 3 retries + 1 initial
        assert info["next_delay"] is not None

        info = handler.get_retry_info(3)  # Last attempt
        assert info["attempt"] == 4
        assert info["next_delay"] is None  # No more retries

    @pytest.mark.asyncio
    async def test_timing_with_actual_delays(self):
        """Test that actual delays are applied during retries."""
        config = RetryConfig(
            max_retries=2, base_delay=0.1, exponential_base=2.0, jitter=False
        )
        handler = RetryHandler(config)
        call_times = []

        async def failing_func():
            call_times.append(time.time())
            raise ValueError("Always fails")

        start_time = time.time()

        with pytest.raises(ValueError):
            await handler.execute_with_retry(failing_func)

        # Check that delays were actually applied
        assert len(call_times) == 3  # Initial + 2 retries

        # First retry should be after ~0.1s
        delay1 = call_times[1] - call_times[0]
        assert 0.08 < delay1 < 0.15  # Allow some timing variance

        # Second retry should be after ~0.2s (exponential backoff)
        delay2 = call_times[2] - call_times[1]
        assert 0.18 < delay2 < 0.25  # Allow some timing variance

    @pytest.mark.asyncio
    async def test_function_with_args_and_kwargs(self, test_retry_config):
        """Test retry handler passes arguments correctly."""
        handler = RetryHandler(test_retry_config)

        async def func_with_args(arg1, arg2, kwarg1=None, kwarg2=None):
            return f"{arg1}-{arg2}-{kwarg1}-{kwarg2}"

        result = await handler.execute_with_retry(
            func_with_args, "test1", "test2", kwarg1="kw1", kwarg2="kw2"
        )

        assert result == "test1-test2-kw1-kw2"

    @pytest.mark.asyncio
    async def test_zero_retries_config(self):
        """Test configuration with zero retries."""
        config = RetryConfig(max_retries=0)
        handler = RetryHandler(config)
        call_count = 0

        async def failing_func():
            nonlocal call_count
            call_count += 1
            raise ValueError("Fails immediately")

        with pytest.raises(ValueError):
            await handler.execute_with_retry(failing_func)

        assert call_count == 1  # Only initial call, no retries
