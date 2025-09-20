"""
Data Contracts for Service Integration

Defines the data models and contracts used for communication between
the ARCHITECT service and other Helios services.
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

class DocumentType(str, Enum):
    """Types of documents the ARCHITECT service can generate."""
    RESUME = "resume"
    COVER_LETTER = "cover_letter"
    LINKEDIN_SUMMARY = "linkedin_summary"
    PORTFOLIO_PAGE = "portfolio_page"

class DocumentFormat(str, Enum):
    """Output formats supported by the ARCHITECT service."""
    PDF = "pdf"
    DOCX = "docx"  
    HTML = "html"
    MARKDOWN = "markdown"
    TXT = "txt"

class ResumeArchitecture(str, Enum):
    """Resume architecture styles supported."""
    T_SHAPED = "t_shaped"        # Impact Summary + Experience Log
    CHRONOLOGICAL = "chronological"
    FUNCTIONAL = "functional"
    HYBRID = "hybrid"

# ANALYST Service Data Contracts

class AnalystRecommendations(BaseModel):
    """Recommendations from the ANALYST service for document optimization."""
    
    session_id: str
    user_profile_id: str
    target_role: Optional[str] = None
    target_company: Optional[str] = None
    
    # Content optimization recommendations
    content_optimization: Dict[str, Any] = Field(
        description="Content suggestions for different document sections"
    )
    
    # Keyword optimization
    priority_keywords: List[str] = Field(
        description="High-priority keywords to include based on market analysis"
    )
    keyword_density_targets: Dict[str, float] = Field(
        description="Optimal keyword density percentages"
    )
    
    # Skills highlighting
    critical_skills: List[str] = Field(
        description="Skills that should be prominently featured"
    )
    emerging_skills: List[str] = Field(
        description="Trending skills to consider adding"
    )
    
    # Market intelligence
    market_insights: Dict[str, Any] = Field(
        description="Market trends and competitive analysis"
    )
    
    # ATS optimization
    ats_recommendations: Dict[str, Any] = Field(
        description="ATS-specific optimization suggestions"
    )
    
    # Performance metrics
    optimization_score: float = Field(
        description="Predicted resume performance score (0-100)"
    )
    
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

class StrategistInsights(BaseModel):
    """Career strategy insights from the STRATEGIST service."""
    
    session_id: str
    user_profile_id: str
    
    # Career path analysis
    recommended_career_paths: List[Dict[str, Any]] = Field(
        description="Suggested career progression paths"
    )
    
    # Skill adjacency mapping
    skill_adjacency: Dict[str, List[str]] = Field(
        description="Skills that commonly appear together"
    )
    skill_progression: Dict[str, Any] = Field(
        description="Skills development roadmap"
    )
    
    # Role targeting
    target_roles: List[Dict[str, Any]] = Field(
        description="Roles that match user's profile and goals"
    )
    role_gap_analysis: Dict[str, Any] = Field(
        description="Skills/experience gaps for target roles"
    )
    
    # Industry insights
    industry_trends: Dict[str, Any] = Field(
        description="Industry-specific trends and opportunities"
    )
    
    # Positioning strategy
    positioning_strategy: Dict[str, Any] = Field(
        description="How to position the candidate in the market"
    )
    
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    confidence_score: float = Field(
        description="Confidence in strategic recommendations (0-100)"
    )

# Orchestrator Service Data Contracts

class OrchestratorSession(BaseModel):
    """Session information from the Orchestrator service."""
    
    session_id: str
    user_id: str
    
    # Session state
    current_stage: str = Field(
        description="Current stage in the career operations pipeline"
    )
    session_metadata: Dict[str, Any] = Field(
        description="Session-specific metadata and preferences"
    )
    
    # User context
    user_profile: Dict[str, Any] = Field(
        description="User profile data from Profile Ingestor"
    )
    user_preferences: Dict[str, Any] = Field(
        description="User preferences for document generation"
    )
    
    # Service coordination
    analyst_status: Optional[str] = None
    strategist_status: Optional[str] = None
    architect_status: Optional[str] = None
    
    created_at: datetime
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

# Document Generation Request/Response

class DocumentGenerationRequest(BaseModel):
    """Request for document generation from other services."""
    
    # Request identification
    request_id: str = Field(description="Unique request identifier")
    session_id: str = Field(description="Orchestrator session ID")
    user_id: str = Field(description="User identifier")
    
    # Document specifications
    document_type: DocumentType
    output_format: DocumentFormat
    architecture: Optional[ResumeArchitecture] = ResumeArchitecture.T_SHAPED
    
    # Content sources
    user_profile: Dict[str, Any] = Field(
        description="User profile data for content generation"
    )
    analyst_recommendations: Optional[AnalystRecommendations] = None
    strategist_insights: Optional[StrategistInsights] = None
    
    # Generation parameters
    target_role: Optional[str] = None
    target_company: Optional[str] = None
    custom_instructions: Optional[str] = None
    
    # Quality requirements
    ats_compliance_level: str = "standard"  # strict, standard, basic
    target_ats_vendors: List[str] = Field(default_factory=lambda: ["generic"])
    
    # Processing options
    include_validation: bool = True
    include_optimization: bool = True
    return_sources: bool = False
    
    requested_at: datetime = Field(default_factory=datetime.utcnow)

class DocumentGenerationResponse(BaseModel):
    """Response from document generation process."""
    
    # Request tracking
    request_id: str
    session_id: str
    processing_time_seconds: float
    
    # Generation results
    success: bool
    document_url: Optional[str] = None  # URL to generated document
    document_content: Optional[str] = None  # Inline content if requested
    
    # Quality metrics
    ats_compliance_score: Optional[float] = None
    optimization_score: Optional[float] = None
    content_quality_score: Optional[float] = None
    
    # Validation results
    validation_results: Optional[Dict[str, Any]] = None
    compliance_violations: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    
    # Generation metadata
    template_used: Optional[str] = None
    research_sources: List[str] = Field(default_factory=list)
    generation_metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Error handling
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    retry_suggestions: List[str] = Field(default_factory=list)
    
    generated_at: datetime = Field(default_factory=datetime.utcnow)

# Integration Health Models

class ServiceHealthStatus(BaseModel):
    """Health status for integrated services."""
    
    service_name: str
    is_healthy: bool
    response_time_ms: Optional[float] = None
    last_checked: datetime = Field(default_factory=datetime.utcnow)
    error_message: Optional[str] = None

class IntegrationHealthReport(BaseModel):
    """Overall integration health report."""
    
    orchestrator: ServiceHealthStatus
    analyst: ServiceHealthStatus
    strategist: ServiceHealthStatus
    
    overall_health: bool
    degraded_services: List[str] = Field(default_factory=list)
    
    generated_at: datetime = Field(default_factory=datetime.utcnow)

# Event Models for Service Communication

class DocumentGenerationEvent(BaseModel):
    """Event model for document generation lifecycle."""
    
    event_id: str
    event_type: str  # started, progress, completed, failed
    request_id: str
    session_id: str
    
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ServiceIntegrationEvent(BaseModel):
    """Event model for service integration activities."""
    
    event_id: str
    source_service: str
    target_service: str
    event_type: str
    
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)