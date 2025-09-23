"""Skill vector models and data structures."""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from pydantic import BaseModel
import numpy as np


class SkillVector(BaseModel):
    """Individual skill vector representation."""
    skill_name: str
    vector: List[float]
    confidence: float = 1.0
    source: str = "user_input"  # user_input, extracted, inferred


class CandidateProfile(BaseModel):
    """User candidate profile with aggregated skill vector."""
    user_id: str
    skills: List[str]
    accomplishments: List[str]
    interests: List[str]
    aggregated_vector: List[float]
    vector_dimension: int
    generation_timestamp: float


@dataclass
class SkillEmbedding:
    """Raw skill embedding data structure."""
    text: str
    embedding: np.ndarray
    metadata: Dict[str, Any]

    def to_vector(self) -> SkillVector:
        """Convert to SkillVector model."""
        return SkillVector(
            skill_name=self.text,
            vector=self.embedding.tolist(),
            confidence=self.metadata.get("confidence", 1.0),
            source=self.metadata.get("source", "extracted")
        )


class VectorSearchResult(BaseModel):
    """Search result for vector similarity queries."""
    item_id: str
    similarity_score: float
    matched_skills: List[str]
    metadata: Dict[str, Any]


class SkillSpace(BaseModel):
    """Configuration for skill vector space."""
    dimension: int = 384  # all-MiniLM-L6-v2 default
    model_name: str = "all-MiniLM-L6-v2"
    normalization: str = "l2"  # l2, unit, none
    distance_metric: str = "cosine"  # cosine, euclidean, dot
