"""Optimized skill vectorization with advanced caching and model management."""

import logging
import time
from typing import List, Dict, Any, Optional
import numpy as np

from .model_optimization import get_optimized_model_manager, OptimizedModelManager
from .skill_vectorizer import SkillVectorizer  # Import base class
from ..models.skill_vector import (
    SkillEmbedding, CandidateProfile, VectorSearchResult
)

logger = logging.getLogger(__name__)


class OptimizedSkillVectorizer(SkillVectorizer):
    """High-performance skill vectorizer using optimized model management."""
    
    def __init__(self, 
                 model_name: str = "all-MiniLM-L6-v2",
                 enable_redis: bool = True,
                 max_cache_size_mb: int = 512,
                 batch_size: int = 32):
        """Initialize optimized skill vectorizer.
        
        Args:
            model_name: Name of the sentence transformer model
            enable_redis: Whether to enable Redis caching
            max_cache_size_mb: Maximum local cache size in MB
            batch_size: Batch size for embedding generation
        """
        # Initialize base class (but we'll override the model loading)
        super().__init__(model_name=model_name, enable_redis=enable_redis)
        
        # Get optimized model manager
        self.model_manager: OptimizedModelManager = get_optimized_model_manager(
            max_cache_size_mb=max_cache_size_mb,
            max_models_in_pool=2  # Keep 2 models in memory max
        )
        
        self.batch_size = batch_size
        self.model_loaded = False
        
        # Override the base class model to prevent double initialization
        self.model = None
        
        logger.info(f"OptimizedSkillVectorizer initialized with model: {model_name}")
    
    async def initialize(self) -> None:
        """Initialize the optimized vectorizer."""
        try:
            logger.info(f"Initializing optimized skill vectorizer with model: {self.model_name}")
            
            # Load model using optimized manager
            start_time = time.time()
            model = await self.model_manager.load_model_optimized(self.model_name)
            load_time = time.time() - start_time
            
            # Update skill space configuration
            dimension = model.get_sentence_embedding_dimension()
            self.skill_space.dimension = dimension
            self.model_loaded = True
            
            # Initialize cache manager if available
            if self.cache_manager:
                await self.cache_manager.initialize()
                logger.info("Distributed cache manager initialized")
            
            logger.info(f"OptimizedSkillVectorizer initialized successfully - "
                       f"Load time: {load_time:.2f}s, Dimension: {dimension}")
                       
        except Exception as e:
            logger.error(f"Failed to initialize OptimizedSkillVectorizer: {str(e)}")
            raise RuntimeError(f"Vectorizer initialization failed: {str(e)}")
    
    async def generate_skill_embeddings(self, skills: List[str]) -> List[SkillEmbedding]:
        """Generate embeddings using optimized batch processing."""
        if not self.model_loaded:
            raise RuntimeError("Vectorizer not initialized. Call initialize() first.")
        
        if not skills:
            return []
        
        # Preprocess all skills
        preprocessed_skills = [self._preprocess_text(skill) for skill in skills]
        
        # Check distributed cache first if available
        cached_embeddings = {}
        skills_to_generate = []
        skill_indices = {}
        
        if self.cache_manager:
            for i, (skill, preprocessed) in enumerate(zip(skills, preprocessed_skills)):
                cached_vector = await self.cache_manager.get_vector(preprocessed)
                if cached_vector is not None:
                    cached_embeddings[i] = cached_vector
                else:
                    skills_to_generate.append(preprocessed)
                    skill_indices[len(skills_to_generate) - 1] = i
        else:
            skills_to_generate = preprocessed_skills
            skill_indices = {i: i for i in range(len(skills))}
        
        # Generate embeddings for uncached skills using optimized manager
        new_embeddings = []
        if skills_to_generate:
            embedding_arrays = await self.model_manager.generate_embeddings_optimized(
                texts=skills_to_generate,
                model_name=self.model_name,
                batch_size=self.batch_size
            )
            
            # Cache new embeddings in distributed cache
            if self.cache_manager:
                for skill_text, embedding in zip(skills_to_generate, embedding_arrays):
                    await self.cache_manager.set_vector(skill_text, embedding)
            
            new_embeddings = embedding_arrays
        
        # Combine cached and new embeddings
        result_embeddings = []
        new_embedding_idx = 0
        
        for i, (original_skill, preprocessed_skill) in enumerate(zip(skills, preprocessed_skills)):
            if i in cached_embeddings:
                embedding_vector = cached_embeddings[i]
            else:
                embedding_vector = new_embeddings[new_embedding_idx]
                new_embedding_idx += 1
            
            # Create SkillEmbedding object
            skill_embedding = SkillEmbedding(
                text=original_skill,
                embedding=embedding_vector,
                metadata={
                    "original_text": original_skill,
                    "preprocessed_text": preprocessed_skill,
                    "dimension": len(embedding_vector),
                    "model": self.model_name,
                    "optimization": "enabled"
                }
            )
            
            result_embeddings.append(skill_embedding)
        
        logger.debug(f"Generated {len(result_embeddings)} skill embeddings "
                    f"(cached: {len(cached_embeddings)}, new: {len(new_embeddings)})")
        
        return result_embeddings
    
    async def generate_candidate_vector_optimized(self, master_career_data: Dict[str, Any]) -> CandidateProfile:
        """Generate candidate vector using optimized embedding generation."""
        if not self.model_loaded:
            raise RuntimeError("Vectorizer not initialized. Call initialize() first.")
        
        # Extract candidate information
        skills = self._extract_candidate_skills(master_career_data)
        accomplishments = self._extract_candidate_accomplishments(master_career_data)
        interests = self._extract_candidate_interests(master_career_data)
        
        # Combine all text for embedding
        combined_text = self._combine_candidate_text(skills, accomplishments, interests)
        
        # Generate embeddings using optimized manager
        if combined_text:
            embeddings = await self.model_manager.generate_embeddings_optimized(
                texts=[combined_text],
                model_name=self.model_name,
                batch_size=1
            )
            profile_embedding = embeddings[0]
        else:
            # Fallback: zero vector if no text available
            profile_embedding = np.zeros(self.skill_space.dimension)
            logger.warning("No candidate text available, using zero vector")
        
        # Create optimized candidate profile
        candidate_profile = CandidateProfile(
            user_id=master_career_data.get("user_id", "unknown"),
            skills=skills,
            accomplishments=accomplishments,
            interests=interests,
            aggregated_vector=profile_embedding.tolist(),
            vector_dimension=len(profile_embedding),
            generation_timestamp=time.time()
        )
        
        logger.info(f"Generated optimized candidate vector for user {candidate_profile.user_id} "
                   f"({len(skills)} skills, {len(accomplishments)} accomplishments)")
        
        return candidate_profile
    
    async def batch_generate_embeddings(self, 
                                      skill_lists: List[List[str]], 
                                      max_concurrent: int = 4) -> List[List[SkillEmbedding]]:
        """Generate embeddings for multiple skill lists concurrently."""
        if not self.model_loaded:
            raise RuntimeError("Vectorizer not initialized. Call initialize() first.")
        
        import asyncio
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def generate_with_semaphore(skills: List[str]) -> List[SkillEmbedding]:
            async with semaphore:
                return await self.generate_skill_embeddings(skills)
        
        # Process all skill lists concurrently
        tasks = [generate_with_semaphore(skills) for skills in skill_lists]
        results = await asyncio.gather(*tasks)
        
        logger.info(f"Batch generated embeddings for {len(skill_lists)} skill lists")
        return results
    
    def get_optimization_metrics(self) -> Dict[str, Any]:
        """Get comprehensive optimization metrics."""
        base_stats = self.get_cache_stats()
        performance_metrics = self.model_manager.get_performance_metrics()
        
        return {
            "vectorizer_stats": base_stats,
            "optimization_metrics": performance_metrics,
            "model_loaded": self.model_loaded,
            "batch_size": self.batch_size,
            "model_name": self.model_name
        }
    
    async def optimize_memory(self) -> Dict[str, Any]:
        """Trigger memory optimization and return stats."""
        logger.info("Triggering memory optimization")
        
        # Get stats before optimization
        before_stats = self.model_manager.get_memory_usage()
        
        # Force garbage collection through model manager
        import gc
        gc.collect()
        
        # Get stats after optimization
        after_stats = self.model_manager.get_memory_usage()
        
        optimization_results = {
            "before_mb": before_stats["rss_mb"],
            "after_mb": after_stats["rss_mb"],
            "freed_mb": before_stats["rss_mb"] - after_stats["rss_mb"],
            "cache_size_mb": after_stats["cache_size_mb"],
            "optimization_timestamp": time.time()
        }
        
        logger.info(f"Memory optimization completed - Freed {optimization_results['freed_mb']:.1f}MB")
        return optimization_results
    
    async def preload_common_skills(self, common_skills: List[str]) -> None:
        """Preload embeddings for commonly used skills."""
        logger.info(f"Preloading embeddings for {len(common_skills)} common skills")
        
        # Generate embeddings (which will cache them)
        await self.generate_skill_embeddings(common_skills)
        
        logger.info("Common skills preloaded and cached")
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        logger.info("Cleaning up OptimizedSkillVectorizer")
        
        if self.cache_manager:
            # Cache manager cleanup is handled by its own lifecycle
            pass
        
        # Model manager cleanup is handled by the singleton
        await self.model_manager.cleanup()
        
        self.model_loaded = False
        logger.info("OptimizedSkillVectorizer cleanup complete")


# Convenience function for creating optimized vectorizer
async def create_optimized_vectorizer(model_name: str = "all-MiniLM-L6-v2",
                                    **kwargs) -> OptimizedSkillVectorizer:
    """Create and initialize optimized skill vectorizer."""
    vectorizer = OptimizedSkillVectorizer(model_name=model_name, **kwargs)
    await vectorizer.initialize()
    return vectorizer