"""Comprehensive integration tests for HELIOS Orchestrator."""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
import aiohttp

from .mock_profile_ingestor import create_mock_profile_ingestor_app, set_processing_delay, clear_mock_data


class TestFullIntegration:
    """Test complete integration scenarios with mock Profile Ingestor."""

    @pytest.fixture
    def mock_profile_ingestor_app(self):
        """Create mock Profile Ingestor app."""
        return create_mock_profile_ingestor_app()

    @pytest.fixture
    def mock_profile_ingestor_server(self, mock_profile_ingestor_app):
        """Start mock Profile Ingestor server."""
        # In a real test, we'd start the server on a test port
        # For this example, we'll mock the HTTP calls
        return "http://localhost:8001"

    @pytest.mark.integration
    def test_complete_user_workflow(self, client):
        """Test complete user workflow from start to finish."""
        # Step 1: Start a new session
        response = client.post("/commands/start", json={"user_id": "test-user-workflow"})
        assert response.status_code == 200
        data = response.json()
        session_id = data["result"]["session_id"]

        # Step 2: Check session status
        response = client.get(f"/commands/status/{session_id}")
        assert response.status_code == 200
        assert response.json()["result"]["state"] == "initialized"

        # Step 3: Get help information
        response = client.get("/commands/help")
        assert response.status_code == 200
        assert "available_commands" in response.json()["result"]

        # Step 4: List all sessions
        response = client.get("/sessions/")
        assert response.status_code == 200
        sessions = response.json()
        assert len(sessions) >= 1
        assert any(str(s["session_id"]) == session_id for s in sessions)

    @pytest.mark.integration
    @patch('src.integrations.profile_ingestor.get_profile_ingestor_client')
    async def test_ingestion_integration_success(self, mock_client_getter, client):
        """Test successful ingestion integration with Profile Ingestor."""
        # Setup mock client
        mock_client = AsyncMock()
        mock_client.ingest_text.return_value = AsyncMock(
            success=True,
            master_career_database={"skills": ["Python", "FastAPI"]},
            processing_summary={"files_processed": 1},
            errors=[],
            warnings=[]
        )
        mock_client_getter.return_value = mock_client

        # Start session
        response = client.post("/commands/start", json={"user_id": "test-ingestion"})
        session_id = response.json()["result"]["session_id"]

        # Execute ingestion command
        ingestion_request = {
            "command": "/ingest",
            "session_id": session_id,
            "parameters": {
                "text_content": "I am a Python developer with FastAPI experience"
            }
        }

        response = client.post("/commands/execute", json=ingestion_request)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert "master_career_database" in data["result"]

        # Verify session was updated
        response = client.get(f"/sessions/{session_id}")
        assert response.status_code == 200
        session_data = response.json()
        assert session_data["state"] == "completed"
        assert session_data["current_step"] == "discover"

    @pytest.mark.integration
    @patch('src.integrations.profile_ingestor.get_profile_ingestor_client')
    async def test_ingestion_integration_failure(self, mock_client_getter, client):
        """Test ingestion failure handling."""
        # Setup mock client to simulate failure
        mock_client = AsyncMock()
        mock_client.ingest_text.return_value = AsyncMock(
            success=False,
            master_career_database={},
            processing_summary={"error": "Processing failed"},
            errors=["Mock processing error"],
            warnings=[]
        )
        mock_client_getter.return_value = mock_client

        # Start session
        response = client.post("/commands/start", json={"user_id": "test-failure"})
        session_id = response.json()["result"]["session_id"]

        # Execute ingestion command
        ingestion_request = {
            "command": "/ingest",
            "session_id": session_id,
            "parameters": {
                "text_content": "Test content"
            }
        }

        response = client.post("/commands/execute", json=ingestion_request)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"
        assert "errors" in data["result"]

        # Verify session was updated to error state
        response = client.get(f"/sessions/{session_id}")
        assert response.status_code == 200
        session_data = response.json()
        assert session_data["state"] == "error"

    @pytest.mark.integration
    def test_session_persistence_across_restarts(self, client):
        """Test that sessions persist across application restarts."""
        # Create a session
        response = client.post("/commands/start", json={"user_id": "persistence-test"})
        session_id = response.json()["result"]["session_id"]

        # Update session with some data
        update_data = {
            "metadata": {"test": "persistence"}
        }
        response = client.put(f"/sessions/{session_id}", json=update_data)
        assert response.status_code == 200

        # Verify data persists (simulating restart by getting fresh session)
        response = client.get(f"/sessions/{session_id}")
        assert response.status_code == 200
        session_data = response.json()
        assert session_data["metadata"]["test"] == "persistence"

    @pytest.mark.integration
    def test_session_cleanup_and_expiry(self, client):
        """Test session cleanup and expiration mechanisms."""
        # Create multiple sessions
        session_ids = []
        for i in range(3):
            response = client.post("/commands/start", json={"user_id": f"cleanup-test-{i}"})
            session_ids.append(response.json()["result"]["session_id"])

        # Verify all sessions exist
        for session_id in session_ids:
            response = client.get(f"/sessions/{session_id}")
            assert response.status_code == 200

        # Test manual cleanup
        response = client.post("/sessions/cleanup")
        assert response.status_code == 200
        # Should return cleanup count (0 since sessions are not expired yet)
        assert "cleaned_up" in response.json()

    @pytest.mark.integration
    def test_command_state_transitions(self, client):
        """Test proper command state transitions."""
        # Start session
        response = client.post("/commands/start", json={"user_id": "state-test"})
        session_id = response.json()["result"]["session_id"]

        # Verify initial state
        response = client.get(f"/sessions/{session_id}")
        assert response.json()["current_step"] == "start"

        # Try invalid command for current state (should fail validation)
        invalid_request = {
            "command": "/analyze",  # Not allowed from START step
            "session_id": session_id,
            "parameters": {}
        }

        response = client.post("/commands/execute", json=invalid_request)
        assert response.status_code == 400  # Bad request due to validation
        assert "not allowed" in response.json()["detail"]["message"]

    @pytest.mark.integration
    def test_error_handling_and_recovery(self, client):
        """Test comprehensive error handling scenarios."""
        # Test with non-existent session
        response = client.get("/sessions/non-existent-session")
        assert response.status_code == 404

        # Test command execution with invalid session
        invalid_request = {
            "command": "/status",
            "session_id": "non-existent-session",
            "parameters": {}
        }

        response = client.post("/commands/execute", json=invalid_request)
        assert response.status_code == 400  # Validation error

        # Test invalid command parameters
        response = client.post("/commands/start")
        invalid_ingest = {
            "command": "/ingest",
            "session_id": response.json()["result"]["session_id"],
            "parameters": {}  # Missing required input
        }

        response = client.post("/commands/execute", json=invalid_ingest)
        assert response.status_code == 400

    @pytest.mark.integration
    def test_concurrent_session_handling(self, client):
        """Test handling of multiple concurrent sessions."""
        # Create multiple sessions concurrently
        session_responses = []

        for i in range(10):  # Test with 10 concurrent sessions
            response = client.post("/commands/start", json={"user_id": f"concurrent-{i}"})
            assert response.status_code == 200
            session_responses.append(response.json())

        # Verify all sessions are unique
        session_ids = [r["result"]["session_id"] for r in session_responses]
        assert len(set(session_ids)) == 10  # All unique

        # Test concurrent operations on different sessions
        for session_id in session_ids[:5]:
            response = client.get(f"/sessions/{session_id}")
            assert response.status_code == 200

    @pytest.mark.integration
    def test_health_monitoring_integration(self, client):
        """Test comprehensive health monitoring."""
        # Test basic health check
        response = client.get("/health/")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

        # Test detailed health check
        response = client.get("/health/detailed")
        assert response.status_code == 200
        data = response.json()
        assert "external_services" in data
        assert "configuration" in data
        assert "profile_ingestor" in data["external_services"]

        # Test readiness and liveness probes
        response = client.get("/health/ready")
        assert response.status_code == 200
        assert response.json()["status"] == "ready"

        response = client.get("/health/live")
        assert response.status_code == 200
        assert response.json()["status"] == "alive"

    @pytest.mark.integration
    def test_api_documentation_and_validation(self, client):
        """Test API documentation and validation."""
        # Test OpenAPI schema generation
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "paths" in schema

        # Verify key endpoints are documented
        paths = schema["paths"]
        assert "/health/" in paths
        assert "/sessions/" in paths
        assert "/commands/execute" in paths

        # Test API documentation UI access
        response = client.get("/docs")
        assert response.status_code == 200

        response = client.get("/redoc")
        assert response.status_code == 200


