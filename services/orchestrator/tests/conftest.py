"""Pytest configuration and shared fixtures."""

import pytest
from unittest.mock import AsyncMock, Mock

# Try to import FastAPI dependencies, skip if not available (during initial setup)
try:
    from fastapi.testclient import TestClient
    from src.main import create_app
    from src.core.config import settings
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    TestClient = None


@pytest.fixture
def app():
    """Create FastAPI application for testing."""
    if not FASTAPI_AVAILABLE:
        pytest.skip("FastAPI not available")
    return create_app()


@pytest.fixture  
def client(app):
    """Create test client."""
    if not FASTAPI_AVAILABLE:
        pytest.skip("FastAPI not available")
    return TestClient(app)


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    test_settings = Mock()
    test_settings.app_name = "Test HELIOS Orchestrator"
    test_settings.app_version = "0.0.1-test"
    test_settings.debug = True
    test_settings.database_url = "sqlite+aiosqlite:///:memory:"
    test_settings.session_timeout_minutes = 30
    test_settings.cors_origins = ["http://testserver"]
    test_settings.profile_ingestor_url = "http://localhost:8001"
    test_settings.http_timeout_seconds = 10
    return test_settings


@pytest.fixture
def mock_database():
    """Mock database session for testing.""" 
    mock_session = AsyncMock()
    return mock_session


@pytest.fixture
def sample_session_data():
    """Sample session data for testing."""
    return {
        "session_id": "test-session-123",
        "user_id": "test-user-456",
        "state": "initialized",
        "master_career_database": {},
        "command_history": [],
        "current_step": "start",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "expires_at": "2024-01-01T01:00:00Z"
    }


@pytest.fixture
def sample_command():
    """Sample command for testing."""
    return {
        "command": "/start",
        "session_id": "test-session-123", 
        "parameters": {},
        "timestamp": "2024-01-01T00:00:00Z"
    }