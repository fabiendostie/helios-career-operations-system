"""Analysis request and response models."""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    """Request model for analysis pipeline."""

    correlation_id: Optional[str] = Field(
        default=None, description="Correlation ID for request tracking"
    )

    user_id: str = Field(description="User ID for session context")

    master_career_data: Dict[str, Any] = Field(
        description="Master Career Database JSON from Profile Ingestor"
    )

    analysis_options: Optional[Dict[str, Any]] = Field(
        default=None, description="Optional analysis configuration"
    )


class PipelineStepResult(BaseModel):
    """Result from individual pipeline step."""

    status: str = Field(description="Step completion status")
    details: Optional[Dict[str, Any]] = Field(
        default=None, description="Step-specific results"
    )


class AnalysisResponse(BaseModel):
    """Response model for analysis pipeline."""

    correlation_id: str = Field(description="Correlation ID for request tracking")

    pipeline_steps: Dict[str, PipelineStepResult] = Field(
        description="Results from each pipeline step"
    )

    recommendations: List[str] = Field(description="Career advancement recommendations")

    processing_time_seconds: float = Field(description="Total processing time")

    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional analysis metadata"
    )
