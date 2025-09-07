"""Tests for ML model optimization and performance improvements."""

import asyncio
import time
import pytest
from unittest.mock import Mock, patch, AsyncMock
import numpy as np

from src.core.model_optimization import (
    OptimizedModelManager, ModelPool, EmbeddingCache, ModelMetrics
)
from src.core.optimized_skill_vectorizer import OptimizedSkillVectorizer


class TestModelPool:
    """Test model pool functionality."""
    
    def test_model_pool_basic_operations(self):
        """Test basic model pool operations."""
        pool = ModelPool(max_models=2)
        
        # Mock models
        model1 = Mock()
        model2 = Mock() 
        model3 = Mock()
        
        # Add models
        pool.add_model("model1", model1)
        pool.add_model("model2", model2)
        
        # Retrieve models
        assert pool.get_model("model1") == model1
        assert pool.get_model("model2") == model2
        assert pool.get_model("nonexistent") is None
        
        # Test LRU eviction
        time.sleep(0.01)  # Ensure different timestamps
        pool.add_model("model3", model3)  # Should evict model1 (oldest)
        
        assert pool.get_model("model1") is None
        assert pool.get_model("model2") == model2
        assert pool.get_model("model3") == model3
    
    def test_model_pool_thread_safety(self):
        """Test thread safety of model pool."""
        import threading
        
        pool = ModelPool(max_models=5)
        results = []
        
        def add_models(start_idx: int, count: int):
            for i in range(start_idx, start_idx + count):
                model = Mock()
                pool.add_model(f"model{i}", model)
                results.append(f"added_model{i}")
        
        # Create multiple threads adding models
        threads = []
        for i in range(3):
            thread = threading.Thread(target=add_models, args=(i*10, 5))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Should have added models without errors
        assert len(results) == 15
        assert len(pool.models) <= 5  # Respects max_models limit


class TestEmbeddingCache:
    """Test embedding cache functionality."""
    
    def test_cache_basic_operations(self):
        """Test basic cache operations."""
        cache = EmbeddingCache(max_cache_size_mb=10)
        
        # Create test embeddings
        embedding1 = np.random.rand(384).astype(np.float32)
        embedding2 = np.random.rand(384).astype(np.float32)
        
        # Test set/get
        cache.set("key1", embedding1)
        cache.set("key2", embedding2)
        
        retrieved1 = cache.get("key1")
        retrieved2 = cache.get("key2")
        
        np.testing.assert_array_equal(retrieved1, embedding1)
        np.testing.assert_array_equal(retrieved2, embedding2)
        
        # Test cache miss
        assert cache.get("nonexistent") is None
    
    def test_cache_eviction(self):
        """Test cache eviction when memory limit is reached."""
        # Very small cache to trigger eviction
        cache = EmbeddingCache(max_cache_size_mb=0.001)  # ~1KB
        
        # Add embeddings that exceed cache size
        large_embedding = np.random.rand(1000).astype(np.float32)  # ~4KB
        
        cache.set("key1", large_embedding)
        cache.set("key2", large_embedding)  # Should trigger eviction
        
        # First key should be evicted
        assert cache.get("key1") is None
        assert cache.get("key2") is not None
    
    def test_cache_hit_rate_calculation(self):
        """Test cache hit rate calculation."""
        cache = EmbeddingCache(max_cache_size_mb=10)
        embedding = np.random.rand(100).astype(np.float32)
        
        # Initial hit rate should be 0
        assert cache.get_hit_rate() == 0.0
        
        # Add and access items
        cache.set("key1", embedding)
        cache.get("key1")  # Hit
        cache.get("key2")  # Miss
        
        # Hit rate should be 50%
        assert cache.get_hit_rate() == 0.5


