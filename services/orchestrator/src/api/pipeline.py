"""Pipeline orchestration API endpoints."""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import Dict, Any, Optional
import logging

from ..core.service_coordinator import ServiceCoordinator, ServiceCoordinationError
from ..core.session_manager import SessionManager
from ..core.database import SessionRepository
from ..integrations.profile_ingestor import ProfileIngestorClient
from ..integrations.strategist import StrategistClient
from ..integrations.analyst import AnalystClient
from ..models.session import SessionCreate, SessionState, CurrentStep

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/pipeline", tags=["Pipeline"])


# Dependency injection
async def get_service_coordinator() -> ServiceCoordinator:
    """Get service coordinator instance."""
    # In production, these would be properly dependency-injected
    session_repo = SessionRepository()
    session_manager = SessionManager(session_repo)
    
    profile_ingestor = ProfileIngestorClient()
    strategist = StrategistClient()
    analyst = AnalystClient()
    
    return ServiceCoordinator(
        session_manager=session_manager,
        profile_ingestor=profile_ingestor,
        strategist=strategist,
        analyst=analyst
    )


@router.post("/execute")
async def execute_pipeline(
    resume_path: Optional[str] = None,
    career_data: Optional[Dict[str, Any]] = None,
    background_tasks: BackgroundTasks = None,
    coordinator: ServiceCoordinator = Depends(get_service_coordinator)
) -> Dict[str, Any]:
    """Execute the complete Profile Ingestor → Strategist → Analyst pipeline.
    
    Args:
        resume_path: Path to resume file (optional)
        career_data: Direct career data input (optional)
        background_tasks: FastAPI background tasks
        coordinator: Service coordinator
        
    Returns:
        Pipeline execution results
    """
    logger.info("Pipeline execution requested")
    
    try:
        # Create new session for pipeline execution
        session_data = SessionCreate(
            user_id=f"pipeline_user_{int(datetime.utcnow().timestamp())}",
            state=SessionState.INITIALIZED,
            current_step=CurrentStep.START
        )
        
        session_manager = coordinator.session_manager
        session_response = await session_manager.create_session(session_data)
        session_id = session_response.session_id
        
        logger.info(f"Created session {session_id} for pipeline execution")
        
        # Execute pipeline
        results = await coordinator.execute_full_pipeline(
            session_id=str(session_id),
            resume_path=resume_path,
            career_data=career_data
        )
        
        return {
            "success": True,
            "session_id": session_id,
            "results": results,
            "message": "Pipeline executed successfully"
        }
        
    except ServiceCoordinationError as e:
        logger.error(f"Pipeline execution failed: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Pipeline execution failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in pipeline execution: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/execute-async")
async def execute_pipeline_async(
    resume_path: Optional[str] = None,
    career_data: Optional[Dict[str, Any]] = None,
    background_tasks: BackgroundTasks = None,
    coordinator: ServiceCoordinator = Depends(get_service_coordinator)
) -> Dict[str, Any]:
    """Execute pipeline asynchronously in background.
    
    Args:
        resume_path: Path to resume file (optional)
        career_data: Direct career data input (optional)
        background_tasks: FastAPI background tasks
        coordinator: Service coordinator
        
    Returns:
        Session ID for tracking pipeline execution
    """
    logger.info("Async pipeline execution requested")
    
    try:
        # Create new session for pipeline execution
        session_data = SessionCreate(
            user_id=f"async_pipeline_user_{int(datetime.utcnow().timestamp())}",
            state=SessionState.INITIALIZED,
            current_step=CurrentStep.START
        )
        
        session_manager = coordinator.session_manager
        session_response = await session_manager.create_session(session_data)
        session_id = session_response.session_id
        
        logger.info(f"Created session {session_id} for async pipeline execution")
        
        # Add pipeline execution to background tasks
        background_tasks.add_task(
            _execute_pipeline_background,
            coordinator,
            str(session_id),
            resume_path,
            career_data
        )
        
        return {
            "success": True,
            "session_id": session_id,
            "message": "Pipeline execution started in background",
            "status_endpoint": f"/api/v1/pipeline/status/{session_id}"
        }
        
    except Exception as e:
        logger.error(f"Failed to start async pipeline execution: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start pipeline execution")


@router.get("/status/{session_id}")
async def get_pipeline_status(
    session_id: str,
    coordinator: ServiceCoordinator = Depends(get_service_coordinator)
) -> Dict[str, Any]:
    """Get pipeline execution status.
    
    Args:
        session_id: Session identifier
        coordinator: Service coordinator
        
    Returns:
        Pipeline status information
    """
    try:
        status = await coordinator.get_pipeline_status(session_id)
        return {
            "success": True,
            "status": status
        }
    except Exception as e:
        logger.error(f"Failed to get pipeline status for session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get pipeline status")


@router.get("/health")
async def pipeline_health_check(
    coordinator: ServiceCoordinator = Depends(get_service_coordinator)
) -> Dict[str, Any]:
    """Check health of all pipeline services.
    
    Args:
        coordinator: Service coordinator
        
    Returns:
        Health status of all services
    """
    try:
        health_status = await coordinator.health_check_all_services()
        return {
            "success": True,
            "health": health_status
        }
    except Exception as e:
        logger.error(f"Pipeline health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Health check failed")


async def _execute_pipeline_background(
    coordinator: ServiceCoordinator,
    session_id: str,
    resume_path: Optional[str],
    career_data: Optional[Dict[str, Any]]
) -> None:
    """Execute pipeline in background task.
    
    Args:
        coordinator: Service coordinator
        session_id: Session identifier
        resume_path: Path to resume file (optional)
        career_data: Direct career data input (optional)
    """
    try:
        logger.info(f"Starting background pipeline execution for session {session_id}")
        
        await coordinator.execute_full_pipeline(
            session_id=session_id,
            resume_path=resume_path,
            career_data=career_data
        )
        
        logger.info(f"Background pipeline execution completed for session {session_id}")
        
    except ServiceCoordinationError as e:
        logger.error(f"Background pipeline execution failed for session {session_id}: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in background pipeline execution for session {session_id}: {str(e)}")


from datetime import datetime