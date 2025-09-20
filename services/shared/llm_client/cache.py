"""
Redis caching implementation for LLM responses.
"""

import hashlib
import json
import logging
from typing import Any

import redis

from .config import CacheConfig
from .exceptions import CacheError

logger = logging.getLogger(__name__)


class LLMCache:
    """
    Redis-based cache for LLM responses to avoid duplicate API calls.
    """

    def __init__(self, config: CacheConfig):
        self.config = config
        self._redis_client: redis.Redis | None = None

        if config.enabled:
            self._init_redis()

    def _init_redis(self) -> None:
        """Initialize Redis connection."""
        try:
            self._redis_client = redis.from_url(
                self.config.redis_url,
                decode_responses=True,
                socket_timeout=5.0,
                socket_connect_timeout=5.0,
                retry_on_timeout=True,
            )
            # Test connection
            self._redis_client.ping()
            logger.info("Redis cache initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize Redis cache: {e}")
            self._redis_client = None

    def _generate_cache_key(self, prompt: str, model: str, **kwargs) -> str:
        """
        Generate a cache key from prompt and parameters.

        Args:
            prompt: The LLM prompt
            model: Model name
            **kwargs: Additional parameters that affect the response

        Returns:
            Cache key string
        """
        # Create a deterministic hash of the prompt and parameters
        cache_data = {
            "prompt": prompt,
            "model": model,
            **{k: v for k, v in kwargs.items() if k not in ["api_key", "headers"]},
        }

        # Sort keys for consistent hashing
        cache_string = json.dumps(cache_data, sort_keys=True)
        cache_hash = hashlib.sha256(cache_string.encode()).hexdigest()

        return f"{self.config.key_prefix}:{cache_hash}"

    async def get(self, prompt: str, model: str, **kwargs) -> dict[str, Any] | None:
        """
        Retrieve cached response for the given prompt and parameters.

        Args:
            prompt: The LLM prompt
            model: Model name
            **kwargs: Additional parameters

        Returns:
            Cached response or None if not found
        """
        if not self.config.enabled or not self._redis_client:
            return None

        try:
            cache_key = self._generate_cache_key(prompt, model, **kwargs)
            cached_data = self._redis_client.get(cache_key)

            if cached_data:
                logger.debug(f"Cache hit for key: {cache_key}")
                return json.loads(cached_data)

            logger.debug(f"Cache miss for key: {cache_key}")
            return None

        except Exception as e:
            logger.warning(f"Cache retrieval error: {e}")
            return None

    async def set(
        self,
        prompt: str,
        model: str,
        response: dict[str, Any],
        ttl: int | None = None,
        **kwargs,
    ) -> bool:
        """
        Cache the LLM response.

        Args:
            prompt: The LLM prompt
            model: Model name
            response: The LLM response to cache
            ttl: Time to live in seconds (optional)
            **kwargs: Additional parameters

        Returns:
            True if cached successfully, False otherwise
        """
        if not self.config.enabled or not self._redis_client:
            return False

        try:
            cache_key = self._generate_cache_key(prompt, model, **kwargs)
            cache_data = json.dumps(response)
            cache_ttl = ttl or self.config.ttl

            result = self._redis_client.setex(cache_key, cache_ttl, cache_data)

            if result:
                logger.debug(
                    f"Cached response for key: {cache_key} (TTL: {cache_ttl}s)"
                )

            return bool(result)

        except Exception as e:
            logger.warning(f"Cache storage error: {e}")
            return False

    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate cache entries matching a pattern.

        Args:
            pattern: Redis key pattern (e.g., "*gpt-4*")

        Returns:
            Number of keys invalidated
        """
        if not self.config.enabled or not self._redis_client:
            return 0

        try:
            full_pattern = f"{self.config.key_prefix}:{pattern}"
            keys = self._redis_client.keys(full_pattern)

            if keys:
                deleted = self._redis_client.delete(*keys)
                logger.info(
                    f"Invalidated {deleted} cache entries matching pattern: {full_pattern}"
                )
                return deleted

            return 0

        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
            raise CacheError(f"Failed to invalidate cache pattern '{pattern}': {e}")

    def clear_all(self) -> int:
        """
        Clear all cache entries with the configured prefix.

        Returns:
            Number of keys cleared
        """
        return self.invalidate_pattern("*")

    def get_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        if not self.config.enabled or not self._redis_client:
            return {"enabled": False, "redis_connected": False}

        try:
            info = self._redis_client.info()
            key_count = len(self._redis_client.keys(f"{self.config.key_prefix}:*"))

            return {
                "enabled": True,
                "redis_connected": True,
                "cached_keys": key_count,
                "redis_memory_used": info.get("used_memory_human", "unknown"),
                "redis_connected_clients": info.get("connected_clients", 0),
                "cache_ttl": self.config.ttl,
                "key_prefix": self.config.key_prefix,
            }

        except Exception as e:
            logger.warning(f"Failed to get cache stats: {e}")
            return {"enabled": True, "redis_connected": False, "error": str(e)}

    def close(self) -> None:
        """Close Redis connection."""
        if self._redis_client:
            try:
                self._redis_client.close()
                logger.info("Redis cache connection closed")
            except Exception as e:
                logger.warning(f"Error closing Redis connection: {e}")
            finally:
                self._redis_client = None
