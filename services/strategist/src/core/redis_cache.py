"""Redis-based caching for vector embeddings and role data in multi-instance deployments."""

import logging
import json
import pickle
import hashlib
from typing import Optional, Dict, Any, List
import numpy as np

try:
    import redis.asyncio as redis
    from redis.asyncio import ConnectionPool
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logging.warning("Redis not available. Install redis package for distributed caching.")

logger = logging.getLogger(__name__)


class RedisVectorCache:
    """Redis-based cache for skill vectors and role embeddings."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379", 
                 ttl: int = 3600, 
                 key_prefix: str = "strategist"):
        """Initialize Redis cache.
        
        Args:
            redis_url: Redis connection URL
            ttl: Time to live for cached items in seconds (default: 1 hour)
            key_prefix: Prefix for all cache keys to avoid collisions
        """
        self.redis_url = redis_url
        self.ttl = ttl
        self.key_prefix = key_prefix
        self.redis_client: Optional[redis.Redis] = None
        self.pool: Optional[ConnectionPool] = None
        self._connected = False
        
    async def connect(self) -> bool:
        """Establish connection to Redis server."""
        if not REDIS_AVAILABLE:
            logger.warning("Redis package not available. Running without distributed cache.")
            return False
        
        try:
            # Create connection pool for better performance
            self.pool = ConnectionPool.from_url(
                self.redis_url,
                max_connections=50,
                decode_responses=False  # We'll handle encoding ourselves for numpy arrays
            )
            
            self.redis_client = redis.Redis(connection_pool=self.pool)
            
            # Test connection
            await self.redis_client.ping()
            
            self._connected = True
            logger.info(f"Connected to Redis at {self.redis_url}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._connected = False
            return False
    
    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
            if self.pool:
                await self.pool.disconnect()
            self._connected = False
            logger.info("Disconnected from Redis")
    
    def _make_key(self, namespace: str, identifier: str) -> str:
        """Generate a cache key with namespace and identifier."""
        # Use hash for long identifiers to keep key size manageable
        if len(identifier) > 100:
            identifier = hashlib.md5(identifier.encode()).hexdigest()
        
        return f"{self.key_prefix}:{namespace}:{identifier}"
    
    async def get_vector(self, text: str) -> Optional[np.ndarray]:
        """Get cached vector embedding for text.
        
        Args:
            text: The text that was embedded
            
        Returns:
            Numpy array if found in cache, None otherwise
        """
        if not self._connected:
            return None
        
        try:
            key = self._make_key("vector", text.lower())
            data = await self.redis_client.get(key)
            
            if data:
                # Deserialize numpy array
                vector = pickle.loads(data)
                logger.debug(f"Cache hit for vector: {text[:50]}...")
                return vector
            
            return None
            
        except Exception as e:
            logger.warning(f"Error retrieving vector from cache: {e}")
            return None
    
    async def set_vector(self, text: str, vector: np.ndarray) -> bool:
        """Cache a vector embedding.
        
        Args:
            text: The text that was embedded
            vector: The numpy array embedding
            
        Returns:
            True if successfully cached, False otherwise
        """
        if not self._connected:
            return False
        
        try:
            key = self._make_key("vector", text.lower())
            # Serialize numpy array
            data = pickle.dumps(vector, protocol=pickle.HIGHEST_PROTOCOL)
            
            # Set with TTL
            await self.redis_client.setex(key, self.ttl, data)
            logger.debug(f"Cached vector for: {text[:50]}...")
            return True
            
        except Exception as e:
            logger.warning(f"Error caching vector: {e}")
            return False
    
    async def get_role_vectors(self, role_ids: List[str]) -> Dict[str, np.ndarray]:
        """Get multiple role vectors from cache.
        
        Args:
            role_ids: List of role IDs to retrieve
            
        Returns:
            Dictionary mapping role_id to vector for found items
        """
        if not self._connected or not role_ids:
            return {}
        
        try:
            # Prepare keys
            keys = [self._make_key("role_vector", role_id) for role_id in role_ids]
            
            # Batch get for efficiency
            values = await self.redis_client.mget(keys)
            
            # Build result dictionary
            result = {}
            for role_id, value in zip(role_ids, values):
                if value:
                    result[role_id] = pickle.loads(value)
            
            if result:
                logger.debug(f"Cache hit for {len(result)}/{len(role_ids)} role vectors")
            
            return result
            
        except Exception as e:
            logger.warning(f"Error retrieving role vectors from cache: {e}")
            return {}
    
    async def set_role_vectors(self, role_vectors: Dict[str, np.ndarray]) -> int:
        """Cache multiple role vectors.
        
        Args:
            role_vectors: Dictionary mapping role_id to vector
            
        Returns:
            Number of vectors successfully cached
        """
        if not self._connected or not role_vectors:
            return 0
        
        try:
            # Use pipeline for batch operations
            pipe = self.redis_client.pipeline()
            
            for role_id, vector in role_vectors.items():
                key = self._make_key("role_vector", role_id)
                data = pickle.dumps(vector, protocol=pickle.HIGHEST_PROTOCOL)
                pipe.setex(key, self.ttl, data)
            
            # Execute pipeline
            results = await pipe.execute()
            
            success_count = sum(1 for r in results if r)
            logger.info(f"Cached {success_count} role vectors")
            
            return success_count
            
        except Exception as e:
            logger.warning(f"Error caching role vectors: {e}")
            return 0
    
    async def get_candidate_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get cached candidate profile.
        
        Args:
            user_id: User identifier
            
        Returns:
            Candidate profile dictionary if found, None otherwise
        """
        if not self._connected:
            return None
        
        try:
            key = self._make_key("candidate_profile", user_id)
            data = await self.redis_client.get(key)
            
            if data:
                profile = json.loads(data)
                logger.debug(f"Cache hit for candidate profile: {user_id}")
                return profile
            
            return None
            
        except Exception as e:
            logger.warning(f"Error retrieving candidate profile from cache: {e}")
            return None
    
    async def set_candidate_profile(self, user_id: str, profile: Dict[str, Any]) -> bool:
        """Cache a candidate profile.
        
        Args:
            user_id: User identifier
            profile: Candidate profile dictionary
            
        Returns:
            True if successfully cached, False otherwise
        """
        if not self._connected:
            return False
        
        try:
            key = self._make_key("candidate_profile", user_id)
            data = json.dumps(profile)
            
            # Set with longer TTL for candidate profiles (they change less frequently)
            await self.redis_client.setex(key, self.ttl * 2, data)
            logger.debug(f"Cached candidate profile for: {user_id}")
            return True
            
        except Exception as e:
            logger.warning(f"Error caching candidate profile: {e}")
            return False
    
    async def get_career_recommendations(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get cached career recommendations for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Career recommendations if found and still valid, None otherwise
        """
        if not self._connected:
            return None
        
        try:
            key = self._make_key("career_recommendations", user_id)
            data = await self.redis_client.get(key)
            
            if data:
                recommendations = json.loads(data)
                logger.debug(f"Cache hit for career recommendations: {user_id}")
                return recommendations
            
            return None
            
        except Exception as e:
            logger.warning(f"Error retrieving career recommendations from cache: {e}")
            return None
    
    async def set_career_recommendations(self, user_id: str, 
                                        recommendations: Dict[str, Any]) -> bool:
        """Cache career recommendations.
        
        Args:
            user_id: User identifier
            recommendations: Career recommendations dictionary
            
        Returns:
            True if successfully cached, False otherwise
        """
        if not self._connected:
            return False
        
        try:
            key = self._make_key("career_recommendations", user_id)
            data = json.dumps(recommendations)
            
            # Shorter TTL for recommendations as they may change with new data
            await self.redis_client.setex(key, self.ttl // 2, data)
            logger.info(f"Cached career recommendations for: {user_id}")
            return True
            
        except Exception as e:
            logger.warning(f"Error caching career recommendations: {e}")
            return False
    
    async def invalidate_user_cache(self, user_id: str) -> int:
        """Invalidate all cached data for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Number of keys deleted
        """
        if not self._connected:
            return 0
        
        try:
            # Delete specific user-related keys
            keys_to_delete = [
                self._make_key("candidate_profile", user_id),
                self._make_key("career_recommendations", user_id)
            ]
            
            deleted = 0
            for key in keys_to_delete:
                result = await self.redis_client.delete(key)
                deleted += result
            
            if deleted:
                logger.info(f"Invalidated {deleted} cache entries for user: {user_id}")
            
            return deleted
            
        except Exception as e:
            logger.warning(f"Error invalidating user cache: {e}")
            return 0
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        if not self._connected:
            return {"connected": False}
        
        try:
            info = await self.redis_client.info("stats")
            memory_info = await self.redis_client.info("memory")
            
            # Count keys by pattern
            vector_keys = await self.redis_client.keys(f"{self.key_prefix}:vector:*")
            role_keys = await self.redis_client.keys(f"{self.key_prefix}:role_vector:*")
            profile_keys = await self.redis_client.keys(f"{self.key_prefix}:candidate_profile:*")
            
            stats = {
                "connected": True,
                "total_connections": info.get("total_connections_received", 0),
                "used_memory_mb": memory_info.get("used_memory", 0) / (1024 * 1024),
                "cached_vectors": len(vector_keys),
                "cached_role_vectors": len(role_keys),
                "cached_profiles": len(profile_keys),
                "hit_rate": info.get("keyspace_hits", 0) / max(1, info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0))
            }
            
            return stats
            
        except Exception as e:
            logger.warning(f"Error getting cache stats: {e}")
            return {"connected": True, "error": str(e)}
    
    async def flush_namespace(self, namespace: str) -> int:
        """Flush all keys in a specific namespace.
        
        Args:
            namespace: The namespace to flush (e.g., "vector", "role_vector")
            
        Returns:
            Number of keys deleted
        """
        if not self._connected:
            return 0
        
        try:
            pattern = f"{self.key_prefix}:{namespace}:*"
            keys = await self.redis_client.keys(pattern)
            
            if keys:
                deleted = await self.redis_client.delete(*keys)
                logger.info(f"Flushed {deleted} keys from namespace: {namespace}")
                return deleted
            
            return 0
            
        except Exception as e:
            logger.warning(f"Error flushing namespace {namespace}: {e}")
            return 0


class CacheManager:
    """Manages caching strategy with fallback to local cache."""
    
    def __init__(self, redis_url: Optional[str] = None, enable_redis: bool = True):
        """Initialize cache manager.
        
        Args:
            redis_url: Redis connection URL (None for default)
            enable_redis: Whether to attempt Redis connection
        """
        self.redis_cache: Optional[RedisVectorCache] = None
        self.local_cache: Dict[str, Any] = {}
        self.enable_redis = enable_redis and REDIS_AVAILABLE
        
        if self.enable_redis:
            redis_url = redis_url or "redis://localhost:6379"
            self.redis_cache = RedisVectorCache(redis_url=redis_url)
    
    async def initialize(self) -> None:
        """Initialize cache connections."""
        if self.redis_cache:
            connected = await self.redis_cache.connect()
            if not connected:
                logger.warning("Redis connection failed. Using local cache only.")
                self.redis_cache = None
    
    async def shutdown(self) -> None:
        """Shutdown cache connections."""
        if self.redis_cache:
            await self.redis_cache.disconnect()
    
    async def get_vector(self, text: str) -> Optional[np.ndarray]:
        """Get vector from cache (Redis first, then local)."""
        # Try Redis first
        if self.redis_cache:
            vector = await self.redis_cache.get_vector(text)
            if vector is not None:
                return vector
        
        # Fallback to local cache
        key = f"vector:{text.lower()}"
        return self.local_cache.get(key)
    
    async def set_vector(self, text: str, vector: np.ndarray) -> None:
        """Set vector in cache (both Redis and local)."""
        # Cache in Redis
        if self.redis_cache:
            await self.redis_cache.set_vector(text, vector)
        
        # Also cache locally for fallback
        key = f"vector:{text.lower()}"
        self.local_cache[key] = vector
        
        # Limit local cache size
        if len(self.local_cache) > 1000:
            # Remove oldest entries (simple FIFO)
            keys_to_remove = list(self.local_cache.keys())[:100]
            for k in keys_to_remove:
                del self.local_cache[k]
    
    def get_local_cache_stats(self) -> Dict[str, Any]:
        """Get local cache statistics."""
        return {
            "entries": len(self.local_cache),
            "memory_estimate_mb": len(self.local_cache) * 0.001  # Rough estimate
        }
    
    async def get_full_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        stats = {
            "local": self.get_local_cache_stats(),
            "redis": None
        }
        
        if self.redis_cache:
            stats["redis"] = await self.redis_cache.get_stats()
        
        return stats