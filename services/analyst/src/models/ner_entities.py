"""NER entity data models for professional resume analysis."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class EntityType(str, Enum):
    """Professional entity types for NER extraction."""

    SKILL = "SKILL"
    TOOL = "TOOL"
    METRIC = "METRIC"
    ACTION_VERB = "ACTION_VERB"
    RESPONSIBILITY = "RESPONSIBILITY"


class ExtractedEntity(BaseModel):
    """Individual extracted entity from resume text."""

    text: str = Field(description="Entity text as it appears in document")
    label: EntityType = Field(description="Entity classification")
    start: int = Field(description="Start character position")
    end: int = Field(description="End character position")
    confidence: float = Field(description="Extraction confidence score")
    context: Optional[str] = Field(
        default=None, description="Surrounding context for disambiguation"
    )


class ProcessedSection(BaseModel):
    """Processed resume section with extracted entities."""

    section_name: str = Field(description="Resume section identifier")
    raw_text: str = Field(description="Original text content")
    entities: List[ExtractedEntity] = Field(description="Extracted entities")
    language: str = Field(description="Detected language (en/fr)")
    processing_metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Processing statistics and metadata"
    )


class ResumeDeconstruction(BaseModel):
    """Complete resume deconstruction result."""

    sections: List[ProcessedSection] = Field(description="Processed sections")

    entity_summary: Dict[EntityType, int] = Field(
        description="Count of entities by type"
    )

    language_distribution: Dict[str, float] = Field(
        description="Language distribution percentages"
    )

    semantic_embeddings: Optional[Dict[str, List[float]]] = Field(
        default=None,
        description="Sentence-BERT embeddings for accomplishment statements",
    )

    processing_time_seconds: float = Field(description="Total processing time")

    quality_metrics: Dict[str, float] = Field(description="Quality assessment metrics")
