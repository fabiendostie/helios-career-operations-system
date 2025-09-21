"""Request and response models for document generation."""

from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field, validator
from enum import Enum


class DocumentType(str, Enum):
    """Supported document types."""
    RESUME = "resume"
    COVER_LETTER = "cover_letter"


class OutputFormat(str, Enum):
    """Supported output formats."""
    PDF = "pdf"
    HTML = "html"
    MARKDOWN = "markdown"
    DOCX = "docx"


class TemplateType(str, Enum):
    """Available template types."""
    # Resume templates
    T_SHAPED_CLASSIC = "t_shaped_classic"
    T_SHAPED_MODERN = "t_shaped_modern"
    T_SHAPED_MINIMAL = "t_shaped_minimal"

    # Cover letter templates
    PAIN_PROMISE = "pain_promise"


class DocumentGenerationRequest(BaseModel):
    """Request model for document generation."""

    # Required fields
    session_id: str = Field(..., description="Session ID from orchestrator")
    document_type: DocumentType = Field(..., description="Type of document to generate")
    template_name: TemplateType = Field(..., description="Template to use for generation")

    # Optional format specification
    output_format: OutputFormat = Field(default=OutputFormat.PDF, description="Output format")

    # Optional job-specific customization
    job_requirements: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Job requirements for customization"
    )

    # Optional template customizations
    customizations: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Template-specific customizations"
    )

    # Optional company data for cover letters
    company_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Company information for cover letter customization"
    )

    # Generation options
    ats_optimization_level: str = Field(
        default="high",
        description="ATS optimization level (minimal, high, maximum)"
    )

    include_metadata: bool = Field(
        default=True,
        description="Include generation metadata in response"
    )

    @validator('template_name')
    def validate_template_for_document_type(cls, v, values):
        """Validate template matches document type."""
        document_type = values.get('document_type')

        if document_type == DocumentType.RESUME:
            if v not in [TemplateType.T_SHAPED_CLASSIC, TemplateType.T_SHAPED_MODERN, TemplateType.T_SHAPED_MINIMAL]:
                raise ValueError(f"Template {v} not valid for resume documents")
        elif document_type == DocumentType.COVER_LETTER:
            if v not in [TemplateType.PAIN_PROMISE]:
                raise ValueError(f"Template {v} not valid for cover letter documents")

        return v

    @validator('customizations')
    def validate_customizations(cls, v):
        """Validate customization parameters."""
        if v is None:
            return v

        # Define allowed customization keys
        allowed_keys = {
            'adjective', 'target_role_title', 'emphasis_areas',
            'color_scheme', 'font_preference', 'section_order',
            'skill_grouping', 'achievement_format'
        }

        invalid_keys = set(v.keys()) - allowed_keys
        if invalid_keys:
            raise ValueError(f"Invalid customization keys: {list(invalid_keys)}")

        return v


class JobRequirements(BaseModel):
    """Job requirements for document customization."""

    role_title: str = Field(..., description="Target job title")
    company: str = Field(..., description="Company name")
    industry: Optional[str] = Field(default=None, description="Industry sector")
    experience_level: Optional[str] = Field(default=None, description="Required experience level")

    required_skills: List[str] = Field(default=[], description="Required skills and technologies")
    preferred_skills: List[str] = Field(default=[], description="Preferred skills and technologies")

    key_requirements: List[str] = Field(default=[], description="Key job requirements")
    company_description: Optional[str] = Field(default=None, description="Company description")

    # ATS-specific requirements
    ats_keywords: List[str] = Field(default=[], description="Important ATS keywords")
    application_deadline: Optional[str] = Field(default=None, description="Application deadline")

    # Hiring manager info for cover letters
    hiring_manager: Optional[str] = Field(default=None, description="Hiring manager name")
    company_address: Optional[str] = Field(default=None, description="Company address")


class CompanyData(BaseModel):
    """Company information for cover letter customization."""

    name: str = Field(..., description="Company name")
    industry: Optional[str] = Field(default=None, description="Industry sector")
    size: Optional[str] = Field(default=None, description="Company size")

    # Pain & Promise model data
    recent_news: List[str] = Field(default=[], description="Recent company news/developments")
    challenges: List[str] = Field(default=[], description="Known company challenges")
    goals: List[str] = Field(default=[], description="Company goals and initiatives")

    # Contact information
    address: Optional[str] = Field(default=None, description="Company address")
    website: Optional[str] = Field(default=None, description="Company website")

    # Cultural information
    values: List[str] = Field(default=[], description="Company values")
    culture_keywords: List[str] = Field(default=[], description="Culture-related keywords")


