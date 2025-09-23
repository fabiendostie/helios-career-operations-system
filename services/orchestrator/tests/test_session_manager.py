"""Test session management system."""

import pytest
from unittest.mock import AsyncMock, Mock
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from src.core.session_manager import SessionManager
from src.core.database import SessionRepository
from src.models.session import (
    Session,
    SessionCreate,
    SessionUpdate,
    SessionResponse,
    SessionSummary,
    SessionState,
    CurrentStep
)


class TestSessionManager:
    """Test SessionManager class."""

    @pytest.fixture
    def mock_repository(self):
        """Mock session repository."""
        return AsyncMock(spec=SessionRepository)

    @pytest.fixture
    def session_manager(self, mock_repository):
        """Create session manager with mock repository."""
        return SessionManager(mock_repository)

    @pytest.fixture
    def sample_db_session(self):
        """Sample database session."""
        session_id = str(uuid4())
        now = datetime.now(timezone.utc)

        session = Mock(spec=Session)
        session.session_id = session_id
        session.user_id = "test-user"
        session.state = SessionState.INITIALIZED
        session.current_step = CurrentStep.START
        session.master_career_database = "{}"
        session.command_history = "[]"
        session.session_metadata = "{}"
        session.created_at = now
        session.updated_at = now
        session.expires_at = now + timedelta(hours=1)

        return session

    @pytest.mark.asyncio
    async def test_create_session(self, session_manager, mock_repository, sample_db_session):
        """Test creating a new session."""
        mock_repository.create_session.return_value = sample_db_session

        session_data = SessionCreate(
            user_id="test-user",
            master_career_database={"key": "value"}
        )

        result = await session_manager.create_session(session_data)

        assert isinstance(result, SessionResponse)
        assert result.user_id == "test-user"
        assert result.state == SessionState.INITIALIZED
        mock_repository.create_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_session(self, session_manager, mock_repository, sample_db_session):
        """Test getting a session by ID."""
        mock_repository.get_session.return_value = sample_db_session

        result = await session_manager.get_session(str(sample_db_session.session_id))

        assert isinstance(result, SessionResponse)
        assert str(result.session_id) == sample_db_session.session_id
        mock_repository.get_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_nonexistent_session(self, session_manager, mock_repository):
        """Test getting a session that doesn't exist."""
        mock_repository.get_session.return_value = None

        result = await session_manager.get_session("nonexistent-id")

        assert result is None
        mock_repository.get_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_session(self, session_manager, mock_repository, sample_db_session):
        """Test updating a session."""
        mock_repository.update_session.return_value = sample_db_session

        updates = SessionUpdate(
            state=SessionState.INGESTING,
            current_step=CurrentStep.INGEST
        )

        result = await session_manager.update_session(
            str(sample_db_session.session_id),
            updates
        )

        assert isinstance(result, SessionResponse)
        mock_repository.update_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_session(self, session_manager, mock_repository):
        """Test deleting a session."""
        mock_repository.delete_session.return_value = True

        result = await session_manager.delete_session("test-session-id")

        assert result is True
        mock_repository.delete_session.assert_called_once_with("test-session-id")

    @pytest.mark.asyncio
    async def test_list_sessions(self, session_manager, mock_repository, sample_db_session):
        """Test listing sessions."""
        mock_repository.list_sessions.return_value = [sample_db_session]

        result = await session_manager.list_sessions(
            user_id="test-user",
            state=SessionState.INITIALIZED,
            limit=10
        )

        assert len(result) == 1
        assert isinstance(result[0], SessionSummary)
        assert str(result[0].session_id) == sample_db_session.session_id

        mock_repository.list_sessions.assert_called_once_with(
            user_id="test-user",
            state=SessionState.INITIALIZED,
            limit=10,
            offset=0
        )

    @pytest.mark.asyncio
    async def test_add_command_to_history(self, session_manager, mock_repository, sample_db_session):
        """Test adding command to session history."""
        # Mock the session manager's own methods
        session_manager.get_session = AsyncMock(return_value=SessionResponse(
            session_id=uuid4(),
            user_id="test-user",
            state=SessionState.INITIALIZED,
            current_step=CurrentStep.START,
            master_career_database={},
            command_history=[],
            metadata={},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        ))
        session_manager.update_session = AsyncMock(return_value=Mock())

        command = {"command": "/status", "params": {}}

        result = await session_manager.add_command_to_history("test-session", command)

        session_manager.get_session.assert_called_once()
        session_manager.update_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_career_database(self, session_manager, mock_repository):
        """Test updating master career database."""
        session_manager.update_session = AsyncMock(return_value=Mock())

        career_data = {"skills": ["Python", "FastAPI"]}

        await session_manager.update_career_database("test-session", career_data)

        session_manager.update_session.assert_called_once()
        call_args = session_manager.update_session.call_args
        assert call_args[0][0] == "test-session"
        updates = call_args[0][1]
        assert updates.master_career_database == career_data

    @pytest.mark.asyncio
    async def test_transition_state(self, session_manager, mock_repository):
        """Test transitioning session state."""
        session_manager.update_session = AsyncMock(return_value=Mock())

        await session_manager.transition_state(
            "test-session",
            SessionState.ANALYZING,
            CurrentStep.ANALYZE
        )

        session_manager.update_session.assert_called_once()
        call_args = session_manager.update_session.call_args
        updates = call_args[0][1]
        assert updates.state == SessionState.ANALYZING
        assert updates.current_step == CurrentStep.ANALYZE

    @pytest.mark.asyncio
    async def test_extend_session(self, session_manager, mock_repository, sample_db_session):
        """Test extending session expiration."""
        mock_repository.extend_session.return_value = sample_db_session

        result = await session_manager.extend_session("test-session", 60)

        assert isinstance(result, SessionResponse)
        mock_repository.extend_session.assert_called_once_with("test-session", 60)

    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions(self, session_manager, mock_repository):
        """Test cleaning up expired sessions."""
        mock_repository.cleanup_expired_sessions.return_value = 5

        result = await session_manager.cleanup_expired_sessions()

        assert result == 5
        mock_repository.cleanup_expired_sessions.assert_called_once()

    @pytest.mark.asyncio
    async def test_db_session_to_response_conversion(self, session_manager, sample_db_session):
        """Test converting database session to response model."""
        # Set up JSON fields with valid data
        sample_db_session.master_career_database = '{"skills": ["Python"]}'
        sample_db_session.command_history = '[{"command": "/start"}]'
        sample_db_session.session_metadata = '{"created_by": "test"}'

        result = await session_manager._db_session_to_response(sample_db_session)

        assert isinstance(result, SessionResponse)
        assert result.master_career_database == {"skills": ["Python"]}
        assert result.command_history == [{"command": "/start"}]
        assert result.metadata == {"created_by": "test"}

    @pytest.mark.asyncio
    async def test_db_session_to_summary_conversion(self, session_manager, sample_db_session):
        """Test converting database session to summary model."""
        result = await session_manager._db_session_to_summary(sample_db_session)

        assert isinstance(result, SessionSummary)
        assert str(result.session_id) == sample_db_session.session_id
        assert result.user_id == sample_db_session.user_id
        assert result.state == sample_db_session.state
        assert result.current_step == sample_db_session.current_step


