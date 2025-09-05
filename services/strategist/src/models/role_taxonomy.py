"""Role taxonomy models and data structures."""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from pydantic import BaseModel
from enum import Enum


class RIASECCode(str, Enum):
    """RIASEC personality types for career matching."""
    REALISTIC = "Realistic"
    INVESTIGATIVE = "Investigative"
    ARTISTIC = "Artistic"
    SOCIAL = "Social"
    ENTERPRISING = "Enterprising"
    CONVENTIONAL = "Conventional"


class CareerAnchor(str, Enum):
    """Edgar Schein's Career Anchors for aspiration alignment."""
    TECHNICAL_COMPETENCE = "Technical Competence"
    GENERAL_MANAGERIAL = "General Managerial"
    AUTONOMY_INDEPENDENCE = "Autonomy Independence"
    SECURITY_STABILITY = "Security Stability"
    ENTREPRENEURIAL_CREATIVITY = "Entrepreneurial Creativity"
    SERVICE_DEDICATION = "Service Dedication"
    PURE_CHALLENGE = "Pure Challenge"
    LIFESTYLE = "Lifestyle"


class IndustryCategory(str, Enum):
    """Major industry categories."""
    TECHNOLOGY = "Technology"
    FINANCE = "Finance"
    HEALTHCARE = "Healthcare"
    EDUCATION = "Education"
    MANUFACTURING = "Manufacturing"
    CONSULTING = "Consulting"
    RETAIL = "Retail"
    GOVERNMENT = "Government"
    NONPROFIT = "Nonprofit"
    MEDIA = "Media"
    ENERGY = "Energy"
    REAL_ESTATE = "Real Estate"
    TRANSPORTATION = "Transportation"
    HOSPITALITY = "Hospitality"
    LEGAL = "Legal"


class ExperienceLevel(str, Enum):
    """Experience level requirements."""
    ENTRY = "Entry Level"
    JUNIOR = "Junior (1-3 years)"
    MID = "Mid Level (3-7 years)"
    SENIOR = "Senior (7-12 years)"
    EXECUTIVE = "Executive (12+ years)"


class JobRole(BaseModel):
    """Individual job role in the taxonomy database."""
    role_id: str
    title: str
    alternative_titles: List[str] = []
    description: str
    industry_categories: List[IndustryCategory]
    experience_level: ExperienceLevel
    required_skill_keywords: List[str]
    preferred_skill_keywords: List[str] = []
    associated_riasec_codes: List[RIASECCode]
    associated_career_anchors: List[CareerAnchor]
    growth_trajectory: List[str] = []  # Potential career progression paths
    median_salary_range: Optional[Dict[str, int]] = None  # {"min": 50000, "max": 80000}
    remote_work_compatibility: float = 0.5  # 0.0 to 1.0 scale
    

@dataclass
class RoleTaxonomyStats:
    """Statistics about the role taxonomy database."""
    total_roles: int
    roles_by_industry: Dict[str, int]
    roles_by_experience: Dict[str, int]
    roles_by_riasec: Dict[str, int]
    unique_skills: int
    

class RoleSearchFilter(BaseModel):
    """Filters for searching the role taxonomy."""
    industries: Optional[List[IndustryCategory]] = None
    experience_levels: Optional[List[ExperienceLevel]] = None
    riasec_codes: Optional[List[RIASECCode]] = None
    career_anchors: Optional[List[CareerAnchor]] = None
    required_skills: Optional[List[str]] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    remote_work_min: Optional[float] = None


class RoleMatchResult(BaseModel):
    """Result of role matching against user profile."""
    role: JobRole
    match_score: float
    skill_match_details: Dict[str, Any]
    riasec_alignment: float
    career_anchor_alignment: float
    explanation: str