class DocumentMetadata(BaseModel):
    """Document generation metadata."""

    template_name: str
    output_format: str
    document_type: str
    file_size: int
    generation_time: float
    memory_usage_mb: float
    timestamp: float

    # ATS compliance info
    ats_score: Optional[float] = Field(default=None, description="ATS compliance score")
    ats_warnings: List[str] = Field(default=[], description="ATS compliance warnings")

    # Quality metrics
    readability_score: Optional[float] = Field(default=None, description="Document readability score")
    keyword_density: Optional[Dict[str, float]] = Field(default=None, description="Keyword density analysis")


class DocumentResponse(BaseModel):
    """Response model for document generation."""

    # Document content (base64 encoded for binary formats)
    content: Union[str, bytes] = Field(..., description="Generated document content")
    content_encoding: str = Field(default="utf-8", description="Content encoding")

    # Metadata
    mime_type: str = Field(..., description="MIME type of generated document")
    metadata: Optional[DocumentMetadata] = Field(default=None, description="Generation metadata")

    # Success indicators
    success: bool = Field(default=True, description="Generation success status")
    message: Optional[str] = Field(default=None, description="Success or error message")

    # Additional data
    suggestions: List[str] = Field(default=[], description="Improvement suggestions")
    template_info: Optional[Dict[str, Any]] = Field(default=None, description="Template information")


class TemplateListRequest(BaseModel):
    """Request model for listing templates."""

    document_type: Optional[DocumentType] = Field(
        default=None,
        description="Filter by document type"
    )

    industry: Optional[str] = Field(
        default=None,
        description="Filter by target industry"
    )

    ats_optimization: Optional[str] = Field(
        default=None,
        description="Filter by ATS optimization level"
    )


class TemplateInfo(BaseModel):
    """Template information model."""

    id: str
    name: str
    description: str
    category: str
    target_industries: List[str]
    ats_optimization: str

    # Template capabilities
    supports_customizations: bool = Field(default=False)
    customization_options: List[str] = Field(default=[])

    # Performance info
    average_generation_time: Optional[float] = Field(default=None)
    complexity_level: Optional[str] = Field(default=None)


class TemplateListResponse(BaseModel):
    """Response model for template listing."""

    templates: List[TemplateInfo]
    total_count: int
    filtered_count: int

    # Available filter options
    available_industries: List[str] = Field(default=[])
    available_optimizations: List[str] = Field(default=[])


class GenerationStatusRequest(BaseModel):
    """Request model for generation status check."""

    generation_id: str = Field(..., description="Generation task ID")


class GenerationStatus(BaseModel):
    """Generation status information."""

    generation_id: str
    status: str  # pending, processing, completed, failed
    progress: Optional[float] = Field(default=None, description="Progress percentage (0-100)")

    # Timing information
    started_at: Optional[float] = Field(default=None)
    completed_at: Optional[float] = Field(default=None)
    estimated_completion: Optional[float] = Field(default=None)

    # Status details
    current_step: Optional[str] = Field(default=None)
    error_message: Optional[str] = Field(default=None)

    # Result (when completed)
    result: Optional[DocumentResponse] = Field(default=None)


class BulkGenerationRequest(BaseModel):
    """Request model for bulk document generation."""

    session_id: str = Field(..., description="Session ID from orchestrator")

    # Multiple generation requests
    generations: List[DocumentGenerationRequest] = Field(
        ...,
        min_items=1,
        max_items=10,
        description="List of document generation requests"
    )

    # Bulk options
    parallel_processing: bool = Field(
        default=True,
        description="Process requests in parallel"
    )

    fail_fast: bool = Field(
        default=False,
        description="Stop processing on first failure"
    )


class BulkGenerationResponse(BaseModel):
    """Response model for bulk document generation."""

    # Results
    results: List[DocumentResponse] = Field(..., description="Generation results")
    success_count: int = Field(..., description="Number of successful generations")
    failure_count: int = Field(..., description="Number of failed generations")

    # Timing
    total_time: float = Field(..., description="Total processing time")

    # Summary
    summary: Dict[str, Any] = Field(default={}, description="Generation summary")
