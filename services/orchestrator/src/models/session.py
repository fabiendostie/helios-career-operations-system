"""Session data models and schemas."""

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from sqlalchemy import Column, String, DateTime, Text, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.dialects.sqlite import INTEGER


Base = declarative_base()


class SessionState(str, Enum):
    """Session state enumeration."""

    INITIALIZED = "initialized"
    INGESTING = "ingesting"
    ANALYZING = "analyzing"
    GENERATING = "generating"
    COMPLETED = "completed"
    ERROR = "error"
    EXPIRED = "expired"


class CurrentStep(str, Enum):
    """Current workflow step enumeration."""

    START = "start"
    INGEST = "ingest"
    DISCOVER = "discover"
    ANALYZE = "analyze"
    BUILD = "build"
    REVIEW = "review"


class SessionBase(BaseModel):
    """Base session model for API operations."""

    user_id: Optional[str] = Field(None, description="Optional user identifier")
    state: SessionState = Field(SessionState.INITIALIZED, description="Current session state")
    current_step: CurrentStep = Field(CurrentStep.START, description="Current workflow step")
    master_career_database: Dict[str, Any] = Field(default_factory=dict, description="Career data from Profile Ingestor")
    command_history: List[Dict[str, Any]] = Field(default_factory=list, description="History of commands executed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional session metadata")


class SessionCreate(SessionBase):
    """Session creation model."""
    pass


class SessionUpdate(BaseModel):
    """Session update model - all fields optional."""

    user_id: Optional[str] = None
    state: Optional[SessionState] = None
    current_step: Optional[CurrentStep] = None
    master_career_database: Optional[Dict[str, Any]] = None
    command_history: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None


class SessionResponse(SessionBase):
    """Session response model with full details."""

    session_id: UUID = Field(description="Unique session identifier")
    created_at: datetime = Field(description="Session creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    expires_at: datetime = Field(description="Session expiration timestamp")

    class Config:
        from_attributes = True


class SessionSummary(BaseModel):
    """Simplified session model for list operations."""

    session_id: UUID
    user_id: Optional[str]
    state: SessionState
    current_step: CurrentStep
    created_at: datetime
    updated_at: datetime
    expires_at: datetime

    class Config:
        from_attributes = True


# SQLAlchemy ORM Model
class Session(Base):
    """SQLAlchemy session model for database operations."""

    __tablename__ = "sessions"

    # Use String for UUID storage (compatible with both SQLite and PostgreSQL)
    session_id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4())
    )

    user_id = Column(String(100), nullable=True, index=True)
    state = Column(SQLEnum(SessionState), nullable=False, default=SessionState.INITIALIZED, index=True)
    current_step = Column(SQLEnum(CurrentStep), nullable=False, default=CurrentStep.START, index=True)

    # JSON fields stored as TEXT
    master_career_database = Column(Text, nullable=False, default="{}")
    command_history = Column(Text, nullable=False, default="[]")
    session_metadata = Column(Text, nullable=False, default="{}")

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<Session(session_id={self.session_id}, state={self.state}, user_id={self.user_id})>"

    @property
    def is_expired(self) -> bool:
        """Check if session has expired."""
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def time_until_expiry(self) -> float:
        """Get seconds until session expires."""
        delta = self.expires_at - datetime.now(timezone.utc)
        return max(0, delta.total_seconds())
