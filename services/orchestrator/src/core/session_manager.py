"""Session management service layer."""

import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from uuid import UUID
import sys
import os

# Add bmad-core to path for internet datetime utility
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'bmad-core'))
try:
    from utils.internet_datetime import get_current_datetime_sync
    INTERNET_TIME_AVAILABLE = True
except ImportError:
    INTERNET_TIME_AVAILABLE = False
    import logging
    logging.warning("Internet time utilities not available in Orchestrator, falling back to system time")

from ..models.session import (
    Session, 
    SessionCreate, 
    SessionUpdate, 
    SessionResponse, 
    SessionSummary,
    SessionState,
    CurrentStep
)
from ..core.database import SessionRepository
from ..utils.logging_config import get_logger


logger = get_logger("session_manager")


class SessionManager:
    """High-level session management operations."""
    
    def __init__(self, repository: SessionRepository):
        """Initialize with session repository.
        
        Args:
            repository: Session database repository
        """
        self.repository = repository
    
    async def create_session(
        self,
        session_data: SessionCreate
    ) -> SessionResponse:
        """Create a new session.
        
        Args:
            session_data: Session creation data
            
        Returns:
            Created session response
        """
        logger.info(f"Creating session for user {session_data.user_id}")
        
        # Create session in database
        db_session = await self.repository.create_session(
            user_id=session_data.user_id,
            initial_data=session_data.master_career_database
        )
        
        # Update with provided data
        if session_data.state != SessionState.INITIALIZED:
            await self.repository.update_session(
                str(db_session.session_id),
                state=session_data.state
            )
        
        if session_data.current_step != CurrentStep.START:
            await self.repository.update_session(
                str(db_session.session_id),
                current_step=session_data.current_step
            )
        
        # Convert to response model
        return await self._db_session_to_response(db_session)
    
    async def get_session(self, session_id: str) -> Optional[SessionResponse]:
        """Get session by ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session response or None if not found
        """
        logger.debug(f"Getting session {session_id}")
        
        db_session = await self.repository.get_session(session_id)
        if not db_session:
            logger.warning(f"Session {session_id} not found")
            return None
        
        return await self._db_session_to_response(db_session)
    
    async def update_session(
        self,
        session_id: str,
        updates: SessionUpdate
    ) -> Optional[SessionResponse]:
        """Update session data.
        
        Args:
            session_id: Session identifier
            updates: Fields to update
            
        Returns:
            Updated session or None if not found
        """
        logger.info(f"Updating session {session_id}")
        
        # Convert Pydantic model to dict, excluding None values
        update_data = updates.model_dump(exclude_unset=True, exclude_none=True)
        
        if not update_data:
            # No updates provided, just return current session
            return await self.get_session(session_id)
        
        db_session = await self.repository.update_session(session_id, **update_data)
        if not db_session:
            logger.warning(f"Session {session_id} not found for update")
            return None
        
        return await self._db_session_to_response(db_session)
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deleted, False if not found
        """
        logger.info(f"Deleting session {session_id}")
        return await self.repository.delete_session(session_id)
    
    async def list_sessions(
        self,
        user_id: Optional[str] = None,
        state: Optional[SessionState] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[SessionSummary]:
        """List sessions with optional filtering.
        
        Args:
            user_id: Filter by user ID
            state: Filter by session state
            limit: Maximum results
            offset: Results to skip
            
        Returns:
            List of session summaries
        """
        logger.debug(f"Listing sessions for user {user_id}, state {state}")
        
        db_sessions = await self.repository.list_sessions(
            user_id=user_id,
            state=state,
            limit=limit,
            offset=offset
        )
        
        return [await self._db_session_to_summary(session) for session in db_sessions]
    
    async def add_command_to_history(
        self,
        session_id: str,
        command: Dict[str, Any]
    ) -> Optional[SessionResponse]:
        """Add command to session history.
        
        Args:
            session_id: Session identifier
            command: Command data to add
            
        Returns:
            Updated session or None if not found
        """
        # Get current session
        current_session = await self.get_session(session_id)
        if not current_session:
            return None
        
        # Add timestamp to command
        # Use internet time with Montreal timezone for accurate timestamps
        if INTERNET_TIME_AVAILABLE:
            current_dt = get_current_datetime_sync()
        else:
            current_dt = datetime.now(timezone.utc)
            
        command_with_timestamp = {
            **command,
            "executed_at": current_dt.isoformat()
        }
        
        # Update command history
        new_history = current_session.command_history + [command_with_timestamp]
        
        updates = SessionUpdate(command_history=new_history)
        return await self.update_session(session_id, updates)
    
    async def update_career_database(
        self,
        session_id: str,
        career_data: Dict[str, Any]
    ) -> Optional[SessionResponse]:
        """Update master career database for session.
        
        Args:
            session_id: Session identifier
            career_data: Career database data
            
        Returns:
            Updated session or None if not found
        """
        logger.info(f"Updating career database for session {session_id}")
        
        updates = SessionUpdate(master_career_database=career_data)
        return await self.update_session(session_id, updates)
    
    async def transition_state(
        self,
        session_id: str,
        new_state: SessionState,
        new_step: Optional[CurrentStep] = None
    ) -> Optional[SessionResponse]:
        """Transition session to new state and optionally new step.
        
        Args:
            session_id: Session identifier
            new_state: New session state
            new_step: Optional new current step
            
        Returns:
            Updated session or None if not found
        """
        logger.info(f"Transitioning session {session_id} to state {new_state}")
        
        update_data = {"state": new_state}
        if new_step:
            update_data["current_step"] = new_step
        
        updates = SessionUpdate(**update_data)
        return await self.update_session(session_id, updates)
    
    async def extend_session(
        self,
        session_id: str,
        minutes: Optional[int] = None
    ) -> Optional[SessionResponse]:
        """Extend session expiration time.
        
        Args:
            session_id: Session identifier
            minutes: Minutes to extend (default from settings)
            
        Returns:
            Updated session or None if not found
        """
        logger.info(f"Extending session {session_id}")
        
        db_session = await self.repository.extend_session(session_id, minutes)
        if not db_session:
            return None
        
        return await self._db_session_to_response(db_session)
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions.
        
        Returns:
            Number of sessions cleaned up
        """
        logger.info("Running expired session cleanup")
        return await self.repository.cleanup_expired_sessions()
    
    async def _db_session_to_response(self, db_session: Session) -> SessionResponse:
        """Convert database session to response model.
        
        Args:
            db_session: Database session object
            
        Returns:
            Session response model
        """
        # Parse JSON fields
        master_career_database = json.loads(db_session.master_career_database or "{}")
        command_history = json.loads(db_session.command_history or "[]")
        metadata = json.loads(db_session.session_metadata or "{}")
        
        return SessionResponse(
            session_id=UUID(db_session.session_id) if isinstance(db_session.session_id, str) else db_session.session_id,
            user_id=db_session.user_id,
            state=db_session.state,
            current_step=db_session.current_step,
            master_career_database=master_career_database,
            command_history=command_history,
            metadata=metadata,
            created_at=db_session.created_at,
            updated_at=db_session.updated_at,
            expires_at=db_session.expires_at
        )
    
    async def _db_session_to_summary(self, db_session: Session) -> SessionSummary:
        """Convert database session to summary model.
        
        Args:
            db_session: Database session object
            
        Returns:
            Session summary model
        """
        return SessionSummary(
            session_id=UUID(db_session.session_id) if isinstance(db_session.session_id, str) else db_session.session_id,
            user_id=db_session.user_id,
            state=db_session.state,
            current_step=db_session.current_step,
            created_at=db_session.created_at,
            updated_at=db_session.updated_at,
            expires_at=db_session.expires_at
        )