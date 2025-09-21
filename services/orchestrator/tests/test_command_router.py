"""Test command routing system."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timezone

from src.core.command_router import CommandRouter
from src.core.session_manager import SessionManager
from src.models.commands import (
    CommandRequest,
    CommandResponse,
    CommandType,
    CommandStatus,
    CommandValidationError,
    CommandExecutionError
)
from src.models.session import SessionState, CurrentStep, SessionResponse


class TestCommandRouter:
    """Test CommandRouter class."""

    @pytest.fixture
    def command_router(self):
        """Create command router instance."""
        return CommandRouter()

    @pytest.fixture
    def mock_session_manager(self):
        """Mock session manager."""
        return AsyncMock(spec=SessionManager)

    @pytest.fixture
    def sample_session(self):
        """Sample session response."""
        from uuid import uuid4
        return SessionResponse(
            session_id=uuid4(),
            user_id="test-user",
            state=SessionState.INITIALIZED,
            current_step=CurrentStep.START,
            master_career_database={},
            command_history=[],
            metadata={},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc)
        )

    @pytest.mark.asyncio
    async def test_route_start_command(self, command_router, mock_session_manager):
        """Test routing /start command."""
        # Mock session creation
        from uuid import uuid4
        session_id = uuid4()
        mock_session_manager.create_session.return_value = AsyncMock(session_id=session_id)

        request = CommandRequest(
            command=CommandType.START,
            session_id="",
            parameters={"user_id": "test-user"}
        )

        response = await command_router.route_command(request, mock_session_manager)

        assert response.command == CommandType.START
        assert response.status == CommandStatus.COMPLETED
        assert str(session_id) in response.result["session_id"]
        assert CommandType.INGEST in response.next_actions

    @pytest.mark.asyncio
    async def test_route_status_command(self, command_router, mock_session_manager, sample_session):
        """Test routing /status command."""
        mock_session_manager.get_session.return_value = sample_session

        request = CommandRequest(
            command=CommandType.STATUS,
            session_id=str(sample_session.session_id),
            parameters={"include_history": True}
        )

        response = await command_router.route_command(request, mock_session_manager)

        assert response.command == CommandType.STATUS
        assert response.status == CommandStatus.COMPLETED
        assert "session_id" in response.result

    @pytest.mark.asyncio
    async def test_route_help_command(self, command_router, mock_session_manager, sample_session):
        """Test routing /help command."""
        # Mock the session manager to return a session with proper current_step
        mock_session_manager.get_session.return_value = sample_session

        request = CommandRequest(
            command=CommandType.HELP,
            session_id="help-session",
            parameters={}
        )

        response = await command_router.route_command(request, mock_session_manager)

        assert response.command == CommandType.HELP
        assert response.status == CommandStatus.COMPLETED
        assert "available_commands" in response.result
        assert "command_flow" in response.result

    @pytest.mark.asyncio
    async def test_validate_command_parameters(self, command_router, mock_session_manager):
        """Test command parameter validation."""
        # Valid parameters
        request = CommandRequest(
            command=CommandType.INGEST,
            session_id="test-session",
            parameters={"file_paths": ["test.pdf"]}
        )

        # Should not raise exception for valid parameters
        await command_router._validate_command_parameters(request)

        # Invalid parameters - no input provided
        invalid_request = CommandRequest(
            command=CommandType.INGEST,
            session_id="test-session",
            parameters={}
        )

        with pytest.raises(ValueError):
            await command_router._validate_command_parameters(invalid_request)

    @pytest.mark.asyncio
    async def test_session_validation_for_non_start_commands(self, command_router, mock_session_manager):
        """Test session validation for commands other than /start."""
        # Mock session not found
        mock_session_manager.get_session.return_value = None

        request = CommandRequest(
            command=CommandType.STATUS,
            session_id="non-existent-session",
            parameters={}
        )

        with pytest.raises(CommandValidationError) as exc_info:
            await command_router.route_command(request, mock_session_manager)

        assert "not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_command_state_validation(self, command_router, mock_session_manager, sample_session):
        """Test command state transition validation."""
        # Set session to INGEST step
        sample_session.current_step = CurrentStep.INGEST
        mock_session_manager.get_session.return_value = sample_session

        # Try to execute /analyze command (not allowed from INGEST step)
        request = CommandRequest(
            command=CommandType.ANALYZE,
            session_id=str(sample_session.session_id),
            parameters={}
        )

        with pytest.raises(CommandValidationError) as exc_info:
            await command_router.route_command(request, mock_session_manager)

        assert "not allowed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_add_to_history(self, command_router, mock_session_manager):
        """Test adding commands to session history."""
        request = CommandRequest(
            command=CommandType.STATUS,
            session_id="test-session",
            parameters={}
        )

        response = CommandResponse(
            command=CommandType.STATUS,
            session_id="test-session",
            status=CommandStatus.COMPLETED,
            result={},
            message="Test message",
            execution_time_ms=100.0
        )

        await command_router._add_to_history(request, response, mock_session_manager)

        # Verify add_command_to_history was called
        mock_session_manager.add_command_to_history.assert_called_once()
        call_args = mock_session_manager.add_command_to_history.call_args
        assert call_args[0][0] == "test-session"  # session_id
        history_entry = call_args[0][1]  # history entry
        assert history_entry["command"] == CommandType.STATUS.value
        assert history_entry["status"] == CommandStatus.COMPLETED.value

    @pytest.mark.asyncio
    async def test_unknown_command_handling(self, command_router, mock_session_manager):
        """Test handling of unknown commands."""
        # Create a command router and manually modify handlers to simulate unknown command
        with patch.object(command_router, '_handlers', {}):
            request = CommandRequest(
                command=CommandType.START,  # This will not be in the empty handlers dict
                session_id="test-session",
                parameters={}
            )

            with pytest.raises(CommandValidationError) as exc_info:
                await command_router.route_command(request, mock_session_manager)

            assert "Unknown command" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execution_time_tracking(self, command_router, mock_session_manager, sample_session):
        """Test that execution time is tracked."""
        # Mock the session manager to return a session with proper current_step
        mock_session_manager.get_session.return_value = sample_session

        request = CommandRequest(
            command=CommandType.HELP,
            session_id="test-session",
            parameters={}
        )

        response = await command_router.route_command(request, mock_session_manager)

        assert response.execution_time_ms is not None
        assert response.execution_time_ms >= 0

    @pytest.mark.asyncio
    async def test_error_handling_wraps_unexpected_errors(self, command_router, mock_session_manager, sample_session):
        """Test that unexpected errors are wrapped in CommandExecutionError."""
        # Mock the session manager to return a session with proper current_step
        mock_session_manager.get_session.return_value = sample_session

        # Mock a handler to raise an unexpected exception
        async def failing_handler(request, session_manager):
            raise ValueError("Unexpected error")

        with patch.object(command_router, '_handlers', {CommandType.HELP: failing_handler}):
            request = CommandRequest(
                command=CommandType.HELP,
                session_id="test-session",
                parameters={}
            )

            with pytest.raises(CommandExecutionError) as exc_info:
                await command_router.route_command(request, mock_session_manager)

            assert "Unexpected error" in str(exc_info.value)


class TestCommandValidation:
    """Test command validation logic."""

    def test_start_command_params(self):
        """Test StartCommandParams validation."""
        from src.models.commands import StartCommandParams

        # Valid parameters
        params = StartCommandParams(user_id="test-user", initial_data={"key": "value"})
        assert params.user_id == "test-user"
        assert params.initial_data == {"key": "value"}

        # Default values
        params = StartCommandParams()
        assert params.user_id is None
        assert params.initial_data == {}

    def test_ingest_command_params(self):
        """Test IngestCommandParams validation."""
        from src.models.commands import IngestCommandParams
        from pydantic import ValidationError

        # Valid with file paths
        params = IngestCommandParams(file_paths=["test.pdf"])
        assert params.file_paths == ["test.pdf"]

        # Valid with text content
        params = IngestCommandParams(text_content="Resume content")
        assert params.text_content == "Resume content"

        # Invalid - no input provided
        with pytest.raises(ValidationError):
            IngestCommandParams()

    def test_discover_command_params(self):
        """Test DiscoverCommandParams validation."""
        from src.models.commands import DiscoverCommandParams
        from pydantic import ValidationError

        # Valid parameters
        params = DiscoverCommandParams(
            focus_areas=["skills", "experience"],
            depth_level="deep",
            include_suggestions=False
        )
        assert params.focus_areas == ["skills", "experience"]
        assert params.depth_level == "deep"
        assert params.include_suggestions is False

        # Invalid depth level
        with pytest.raises(ValidationError):
            DiscoverCommandParams(depth_level="invalid")

    def test_build_command_params(self):
        """Test BuildCommandParams validation."""
        from src.models.commands import BuildCommandParams
        from pydantic import ValidationError

        # Valid document types
        params = BuildCommandParams(document_types=["resume", "cover_letter"])
        assert params.document_types == ["resume", "cover_letter"]

        # Invalid document type
        with pytest.raises(ValidationError):
            BuildCommandParams(document_types=["invalid_type"])
