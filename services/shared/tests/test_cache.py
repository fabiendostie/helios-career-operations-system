"""
Tests for LLM cache implementation.
"""

import json
import os
import sys
from unittest.mock import patch

import pytest
import redis

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_client.cache import LLMCache
from llm_client.config import CacheConfig
from llm_client.exceptions import CacheError


class TestLLMCache:
    """Test LLMCache class."""

    @pytest.mark.asyncio
    async def test_cache_disabled(self):
        """Test cache behavior when disabled."""
        config = CacheConfig(enabled=False)
        cache = LLMCache(config)

        result = await cache.get("test prompt", "gpt-4")
        assert result is None

        success = await cache.set("test prompt", "gpt-4", {"content": "response"})
        assert success is False

    @patch("redis.from_url")
    def test_redis_initialization_success(
        self, mock_redis_from_url, test_cache_config, mock_redis
    ):
        """Test successful Redis initialization."""
        mock_redis_from_url.return_value = mock_redis

        cache = LLMCache(test_cache_config)

        mock_redis_from_url.assert_called_once_with(
            test_cache_config.redis_url,
            decode_responses=True,
            socket_timeout=5.0,
            socket_connect_timeout=5.0,
            retry_on_timeout=True,
        )
        mock_redis.ping.assert_called_once()

    @patch("redis.from_url")
    def test_redis_initialization_failure(self, mock_redis_from_url, test_cache_config):
        """Test Redis initialization failure."""
        mock_redis_from_url.side_effect = redis.ConnectionError("Connection failed")

        cache = LLMCache(test_cache_config)

        # Should handle failure gracefully
        assert cache._redis_client is None

    @pytest.mark.asyncio
    @patch("redis.from_url")
    async def test_cache_key_generation(
        self, mock_redis_from_url, test_cache_config, mock_redis
    ):
        """Test cache key generation is consistent."""
        mock_redis_from_url.return_value = mock_redis
        cache = LLMCache(test_cache_config)

        # Same inputs should generate same key
        key1 = cache._generate_cache_key("test prompt", "gpt-4", temperature=0.7)
        key2 = cache._generate_cache_key("test prompt", "gpt-4", temperature=0.7)
        assert key1 == key2

        # Different inputs should generate different keys
        key3 = cache._generate_cache_key("different prompt", "gpt-4", temperature=0.7)
        assert key1 != key3

        key4 = cache._generate_cache_key("test prompt", "gpt-3.5", temperature=0.7)
        assert key1 != key4

        key5 = cache._generate_cache_key("test prompt", "gpt-4", temperature=0.5)
        assert key1 != key5

    @pytest.mark.asyncio
    @patch("redis.from_url")
    async def test_cache_get_hit(
        self, mock_redis_from_url, test_cache_config, mock_redis
    ):
        """Test cache hit scenario."""
        mock_redis_from_url.return_value = mock_redis

        cached_response = {"content": "cached response", "model": "gpt-4"}
        mock_redis.get.return_value = json.dumps(cached_response)

        cache = LLMCache(test_cache_config)
        result = await cache.get("test prompt", "gpt-4")

        assert result == cached_response
        mock_redis.get.assert_called_once()

    @pytest.mark.asyncio
    @patch("redis.from_url")
    async def test_cache_get_miss(
        self, mock_redis_from_url, test_cache_config, mock_redis
    ):
        """Test cache miss scenario."""
        mock_redis_from_url.return_value = mock_redis
        mock_redis.get.return_value = None

        cache = LLMCache(test_cache_config)
        result = await cache.get("test prompt", "gpt-4")

        assert result is None
        mock_redis.get.assert_called_once()

    @pytest.mark.asyncio
    @patch("redis.from_url")
    async def test_cache_get_error(
        self, mock_redis_from_url, test_cache_config, mock_redis
    ):
        """Test cache get with Redis error."""
        mock_redis_from_url.return_value = mock_redis
        mock_redis.get.side_effect = redis.ConnectionError("Connection lost")

        cache = LLMCache(test_cache_config)
        result = await cache.get("test prompt", "gpt-4")

        # Should return None on error, not raise
        assert result is None

    @pytest.mark.asyncio
    @patch("redis.from_url")
    async def test_cache_set_success(
        self, mock_redis_from_url, test_cache_config, mock_redis
    ):
        """Test successful cache set."""
        mock_redis_from_url.return_value = mock_redis
        mock_redis.setex.return_value = True

        cache = LLMCache(test_cache_config)
        response = {"content": "test response", "model": "gpt-4"}

        result = await cache.set("test prompt", "gpt-4", response)

        assert result is True
        mock_redis.setex.assert_called_once()
        # Check that the call included TTL
        args, kwargs = mock_redis.setex.call_args
        assert args[1] == test_cache_config.ttl  # TTL argument

    @pytest.mark.asyncio
    @patch("redis.from_url")
    async def test_cache_set_custom_ttl(
        self, mock_redis_from_url, test_cache_config, mock_redis
    ):
        """Test cache set with custom TTL."""
        mock_redis_from_url.return_value = mock_redis
        mock_redis.setex.return_value = True

        cache = LLMCache(test_cache_config)
        response = {"content": "test response", "model": "gpt-4"}
        custom_ttl = 7200

        result = await cache.set("test prompt", "gpt-4", response, ttl=custom_ttl)

        assert result is True
        args, kwargs = mock_redis.setex.call_args
        assert args[1] == custom_ttl  # Custom TTL

    @pytest.mark.asyncio
    @patch("redis.from_url")
    async def test_cache_set_error(
        self, mock_redis_from_url, test_cache_config, mock_redis
    ):
        """Test cache set with Redis error."""
        mock_redis_from_url.return_value = mock_redis
        mock_redis.setex.side_effect = redis.ConnectionError("Connection lost")

        cache = LLMCache(test_cache_config)
        response = {"content": "test response", "model": "gpt-4"}

        result = await cache.set("test prompt", "gpt-4", response)

        # Should return False on error, not raise
        assert result is False

    @patch("redis.from_url")
    def test_invalidate_pattern(
        self, mock_redis_from_url, test_cache_config, mock_redis
    ):
        """Test cache invalidation by pattern."""
        mock_redis_from_url.return_value = mock_redis
        mock_redis.keys.return_value = ["key1", "key2", "key3"]
        mock_redis.delete.return_value = 3

        cache = LLMCache(test_cache_config)
        result = cache.invalidate_pattern("gpt-4*")

        assert result == 3
        mock_redis.keys.assert_called_once_with(
            f"{test_cache_config.key_prefix}:gpt-4*"
        )
        mock_redis.delete.assert_called_once_with("key1", "key2", "key3")

    @patch("redis.from_url")
    def test_invalidate_pattern_no_keys(
        self, mock_redis_from_url, test_cache_config, mock_redis
    ):
        """Test cache invalidation when no keys match."""
        mock_redis_from_url.return_value = mock_redis
        mock_redis.keys.return_value = []

        cache = LLMCache(test_cache_config)
        result = cache.invalidate_pattern("nonexistent*")

        assert result == 0
        mock_redis.delete.assert_not_called()

    @patch("redis.from_url")
    def test_invalidate_pattern_error(
        self, mock_redis_from_url, test_cache_config, mock_redis
    ):
        """Test cache invalidation with Redis error."""
        mock_redis_from_url.return_value = mock_redis
        mock_redis.keys.side_effect = redis.ConnectionError("Connection lost")

        cache = LLMCache(test_cache_config)

        with pytest.raises(CacheError, match="Failed to invalidate cache pattern"):
            cache.invalidate_pattern("test*")

    @patch("redis.from_url")
    def test_clear_all(self, mock_redis_from_url, test_cache_config, mock_redis):
        """Test clearing all cache entries."""
        mock_redis_from_url.return_value = mock_redis
        mock_redis.keys.return_value = ["key1", "key2"]
        mock_redis.delete.return_value = 2

        cache = LLMCache(test_cache_config)
        result = cache.clear_all()

        assert result == 2
        mock_redis.keys.assert_called_once_with(f"{test_cache_config.key_prefix}:*")

    @patch("redis.from_url")
    def test_get_stats_success(
        self, mock_redis_from_url, test_cache_config, mock_redis
    ):
        """Test getting cache statistics successfully."""
        mock_redis_from_url.return_value = mock_redis
        mock_redis.info.return_value = {
            "used_memory_human": "2.5M",
            "connected_clients": 5,
        }
        mock_redis.keys.return_value = ["key1", "key2", "key3"]

        cache = LLMCache(test_cache_config)
        stats = cache.get_stats()

        assert stats["enabled"] is True
        assert stats["redis_connected"] is True
        assert stats["cached_keys"] == 3
        assert stats["redis_memory_used"] == "2.5M"
        assert stats["redis_connected_clients"] == 5
        assert stats["cache_ttl"] == test_cache_config.ttl
        assert stats["key_prefix"] == test_cache_config.key_prefix

    @patch("redis.from_url")
    def test_get_stats_error(self, mock_redis_from_url, test_cache_config, mock_redis):
        """Test getting cache statistics with error."""
        mock_redis_from_url.return_value = mock_redis
        mock_redis.info.side_effect = redis.ConnectionError("Connection lost")

        cache = LLMCache(test_cache_config)
        stats = cache.get_stats()

        assert stats["enabled"] is True
        assert stats["redis_connected"] is False
        assert "error" in stats

    def test_get_stats_disabled(self):
        """Test getting cache statistics when disabled."""
        config = CacheConfig(enabled=False)
        cache = LLMCache(config)

        stats = cache.get_stats()

        assert stats["enabled"] is False
        assert stats["redis_connected"] is False

    @patch("redis.from_url")
    def test_close_connection(self, mock_redis_from_url, test_cache_config, mock_redis):
        """Test closing Redis connection."""
        mock_redis_from_url.return_value = mock_redis

        cache = LLMCache(test_cache_config)
        cache.close()

        mock_redis.close.assert_called_once()
        assert cache._redis_client is None

    @patch("redis.from_url")
    def test_close_connection_error(
        self, mock_redis_from_url, test_cache_config, mock_redis
    ):
        """Test closing Redis connection with error."""
        mock_redis_from_url.return_value = mock_redis
        mock_redis.close.side_effect = redis.ConnectionError("Close failed")

        cache = LLMCache(test_cache_config)
        cache.close()  # Should not raise

        assert cache._redis_client is None