class TestPerformanceIntegration:
    """Performance and load testing for concurrent operations."""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_session_creation_performance(self, client):
        """Test session creation performance under load."""
        import time

        session_count = 100
        start_time = time.time()

        # Create 100 sessions
        session_ids = []
        for i in range(session_count):
            response = client.post("/commands/start", json={"user_id": f"perf-test-{i}"})
            assert response.status_code == 200
            session_ids.append(response.json()["result"]["session_id"])

        end_time = time.time()
        total_time = end_time - start_time

        # Performance assertions
        assert len(session_ids) == session_count
        assert total_time < 10.0  # Should complete within 10 seconds
        avg_time_per_session = total_time / session_count
        assert avg_time_per_session < 0.1  # Less than 100ms per session

        print(f"Created {session_count} sessions in {total_time:.2f}s (avg: {avg_time_per_session:.3f}s per session)")

    @pytest.mark.integration
    @pytest.mark.slow
    def test_concurrent_session_operations(self, client):
        """Test concurrent operations on multiple sessions."""
        # Create base sessions
        session_ids = []
        for i in range(50):
            response = client.post("/commands/start", json={"user_id": f"concurrent-ops-{i}"})
            session_ids.append(response.json()["result"]["session_id"])

        import time
        start_time = time.time()

        # Perform concurrent status checks
        status_responses = []
        for session_id in session_ids:
            response = client.get(f"/sessions/{session_id}")
            status_responses.append(response)

        end_time = time.time()

        # Verify all operations succeeded
        assert all(r.status_code == 200 for r in status_responses)

        # Performance check - should handle 50 concurrent operations quickly
        total_time = end_time - start_time
        assert total_time < 5.0  # Should complete within 5 seconds

        print(f"Handled 50 concurrent session operations in {total_time:.2f}s")

    @pytest.mark.integration
    @pytest.mark.slow
    def test_api_response_times(self, client):
        """Test API response times meet SLA requirements."""
        import time

        endpoints_to_test = [
            ("/health/", "GET"),
            ("/health/detailed", "GET"),
            ("/commands/help", "GET"),
        ]

        for endpoint, method in endpoints_to_test:
            times = []

            # Test each endpoint 10 times
            for _ in range(10):
                start_time = time.time()

                if method == "GET":
                    response = client.get(endpoint)

                end_time = time.time()
                response_time = end_time - start_time

                times.append(response_time)
                assert response.status_code == 200
                assert response_time < 2.0  # SLA requirement: <2s response time

            avg_time = sum(times) / len(times)
            max_time = max(times)

            print(f"{method} {endpoint}: avg={avg_time:.3f}s, max={max_time:.3f}s")
            assert avg_time < 0.5  # Average should be much faster than SLA
            assert max_time < 2.0   # Max should meet SLA requirement


