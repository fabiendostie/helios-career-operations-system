"""Pytest configuration and fixtures for Editor service tests."""

import pytest
import asyncio
from typing import Generator
from unittest.mock import Mock

import sys
import os

# Add src to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_language_tool():
    """Mock LanguageTool for testing."""
    mock_tool = Mock()
    mock_match = Mock()
    mock_match.offset = 0
    mock_match.errorLength = 4
    mock_match.message = "Test grammar error"
    mock_match.replacements = ["fixed"]
    mock_match.ruleId = "TEST_RULE"
    mock_match.category = "Grammar"

    mock_tool.check.return_value = [mock_match]
    return mock_tool


@pytest.fixture
def mock_spacy_model():
    """Mock spaCy model for testing."""
    mock_model = Mock()
    mock_doc = Mock()
    mock_model.return_value = mock_doc
    return mock_model


@pytest.fixture
def sample_texts():
    """Sample texts for testing."""
    return {
        "weak": "I did some work on various things and helped with stuff.",
        "grammar_errors": "This are a test sentence with grammar error.",
        "professional": "I led a cross-functional team to develop and deploy a scalable software solution.",
        "quantified": "I increased sales by 25% and reduced costs by $50,000.",
        "passive": "The project was completed by me and results were achieved.",
        "empty": "",
        "long": " ".join(["This is a very long text."] * 1000)
    }


@pytest.fixture
def sample_sessions():
    """Sample session IDs for testing."""
    return {
        "main": "test-session-main",
        "batch": "test-session-batch",
        "version": "test-session-version",
        "concurrent": "test-session-concurrent"
    }


@pytest.fixture(autouse=True)
def reset_global_state():
    """Reset global state before each test."""
    # Reset metrics
    from src.api.editing import _metrics
    _metrics.update({
        "total_edits": 0,
        "total_processing_time": 0.0,
        "successful_edits": 0,
        "failed_edits": 0
    })

    yield

    # Cleanup after test
    pass