"""Cross-service coordination and pipeline management."""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import uuid4

from ..models.session import SessionState, CurrentStep
from ..core.session_manager import SessionManager
from ..integrations.profile_ingestor import ProfileIngestorClient
from ..integrations.strategist import StrategistClient
from ..integrations.analyst import AnalystClient
from .schema_validator import SchemaValidator

logger = logging.getLogger(__name__)


class ServiceCoordinationError(Exception):
    """Exception raised during service coordination."""
    pass


class ServiceCoordinator:
    """Coordinates cross-service operations and pipeline execution."""
    
    def __init__(
        self,
        session_manager: SessionManager,
        profile_ingestor: ProfileIngestorClient,
        strategist: StrategistClient,
        analyst: AnalystClient
    ):
        """Initialize service coordinator.
        
        Args:
            session_manager: Session management service
            profile_ingestor: Profile ingestor client
            strategist: Strategist service client
            analyst: Analyst service client
        """
        self.session_manager = session_manager
        self.profile_ingestor = profile_ingestor
        self.strategist = strategist
        self.analyst = analyst
        self.schema_validator = SchemaValidator()
        
    async def execute_full_pipeline(
        self,
        session_id: str,
        resume_path: Optional[str] = None,
        career_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute the complete Profile Ingestor → Strategist → Analyst pipeline.
        
        Args:
            session_id: Session identifier
            resume_path: Path to resume file (optional)
            career_data: Direct career data input (optional)
            
        Returns:
            Complete pipeline results
            
        Raises:
            ServiceCoordinationError: If pipeline execution fails
        """
        logger.info(f"Starting full pipeline execution for session {session_id}")
        
        try:
            # Step 1: Profile Ingestion
            await self._update_session_state(session_id, SessionState.INGESTING, CurrentStep.INGEST)
            
            if resume_path:
                profile_data = await self._execute_profile_ingestion(session_id, resume_path)
            elif career_data:
                profile_data = career_data
            else:
                # Get existing data from session
                session = await self.session_manager.get_session(session_id)
                if not session or not session.master_career_database:
                    raise ServiceCoordinationError("No career data available for pipeline execution")
                profile_data = session.master_career_database
            
            # Step 2: Career Strategy Generation
            await self._update_session_state(session_id, SessionState.GENERATING, CurrentStep.DISCOVER)
            
            strategy_results = await self._execute_career_strategy(session_id, profile_data)
            
            # Step 3: Market Analysis
            await self._update_session_state(session_id, SessionState.ANALYZING, CurrentStep.ANALYZE)
            
            analysis_results = await self._execute_market_analysis(session_id, profile_data, strategy_results)
            
            # Step 4: Validate Complete Pipeline Data Flow
            logger.info(f"Validating complete pipeline data flow for session {session_id}")
            
            # Validate pipeline data consistency
            pipeline_valid, pipeline_errors = self.schema_validator.validate_pipeline_data_flow(
                profile_data, strategy_results, analysis_results
            )
            
            if not pipeline_valid:
                logger.error(f"Pipeline data flow validation failed for session {session_id}: {pipeline_errors}")
                await self._update_session_state(session_id, SessionState.ERROR, CurrentStep.REVIEW)
                raise ServiceCoordinationError(f"Pipeline data flow validation failed: {pipeline_errors}")
            
            logger.info(f"Pipeline data flow validation passed for session {session_id}")
            
            # Generate comprehensive schema compliance report
            schema_report = self.schema_validator.generate_schema_report(profile_data)
            
            # Step 5: Consolidate Results
            await self._update_session_state(session_id, SessionState.COMPLETED, CurrentStep.REVIEW)
            
            pipeline_results = {
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "profile_data": profile_data,
                "career_strategies": strategy_results,
                "market_analysis": analysis_results,
                "pipeline_status": "completed",
                "schema_validation": {
                    "is_valid": pipeline_valid,
                    "report": schema_report
                }
            }
            
            # Update session with final results
            await self._update_session_data(session_id, pipeline_results)
            
            logger.info(f"Pipeline execution completed successfully for session {session_id}")
            return pipeline_results
            
        except Exception as e:
            logger.error(f"Pipeline execution failed for session {session_id}: {str(e)}")
            await self._update_session_state(session_id, SessionState.ERROR, CurrentStep.REVIEW)
            raise ServiceCoordinationError(f"Pipeline execution failed: {str(e)}")
    
    async def _execute_profile_ingestion(
        self,
        session_id: str,
        resume_path: str
    ) -> Dict[str, Any]:
        """Execute profile ingestion step.
        
        Args:
            session_id: Session identifier
            resume_path: Path to resume file
            
        Returns:
            Profile data from ingestion
        """
        logger.info(f"Executing profile ingestion for session {session_id}")
        
        try:
            # Call Profile Ingestor service
            ingestion_result = await self.profile_ingestor.ingest_resume(
                resume_path=resume_path,
                session_id=session_id
            )
            
            if not ingestion_result.get("success"):
                raise ServiceCoordinationError(
                    f"Profile ingestion failed: {ingestion_result.get('error', 'Unknown error')}"
                )
            
            profile_data = ingestion_result.get("master_career_database", {})
            
            # Validate Master Career Database schema
            logger.info(f"Validating Master Career Database schema for session {session_id}")
            is_valid, errors, warnings = self.schema_validator.validate_master_career_database(
                profile_data, strict=False
            )
            
            if not is_valid:
                logger.warning(f"Schema validation failed for session {session_id}: {errors}")
                # Continue with warnings but log validation issues
                logger.warning(f"Schema warnings for session {session_id}: {warnings}")
            else:
                logger.info(f"Schema validation passed for session {session_id}")
            
            # Update session with profile data
            await self._update_session_data(session_id, {"master_career_database": profile_data})
            
            logger.info(f"Profile ingestion completed for session {session_id}")
            return profile_data
            
        except Exception as e:
            logger.error(f"Profile ingestion failed for session {session_id}: {str(e)}")
            raise ServiceCoordinationError(f"Profile ingestion failed: {str(e)}")
    
    async def _execute_career_strategy(
        self,
        session_id: str,
        profile_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute career strategy generation step.
        
        Args:
            session_id: Session identifier
            profile_data: Profile data from ingestion
            
        Returns:
            Career strategy results
        """
        logger.info(f"Executing career strategy generation for session {session_id}")
        
        try:
            # Call Strategist service
            strategy_result = await self.strategist.generate_career_paths(
                profile_data=profile_data,
                session_id=session_id
            )
            
            if not strategy_result.get("success"):
                raise ServiceCoordinationError(
                    f"Career strategy generation failed: {strategy_result.get('error', 'Unknown error')}"
                )
            
            strategy_data = strategy_result.get("career_paths", {})
            
            logger.info(f"Career strategy generation completed for session {session_id}")
            return strategy_data
            
        except Exception as e:
            logger.error(f"Career strategy generation failed for session {session_id}: {str(e)}")
            raise ServiceCoordinationError(f"Career strategy generation failed: {str(e)}")
    
    async def _execute_market_analysis(
        self,
        session_id: str,
        profile_data: Dict[str, Any],
        strategy_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute market analysis step.
        
        Args:
            session_id: Session identifier
            profile_data: Profile data from ingestion
            strategy_results: Results from career strategy generation
            
        Returns:
            Market analysis results
        """
        logger.info(f"Executing market analysis for session {session_id}")
        
        try:
            # Call Analyst service
            analysis_result = await self.analyst.analyze_market_position(
                profile_data=profile_data,
                career_paths=strategy_results,
                session_id=session_id
            )
            
            if not analysis_result.get("success"):
                raise ServiceCoordinationError(
                    f"Market analysis failed: {analysis_result.get('error', 'Unknown error')}"
                )
            
            analysis_data = analysis_result.get("analysis", {})
            
            logger.info(f"Market analysis completed for session {session_id}")
            return analysis_data
            
        except Exception as e:
            logger.error(f"Market analysis failed for session {session_id}: {str(e)}")
            raise ServiceCoordinationError(f"Market analysis failed: {str(e)}")
    
    async def _update_session_state(
        self,
        session_id: str,
        state: SessionState,
        step: CurrentStep
    ) -> None:
        """Update session state and step.
        
        Args:
            session_id: Session identifier
            state: New session state
            step: New current step
        """
        from ..models.session import SessionUpdate
        
        updates = SessionUpdate(
            state=state,
            current_step=step,
            metadata={
                "last_updated": datetime.utcnow().isoformat(),
                "updated_by": "service_coordinator"
            }
        )
        
        await self.session_manager.update_session(session_id, updates)
        logger.debug(f"Updated session {session_id} state to {state.value}, step to {step.value}")
    
    async def _update_session_data(
        self,
        session_id: str,
        data: Dict[str, Any]
    ) -> None:
        """Update session with additional data.
        
        Args:
            session_id: Session identifier
            data: Data to add to session
        """
        from ..models.session import SessionUpdate
        
        updates = SessionUpdate(
            metadata={
                "pipeline_data": data,
                "last_updated": datetime.utcnow().isoformat()
            }
        )
        
        await self.session_manager.update_session(session_id, updates)
        logger.debug(f"Updated session {session_id} with pipeline data")
    
    async def get_pipeline_status(self, session_id: str) -> Dict[str, Any]:
        """Get current pipeline execution status.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Pipeline status information
        """
        session = await self.session_manager.get_session(session_id)
        if not session:
            return {"error": "Session not found"}
        
        return {
            "session_id": session_id,
            "state": session.state,
            "current_step": session.current_step,
            "progress": self._calculate_progress(session.current_step),
            "last_updated": session.updated_at.isoformat() if session.updated_at else None
        }
    
    def _calculate_progress(self, current_step: CurrentStep) -> float:
        """Calculate pipeline progress percentage.
        
        Args:
            current_step: Current pipeline step
            
        Returns:
            Progress percentage (0.0 to 1.0)
        """
        step_progress = {
            CurrentStep.START: 0.0,
            CurrentStep.INGEST: 0.25,
            CurrentStep.DISCOVER: 0.5,
            CurrentStep.ANALYZE: 0.75,
            CurrentStep.BUILD: 0.9,
            CurrentStep.REVIEW: 1.0
        }
        
        return step_progress.get(current_step, 0.0)
    
    async def health_check_all_services(self) -> Dict[str, Any]:
        """Perform health check on all coordinated services.
        
        Returns:
            Health status of all services
        """
        logger.info("Performing health check on all services")
        
        health_results = {}
        
        # Check Profile Ingestor
        try:
            profile_health = await self.profile_ingestor.health_check()
            health_results["profile_ingestor"] = {
                "status": "healthy" if profile_health.get("status") == "healthy" else "unhealthy",
                "details": profile_health
            }
        except Exception as e:
            health_results["profile_ingestor"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # Check Strategist
        try:
            strategist_health = await self.strategist.health_check()
            health_results["strategist"] = {
                "status": "healthy" if strategist_health.get("status") == "healthy" else "unhealthy",
                "details": strategist_health
            }
        except Exception as e:
            health_results["strategist"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # Check Analyst
        try:
            analyst_health = await self.analyst.health_check()
            health_results["analyst"] = {
                "status": "healthy" if analyst_health.get("status") == "healthy" else "unhealthy",
                "details": analyst_health
            }
        except Exception as e:
            health_results["analyst"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        overall_status = "healthy" if all(
            service["status"] == "healthy" 
            for service in health_results.values()
        ) else "degraded"
        
        return {
            "overall_status": overall_status,
            "services": health_results,
            "timestamp": datetime.utcnow().isoformat()
        }