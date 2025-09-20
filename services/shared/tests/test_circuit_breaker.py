"""
Tests for circuit breaker implementation.
"""

import asyncio
import os
import sys
import time

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_client.circuit_breaker import CircuitBreaker, CircuitBreakerState
from llm_client.exceptions import CircuitBreakerOpenError


class TestCircuitBreaker:
    """Test CircuitBreaker class."""

    def test_initial_state(self, test_circuit_breaker_config):
        """Test circuit breaker starts in closed state."""
        cb = CircuitBreaker(test_circuit_breaker_config, "test")

        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.stats.failure_count == 0
        assert cb.stats.success_count == 0

    def test_successful_call(self, test_circuit_breaker_config):
        """Test successful function call."""
        cb = CircuitBreaker(test_circuit_breaker_config, "test")

        def test_func():
            return "success"

        result = cb.call(test_func)

        assert result == "success"
        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.stats.success_count == 1
        assert cb.stats.failure_count == 0

    def test_failed_call(self, test_circuit_breaker_config):
        """Test failed function call."""
        cb = CircuitBreaker(test_circuit_breaker_config, "test")

        def test_func():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            cb.call(test_func)

        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.stats.failure_count == 1
        assert cb.stats.success_count == 0

    def test_circuit_opens_after_threshold(self, test_circuit_breaker_config):
        """Test circuit breaker opens after failure threshold."""
        test_circuit_breaker_config.failure_threshold = 3
        cb = CircuitBreaker(test_circuit_breaker_config, "test")

        def failing_func():
            raise ValueError("Test error")

        # First 2 failures should keep circuit closed
        for i in range(2):
            with pytest.raises(ValueError):
                cb.call(failing_func)
            assert cb.state == CircuitBreakerState.CLOSED

        # Third failure should open the circuit
        with pytest.raises(ValueError):
            cb.call(failing_func)
        assert cb.state == CircuitBreakerState.OPEN

    def test_circuit_rejects_when_open(self, test_circuit_breaker_config):
        """Test circuit breaker rejects calls when open."""
        test_circuit_breaker_config.failure_threshold = 1
        cb = CircuitBreaker(test_circuit_breaker_config, "test")

        def failing_func():
            raise ValueError("Test error")

        # Cause circuit to open
        with pytest.raises(ValueError):
            cb.call(failing_func)
        assert cb.state == CircuitBreakerState.OPEN

        # Now calls should be rejected
        def success_func():
            return "success"

        with pytest.raises(CircuitBreakerOpenError):
            cb.call(success_func)

    def test_circuit_moves_to_half_open(self, test_circuit_breaker_config):
        """Test circuit breaker moves to half-open after recovery timeout."""
        test_circuit_breaker_config.failure_threshold = 1
        test_circuit_breaker_config.recovery_timeout = 0.1  # 100ms
        cb = CircuitBreaker(test_circuit_breaker_config, "test")

        def failing_func():
            raise ValueError("Test error")

        # Cause circuit to open
        with pytest.raises(ValueError):
            cb.call(failing_func)
        assert cb.state == CircuitBreakerState.OPEN

        # Wait for recovery timeout
        time.sleep(0.2)

        def success_func():
            return "success"

        # Should move to half-open and allow the call
        result = cb.call(success_func)
        assert result == "success"
        assert cb.state == CircuitBreakerState.CLOSED

    def test_half_open_success_closes_circuit(self, test_circuit_breaker_config):
        """Test successful call in half-open state closes circuit."""
        test_circuit_breaker_config.failure_threshold = 1
        test_circuit_breaker_config.recovery_timeout = 0.1
        cb = CircuitBreaker(test_circuit_breaker_config, "test")

        # Force circuit to open
        cb._move_to_open()
        assert cb.state == CircuitBreakerState.OPEN

        # Manually move to half-open
        cb._move_to_half_open()
        assert cb.state == CircuitBreakerState.HALF_OPEN

        def success_func():
            return "success"

        result = cb.call(success_func)
        assert result == "success"
        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.stats.failure_count == 0

    def test_half_open_failure_reopens_circuit(self, test_circuit_breaker_config):
        """Test failed call in half-open state reopens circuit."""
        cb = CircuitBreaker(test_circuit_breaker_config, "test")

        # Manually move to half-open
        cb._move_to_half_open()
        assert cb.state == CircuitBreakerState.HALF_OPEN

        def failing_func():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            cb.call(failing_func)
        assert cb.state == CircuitBreakerState.OPEN

    def test_reset_circuit_breaker(self, test_circuit_breaker_config):
        """Test manually resetting circuit breaker."""
        cb = CircuitBreaker(test_circuit_breaker_config, "test")

        # Force circuit to open
        cb._move_to_open()
        cb.stats.failure_count = 5
        assert cb.state == CircuitBreakerState.OPEN

        # Reset the circuit breaker
        cb.reset()
        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.stats.failure_count == 0

    def test_get_stats(self, test_circuit_breaker_config):
        """Test getting circuit breaker statistics."""
        cb = CircuitBreaker(test_circuit_breaker_config, "test")

        stats = cb.get_stats()

        assert stats["name"] == "test"
        assert stats["state"] == "closed"
        assert stats["failure_count"] == 0
        assert stats["success_count"] == 0
        assert (
            stats["failure_threshold"] == test_circuit_breaker_config.failure_threshold
        )
        assert stats["recovery_timeout"] == test_circuit_breaker_config.recovery_timeout

    def test_ignore_non_expected_exceptions(self, test_circuit_breaker_config):
        """Test circuit breaker ignores non-expected exceptions."""
        test_circuit_breaker_config.expected_exception = ValueError
        cb = CircuitBreaker(test_circuit_breaker_config, "test")

        def func_with_runtime_error():
            raise RuntimeError("Not tracked")

        with pytest.raises(RuntimeError):
            cb.call(func_with_runtime_error)

        # Should not count as failure since it's not the expected exception type
        assert cb.stats.failure_count == 0
        assert cb.state == CircuitBreakerState.CLOSED

    @pytest.mark.asyncio
    async def test_async_function_support(self, test_circuit_breaker_config):
        """Test circuit breaker works with async functions."""
        cb = CircuitBreaker(test_circuit_breaker_config, "test")

        async def async_success_func():
            await asyncio.sleep(0.01)
            return "async success"

        result = cb.call(async_success_func)
        # Since we're not awaiting, we get a coroutine
        assert asyncio.iscoroutine(result)

        # Clean up the coroutine
        result.close()

    def test_time_based_recovery_logic(self, test_circuit_breaker_config):
        """Test time-based recovery logic is working correctly."""
        test_circuit_breaker_config.recovery_timeout = 0.1
        cb = CircuitBreaker(test_circuit_breaker_config, "test")

        # Set last failure time manually
        cb.stats.last_failure_time = time.time() - 0.05  # 50ms ago

        # Should not attempt reset yet
        assert not cb._should_attempt_reset()

        # Wait and check again
        time.sleep(0.1)
        assert cb._should_attempt_reset()
