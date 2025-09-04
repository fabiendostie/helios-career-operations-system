"""Command data models and schemas."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from uuid import UUID

from pydantic import BaseModel, Field, validator, model_validator


class CommandType(str, Enum):
    """Supported command types."""
    
    START = "/start"
    INGEST = "/ingest"
    DISCOVER = "/discover"
    ANALYZE = "/analyze"
    BUILD = "/build"
    STATUS = "/status"
    HELP = "/help"


class CommandStatus(str, Enum):
    """Command execution status."""
    
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CommandRequest(BaseModel):
    """Base command request model."""
    
    command: CommandType = Field(..., description="Command to execute")
    session_id: str = Field(..., description="Session identifier")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Command-specific parameters")
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow, description="Request timestamp")
    
    @validator('session_id')
    def validate_session_id(cls, v, values):
        """Validate session ID format."""
        # Allow empty session_id for START commands only
        command = values.get('command')
        if command != CommandType.START and (not v or len(v.strip()) == 0):
            raise ValueError("Session ID cannot be empty")
        return v.strip() if v else v


class CommandResponse(BaseModel):
    """Base command response model."""
    
    command: CommandType = Field(..., description="Original command")
    session_id: str = Field(..., description="Session identifier")
    status: CommandStatus = Field(..., description="Command execution status")
    result: Dict[str, Any] = Field(default_factory=dict, description="Command-specific result")
    message: str = Field(..., description="Human-readable message")
    next_actions: List[CommandType] = Field(default_factory=list, description="Available next commands")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    execution_time_ms: Optional[float] = Field(None, description="Command execution time in milliseconds")


# Specific command parameter models
class StartCommandParams(BaseModel):
    """Parameters for /start command."""
    
    user_id: Optional[str] = Field(None, description="Optional user identifier")
    initial_data: Dict[str, Any] = Field(default_factory=dict, description="Initial session data")


class IngestCommandParams(BaseModel):
    """Parameters for /ingest command."""
    
    file_paths: List[str] = Field(default_factory=list, description="Paths to files to ingest")
    file_urls: List[str] = Field(default_factory=list, description="URLs to files to ingest")
    text_content: Optional[str] = Field(None, description="Direct text content to ingest")
    format_hint: Optional[str] = Field(None, description="Hint about file format (pdf, docx, etc.)")
    
    @model_validator(mode='after')
    def at_least_one_input(self):
        """Ensure at least one input method is provided."""
        if not any([
            self.file_paths,
            self.file_urls,
            self.text_content
        ]):
            raise ValueError("Must provide at least one of: file_paths, file_urls, or text_content")
        return self


class DiscoverCommandParams(BaseModel):
    """Parameters for /discover command."""
    
    focus_areas: List[str] = Field(default_factory=list, description="Specific areas to focus discovery on")
    depth_level: str = Field("standard", description="Analysis depth: shallow, standard, deep")
    include_suggestions: bool = Field(True, description="Include improvement suggestions")
    
    @validator('depth_level')
    def validate_depth_level(cls, v):
        """Validate depth level."""
        allowed = ["shallow", "standard", "deep"]
        if v not in allowed:
            raise ValueError(f"Depth level must be one of: {allowed}")
        return v


class AnalyzeCommandParams(BaseModel):
    """Parameters for /analyze command."""
    
    analysis_type: str = Field("comprehensive", description="Type of analysis to perform")
    target_roles: List[str] = Field(default_factory=list, description="Target job roles for analysis")
    market_focus: Optional[str] = Field(None, description="Geographic or industry market focus")
    
    @validator('analysis_type')
    def validate_analysis_type(cls, v):
        """Validate analysis type."""
        allowed = ["comprehensive", "skills", "market", "compatibility"]
        if v not in allowed:
            raise ValueError(f"Analysis type must be one of: {allowed}")
        return v


class BuildCommandParams(BaseModel):
    """Parameters for /build command."""
    
    document_types: List[str] = Field(default_factory=list, description="Types of documents to build")
    target_role: Optional[str] = Field(None, description="Specific target role for document optimization")
    style_preferences: Dict[str, Any] = Field(default_factory=dict, description="Document style preferences")
    
    @validator('document_types')
    def validate_document_types(cls, v):
        """Validate document types."""
        allowed = ["resume", "cover_letter", "linkedin", "summary"]
        invalid = [doc for doc in v if doc not in allowed]
        if invalid:
            raise ValueError(f"Invalid document types: {invalid}. Allowed: {allowed}")
        return v


class StatusCommandParams(BaseModel):
    """Parameters for /status command."""
    
    include_history: bool = Field(False, description="Include command history in response")
    include_details: bool = Field(False, description="Include detailed session information")


# Union type for all command parameters
CommandParameters = Union[
    StartCommandParams,
    IngestCommandParams,
    DiscoverCommandParams,
    AnalyzeCommandParams,
    BuildCommandParams,
    StatusCommandParams,
    Dict[str, Any]  # Fallback for unknown parameters
]


class CommandHistory(BaseModel):
    """Command history entry."""
    
    command: CommandType
    parameters: Dict[str, Any]
    status: CommandStatus
    result: Dict[str, Any]
    message: str
    timestamp: datetime
    execution_time_ms: Optional[float] = None
    
    
class CommandValidationError(Exception):
    """Exception raised for command validation errors."""
    
    def __init__(self, message: str, command: Optional[CommandType] = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.command = command
        self.details = details or {}
        super().__init__(self.message)


class CommandExecutionError(Exception):
    """Exception raised for command execution errors."""
    
    def __init__(self, message: str, command: Optional[CommandType] = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.command = command
        self.details = details or {}
        super().__init__(self.message)