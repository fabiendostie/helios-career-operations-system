"""Skill vectorization using sentence transformers for embedding generation."""

import logging
import re
import time
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Production requirement: These dependencies must be installed
DEPENDENCIES_AVAILABLE = True

from ..models.skill_vector import (
    SkillVector, CandidateProfile, SkillEmbedding,
    VectorSearchResult, SkillSpace
)

# Import cache manager for distributed caching
try:
    from .redis_cache import CacheManager
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False

logger = logging.getLogger(__name__)


class SkillVectorizer:
    """Handles skill text to vector conversion using sentence transformers."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", enable_redis: bool = True):
        """Initialize vectorizer with specified model.

        Args:
            model_name: Name of the sentence transformer model to use
            enable_redis: Whether to enable Redis caching for distributed deployments
        """
        self.model_name = model_name
        self.model: Optional[SentenceTransformer] = None
        self.skill_space = SkillSpace(model_name=model_name)
        self._skill_cache: Dict[str, np.ndarray] = {}

        # Initialize cache manager
        self.cache_manager: Optional[CacheManager] = None
        if CACHE_AVAILABLE and enable_redis:
            self.cache_manager = CacheManager(enable_redis=enable_redis)

    async def initialize(self) -> None:
        """Async initialization of the sentence transformer model."""
        try:
            if not DEPENDENCIES_AVAILABLE:
                raise RuntimeError("Required ML dependencies not installed. Install sentence-transformers and scikit-learn.")

            logger.info(f"Loading sentence transformer model: {self.model_name}")

            # Production optimization: Model loading with validation
            self.model = SentenceTransformer(self.model_name)

            # Validate model is working
            test_embedding = self.model.encode(["test"], show_progress_bar=False)
            if test_embedding is None or len(test_embedding) == 0:
                raise RuntimeError(f"Model {self.model_name} failed validation test")

            dimension = self.model.get_sentence_embedding_dimension()
            logger.info(f"Model loaded successfully, dimension: {dimension}")

            # Update skill space configuration
            self.skill_space.dimension = dimension

            # Pre-warm the model for better first-request performance
            _ = self.model.encode(["warmup"], show_progress_bar=False)

            # Initialize cache manager if available
            if self.cache_manager:
                await self.cache_manager.initialize()
                logger.info("Cache manager initialized for distributed caching")

        except Exception as e:
            logger.error(f"Failed to load sentence transformer model: {e}")
            raise RuntimeError(f"Model initialization failed: {str(e)}")

    def _preprocess_text(self, text: str) -> str:
        """Preprocess skill text for better embedding quality."""
        # Clean and normalize text
        text = text.strip().lower()

        # Remove special characters but keep spaces, dots, hyphens, and plus signs
        # Keep + for C++, # for C#, etc.
        text = re.sub(r'[^\w\s\.\-\+#]', ' ', text)

        # Collapse multiple spaces
        text = re.sub(r'\s+', ' ', text)

        return text

    def _extract_skills_from_text(self, text: str) -> List[str]:
        """Extract individual skills from combined text."""
        # Split by common delimiters
        skills = []

        # Split by common separators
        for separator in [',', ';', '|', '\n']:
            if separator in text:
                skills.extend([s.strip() for s in text.split(separator) if s.strip()])
                break
        else:
            # No separators found, treat as single skill
            skills.append(text.strip())

        # Filter out empty strings and very short skills
        skills = [s for s in skills if len(s) >= 2]

        return skills

    async def generate_skill_embeddings(self, skills: List[str]) -> List[SkillEmbedding]:
        """Generate embeddings for a list of skills."""
        if not self.model:
            raise RuntimeError("Model not initialized. Call initialize() first.")

        if not skills:
            return []

        embeddings = []

        for skill in skills:
            # Check cache first (distributed then local)
            cache_key = self._preprocess_text(skill)

            # Try distributed cache first
            embedding_vector = None
            if self.cache_manager:
                embedding_vector = await self.cache_manager.get_vector(cache_key)

            # Fall back to local cache
            if embedding_vector is None and cache_key in self._skill_cache:
                embedding_vector = self._skill_cache[cache_key]

            # Generate new embedding if not cached
            if embedding_vector is None:
                # Generate new embedding
                preprocessed = self._preprocess_text(skill)
                embedding_vector = self.model.encode([preprocessed], show_progress_bar=False)[0]

                # Cache the result (both distributed and local)
                if self.cache_manager:
                    await self.cache_manager.set_vector(cache_key, embedding_vector)
                self._skill_cache[cache_key] = embedding_vector

            # Create SkillEmbedding object
            skill_embedding = SkillEmbedding(
                text=skill,
                embedding=embedding_vector,
                metadata={
                    "original_text": skill,
                    "preprocessed_text": cache_key,
                    "dimension": len(embedding_vector),
                    "model": self.model_name
                }
            )

            embeddings.append(skill_embedding)

        logger.debug(f"Generated {len(embeddings)} skill embeddings")
        return embeddings

    async def generate_candidate_vector(self, master_career_data: Dict[str, Any]) -> CandidateProfile:
        """Generate aggregated candidate vector from Master Career Database."""
        if not self.model:
            raise RuntimeError("Model not initialized. Call initialize() first.")

        # Extract skills, accomplishments, and interests from Master Career Database
        skills = self._extract_candidate_skills(master_career_data)
        accomplishments = self._extract_candidate_accomplishments(master_career_data)
        interests = self._extract_candidate_interests(master_career_data)

        # Combine all text for embedding
        combined_text = self._combine_candidate_text(skills, accomplishments, interests)

        # Generate embeddings for the combined profile
        if combined_text:
            profile_embedding = self.model.encode([combined_text])[0]
        else:
            # Fallback: zero vector if no text available
            profile_embedding = np.zeros(self.skill_space.dimension)
            logger.warning("No candidate text available, using zero vector")

        # Create candidate profile
        candidate_profile = CandidateProfile(
            user_id=master_career_data.get("user_id", "unknown"),
            skills=skills,
            accomplishments=accomplishments,
            interests=interests,
            aggregated_vector=profile_embedding.tolist(),
            vector_dimension=len(profile_embedding),
            generation_timestamp=time.time()
        )

        logger.info(f"Generated candidate vector for user {candidate_profile.user_id}")
        return candidate_profile

    def _extract_candidate_skills(self, master_career_data: Dict[str, Any]) -> List[str]:
        """Extract skills from Master Career Database."""
        skills = []

        # Extract from skills_inventory
        skills_inventory = master_career_data.get("skills_inventory", {})
        for category, skill_list in skills_inventory.items():
            if isinstance(skill_list, list):
                skills.extend(skill_list)
            elif isinstance(skill_list, dict):
                # Handle nested skill structure
                for skill_name, skill_data in skill_list.items():
                    skills.append(skill_name)

        # Extract from work experience
        work_experience = master_career_data.get("work_experience", [])
        for job in work_experience:
            job_skills = job.get("skills_demonstrated", [])
            skills.extend(job_skills)

        # Extract from projects
        projects = master_career_data.get("projects", [])
        for project in projects:
            project_skills = project.get("technologies_used", [])
            skills.extend(project_skills)

        return list(set(skills))  # Remove duplicates

    def _extract_candidate_accomplishments(self, master_career_data: Dict[str, Any]) -> List[str]:
        """Extract accomplishments from Master Career Database."""
        accomplishments = []

        # Extract from work experience
        work_experience = master_career_data.get("work_experience", [])
        for job in work_experience:
            job_accomplishments = job.get("accomplishments", [])
            if isinstance(job_accomplishments, list):
                accomplishments.extend(job_accomplishments)
            elif isinstance(job_accomplishments, str):
                accomplishments.append(job_accomplishments)

        # Extract from projects
        projects = master_career_data.get("projects", [])
        for project in projects:
            project_desc = project.get("description", "")
            if project_desc:
                accomplishments.append(project_desc)

        return accomplishments

    def _extract_candidate_interests(self, master_career_data: Dict[str, Any]) -> List[str]:
        """Extract interests and aspirations from Master Career Database."""
        interests = []

        # Extract from holistic_profile
        holistic_profile = master_career_data.get("holistic_profile", {})

        aspirations = holistic_profile.get("aspirations", [])
        if isinstance(aspirations, list):
            interests.extend(aspirations)
        elif isinstance(aspirations, str):
            interests.append(aspirations)

        motivators = holistic_profile.get("motivators", [])
        if isinstance(motivators, list):
            interests.extend(motivators)
        elif isinstance(motivators, str):
            interests.append(motivators)

        return interests

    def _combine_candidate_text(self, skills: List[str], accomplishments: List[str],
                               interests: List[str]) -> str:
        """Combine candidate information into single text for embedding."""
        text_parts = []

        if skills:
            text_parts.append(f"Skills: {', '.join(skills)}")

        if accomplishments:
            # Truncate long accomplishments for better embedding
            short_accomplishments = [acc[:200] + "..." if len(acc) > 200 else acc
                                   for acc in accomplishments]
            text_parts.append(f"Accomplishments: {' '.join(short_accomplishments)}")

        if interests:
            text_parts.append(f"Interests: {', '.join(interests)}")

        return ". ".join(text_parts)

    def calculate_similarity(self, vector1: List[float], vector2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if len(vector1) != len(vector2):
            raise ValueError("Vectors must have the same dimension")

        # Convert to numpy arrays and reshape for sklearn
        v1 = np.array(vector1).reshape(1, -1)
        v2 = np.array(vector2).reshape(1, -1)

        # Calculate cosine similarity
        similarity = cosine_similarity(v1, v2)[0][0]

        # Ensure similarity is between 0 and 1 (cosine can be -1 to 1)
        return max(0.0, similarity)

    async def find_similar_skills(self, query_vector: List[float],
                                skill_database: List[SkillVector],
                                top_k: int = 10) -> List[VectorSearchResult]:
        """Find most similar skills to a query vector."""
        if not skill_database:
            return []

        results = []

        for skill in skill_database:
            similarity = self.calculate_similarity(query_vector, skill.vector)

            result = VectorSearchResult(
                item_id=skill.skill_name,
                similarity_score=similarity,
                matched_skills=[skill.skill_name],
                metadata={
                    "confidence": skill.confidence,
                    "source": skill.source
                }
            )
            results.append(result)

        # Sort by similarity score (descending) and return top_k
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results[:top_k]

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get caching statistics."""
        return {
            "cached_skills": len(self._skill_cache),
            "cache_memory_estimate": len(self._skill_cache) * self.skill_space.dimension * 4  # float32 bytes
        }
