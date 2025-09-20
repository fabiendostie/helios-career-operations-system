"""Pytest configuration and shared fixtures for Strategist service tests."""

from unittest.mock import AsyncMock, Mock, patch

import aiohttp
import pytest


@pytest.fixture
def async_context_manager_mock():
    """Create properly configured async context manager mock for aiohttp responses."""

    def _create_mock(status=200, json_data=None, text_data="OK"):
        mock_response = AsyncMock()
        mock_response.status = status
        if json_data:
            mock_response.json = AsyncMock(return_value=json_data)
        mock_response.text = AsyncMock(return_value=text_data)

        # Create a mock that properly handles async context manager protocol
        context_manager = AsyncMock()
        context_manager.__aenter__.return_value = mock_response
        context_manager.__aexit__.return_value = None

        return context_manager

    return _create_mock


@pytest.fixture
def mock_orchestrator_session(async_context_manager_mock):
    """Create mock aiohttp ClientSession for orchestrator tests."""
    session = AsyncMock(spec=aiohttp.ClientSession)

    # Configure default responses
    session.post.return_value = async_context_manager_mock(
        status=200, json_data={"status": "success"}
    )
    session.get.return_value = async_context_manager_mock(
        status=200, json_data={"data": "test"}
    )
    session.put.return_value = async_context_manager_mock(
        status=200, json_data={"status": "updated"}
    )

    return session


@pytest.fixture
def mock_sentence_transformer():
    """Mock sentence transformer to avoid model loading in tests."""
    with patch("sentence_transformers.SentenceTransformer") as mock:
        transformer = Mock()
        transformer.encode.return_value = [[0.1, 0.2, 0.3] * 128]  # 384-dim vector
        mock.return_value = transformer
        yield transformer


@pytest.fixture
def mock_career_generator():
    """Mock CareerGenerator to avoid initialization issues."""
    with patch("src.core.career_generator.CareerGenerator") as mock:
        generator = AsyncMock()
        generator.initialize.return_value = None
        generator.is_initialized = True
        mock.return_value = generator
        yield generator


@pytest.fixture
def mock_role_taxonomy():
    """Mock RoleTaxonomyManager to avoid vector generation issues."""
    with patch("src.core.role_taxonomy_manager.RoleTaxonomyManager") as mock:
        manager = Mock()
        manager.generate_role_vectors.return_value = {
            "test_001": [0.1] * 384,
            "test_002": [0.2] * 384,
            "test_003": [0.3] * 384,
        }
        mock.return_value = manager
        yield manager


# Auto-apply common mocks for problematic imports
@pytest.fixture(autouse=True)
def mock_slow_imports():
    """Automatically mock slow/problematic imports for all tests."""
    with patch("src.integrations.orchestrator.aiohttp.ClientSession") as mock_session:
        # Configure the session mock to return proper async context managers
        session_instance = AsyncMock()

        # Make all HTTP methods return async context managers
        for method in ["get", "post", "put", "delete"]:
            method_mock = AsyncMock()
            response_mock = AsyncMock()
            response_mock.status = 200
            response_mock.json = AsyncMock(return_value={"status": "success"})
            response_mock.text = AsyncMock(return_value="OK")

            method_mock.__aenter__.return_value = response_mock
            method_mock.__aexit__.return_value = None
            setattr(session_instance, method, AsyncMock(return_value=method_mock))

        mock_session.return_value = session_instance

        # Mock Redis to prevent connection attempts
        with patch("src.core.redis_cache.RedisVectorCache") as mock_redis_class:
            mock_redis_instance = AsyncMock()
            mock_redis_instance.connect.return_value = True
            mock_redis_instance.disconnect.return_value = None
            mock_redis_class.return_value = mock_redis_instance
            # Mock role taxonomy manager to prevent data loading
            with patch(
                "src.core.role_taxonomy_manager.RoleTaxonomyManager"
            ) as mock_taxonomy:
                manager = Mock()
                manager.load_role_data.return_value = None
                manager.roles = {}
                mock_taxonomy.return_value = manager
                yield
