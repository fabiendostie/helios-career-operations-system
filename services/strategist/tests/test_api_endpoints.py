"""Test API endpoints for STRATEGIST service."""

import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint returns service information."""
    response = client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert data["service"] == "STRATEGIST"
    assert data["version"] == "1.0.0"
    assert data["status"] == "active"


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "strategist"
    assert data["version"] == "1.0.0"
    assert "timestamp" in data
    assert "uptime" in data


def test_readiness_check():
    """Test readiness check endpoint."""
    response = client.get("/health/ready")
    assert response.status_code == 200
    
    data = response.json()
    assert data["service"] == "strategist"
    assert "status" in data
    assert "checks" in data
    assert "timestamp" in data


def test_correlation_id_middleware():
    """Test correlation ID middleware adds headers."""
    response = client.get("/health")
    assert "x-correlation-id" in response.headers
    
    # Test with existing correlation ID
    correlation_id = "test-123"
    response = client.get(
        "/health", 
        headers={"x-correlation-id": correlation_id}
    )
    assert response.headers["x-correlation-id"] == correlation_id


@pytest.mark.asyncio
async def test_async_endpoints():
    """Test async endpoint functionality."""
    from httpx import ASGITransport
    
    async with AsyncClient(
        transport=ASGITransport(app=app), 
        base_url="http://test"
    ) as ac:
        response = await ac.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"