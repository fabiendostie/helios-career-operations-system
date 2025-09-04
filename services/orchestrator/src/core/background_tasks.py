"""Background tasks for session management."""

import asyncio
from datetime import datetime, timezone
from typing import Dict, Any

from ..core.database import db_manager, SessionRepository
from ..core.session_manager import SessionManager
from ..models.session import SessionState
from ..utils.logging_config import get_logger
from .config import settings


logger = get_logger("background_tasks")


class BackgroundTaskManager:
    """Manages background tasks for session maintenance."""
    
    def __init__(self):
        """Initialize background task manager."""
        self._tasks: Dict[str, asyncio.Task] = {}
        self._running = False
    
    async def start(self):
        """Start all background tasks."""
        if self._running:
            logger.warning("Background tasks already running")
            return
        
        self._running = True
        logger.info("Starting background tasks")
        
        # Start session cleanup task
        self._tasks["session_cleanup"] = asyncio.create_task(
            self._session_cleanup_loop()
        )
        
        # Start session recovery task
        self._tasks["session_recovery"] = asyncio.create_task(
            self._session_recovery_loop()
        )
        
        logger.info("Background tasks started")
    
    async def stop(self):
        """Stop all background tasks."""
        if not self._running:
            return
        
        self._running = False
        logger.info("Stopping background tasks")
        
        # Cancel all tasks
        for name, task in self._tasks.items():
            if not task.done():
                logger.debug(f"Cancelling task: {name}")
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        self._tasks.clear()
        logger.info("Background tasks stopped")
    
    async def _session_cleanup_loop(self):
        """Periodically clean up expired sessions."""
        cleanup_interval = settings.session_cleanup_interval_minutes * 60  # Convert to seconds
        
        while self._running:
            try:
                logger.debug("Running session cleanup")
                
                # Get database session and manager
                async for db_session in db_manager.get_session():
                    repository = SessionRepository(db_session)
                    manager = SessionManager(repository)
                    
                    # Clean up expired sessions
                    cleaned_count = await manager.cleanup_expired_sessions()
                    
                    if cleaned_count > 0:
                        logger.info(f"Cleaned up {cleaned_count} expired sessions")
                    
                    break  # Exit the async generator loop
                
            except Exception as e:
                logger.error(f"Error during session cleanup: {str(e)}")
            
            # Wait for next cleanup cycle
            try:
                await asyncio.sleep(cleanup_interval)
            except asyncio.CancelledError:
                break
    
    async def _session_recovery_loop(self):
        """Periodically recover interrupted sessions."""
        recovery_interval = settings.session_cleanup_interval_minutes * 60 * 2  # Run less frequently
        
        while self._running:
            try:
                logger.debug("Running session recovery")
                
                # Get database session and manager
                async for db_session in db_manager.get_session():
                    repository = SessionRepository(db_session)
                    manager = SessionManager(repository)
                    
                    # Find sessions that might need recovery
                    await self._recover_interrupted_sessions(manager)
                    
                    break  # Exit the async generator loop
                
            except Exception as e:
                logger.error(f"Error during session recovery: {str(e)}")
            
            # Wait for next recovery cycle
            try:
                await asyncio.sleep(recovery_interval)
            except asyncio.CancelledError:
                break
    
    async def _recover_interrupted_sessions(self, manager: SessionManager):
        """Recover sessions that were interrupted during processing.
        
        Args:
            manager: Session manager instance
        """
        # Find sessions in processing states that haven't been updated recently
        processing_states = [
            SessionState.INGESTING,
            SessionState.ANALYZING, 
            SessionState.GENERATING
        ]
        
        recovery_count = 0
        
        for state in processing_states:
            sessions = await manager.list_sessions(state=state, limit=100)
            
            for session in sessions:
                # Check if session has been inactive for too long
                time_since_update = datetime.now(timezone.utc) - session.updated_at
                inactive_minutes = time_since_update.total_seconds() / 60
                
                # If inactive for more than 30 minutes, consider it interrupted
                if inactive_minutes > 30:
                    logger.info(f"Recovering interrupted session {session.session_id} from state {state}")
                    
                    # Transition back to initialized state for manual recovery
                    await manager.transition_state(
                        str(session.session_id),
                        SessionState.ERROR,  # Mark as error for investigation
                        None
                    )
                    
                    # Add recovery note to command history
                    recovery_command = {
                        "command": "/recover",
                        "reason": f"Session recovered from interrupted {state} state",
                        "original_state": state.value,
                        "recovery_timestamp": datetime.now(timezone.utc).isoformat()
                    }
                    
                    await manager.add_command_to_history(
                        str(session.session_id),
                        recovery_command
                    )
                    
                    recovery_count += 1
        
        if recovery_count > 0:
            logger.info(f"Recovered {recovery_count} interrupted sessions")
    
    def is_running(self) -> bool:
        """Check if background tasks are running."""
        return self._running
    
    def get_task_status(self) -> Dict[str, str]:
        """Get status of all background tasks."""
        status = {}
        for name, task in self._tasks.items():
            if task.done():
                if task.exception():
                    status[name] = f"failed: {task.exception()}"
                else:
                    status[name] = "completed"
            elif task.cancelled():
                status[name] = "cancelled"
            else:
                status[name] = "running"
        
        return status


# Global background task manager
background_tasks = BackgroundTaskManager()