class TestOptimizedModelManager:
    """Test optimized model manager."""
    
    @pytest.fixture
    def mock_sentence_transformer(self):
        """Create mock SentenceTransformer."""
        with patch('src.core.model_optimization.SentenceTransformer') as mock_class:
            mock_model = Mock()
            mock_model.get_sentence_embedding_dimension.return_value = 384
            mock_model.encode.return_value = np.random.rand(2, 384).astype(np.float32)
            mock_model.eval.return_value = mock_model
            mock_model.half.return_value = mock_model
            mock_class.return_value = mock_model
            yield mock_model
    
    @pytest.mark.asyncio
    async def test_model_loading_optimization(self, mock_sentence_transformer):
        """Test optimized model loading."""
        with patch('src.core.model_optimization.torch.cuda.is_available', return_value=False):
            manager = OptimizedModelManager(max_models_in_pool=1)
            
            # Load model
            model = await manager.load_model_optimized("test-model")
            
            assert model is not None
            assert "test-model" in manager.model_pool.models
            assert "test-model" in manager.model_pool.model_metrics
            
            # Verify metrics were created
            metrics = manager.model_pool.model_metrics["test-model"]
            assert isinstance(metrics, ModelMetrics)
            assert metrics.embedding_dimension == 384
    
    @pytest.mark.asyncio
    async def test_embedding_generation_with_caching(self, mock_sentence_transformer):
        """Test embedding generation with caching."""
        with patch('src.core.model_optimization.torch.cuda.is_available', return_value=False):
            manager = OptimizedModelManager(max_cache_size_mb=10)
            
            texts = ["python", "machine learning", "data science"]
            
            # First generation should load model and cache embeddings
            embeddings1 = await manager.generate_embeddings_optimized(texts, "test-model")
            
            assert len(embeddings1) == 3
            assert all(isinstance(emb, np.ndarray) for emb in embeddings1)
            
            # Second generation should use cache
            embeddings2 = await manager.generate_embeddings_optimized(texts, "test-model")
            
            # Results should be identical (from cache)
            for e1, e2 in zip(embeddings1, embeddings2):
                np.testing.assert_array_equal(e1, e2)
    
    @pytest.mark.asyncio
    async def test_batch_processing(self, mock_sentence_transformer):
        """Test batch processing of embeddings."""
        with patch('src.core.model_optimization.torch.cuda.is_available', return_value=False):
            manager = OptimizedModelManager()
            
            # Large batch to test batching
            texts = [f"skill_{i}" for i in range(100)]
            
            embeddings = await manager.generate_embeddings_optimized(
                texts, "test-model", batch_size=10
            )
            
            assert len(embeddings) == 100
            # Verify model.encode was called multiple times for batching
            assert mock_sentence_transformer.encode.call_count >= 10
    
    def test_performance_metrics_collection(self):
        """Test performance metrics collection."""
        manager = OptimizedModelManager()
        
        # Add some request times
        manager.request_times = [0.1, 0.2, 0.15, 0.25, 0.3]
        
        metrics = manager.get_performance_metrics()
        
        assert "memory_usage" in metrics
        assert "cache_stats" in metrics
        assert "request_stats" in metrics
        assert "model_metrics" in metrics
        
        # Verify request stats calculation
        request_stats = metrics["request_stats"]
        assert "avg_request_time_ms" in request_stats
        assert "p95_request_time_ms" in request_stats
        assert "p99_request_time_ms" in request_stats


class TestOptimizedSkillVectorizer:
    """Test optimized skill vectorizer."""
    
    @pytest.fixture
    def mock_model_manager(self):
        """Create mock optimized model manager."""
        manager = AsyncMock()
        manager.load_model_optimized.return_value = Mock()
        manager.generate_embeddings_optimized.return_value = [
            np.random.rand(384).astype(np.float32) for _ in range(3)
        ]
        manager.get_performance_metrics.return_value = {
            "memory_usage": {"rss_mb": 100},
            "cache_stats": {"hit_rate": 0.8}
        }
        return manager
    
    @pytest.mark.asyncio
    async def test_optimized_initialization(self, mock_model_manager):
        """Test optimized vectorizer initialization."""
        with patch('src.core.optimized_skill_vectorizer.get_optimized_model_manager', 
                  return_value=mock_model_manager):
            
            vectorizer = OptimizedSkillVectorizer(model_name="test-model")
            
            # Mock the model to have required methods
            mock_model = Mock()
            mock_model.get_sentence_embedding_dimension.return_value = 384
            mock_model_manager.load_model_optimized.return_value = mock_model
            
            await vectorizer.initialize()
            
            assert vectorizer.model_loaded is True
            assert vectorizer.skill_space.dimension == 384
            mock_model_manager.load_model_optimized.assert_called_with("test-model")
    
    @pytest.mark.asyncio
    async def test_optimized_skill_embedding_generation(self, mock_model_manager):
        """Test optimized skill embedding generation."""
        with patch('src.core.optimized_skill_vectorizer.get_optimized_model_manager', 
                  return_value=mock_model_manager):
            
            vectorizer = OptimizedSkillVectorizer()
            
            # Mock initialization
            mock_model = Mock()
            mock_model.get_sentence_embedding_dimension.return_value = 384
            mock_model_manager.load_model_optimized.return_value = mock_model
            await vectorizer.initialize()
            
            # Test embedding generation
            skills = ["Python", "Machine Learning", "Data Science"]
            embeddings = await vectorizer.generate_skill_embeddings(skills)
            
            assert len(embeddings) == 3
            assert all(hasattr(emb, 'text') for emb in embeddings)
            assert all(hasattr(emb, 'embedding') for emb in embeddings)
            
            # Verify optimized manager was called
            mock_model_manager.generate_embeddings_optimized.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_batch_embedding_generation(self, mock_model_manager):
        """Test batch embedding generation."""
        with patch('src.core.optimized_skill_vectorizer.get_optimized_model_manager', 
                  return_value=mock_model_manager):
            
            vectorizer = OptimizedSkillVectorizer()
            
            # Mock initialization
            mock_model = Mock()
            mock_model.get_sentence_embedding_dimension.return_value = 384
            mock_model_manager.load_model_optimized.return_value = mock_model
            await vectorizer.initialize()
            
            # Mock different return values for different batches
            def mock_generate_side_effect(texts, **kwargs):
                return [np.random.rand(384).astype(np.float32) for _ in texts]
            
            mock_model_manager.generate_embeddings_optimized.side_effect = mock_generate_side_effect
            
            # Test batch generation
            skill_lists = [
                ["Python", "Java"],
                ["React", "Vue"],
                ["SQL", "MongoDB"]
            ]
            
            results = await vectorizer.batch_generate_embeddings(skill_lists, max_concurrent=2)
            
            assert len(results) == 3
            assert all(len(result) == 2 for result in results)
    
    @pytest.mark.asyncio
    async def test_memory_optimization(self, mock_model_manager):
        """Test memory optimization functionality."""
        with patch('src.core.optimized_skill_vectorizer.get_optimized_model_manager', 
                  return_value=mock_model_manager):
            
            vectorizer = OptimizedSkillVectorizer()
            
            # Mock memory usage stats
            mock_model_manager.get_memory_usage.side_effect = [
                {"rss_mb": 1000, "cache_size_mb": 100},  # Before
                {"rss_mb": 800, "cache_size_mb": 50}     # After
            ]
            
            # Mock initialization
            mock_model = Mock()
            mock_model.get_sentence_embedding_dimension.return_value = 384
            mock_model_manager.load_model_optimized.return_value = mock_model
            await vectorizer.initialize()
            
            # Test memory optimization
            results = await vectorizer.optimize_memory()
            
            assert "before_mb" in results
            assert "after_mb" in results
            assert "freed_mb" in results
            assert results["freed_mb"] == 200  # 1000 - 800
    
    def test_optimization_metrics_collection(self, mock_model_manager):
        """Test optimization metrics collection."""
        with patch('src.core.optimized_skill_vectorizer.get_optimized_model_manager', 
                  return_value=mock_model_manager):
            
            vectorizer = OptimizedSkillVectorizer()
            
            metrics = vectorizer.get_optimization_metrics()
            
            assert "vectorizer_stats" in metrics
            assert "optimization_metrics" in metrics
            assert "model_loaded" in metrics
            assert "batch_size" in metrics