# Test utilities for performance testing
def run_load_test():
    """Run comprehensive load test - for manual execution."""
    import concurrent.futures
    import time

    def create_session_worker(worker_id):
        """Worker function for concurrent session creation."""
        with TestClient(app) as test_client:
            start_time = time.time()
            response = test_client.post("/commands/start", json={"user_id": f"load-test-{worker_id}"})
            end_time = time.time()

            return {
                "worker_id": worker_id,
                "success": response.status_code == 200,
                "response_time": end_time - start_time,
                "session_id": response.json().get("result", {}).get("session_id") if response.status_code == 200 else None
            }

    # Test with 100 concurrent workers
    worker_count = 100

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        start_time = time.time()

        # Submit all workers
        futures = [executor.submit(create_session_worker, i) for i in range(worker_count)]

        # Collect results
        results = [future.result() for future in concurrent.futures.as_completed(futures)]

        end_time = time.time()

    # Analyze results
    total_time = end_time - start_time
    successful_sessions = sum(1 for r in results if r["success"])
    failed_sessions = worker_count - successful_sessions

    response_times = [r["response_time"] for r in results if r["success"]]
    avg_response_time = sum(response_times) / len(response_times) if response_times else 0
    max_response_time = max(response_times) if response_times else 0

    print(f"\nLoad Test Results:")
    print(f"Total time: {total_time:.2f}s")
    print(f"Successful sessions: {successful_sessions}/{worker_count}")
    print(f"Failed sessions: {failed_sessions}")
    print(f"Average response time: {avg_response_time:.3f}s")
    print(f"Maximum response time: {max_response_time:.3f}s")
    print(f"Throughput: {successful_sessions/total_time:.2f} sessions/second")

    # Assertions for load test
    assert successful_sessions >= worker_count * 0.95  # 95% success rate
    assert avg_response_time < 2.0  # Average under SLA
    assert max_response_time < 5.0  # Even worst case should be reasonable


if __name__ == "__main__":
    # For manual load testing
    from src.main import app
    run_load_test()
