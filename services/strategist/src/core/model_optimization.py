"""ML Model optimization for large transformer models (2.8GB+)."""

import asyncio
import logging
import os
import time
import threading
from typing import Dict, Any, Optional, Tuple, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from contextlib import asynccontextmanager
import weakref
import gc

import numpy as np
from sentence_transformers import SentenceTransformer
import torch
import psutil

logger = logging.getLogger(__name__)


@dataclass
class ModelMetrics:
    """Container for model performance metrics."""
    model_name: str
    memory_usage_mb: float
    load_time_seconds: float
    warmup_time_seconds: float
    embedding_dimension: int
    cache_hit_rate: float = 0.0
    total_requests: int = 0
    avg_inference_time_ms: float = 0.0


class ModelPool:
    """Thread-safe model pool for efficient model reuse."""
    
    def __init__(self, max_models: int = 2):
        """Initialize model pool.
        
        Args:
            max_models: Maximum number of models to keep in memory
        """
        self.max_models = max_models
        self.models: Dict[str, SentenceTransformer] = {}
        self.model_metrics: Dict[str, ModelMetrics] = {}
        self.access_times: Dict[str, float] = {}
        self.lock = threading.RLock()
        self._loading_locks: Dict[str, threading.Lock] = {}
        
    def get_model(self, model_name: str) -> Optional[SentenceTransformer]:
        """Get model from pool (thread-safe)."""
        with self.lock:
            model = self.models.get(model_name)
            if model:
                self.access_times[model_name] = time.time()
            return model
    
    def add_model(self, model_name: str, model: SentenceTransformer) -> None:
        """Add model to pool with LRU eviction."""
        with self.lock:
            # Evict oldest model if at capacity
            if len(self.models) >= self.max_models and model_name not in self.models:
                self._evict_oldest_model()
            
            self.models[model_name] = model
            self.access_times[model_name] = time.time()
    
    def _evict_oldest_model(self) -> None:
        """Evict the least recently used model."""
        if not self.access_times:
            return
        
        # Find oldest model
        oldest_model = min(self.access_times.keys(), 
                          key=lambda x: self.access_times[x])
        
        logger.info(f"Evicting model {oldest_model} from pool (LRU)")
        
        # Clean up
        if oldest_model in self.models:
            del self.models[oldest_model]
        del self.access_times[oldest_model]
        
        # Force garbage collection
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    
    def get_loading_lock(self, model_name: str) -> threading.Lock:
        """Get or create loading lock for model."""
        with self.lock:
            if model_name not in self._loading_locks:
                self._loading_locks[model_name] = threading.Lock()
            return self._loading_locks[model_name]
    
    def clear_all(self) -> None:
        """Clear all models from pool."""
        with self.lock:
            self.models.clear()
            self.access_times.clear()
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()


class EmbeddingCache:
    """High-performance embedding cache with memory management."""
    
    def __init__(self, max_cache_size_mb: int = 512):
        """Initialize embedding cache.
        
        Args:
            max_cache_size_mb: Maximum cache size in megabytes
        """
        self.max_cache_size_mb = max_cache_size_mb
        self.cache: Dict[str, Tuple[np.ndarray, float]] = {}  # key -> (embedding, timestamp)
        self.cache_hits = 0
        self.cache_misses = 0
        self.lock = threading.RLock()
    
    def get(self, key: str) -> Optional[np.ndarray]:
        """Get embedding from cache."""
        with self.lock:
            if key in self.cache:
                embedding, _ = self.cache[key]
                # Update timestamp
                self.cache[key] = (embedding, time.time())
                self.cache_hits += 1
                return embedding
            
            self.cache_misses += 1
            return None
    
    def set(self, key: str, embedding: np.ndarray) -> None:
        """Set embedding in cache with automatic eviction."""
        with self.lock:
            # Check if we need to evict
            current_size_mb = self._estimate_cache_size_mb()
            embedding_size_mb = embedding.nbytes / (1024 * 1024)
            
            # Evict if needed
            if current_size_mb + embedding_size_mb > self.max_cache_size_mb:
                self._evict_old_entries(target_free_mb=embedding_size_mb * 2)
            
            self.cache[key] = (embedding.copy(), time.time())
    
    def _estimate_cache_size_mb(self) -> float:
        """Estimate current cache size in MB."""
        if not self.cache:
            return 0.0
        
        total_bytes = sum(embedding.nbytes for embedding, _ in self.cache.values())
        return total_bytes / (1024 * 1024)
    
    def _evict_old_entries(self, target_free_mb: float) -> None:
        """Evict old entries to free up space."""
        if not self.cache:
            return
        
        # Sort by timestamp (oldest first)
        sorted_items = sorted(self.cache.items(), key=lambda x: x[1][1])
        
        freed_mb = 0.0
        keys_to_remove = []
        
        for key, (embedding, timestamp) in sorted_items:
            if freed_mb >= target_free_mb:
                break
            
            freed_mb += embedding.nbytes / (1024 * 1024)
            keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.cache[key]
        
        logger.debug(f"Evicted {len(keys_to_remove)} cache entries, freed {freed_mb:.1f}MB")
    
    def get_hit_rate(self) -> float:
        """Get cache hit rate."""
        total_requests = self.cache_hits + self.cache_misses
        if total_requests == 0:
            return 0.0
        return self.cache_hits / total_requests
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self.lock:
            return {
                "cache_size_mb": self._estimate_cache_size_mb(),
                "cached_items": len(self.cache),
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses,
                "hit_rate": self.get_hit_rate(),
                "max_cache_size_mb": self.max_cache_size_mb
            }


