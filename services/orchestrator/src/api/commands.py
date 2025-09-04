"""Command execution API endpoints."""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db, SessionRepository
from ..core.session_manager import SessionManager
from ..core.command_router import CommandRouter
from ..models.commands import (
    CommandRequest,
    CommandResponse,
    CommandValidationError,
    CommandExecutionError,
    CommandType
)
from ..utils.logging_config import get_logger


logger = get_logger("commands_api")
router = APIRouter()


async def get_session_manager(db: AsyncSession = Depends(get_db)) -> SessionManager:
    """Dependency to get session manager."""
    repository = SessionRepository(db)
    return SessionManager(repository)


async def get_command_router() -> CommandRouter:
    """Dependency to get command router."""
    return CommandRouter()


@router.post("/execute", response_model=CommandResponse)
async def execute_command(
    request: CommandRequest,
    session_manager: SessionManager = Depends(get_session_manager),
    command_router: CommandRouter = Depends(get_command_router)
):
    """Execute a command.
    
    Args:
        request: Command request to execute
        session_manager: Session manager dependency
        command_router: Command router dependency
        
    Returns:
        Command response
        
    Raises:
        HTTPException: If command validation or execution fails
    """
    try:
        logger.info(f"Executing command {request.command} for session {request.session_id}")
        
        response = await command_router.route_command(request, session_manager)
        
        logger.info(f"Command {request.command} executed successfully")
        return response
        
    except CommandValidationError as e:
        logger.error(f"Command validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Command validation failed",
                "message": e.message,
                "command": e.command.value if e.command else None,
                "details": e.details
            }
        )
    except CommandExecutionError as e:
        logger.error(f"Command execution failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Command execution failed",
                "message": e.message,
                "command": e.command.value if e.command else None,
                "details": e.details
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error executing command: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "message": "An unexpected error occurred while executing the command"
            }
        )


@router.post("/start", response_model=CommandResponse)
async def start_session(
    user_id: str = None,
    initial_data: Dict[str, Any] = None,
    session_manager: SessionManager = Depends(get_session_manager),
    command_router: CommandRouter = Depends(get_command_router)
):
    """Start a new session (convenience endpoint for /start command).
    
    Args:
        user_id: Optional user identifier
        initial_data: Optional initial session data
        session_manager: Session manager dependency
        command_router: Command router dependency
        
    Returns:
        Command response with new session ID
    """
    try:
        request = CommandRequest(
            command=CommandType.START,
            session_id="",  # Will be generated
            parameters={
                "user_id": user_id,
                "initial_data": initial_data or {}
            }
        )
        
        return await execute_command(request, session_manager, command_router)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start new session"
        )


@router.get("/help", response_model=CommandResponse)
async def get_help(
    session_id: str = "help-session",
    session_manager: SessionManager = Depends(get_session_manager),
    command_router: CommandRouter = Depends(get_command_router)
):
    """Get command help information.
    
    Args:
        session_id: Session ID (defaults to help-session)
        session_manager: Session manager dependency
        command_router: Command router dependency
        
    Returns:
        Help information response
    """
    try:
        request = CommandRequest(
            command=CommandType.HELP,
            session_id=session_id,
            parameters={}
        )
        
        return await execute_command(request, session_manager, command_router)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get help: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get help information"
        )


@router.get("/status/{session_id}", response_model=CommandResponse)
async def get_session_status(
    session_id: str,
    include_history: bool = False,
    include_details: bool = False,
    session_manager: SessionManager = Depends(get_session_manager),
    command_router: CommandRouter = Depends(get_command_router)
):
    """Get session status (convenience endpoint for /status command).
    
    Args:
        session_id: Session identifier
        include_history: Include command history in response
        include_details: Include detailed session information
        session_manager: Session manager dependency
        command_router: Command router dependency
        
    Returns:
        Session status response
    """
    try:
        request = CommandRequest(
            command=CommandType.STATUS,
            session_id=session_id,
            parameters={
                "include_history": include_history,
                "include_details": include_details
            }
        )
        
        return await execute_command(request, session_manager, command_router)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get session status"
        )


@router.get("/commands", response_model=Dict[str, str])
async def list_commands():
    """List all available commands.
    
    Returns:
        Dictionary of available commands and their descriptions
    """
    return {
        "/start": "Initialize a new session",
        "/ingest": "Process resume/profile documents",
        "/discover": "Analyze career profile and opportunities", 
        "/analyze": "Perform detailed career analysis",
        "/build": "Generate career documents",
        "/status": "Get current session status",
        "/help": "Show command help information"
    }