class TestSessionModels:
    """Test session data models."""

    def test_session_create_model(self):
        """Test SessionCreate model."""
        data = SessionCreate(
            user_id="test-user",
            master_career_database={"key": "value"}
        )

        assert data.user_id == "test-user"
        assert data.state == SessionState.INITIALIZED
        assert data.current_step == CurrentStep.START
        assert data.master_career_database == {"key": "value"}

    def test_session_update_model(self):
        """Test SessionUpdate model."""
        updates = SessionUpdate(
            state=SessionState.ANALYZING,
            current_step=CurrentStep.ANALYZE
        )

        # Test that only set fields are included
        update_dict = updates.model_dump(exclude_unset=True, exclude_none=True)
        assert "state" in update_dict
        assert "current_step" in update_dict
        assert "user_id" not in update_dict  # Not set

    def test_session_response_model(self):
        """Test SessionResponse model."""
        session_id = uuid4()
        now = datetime.now(timezone.utc)

        response = SessionResponse(
            session_id=session_id,
            user_id="test-user",
            state=SessionState.INITIALIZED,
            current_step=CurrentStep.START,
            master_career_database={},
            command_history=[],
            metadata={},
            created_at=now,
            updated_at=now,
            expires_at=now + timedelta(hours=1)
        )

        assert response.session_id == session_id
        assert response.user_id == "test-user"
        assert isinstance(response.created_at, datetime)

    def test_session_summary_model(self):
        """Test SessionSummary model."""
        session_id = uuid4()
        now = datetime.now(timezone.utc)

        summary = SessionSummary(
            session_id=session_id,
            user_id="test-user",
            state=SessionState.INITIALIZED,
            current_step=CurrentStep.START,
            created_at=now,
            updated_at=now,
            expires_at=now + timedelta(hours=1)
        )

        assert summary.session_id == session_id
        assert summary.user_id == "test-user"
        # Summary should not have master_career_database or other detailed fields