class OptimizedModelManager:
    """Optimized manager for large ML models with advanced caching and pooling."""
    
    def __init__(self, 
                 max_models_in_pool: int = 2,
                 max_cache_size_mb: int = 512,
                 enable_gpu: bool = True,
                 model_load_timeout: int = 300):
        """Initialize optimized model manager.
        
        Args:
            max_models_in_pool: Maximum models in memory pool
            max_cache_size_mb: Maximum embedding cache size in MB
            enable_gpu: Whether to use GPU acceleration if available
            model_load_timeout: Timeout for model loading in seconds
        """
        self.model_pool = ModelPool(max_models=max_models_in_pool)
        self.embedding_cache = EmbeddingCache(max_cache_size_mb=max_cache_size_mb)
        self.enable_gpu = enable_gpu and torch.cuda.is_available()
        self.model_load_timeout = model_load_timeout
        
        # Performance tracking
        self.request_times: List[float] = []
        self.max_request_history = 1000
        
        # Thread pool for async operations
        self.executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="model-opt")
        
        logger.info(f"OptimizedModelManager initialized - GPU: {self.enable_gpu}, "
                   f"Cache: {max_cache_size_mb}MB, Pool: {max_models_in_pool} models")
    
    async def load_model_optimized(self, model_name: str) -> SentenceTransformer:
        """Load model with optimizations and caching."""
        # Check if already loaded
        model = self.model_pool.get_model(model_name)
        if model:
            return model
        
        # Get loading lock to prevent duplicate loads
        loading_lock = self.model_pool.get_loading_lock(model_name)
        
        # Use thread pool to avoid blocking async event loop
        loop = asyncio.get_event_loop()
        model = await loop.run_in_executor(
            self.executor, 
            self._load_model_sync, 
            model_name, 
            loading_lock
        )
        
        return model
    
    def _load_model_sync(self, model_name: str, loading_lock: threading.Lock) -> SentenceTransformer:
        """Synchronous model loading with optimizations."""
        with loading_lock:
            # Double-check if model was loaded by another thread
            model = self.model_pool.get_model(model_name)
            if model:
                return model
            
            logger.info(f"Loading optimized model: {model_name}")
            start_time = time.time()
            
            # Memory snapshot before loading
            process = psutil.Process()
            memory_before = process.memory_info().rss / (1024 * 1024)  # MB
            
            try:
                # Load model with optimizations
                device = 'cuda' if self.enable_gpu else 'cpu'
                model = SentenceTransformer(
                    model_name,
                    device=device,
                    trust_remote_code=True  # For newer models
                )
                
                # Optimize for inference
                model.eval()
                if self.enable_gpu and torch.cuda.is_available():
                    model = model.half()  # Use half precision for memory efficiency
                
                load_time = time.time() - start_time
                
                # Memory snapshot after loading
                memory_after = process.memory_info().rss / (1024 * 1024)  # MB
                memory_usage = memory_after - memory_before
                
                # Warmup
                warmup_start = time.time()
                _ = model.encode(["warmup"], show_progress_bar=False)
                warmup_time = time.time() - warmup_start
                
                # Create metrics
                metrics = ModelMetrics(
                    model_name=model_name,
                    memory_usage_mb=memory_usage,
                    load_time_seconds=load_time,
                    warmup_time_seconds=warmup_time,
                    embedding_dimension=model.get_sentence_embedding_dimension()
                )
                
                # Add to pool
                self.model_pool.add_model(model_name, model)
                self.model_pool.model_metrics[model_name] = metrics
                
                logger.info(f"Model {model_name} loaded successfully - "
                           f"Load: {load_time:.2f}s, Memory: {memory_usage:.1f}MB, "
                           f"Dimension: {metrics.embedding_dimension}")
                
                return model
                
            except Exception as e:
                logger.error(f"Failed to load model {model_name}: {str(e)}")
                raise RuntimeError(f"Model loading failed: {str(e)}")
    
    async def generate_embeddings_optimized(self, 
                                          texts: List[str], 
                                          model_name: str = "all-MiniLM-L6-v2",
                                          batch_size: int = 32) -> List[np.ndarray]:
        """Generate embeddings with caching and batching optimizations."""
        if not texts:
            return []
        
        start_time = time.time()
        
        # Check cache for existing embeddings
        cached_embeddings = []
        uncached_texts = []
        uncached_indices = []
        
        for i, text in enumerate(texts):
            cache_key = f"{model_name}:{hash(text.strip().lower())}"
            cached = self.embedding_cache.get(cache_key)
            
            if cached is not None:
                cached_embeddings.append((i, cached))
            else:
                uncached_texts.append(text)
                uncached_indices.append(i)
        
        # Generate embeddings for uncached texts
        new_embeddings = []
        if uncached_texts:
            model = await self.load_model_optimized(model_name)
            
            # Process in batches for memory efficiency
            loop = asyncio.get_event_loop()
            
            for batch_start in range(0, len(uncached_texts), batch_size):
                batch_end = min(batch_start + batch_size, len(uncached_texts))
                batch_texts = uncached_texts[batch_start:batch_end]
                
                # Run encoding in thread pool to avoid blocking
                batch_embeddings = await loop.run_in_executor(
                    self.executor,
                    lambda: model.encode(batch_texts, show_progress_bar=False)
                )
                
                # Cache new embeddings
                for text, embedding in zip(batch_texts, batch_embeddings):
                    cache_key = f"{model_name}:{hash(text.strip().lower())}"
                    self.embedding_cache.set(cache_key, embedding)
                
                new_embeddings.extend(batch_embeddings)
        
        # Combine cached and new embeddings in correct order
        result_embeddings = [None] * len(texts)
        
        # Place cached embeddings
        for idx, embedding in cached_embeddings:
            result_embeddings[idx] = embedding
        
        # Place new embeddings
        for i, embedding in enumerate(new_embeddings):
            original_idx = uncached_indices[i]
            result_embeddings[original_idx] = embedding
        
        # Track performance
        total_time = time.time() - start_time
        self.request_times.append(total_time)
        if len(self.request_times) > self.max_request_history:
            self.request_times.pop(0)
        
        # Update metrics
        if model_name in self.model_pool.model_metrics:
            metrics = self.model_pool.model_metrics[model_name]
            metrics.cache_hit_rate = self.embedding_cache.get_hit_rate()
            metrics.total_requests += 1
            metrics.avg_inference_time_ms = np.mean(self.request_times) * 1000
        
        logger.debug(f"Generated {len(result_embeddings)} embeddings in {total_time:.3f}s "
                    f"(cached: {len(cached_embeddings)}, new: {len(new_embeddings)})")
        
        return result_embeddings
    
    def get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage statistics."""
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            "rss_mb": memory_info.rss / (1024 * 1024),
            "vms_mb": memory_info.vms / (1024 * 1024),
            "memory_percent": process.memory_percent(),
            "cache_size_mb": self.embedding_cache._estimate_cache_size_mb()
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics."""
        memory_usage = self.get_memory_usage()
        cache_stats = self.embedding_cache.get_stats()
        
        # Calculate request statistics
        request_stats = {}
        if self.request_times:
            request_stats = {
                "avg_request_time_ms": np.mean(self.request_times) * 1000,
                "p95_request_time_ms": np.percentile(self.request_times, 95) * 1000,
                "p99_request_time_ms": np.percentile(self.request_times, 99) * 1000,
                "total_requests": len(self.request_times)
            }
        
        model_metrics = {}
        for model_name, metrics in self.model_pool.model_metrics.items():
            model_metrics[model_name] = {
                "memory_usage_mb": metrics.memory_usage_mb,
                "load_time_seconds": metrics.load_time_seconds,
                "embedding_dimension": metrics.embedding_dimension,
                "cache_hit_rate": metrics.cache_hit_rate,
                "total_requests": metrics.total_requests,
                "avg_inference_time_ms": metrics.avg_inference_time_ms
            }
        
        return {
            "memory_usage": memory_usage,
            "cache_stats": cache_stats,
            "request_stats": request_stats,
            "model_metrics": model_metrics,
            "gpu_enabled": self.enable_gpu,
            "models_in_pool": len(self.model_pool.models)
        }
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        logger.info("Cleaning up OptimizedModelManager")
        
        # Clear model pool
        self.model_pool.clear_all()
        
        # Clear cache
        with self.embedding_cache.lock:
            self.embedding_cache.cache.clear()
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        
        # Force garbage collection
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        logger.info("OptimizedModelManager cleanup complete")


# Global instance for singleton pattern
_global_model_manager: Optional[OptimizedModelManager] = None
_manager_lock = threading.Lock()


def get_optimized_model_manager(**kwargs) -> OptimizedModelManager:
    """Get global optimized model manager instance."""
    global _global_model_manager
    
    with _manager_lock:
        if _global_model_manager is None:
            _global_model_manager = OptimizedModelManager(**kwargs)
        
        return _global_model_manager


@asynccontextmanager
async def optimized_model_context(**kwargs):
    """Context manager for optimized model operations."""
    manager = get_optimized_model_manager(**kwargs)
    try:
        yield manager
    finally:
        # Cleanup is handled by the singleton instance
        pass