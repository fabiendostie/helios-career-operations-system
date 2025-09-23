"""Career Target Profile (CTP) models and career path generation structures."""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from pydantic import BaseModel
from enum import Enum

from .role_taxonomy import JobRole


class TransitionDifficulty(str, Enum):
    """Career transition difficulty levels."""
    EASY = "easy"
    MODERATE = "moderate"
    CHALLENGING = "challenging"
    VERY_CHALLENGING = "very_challenging"


class SkillGapPriority(str, Enum):
    """Priority levels for skill gaps."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    OPTIONAL = "optional"


class SkillGap(BaseModel):
    """Individual skill gap with development recommendations."""
    skill_name: str
    gap_description: str
    priority: SkillGapPriority
    estimated_learning_time: str  # e.g., "2-3 months", "6 months"
    learning_resources: List[str] = []  # e.g., ["Online course", "Certification"]
    current_level: Optional[str] = None  # User's current level
    target_level: str  # Required level for role


class TransitionStep(BaseModel):
    """Individual step in career transition roadmap."""
    step_number: int
    title: str
    description: str
    estimated_duration: str
    prerequisites: List[str] = []
    success_metrics: List[str] = []
    resources: List[str] = []


class CareerTargetProfile(BaseModel):
    """Career Target Profile - recommended career path for a user."""
    ctp_id: str
    user_id: str
    role: JobRole

    # Fit scoring results
    fit_score: float  # Overall fit score (0-1)
    skill_match_score: float  # Skill alignment (0-1)
    aspiration_score: float  # Aspiration alignment (0-1)
    confidence_level: float  # Confidence in recommendation (0-1)

    # Skill gap analysis
    skill_gaps: List[SkillGap]
    existing_strengths: List[str]  # User's relevant existing skills
    skill_overlap_percentage: float

    # Career transition analysis
    transition_difficulty: TransitionDifficulty
    transition_roadmap: List[TransitionStep]
    estimated_transition_time: str  # e.g., "6-12 months"

    # Additional insights
    explanation: str  # Why this role is recommended
    key_selling_points: List[str]  # Strengths for this transition
    potential_challenges: List[str]  # Challenges to be aware of
    next_steps: List[str]  # Immediate action items

    # Metadata
    generation_timestamp: float
    model_version: str = "1.0.0"


class CareerPathRequest(BaseModel):
    """Request for career path generation."""
    user_id: str
    master_career_database: Dict[str, Any]
    max_recommendations: int = 3
    include_challenging_transitions: bool = True
    preferred_industries: Optional[List[str]] = None
    salary_requirements: Optional[Dict[str, int]] = None  # {"min": 80000, "max": 150000}
    location_preferences: Optional[Dict[str, Any]] = None


class CareerPathResponse(BaseModel):
    """Response containing generated career path recommendations."""
    user_id: str
    career_target_profiles: List[CareerTargetProfile]
    generation_summary: Dict[str, Any]  # Statistics and metadata
    processing_time_ms: float
    model_version: str = "1.0.0"


@dataclass
class GenerationStats:
    """Statistics about career path generation."""
    total_roles_analyzed: int
    roles_above_threshold: int
    skill_gaps_identified: int
    avg_fit_score: float
    processing_time_ms: float
