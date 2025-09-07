"""ATS scoring models and data structures."""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


class ScoringCriteria(str, Enum):
    """ATS scoring criteria categories."""

    KEYWORD_MATCH = "keyword_match"
    FORMAT_PARSABILITY = "format_parsability"
    QUANTIFICATION = "quantification"
    ACTION_VERBS = "action_verbs"


class ScoreLevel(str, Enum):
    """ATS score performance levels."""

    EXCELLENT = "excellent"  # 80-100%
    GOOD = "good"  # 60-79%
    FAIR = "fair"  # 40-59%
    POOR = "poor"  # 0-39%


class CriteriaScore(BaseModel):
    """Individual scoring criteria result."""

    criteria: ScoringCriteria = Field(description="Scoring criteria type")
    score: float = Field(description="Score (0.0 to 1.0)")
    weight: float = Field(description="Criteria weight in overall score")
    weighted_score: float = Field(description="Score × weight")

    details: Dict[str, Any] = Field(description="Detailed scoring breakdown")
    recommendations: List[str] = Field(
        default=[], description="Improvement recommendations for this criteria"
    )


class ATSScore(BaseModel):
    """Complete ATS scoring result."""

    overall_score: float = Field(description="Overall ATS score (0.0 to 1.0)")
    percentage_score: int = Field(description="Score as percentage (0-100)")
    performance_level: ScoreLevel = Field(description="Performance level rating")

    criteria_scores: List[CriteriaScore] = Field(
        description="Individual criteria scores"
    )

    summary: Dict[str, Any] = Field(description="Scoring summary statistics")

    optimization_recommendations: List[str] = Field(
        description="Overall optimization recommendations"
    )

    ats_readiness_feedback: Dict[str, Any] = Field(
        description="Detailed feedback for ATS readiness"
    )


class OptimizationSuggestion(BaseModel):
    """ATS optimization suggestion."""

    category: ScoringCriteria = Field(description="Optimization category")
    priority: str = Field(description="Priority level (high/medium/low)")
    suggestion: str = Field(description="Specific suggestion text")
    impact_estimate: float = Field(description="Estimated score improvement")

    before_example: Optional[str] = Field(
        default=None, description="Example of current text"
    )
    after_example: Optional[str] = Field(
        default=None, description="Example of optimized text"
    )


class ATSOptimizationReport(BaseModel):
    """Complete ATS optimization report."""

    current_score: ATSScore = Field(description="Current ATS score")

    optimization_suggestions: List[OptimizationSuggestion] = Field(
        description="Prioritized optimization suggestions"
    )

    projected_improvements: Dict[str, float] = Field(
        description="Projected score improvements by category"
    )

    quick_wins: List[str] = Field(description="Easy improvements with high impact")

    long_term_improvements: List[str] = Field(
        description="Strategic improvements requiring more effort"
    )