class TestModelOptimizationIntegration:
    """Integration tests for model optimization."""
    
    @pytest.mark.asyncio
    async def test_concurrent_model_loading(self):
        """Test concurrent model loading doesn't cause issues."""
        with patch('src.core.model_optimization.SentenceTransformer') as mock_class, \
             patch('src.core.model_optimization.torch.cuda.is_available', return_value=False):
            
            mock_model = Mock()
            mock_model.get_sentence_embedding_dimension.return_value = 384
            mock_model.encode.return_value = np.random.rand(1, 384).astype(np.float32)
            mock_model.eval.return_value = mock_model
            mock_class.return_value = mock_model
            
            manager = OptimizedModelManager(max_models_in_pool=1)
            
            # Start multiple concurrent loads of the same model
            tasks = [
                manager.load_model_optimized("test-model")
                for _ in range(5)
            ]
            
            results = await asyncio.gather(*tasks)
            
            # All should return the same model instance
            assert all(result == results[0] for result in results)
            # Model should only be loaded once
            assert mock_class.call_count == 1
    
    @pytest.mark.asyncio  
    async def test_performance_under_load(self):
        """Test performance characteristics under load."""
        with patch('src.core.model_optimization.SentenceTransformer') as mock_class, \
             patch('src.core.model_optimization.torch.cuda.is_available', return_value=False):
            
            mock_model = Mock()
            mock_model.get_sentence_embedding_dimension.return_value = 384
            mock_model.encode.side_effect = lambda texts, **kwargs: np.random.rand(len(texts), 384).astype(np.float32)
            mock_model.eval.return_value = mock_model
            mock_class.return_value = mock_model
            
            manager = OptimizedModelManager(max_cache_size_mb=50)
            
            # Generate many embeddings to test caching and performance
            all_texts = [f"skill_{i}" for i in range(500)]
            
            start_time = time.time()
            
            # First generation (no cache)
            embeddings1 = await manager.generate_embeddings_optimized(
                all_texts, "test-model", batch_size=50
            )
            
            first_gen_time = time.time() - start_time
            
            # Second generation (should use cache)
            start_time = time.time()
            embeddings2 = await manager.generate_embeddings_optimized(
                all_texts, "test-model", batch_size=50
            )
            
            second_gen_time = time.time() - start_time
            
            # Verify results
            assert len(embeddings1) == 500
            assert len(embeddings2) == 500
            
            # Second generation should be faster due to caching
            assert second_gen_time < first_gen_time
            
            # Get performance metrics
            metrics = manager.get_performance_metrics()
            assert metrics["cache_stats"]["hit_rate"] > 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])