"""Test API endpoints for the Analyst service."""

import pytest
from fastapi.testclient import TestClient

from src.main import create_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health/")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "analyst"
    assert data["version"] == "1.0.0"


def test_readiness_check(client):
    """Test readiness check endpoint."""
    response = client.get("/health/ready")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ready"
    assert data["service"] == "analyst"


@pytest.mark.asyncio
async def test_analyze_endpoint_with_mock_orchestrator(client):
    """Test analyze endpoint with mocked orchestrator."""
    from unittest.mock import patch, AsyncMock

    # Mock the orchestrator integration
    with patch("src.api.analysis.AsyncOrchestratorIntegration") as mock_orchestrator:
        mock_instance = AsyncMock()
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=None)

        # Mock the analysis result
        mock_instance.execute_analysis_with_orchestrator = AsyncMock(
            return_value={
                "pipeline_steps": {
                    "resume_deconstruction": {
                        "status": "completed",
                        "entities_extracted": 5,
                    },
                    "market_analysis": {"status": "completed", "jobs_matched": 3},
                    "ats_simulation": {"status": "completed", "ats_score": 75},
                    "skill_recalibration": {
                        "status": "completed",
                        "skills_analyzed": 10,
                    },
                    "career_inference": {"status": "completed", "paths_generated": 4},
                },
                "recommendations": ["Focus on Python skills", "Consider senior roles"],
                "processing_time_seconds": 2.5,
                "detailed_results": {},
            }
        )

        mock_orchestrator.return_value = mock_instance

        request_data = {
            "user_id": "test_user",
            "master_career_data": {"test": "data"},
            "correlation_id": "test_123",
        }

        response = client.post("/analysis/analyze", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert data["correlation_id"] == "test_123"
        assert "pipeline_steps" in data
        assert "recommendations" in data
        assert len(data["recommendations"]) > 0
