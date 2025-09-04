"""Test API endpoints."""

import pytest
from fastapi.testclient import TestClient


class TestRootEndpoint:
    """Test root endpoint."""
    
    def test_read_root_success(self, client: TestClient):
        """Test root endpoint returns correct response."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "version" in data
        assert "status" in data
        assert "message" in data
        assert data["status"] == "operational"


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_health_check_basic(self, client: TestClient):
        """Test basic health check endpoint."""
        response = client.get("/health/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "service" in data
        assert "version" in data
        assert "uptime_seconds" in data
    
    def test_health_check_detailed(self, client: TestClient):
        """Test detailed health check endpoint."""
        response = client.get("/health/detailed")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "database" in data
        assert "external_services" in data
        assert "configuration" in data
        assert "profile_ingestor" in data["external_services"]
    
    def test_readiness_probe(self, client: TestClient):
        """Test Kubernetes readiness probe."""
        response = client.get("/health/ready")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
    
    def test_liveness_probe(self, client: TestClient):
        """Test Kubernetes liveness probe."""
        response = client.get("/health/live")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"


class TestCORSHeaders:
    """Test CORS configuration."""
    
    def test_cors_preflight_request(self, client: TestClient):
        """Test CORS preflight request."""
        response = client.options("/health/", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Content-Type"
        })
        
        # FastAPI's CORS middleware should handle this
        assert response.status_code in [200, 204]


class TestCorrelationID:
    """Test correlation ID functionality."""
    
    def test_correlation_id_in_response_headers(self, client: TestClient):
        """Test that correlation ID is included in response headers."""
        response = client.get("/health/")
        
        assert "X-Correlation-ID" in response.headers
        correlation_id = response.headers["X-Correlation-ID"]
        assert len(correlation_id) > 0
    
    def test_custom_correlation_id_preserved(self, client: TestClient):
        """Test that custom correlation ID is preserved."""
        custom_id = "test-correlation-123"
        response = client.get("/health/", headers={
            "X-Correlation-ID": custom_id
        })
        
        assert response.headers["X-Correlation-ID"] == custom_id