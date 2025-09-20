"""Edit request and response models."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class EditType(str, Enum):
    """Types of editing operations."""

    GRAMMAR = "grammar"
    STYLE = "style"
    CONTENT_ENHANCEMENT = "content_enhancement"
    QUANTIFICATION = "quantification"
    TONE_ADJUSTMENT = "tone_adjustment"
    COMPREHENSIVE = "comprehensive"


class EditRequest(BaseModel):
    """Request for text editing."""

    session_id: str = Field(..., description="Session identifier")
    text: str = Field(..., description="Text to edit")
    edit_type: EditType = Field(
        default=EditType.COMPREHENSIVE, description="Type of editing"
    )
    industry: str | None = Field(None, description="Industry context for editing")
    role: str | None = Field(None, description="Target role for content optimization")
    language: str = Field(default="en", description="Text language")
    tone: str | None = Field(
        None, description="Desired tone (professional, casual, etc.)"
    )

    # Version control options
    track_changes: bool = Field(
        default=True, description="Track changes for version control"
    )
    version_comment: str | None = Field(None, description="Comment for this version")


class EditSuggestion(BaseModel):
    """Individual edit suggestion."""

    start_pos: int = Field(..., description="Start position of text to edit")
    end_pos: int = Field(..., description="End position of text to edit")
    original_text: str = Field(..., description="Original text")
    suggested_text: str = Field(..., description="Suggested replacement text")
    reason: str = Field(..., description="Reason for the suggestion")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    edit_type: EditType = Field(..., description="Type of edit")


class EditResponse(BaseModel):
    """Response from text editing."""

    session_id: str = Field(..., description="Session identifier")
    original_text: str = Field(..., description="Original text")
    edited_text: str = Field(..., description="Edited text")
    suggestions: list[EditSuggestion] = Field(
        default_factory=list, description="Individual suggestions"
    )

    # Analysis metrics
    readability_score: float | None = Field(None, description="Readability score")
    grammar_issues_fixed: int = Field(
        default=0, description="Number of grammar issues fixed"
    )
    style_improvements: int = Field(
        default=0, description="Number of style improvements"
    )
    content_enhancements: int = Field(
        default=0, description="Number of content enhancements"
    )

    # Version information
    version_id: str | None = Field(None, description="Version identifier")
    version_number: int = Field(default=1, description="Version number")

    # Processing metadata
    processing_time: float = Field(..., description="Processing time in seconds")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Processing timestamp"
    )


class EditBatch(BaseModel):
    """Batch editing request for multiple texts."""

    session_id: str = Field(..., description="Session identifier")
    texts: list[str] = Field(..., description="Texts to edit")
    edit_type: EditType = Field(
        default=EditType.COMPREHENSIVE, description="Type of editing"
    )
    industry: str | None = Field(None, description="Industry context")
    role: str | None = Field(None, description="Target role")


class EditBatchResponse(BaseModel):
    """Response from batch editing."""

    session_id: str = Field(..., description="Session identifier")
    results: list[EditResponse] = Field(..., description="Individual edit results")
    total_processing_time: float = Field(..., description="Total processing time")
    success_count: int = Field(..., description="Number of successful edits")
    error_count: int = Field(..., description="Number of failed edits")
