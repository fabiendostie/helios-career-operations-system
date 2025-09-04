"""Session management API endpoints."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db, SessionRepository
from ..core.session_manager import SessionManager
from ..models.session import (
    SessionCreate,
    SessionUpdate, 
    SessionResponse,
    SessionSummary,
    SessionState
)
from ..utils.logging_config import get_logger


logger = get_logger("sessions_api")
router = APIRouter()


async def get_session_manager(db: AsyncSession = Depends(get_db)) -> SessionManager:
    """Dependency to get session manager."""
    repository = SessionRepository(db)
    return SessionManager(repository)


@router.post("/", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    session_data: SessionCreate,
    manager: SessionManager = Depends(get_session_manager)
):
    """Create a new session.
    
    Args:
        session_data: Session creation data
        manager: Session manager dependency
        
    Returns:
        Created session
    """
    try:
        logger.info("Creating new session")
        session = await manager.create_session(session_data)
        logger.info(f"Created session {session.session_id}")
        return session
    except Exception as e:
        logger.error(f"Failed to create session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create session"
        )


@router.get("/", response_model=List[SessionSummary])
async def list_sessions(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    state: Optional[SessionState] = Query(None, description="Filter by session state"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    manager: SessionManager = Depends(get_session_manager)
):
    """List sessions with optional filtering.
    
    Args:
        user_id: Optional user ID filter
        state: Optional state filter
        limit: Maximum results
        offset: Results to skip
        manager: Session manager dependency
        
    Returns:
        List of session summaries
    """
    try:
        logger.debug(f"Listing sessions with filters: user_id={user_id}, state={state}")
        sessions = await manager.list_sessions(
            user_id=user_id,
            state=state,
            limit=limit,
            offset=offset
        )
        return sessions
    except Exception as e:
        logger.error(f"Failed to list sessions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list sessions"
        )


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    manager: SessionManager = Depends(get_session_manager)
):
    """Get session by ID.
    
    Args:
        session_id: Session identifier
        manager: Session manager dependency
        
    Returns:
        Session details
        
    Raises:
        HTTPException: If session not found
    """
    try:
        logger.debug(f"Getting session {session_id}")
        session = await manager.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        return session
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get session"
        )


@router.put("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    updates: SessionUpdate,
    manager: SessionManager = Depends(get_session_manager)
):
    """Update session data.
    
    Args:
        session_id: Session identifier
        updates: Fields to update
        manager: Session manager dependency
        
    Returns:
        Updated session
        
    Raises:
        HTTPException: If session not found
    """
    try:
        logger.info(f"Updating session {session_id}")
        session = await manager.update_session(session_id, updates)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        return session
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update session"
        )


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str,
    manager: SessionManager = Depends(get_session_manager)
):
    """Delete session.
    
    Args:
        session_id: Session identifier
        manager: Session manager dependency
        
    Raises:
        HTTPException: If session not found
    """
    try:
        logger.info(f"Deleting session {session_id}")
        deleted = await manager.delete_session(session_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete session"
        )


@router.post("/{session_id}/extend", response_model=SessionResponse)
async def extend_session(
    session_id: str,
    minutes: Optional[int] = Query(None, ge=1, le=1440, description="Minutes to extend (default: session timeout)"),
    manager: SessionManager = Depends(get_session_manager)
):
    """Extend session expiration time.
    
    Args:
        session_id: Session identifier
        minutes: Minutes to extend (default from settings)
        manager: Session manager dependency
        
    Returns:
        Updated session
        
    Raises:
        HTTPException: If session not found
    """
    try:
        logger.info(f"Extending session {session_id} by {minutes} minutes")
        session = await manager.extend_session(session_id, minutes)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        return session
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to extend session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to extend session"
        )


@router.post("/{session_id}/state", response_model=SessionResponse)
async def transition_session_state(
    session_id: str,
    new_state: SessionState,
    manager: SessionManager = Depends(get_session_manager)
):
    """Transition session to new state.
    
    Args:
        session_id: Session identifier
        new_state: New session state
        manager: Session manager dependency
        
    Returns:
        Updated session
        
    Raises:
        HTTPException: If session not found
    """
    try:
        logger.info(f"Transitioning session {session_id} to state {new_state}")
        session = await manager.transition_state(session_id, new_state)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        return session
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to transition session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to transition session state"
        )


@router.post("/cleanup", response_model=dict)
async def cleanup_expired_sessions(
    manager: SessionManager = Depends(get_session_manager)
):
    """Clean up expired sessions.
    
    Args:
        manager: Session manager dependency
        
    Returns:
        Cleanup results
    """
    try:
        logger.info("Running expired session cleanup")
        count = await manager.cleanup_expired_sessions()
        return {"cleaned_up": count, "message": f"Cleaned up {count} expired sessions"}
    except Exception as e:
        logger.error(f"Failed to cleanup expired sessions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cleanup expired sessions"
        )