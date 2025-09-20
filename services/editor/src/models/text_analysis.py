"""Text analysis models for grammar, style, and content analysis."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class IssueSeverity(str, Enum):
    """Severity levels for text issues."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class GrammarIssue(BaseModel):
    """Grammar issue identified in text."""

    start_pos: int = Field(..., description="Start position of issue")
    end_pos: int = Field(..., description="End position of issue")
    message: str = Field(..., description="Description of the grammar issue")
    rule_id: str = Field(..., description="Grammar rule identifier")
    severity: IssueSeverity = Field(..., description="Issue severity")
    suggestions: List[str] = Field(default_factory=list, description="Suggested corrections")
    category: str = Field(..., description="Grammar category (e.g., 'Spelling', 'Grammar')")


class StyleIssue(BaseModel):
    """Style issue identified in text."""

    start_pos: int = Field(..., description="Start position of issue")
    end_pos: int = Field(..., description="End position of issue")
    message: str = Field(..., description="Description of the style issue")
    issue_type: str = Field(..., description="Type of style issue")
    severity: IssueSeverity = Field(..., description="Issue severity")
    suggestions: List[str] = Field(default_factory=list, description="Style improvement suggestions")
    improvement_reason: str = Field(..., description="Why this is an improvement")


class ReadabilityMetrics(BaseModel):
    """Text readability metrics."""

    flesch_reading_ease: float = Field(..., description="Flesch Reading Ease score")
    flesch_kincaid_grade: float = Field(..., description="Flesch-Kincaid Grade Level")
    gunning_fog: float = Field(..., description="Gunning Fog Index")
    automated_readability_index: float = Field(..., description="Automated Readability Index")
    coleman_liau_index: float = Field(..., description="Coleman-Liau Index")

    # Text statistics
    sentence_count: int = Field(..., description="Number of sentences")
    word_count: int = Field(..., description="Number of words")
    character_count: int = Field(..., description="Number of characters")
    syllable_count: int = Field(..., description="Number of syllables")
    avg_sentence_length: float = Field(..., description="Average sentence length")
    avg_syllables_per_word: float = Field(..., description="Average syllables per word")


class ContentAnalysis(BaseModel):
    """Content quality analysis."""

    # Achievement and impact analysis
    quantified_achievements: int = Field(default=0, description="Number of quantified achievements")
    action_verbs_count: int = Field(default=0, description="Number of strong action verbs")
    passive_voice_count: int = Field(default=0, description="Number of passive voice instances")
    weak_words_count: int = Field(default=0, description="Number of weak words")

    # Professional language
    industry_keywords: List[str] = Field(default_factory=list, description="Identified industry keywords")
    technical_terms: List[str] = Field(default_factory=list, description="Technical terms found")
    jargon_count: int = Field(default=0, description="Amount of unnecessary jargon")

    # Structure analysis
    bullet_points: int = Field(default=0, description="Number of bullet points")
    paragraphs: int = Field(default=0, description="Number of paragraphs")
    headings: int = Field(default=0, description="Number of headings")

    # Tone analysis
    tone_scores: Dict[str, float] = Field(
        default_factory=dict, description="Tone analysis scores"
    )
    formality_score: float = Field(default=0.5, description="Formality score (0-1)")


class TextAnalysis(BaseModel):
    """Comprehensive text analysis results."""

    text: str = Field(..., description="Analyzed text")
    language: str = Field(default="en", description="Detected language")

    # Issues
    grammar_issues: List[GrammarIssue] = Field(default_factory=list, description="Grammar issues")
    style_issues: List[StyleIssue] = Field(default_factory=list, description="Style issues")

    # Metrics
    readability: ReadabilityMetrics = Field(..., description="Readability metrics")
    content_analysis: ContentAnalysis = Field(..., description="Content analysis")

    # Overall scores
    overall_quality_score: float = Field(..., ge=0.0, le=100.0, description="Overall quality score")
    grammar_score: float = Field(..., ge=0.0, le=100.0, description="Grammar quality score")
    style_score: float = Field(..., ge=0.0, le=100.0, description="Style quality score")
    content_score: float = Field(..., ge=0.0, le=100.0, description="Content quality score")

    # Analysis metadata
    analysis_time: float = Field(..., description="Analysis time in seconds")
    timestamp: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")