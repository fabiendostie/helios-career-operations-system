"""Market analysis data structures and models."""

from typing import List, Optional, Dict, Any
from datetime import date
from pydantic import BaseModel, Field
from enum import Enum


class JobLevel(str, Enum):
    """Job seniority levels."""

    ENTRY = "entry"
    MID = "mid"
    SENIOR = "senior"
    STAFF = "staff"
    PRINCIPAL = "principal"
    DIRECTOR = "director"


class RemotePolicy(str, Enum):
    """Remote work policies."""

    ONSITE = "onsite"
    HYBRID = "hybrid"
    REMOTE = "remote"


class MarketJob(BaseModel):
    """Market job posting data structure."""

    job_id: str = Field(description="Unique job identifier")
    role_title: str = Field(description="Job title/role name")
    company_name: str = Field(description="Company name")
    location: str = Field(description="Job location or 'Remote'")
    remote_policy: RemotePolicy = Field(description="Remote work policy")
    post_date: date = Field(description="Job posting date")
    required_skills: List[str] = Field(description="Required skills list")
    preferred_skills: List[str] = Field(default=[], description="Preferred skills list")
    level: JobLevel = Field(description="Seniority level")
    full_description_text: str = Field(description="Complete job description")

    # Additional fields for analysis
    company_size: Optional[str] = Field(
        default=None, description="Company size category"
    )
    industry: Optional[str] = Field(default=None, description="Industry classification")
    benefits: List[str] = Field(default=[], description="Benefits offered")


class CompensationData(BaseModel):
    """Compensation data structure."""

    role_title: str = Field(description="Role title")
    company_name: str = Field(description="Company name")
    level: JobLevel = Field(description="Seniority level")
    location: str = Field(description="Location")
    year: int = Field(description="Compensation year")

    # Compensation components
    base_salary_usd: int = Field(description="Base salary in USD")
    stock_grant_usd: Optional[int] = Field(
        default=None, description="Annual stock grant value"
    )
    bonus_usd: Optional[int] = Field(default=None, description="Annual bonus")
    total_comp_usd: Optional[int] = Field(
        default=None, description="Total compensation"
    )

    # Additional context
    years_experience: Optional[int] = Field(
        default=None, description="Years of experience"
    )
    company_size: Optional[str] = Field(default=None, description="Company size")
    industry: Optional[str] = Field(default=None, description="Industry")


class JobMatch(BaseModel):
    """Job matching result with similarity scoring."""

    job: MarketJob = Field(description="Matched job posting")
    similarity_score: float = Field(description="Cosine similarity score")
    matched_skills: List[str] = Field(description="Skills that matched")
    missing_skills: List[str] = Field(description="Skills candidate lacks")
    match_details: Dict[str, Any] = Field(description="Detailed matching analysis")


class MarketAnalysisResult(BaseModel):
    """Complete market analysis result."""

    job_matches: List[JobMatch] = Field(description="Matched job opportunities")

    market_insights: Dict[str, Any] = Field(description="Market trends and insights")

    compensation_analysis: Dict[str, Any] = Field(
        description="Salary and compensation analysis"
    )

    skill_demand_analysis: Dict[str, Any] = Field(
        description="Skills in demand analysis"
    )

    location_analysis: Dict[str, Any] = Field(
        description="Geographic opportunities analysis"
    )

    recommendations: List[str] = Field(description="Actionable market recommendations")

    processing_metadata: Dict[str, Any] = Field(
        description="Processing statistics and metadata"
    )
