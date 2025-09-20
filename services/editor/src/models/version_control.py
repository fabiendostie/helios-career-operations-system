"""Version control models for tracking text changes."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class DiffOperation(str, Enum):
    """Types of diff operations."""

    INSERT = "insert"
    DELETE = "delete"
    REPLACE = "replace"
    EQUAL = "equal"


class TextDiff(BaseModel):
    """Individual text difference."""

    operation: DiffOperation = Field(..., description="Type of operation")
    start_pos: int = Field(..., description="Start position in original text")
    end_pos: int = Field(..., description="End position in original text")
    original_text: str = Field(default="", description="Original text")
    new_text: str = Field(default="", description="New text")
    length: int = Field(..., description="Length of the change")


class ChangeLog(BaseModel):
    """Log of changes made to text."""

    session_id: str = Field(..., description="Session identifier")
    version_from: int = Field(..., description="Source version number")
    version_to: int = Field(..., description="Target version number")
    changes: list[TextDiff] = Field(..., description="List of changes")
    change_summary: str = Field(..., description="Summary of changes")
    change_count: int = Field(..., description="Total number of changes")
    editor_type: str = Field(..., description="Type of editor that made changes")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Change timestamp"
    )


class Version(BaseModel):
    """Text version for version control."""

    version_id: str = Field(..., description="Unique version identifier")
    session_id: str = Field(..., description="Session identifier")
    version_number: int = Field(..., description="Version number")
    text: str = Field(..., description="Text content for this version")
    comment: str | None = Field(None, description="Version comment")

    # Metadata
    author: str = Field(default="system", description="Author of this version")
    edit_type: str = Field(..., description="Type of edit that created this version")

    # Quality metrics
    quality_score: float | None = Field(
        None, description="Quality score for this version"
    )
    word_count: int = Field(..., description="Word count")
    character_count: int = Field(..., description="Character count")

    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime.now, description="Version creation time"
    )

    # Relationships
    parent_version_id: str | None = Field(None, description="Parent version ID")
    is_current: bool = Field(
        default=True, description="Whether this is the current version"
    )


class VersionHistory(BaseModel):
    """Complete version history for a text."""

    session_id: str = Field(..., description="Session identifier")
    versions: list[Version] = Field(..., description="List of versions")
    current_version_id: str = Field(..., description="Current version ID")
    total_versions: int = Field(..., description="Total number of versions")

    # Summary statistics
    total_edits: int = Field(default=0, description="Total number of edits")
    creation_date: datetime = Field(
        default_factory=datetime.now, description="Initial creation date"
    )
    last_modified: datetime = Field(
        default_factory=datetime.now, description="Last modification date"
    )


class VersionComparison(BaseModel):
    """Comparison between two versions."""

    session_id: str = Field(..., description="Session identifier")
    version_a_id: str = Field(..., description="First version ID")
    version_b_id: str = Field(..., description="Second version ID")
    version_a_number: int = Field(..., description="First version number")
    version_b_number: int = Field(..., description="Second version number")

    # Comparison data
    diff: list[TextDiff] = Field(..., description="Differences between versions")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Similarity score")
    change_summary: str = Field(..., description="Summary of changes")

    # Statistics
    additions: int = Field(default=0, description="Number of additions")
    deletions: int = Field(default=0, description="Number of deletions")
    modifications: int = Field(default=0, description="Number of modifications")

    # Quality comparison
    quality_improvement: float | None = Field(
        None, description="Quality improvement score"
    )
    readability_change: float | None = Field(None, description="Readability change")

    timestamp: datetime = Field(
        default_factory=datetime.now, description="Comparison timestamp"
    )
