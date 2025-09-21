"""Command routing and execution system."""

import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Callable, Awaitable

from ..models.commands import (
    CommandType,
    CommandStatus,
    CommandRequest,
    CommandResponse,
    CommandParameters,
    StartCommandParams,
    IngestCommandParams,
    DiscoverCommandParams,
    AnalyzeCommandParams,
    BuildCommandParams,
    StatusCommandParams,
    CommandValidationError,
    CommandExecutionError
)
from ..models.session import SessionState, CurrentStep
from ..core.session_manager import SessionManager
from ..utils.logging_config import get_logger


logger = get_logger("command_router")

# Type alias for command handlers
CommandHandler = Callable[[CommandRequest, SessionManager], Awaitable[CommandResponse]]


class CommandRouter:
    """Routes and executes commands with proper validation and error handling."""

    def __init__(self):
        """Initialize command router with handlers."""
        self._handlers: Dict[CommandType, CommandHandler] = {
            CommandType.START: self._handle_start,
            CommandType.INGEST: self._handle_ingest,
            CommandType.DISCOVER: self._handle_discover,
            CommandType.ANALYZE: self._handle_analyze,
            CommandType.BUILD: self._handle_build,
            CommandType.STATUS: self._handle_status,
            CommandType.HELP: self._handle_help,
        }

        # Define valid command transitions based on current session state/step
        self._valid_transitions: Dict[CurrentStep, List[CommandType]] = {
            CurrentStep.START: [CommandType.START, CommandType.STATUS, CommandType.HELP],
            CurrentStep.INGEST: [CommandType.INGEST, CommandType.STATUS, CommandType.HELP],
            CurrentStep.DISCOVER: [CommandType.DISCOVER, CommandType.STATUS, CommandType.HELP],
            CurrentStep.ANALYZE: [CommandType.ANALYZE, CommandType.STATUS, CommandType.HELP],
            CurrentStep.BUILD: [CommandType.BUILD, CommandType.STATUS, CommandType.HELP],
            CurrentStep.REVIEW: [CommandType.STATUS, CommandType.BUILD, CommandType.HELP],
        }

    async def route_command(
        self,
        request: CommandRequest,
        session_manager: SessionManager
    ) -> CommandResponse:
        """Route and execute a command request.

        Args:
            request: Command request to execute
            session_manager: Session manager instance

        Returns:
            Command response

        Raises:
            CommandValidationError: If command validation fails
            CommandExecutionError: If command execution fails
        """
        start_time = time.time()

        try:
            logger.info(f"Routing command {request.command} for session {request.session_id}")

            # Validate command request
            await self._validate_command(request, session_manager)

            # Get command handler
            handler = self._handlers.get(request.command)
            if not handler:
                raise CommandValidationError(
                    f"Unknown command: {request.command}",
                    command=request.command
                )

            # Execute command
            response = await handler(request, session_manager)

            # Calculate execution time
            execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            response.execution_time_ms = execution_time

            # Add command to session history if session exists
            if request.session_id:
                await self._add_to_history(request, response, session_manager)

            logger.info(f"Command {request.command} completed in {execution_time:.2f}ms")
            return response

        except (CommandValidationError, CommandExecutionError) as e:
            # Re-raise known command errors
            logger.error(f"Command {request.command} failed: {str(e)}")
            raise
        except Exception as e:
            # Wrap unexpected errors
            logger.error(f"Unexpected error executing command {request.command}: {str(e)}")
            raise CommandExecutionError(
                f"Unexpected error: {str(e)}",
                command=request.command,
                details={"original_error": str(e)}
            )

    async def _validate_command(
        self,
        request: CommandRequest,
        session_manager: SessionManager
    ) -> None:
        """Validate command request.

        Args:
            request: Command request to validate
            session_manager: Session manager instance

        Raises:
            CommandValidationError: If validation fails
        """
        # Validate command parameters based on command type
        try:
            await self._validate_command_parameters(request)
        except Exception as e:
            raise CommandValidationError(
                f"Invalid parameters for {request.command}: {str(e)}",
                command=request.command,
                details={"parameters": request.parameters}
            )

        # For non-/start commands, validate session exists
        if request.command != CommandType.START:
            session = await session_manager.get_session(request.session_id)
            if not session:
                raise CommandValidationError(
                    f"Session {request.session_id} not found",
                    command=request.command,
                    details={"session_id": request.session_id}
                )

            # Validate command is allowed for current session step
            valid_commands = self._valid_transitions.get(session.current_step, [])
            if request.command not in valid_commands:
                raise CommandValidationError(
                    f"Command {request.command} not allowed in step {session.current_step}",
                    command=request.command,
                    details={
                        "current_step": session.current_step,
                        "allowed_commands": [cmd.value for cmd in valid_commands]
                    }
                )

    async def _validate_command_parameters(self, request: CommandRequest) -> None:
        """Validate command-specific parameters.

        Args:
            request: Command request to validate

        Raises:
            ValueError: If parameters are invalid
        """
        # Map command types to their parameter models
        param_models = {
            CommandType.START: StartCommandParams,
            CommandType.INGEST: IngestCommandParams,
            CommandType.DISCOVER: DiscoverCommandParams,
            CommandType.ANALYZE: AnalyzeCommandParams,
            CommandType.BUILD: BuildCommandParams,
            CommandType.STATUS: StatusCommandParams,
        }

        # Validate parameters if model exists
        model_class = param_models.get(request.command)
        if model_class:
            # This will raise ValidationError if parameters are invalid
            model_class(**request.parameters)

    async def _add_to_history(
        self,
        request: CommandRequest,
        response: CommandResponse,
        session_manager: SessionManager
    ) -> None:
        """Add command execution to session history.

        Args:
            request: Original command request
            response: Command response
            session_manager: Session manager instance
        """
        try:
            history_entry = {
                "command": request.command.value,
                "parameters": request.parameters,
                "status": response.status.value,
                "result": response.result,
                "message": response.message,
                "timestamp": response.timestamp.isoformat(),
                "execution_time_ms": response.execution_time_ms,
            }

            await session_manager.add_command_to_history(request.session_id, history_entry)
        except Exception as e:
            # Log error but don't fail the command
            logger.error(f"Failed to add command to history: {str(e)}")

    # Command handlers
    async def _handle_start(
        self,
        request: CommandRequest,
        session_manager: SessionManager
    ) -> CommandResponse:
        """Handle /start command - initialize new session."""
        try:
            params = StartCommandParams(**request.parameters)

            # Create new session
            from ..models.session import SessionCreate
            session_data = SessionCreate(
                user_id=params.user_id,
                master_career_database=params.initial_data
            )

            session = await session_manager.create_session(session_data)

            return CommandResponse(
                command=request.command,
                session_id=str(session.session_id),
                status=CommandStatus.COMPLETED,
                result={"session_id": str(session.session_id)},
                message="New session started successfully",
                next_actions=[CommandType.INGEST, CommandType.STATUS]
            )

        except Exception as e:
            raise CommandExecutionError(
                f"Failed to start session: {str(e)}",
                command=request.command,
                details={"error": str(e)}
            )

    async def _handle_ingest(
        self,
        request: CommandRequest,
        session_manager: SessionManager
    ) -> CommandResponse:
        """Handle /ingest command - integrate with Profile Ingestor service."""
        params = IngestCommandParams(**request.parameters)

        try:
            # Transition session to ingesting state
            await session_manager.transition_state(
                request.session_id,
                SessionState.INGESTING,
                CurrentStep.INGEST
            )

            # Import here to avoid circular imports
            from ..integrations.profile_ingestor import get_profile_ingestor_client

            # Get Profile Ingestor client
            client = await get_profile_ingestor_client()

            # Determine ingestion type and start processing
            if params.text_content:
                # Process text content
                logger.info(f"Starting text ingestion for session {request.session_id}")
                response = await client.ingest_text(
                    session_id=request.session_id,
                    text_content=params.text_content,
                    processing_options={
                        "format_hint": params.format_hint
                    }
                )
            elif params.file_paths:
                # Process files
                logger.info(f"Starting file ingestion for session {request.session_id}")
                response = await client.ingest_files(
                    session_id=request.session_id,
                    file_paths=params.file_paths,
                    processing_options={
                        "format_hint": params.format_hint
                    }
                )
            else:
                # This should not happen due to parameter validation, but handle it
                raise CommandExecutionError(
                    "No input provided for ingestion",
                    command=request.command,
                    details={"parameters": request.parameters}
                )

            # Update session with extracted data
            if response.success:
                await session_manager.update_career_database(
                    request.session_id,
                    response.master_career_database
                )

                # Transition to completed state
                await session_manager.transition_state(
                    request.session_id,
                    SessionState.COMPLETED,
                    CurrentStep.DISCOVER
                )

                return CommandResponse(
                    command=request.command,
                    session_id=request.session_id,
                    status=CommandStatus.COMPLETED,
                    result={
                        "master_career_database": response.master_career_database,
                        "processing_summary": response.processing_summary,
                        "warnings": response.warnings
                    },
                    message="Ingestion completed successfully",
                    next_actions=[CommandType.DISCOVER, CommandType.STATUS]
                )
            else:
                # Ingestion failed
                await session_manager.transition_state(
                    request.session_id,
                    SessionState.ERROR,
                    CurrentStep.INGEST
                )

                return CommandResponse(
                    command=request.command,
                    session_id=request.session_id,
                    status=CommandStatus.FAILED,
                    result={
                        "errors": response.errors,
                        "warnings": response.warnings,
                        "processing_summary": response.processing_summary
                    },
                    message="Ingestion failed - see errors for details",
                    next_actions=[CommandType.STATUS]
                )

        except Exception as e:
            # Handle any unexpected errors
            logger.error(f"Ingestion failed for session {request.session_id}: {str(e)}")

            # Transition to error state
            await session_manager.transition_state(
                request.session_id,
                SessionState.ERROR,
                CurrentStep.INGEST
            )

            raise CommandExecutionError(
                f"Ingestion failed: {str(e)}",
                command=request.command,
                details={"error": str(e), "session_id": request.session_id}
            )

    async def _handle_discover(
        self,
        request: CommandRequest,
        session_manager: SessionManager
    ) -> CommandResponse:
        """Handle /discover command - career discovery analysis."""
        params = DiscoverCommandParams(**request.parameters)

        await session_manager.transition_state(
            request.session_id,
            SessionState.ANALYZING,
            CurrentStep.DISCOVER
        )

        # TODO: Implement discovery logic
        return CommandResponse(
            command=request.command,
            session_id=request.session_id,
            status=CommandStatus.PROCESSING,
            result={"message": "Discovery analysis will be implemented in later tasks"},
            message="Career discovery analysis started",
            next_actions=[CommandType.ANALYZE, CommandType.STATUS]
        )

    async def _handle_analyze(
        self,
        request: CommandRequest,
        session_manager: SessionManager
    ) -> CommandResponse:
        """Handle /analyze command - career analysis."""
        params = AnalyzeCommandParams(**request.parameters)

        await session_manager.transition_state(
            request.session_id,
            SessionState.ANALYZING,
            CurrentStep.ANALYZE
        )

        # TODO: Implement analysis logic
        return CommandResponse(
            command=request.command,
            session_id=request.session_id,
            status=CommandStatus.PROCESSING,
            result={"message": "Analysis will be implemented in later tasks"},
            message="Career analysis started",
            next_actions=[CommandType.BUILD, CommandType.STATUS]
        )

    async def _handle_build(
        self,
        request: CommandRequest,
        session_manager: SessionManager
    ) -> CommandResponse:
        """Handle /build command - document building."""
        params = BuildCommandParams(**request.parameters)

        await session_manager.transition_state(
            request.session_id,
            SessionState.GENERATING,
            CurrentStep.BUILD
        )

        # TODO: Implement document building logic
        return CommandResponse(
            command=request.command,
            session_id=request.session_id,
            status=CommandStatus.PROCESSING,
            result={"message": "Document building will be implemented in later tasks"},
            message="Document building started",
            next_actions=[CommandType.STATUS]
        )

    async def _handle_status(
        self,
        request: CommandRequest,
        session_manager: SessionManager
    ) -> CommandResponse:
        """Handle /status command - get session status."""
        params = StatusCommandParams(**request.parameters)

        # Get current session
        session = await session_manager.get_session(request.session_id)
        if not session:
            raise CommandExecutionError(
                f"Session {request.session_id} not found",
                command=request.command
            )

        result = {
            "session_id": str(session.session_id),
            "state": session.state.value,
            "current_step": session.current_step.value,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "expires_at": session.expires_at.isoformat(),
        }

        if params.include_history:
            result["command_history"] = session.command_history

        if params.include_details:
            result["master_career_database"] = session.master_career_database
            result["metadata"] = session.session_metadata

        # Determine next actions based on current step
        next_actions = self._valid_transitions.get(session.current_step, [])

        return CommandResponse(
            command=request.command,
            session_id=request.session_id,
            status=CommandStatus.COMPLETED,
            result=result,
            message=f"Session {session.session_id} is in {session.state.value} state",
            next_actions=next_actions
        )

    async def _handle_help(
        self,
        request: CommandRequest,
        session_manager: SessionManager
    ) -> CommandResponse:
        """Handle /help command - provide command help."""
        help_info = {
            "available_commands": {
                "/start": "Initialize a new session",
                "/ingest": "Process resume/profile documents",
                "/discover": "Analyze career profile and opportunities",
                "/analyze": "Perform detailed career analysis",
                "/build": "Generate career documents",
                "/status": "Get current session status",
                "/help": "Show this help information"
            },
            "command_flow": [
                "1. /start - Begin new session",
                "2. /ingest - Add your documents/profile",
                "3. /discover - Explore career opportunities",
                "4. /analyze - Get detailed analysis",
                "5. /build - Generate optimized documents"
            ]
        }

        return CommandResponse(
            command=request.command,
            session_id=request.session_id,
            status=CommandStatus.COMPLETED,
            result=help_info,
            message="HELIOS Orchestrator command help",
            next_actions=list(CommandType)
        )
