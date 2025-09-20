"""Integration tests for the Editor service."""

from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient
from src.integrations.orchestrator import OrchestratorClient
from src.main import app


class TestEditorIntegration:
    """Integration tests for the entire Editor service."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def sample_session_id(self):
        """Sample session ID for testing."""
        return "integration-test-session"

    def test_complete_editing_workflow(self, client, sample_session_id):
        """Test complete editing workflow from request to response."""
        # Step 1: Analyze original text
        analyze_request = {
            "text": "I worked on computer things and helped with various projects.",
            "language": "en",
        }

        analyze_response = client.post("/analyze", json=analyze_request)
        assert analyze_response.status_code == 200

        analysis = analyze_response.json()
        assert "overall_quality_score" in analysis
        assert "grammar_issues" in analysis
        assert "style_issues" in analysis

        # Step 2: Get suggestions
        suggestions_request = {
            "session_id": sample_session_id,
            "text": analyze_request["text"],
            "edit_type": "comprehensive",
            "industry": "technology",
            "role": "software developer",
        }

        suggestions_response = client.post(
            "/edit/suggestions", json=suggestions_request
        )
        assert suggestions_response.status_code == 200

        suggestions_data = suggestions_response.json()
        assert "suggestions" in suggestions_data
        assert "analysis" in suggestions_data

        # Step 3: Apply edit
        edit_request = {
            "session_id": sample_session_id,
            "text": analyze_request["text"],
            "edit_type": "comprehensive",
            "industry": "technology",
            "role": "software developer",
        }

        edit_response = client.post("/edit", json=edit_request)
        assert edit_response.status_code == 200

        edit_data = edit_response.json()
        assert edit_data["edited_text"] != edit_data["original_text"]
        assert "version_id" in edit_data

        # Step 4: Check version history
        history_response = client.get(f"/versions/{sample_session_id}")
        assert history_response.status_code == 200

        history = history_response.json()
        assert history["total_versions"] >= 1
        assert len(history["versions"]) >= 1

    def test_batch_editing_workflow(self, client):
        """Test batch editing functionality."""
        batch_request = {
            "session_id": "batch-test-session",
            "texts": [
                "I did work on projects.",
                "I helped with various things.",
                "I was responsible for tasks.",
            ],
            "edit_type": "comprehensive",
            "industry": "technology",
        }

        response = client.post("/edit/batch", json=batch_request)
        assert response.status_code == 200

        data = response.json()
        assert len(data["results"]) == 3
        assert data["success_count"] == 3
        assert data["error_count"] == 0

        # Check that all texts were improved
        for result in data["results"]:
            assert result["edited_text"] != result["original_text"]

    def test_version_control_workflow(self, client, sample_session_id):
        """Test version control features."""
        # Create multiple versions by editing
        texts = [
            "Original text with issues.",
            "First edit of the text.",
            "Second edit of the text.",
        ]

        version_ids = []
        for i, text in enumerate(texts):
            edit_request = {
                "session_id": sample_session_id,
                "text": text,
                "edit_type": "grammar",
                "version_comment": f"Version {i + 1}",
            }

            response = client.post("/edit", json=edit_request)
            assert response.status_code == 200
            version_ids.append(response.json()["version_id"])

        # Get version history
        history_response = client.get(f"/versions/{sample_session_id}")
        assert history_response.status_code == 200
        assert history_response.json()["total_versions"] == 3

        # Compare versions
        if len(version_ids) >= 2:
            compare_response = client.get(
                f"/versions/{sample_session_id}/compare"
                f"?version_a={version_ids[0]}&version_b={version_ids[1]}"
            )
            assert compare_response.status_code == 200

            comparison = compare_response.json()
            assert "similarity_score" in comparison
            assert "diff" in comparison

        # Revert to previous version
        if len(version_ids) >= 2:
            revert_request = {
                "target_version_id": version_ids[0],
                "comment": "Reverting to original",
            }

            revert_response = client.post(
                f"/versions/{sample_session_id}/revert", json=revert_request
            )
            assert revert_response.status_code == 200

    def test_error_handling_workflow(self, client):
        """Test error handling across the service."""
        # Test empty text
        response = client.post(
            "/edit",
            json={"session_id": "error-test", "text": "", "edit_type": "comprehensive"},
        )
        assert response.status_code == 400

        # Test invalid edit type
        response = client.post(
            "/edit",
            json={
                "session_id": "error-test",
                "text": "Valid text",
                "edit_type": "invalid_type",
            },
        )
        assert response.status_code == 422

        # Test missing required fields
        response = client.post("/edit", json={"text": "Missing session_id"})
        assert response.status_code == 422

    def test_metrics_and_monitoring(self, client):
        """Test metrics collection and monitoring."""
        # Perform some edits to generate metrics
        for i in range(3):
            edit_request = {
                "session_id": f"metrics-test-{i}",
                "text": f"Test text {i} for metrics collection.",
                "edit_type": "grammar",
            }

            response = client.post("/edit", json=edit_request)
            assert response.status_code == 200

        # Check metrics
        metrics_response = client.get("/metrics")
        assert metrics_response.status_code == 200

        metrics = metrics_response.json()
        assert metrics["total_edits"] >= 3
        assert metrics["success_rate"] > 0
        assert "average_processing_time" in metrics

    def test_service_health_monitoring(self, client):
        """Test health monitoring endpoints."""
        # Basic health check
        response = client.get("/health/")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

        # Detailed health check
        response = client.get("/health/detailed")
        assert response.status_code == 200

        health_data = response.json()
        assert "components" in health_data
        assert "text_optimizer" in health_data["components"]

    @pytest.mark.asyncio
    async def test_orchestrator_integration(self):
        """Test integration with orchestrator service."""
        with patch("httpx.AsyncClient") as mock_client:
            # Mock successful responses
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "success"}
            mock_response.raise_for_status.return_value = None

            mock_client.return_value.__aenter__.return_value.post.return_value = (
                mock_response
            )
            mock_client.return_value.__aenter__.return_value.get.return_value = (
                mock_response
            )

            orchestrator = OrchestratorClient()

            # Test service registration
            result = await orchestrator.register_service()
            assert result is True

            # Test status update
            result = await orchestrator.send_status_update("healthy")
            assert result is True

            # Test session context retrieval
            context = await orchestrator.get_session_context("test-session")
            assert context is not None

    def test_concurrent_editing_sessions(self, client):
        """Test handling of concurrent editing sessions."""
        import threading

        results = []

        def edit_worker(session_id, text):
            try:
                response = client.post(
                    "/edit",
                    json={
                        "session_id": session_id,
                        "text": text,
                        "edit_type": "comprehensive",
                    },
                )
                results.append(response.status_code)
            except Exception:
                results.append(500)

        threads = []
        for i in range(5):
            thread = threading.Thread(
                target=edit_worker,
                args=(f"concurrent-session-{i}", f"Test text for session {i}"),
            )
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # All should succeed
        assert all(status == 200 for status in results)
        assert len(results) == 5

    def test_performance_under_load(self, client):
        """Test service performance under load."""
        import time

        start_time = time.time()
        responses = []

        # Simulate load with multiple requests
        for i in range(20):
            response = client.post(
                "/edit",
                json={
                    "session_id": f"load-test-{i}",
                    "text": f"Performance test text {i} with various content to edit and optimize.",
                    "edit_type": "comprehensive",
                },
            )
            responses.append(response)

        end_time = time.time()
        total_time = end_time - start_time

        # Check all requests succeeded
        assert all(r.status_code == 200 for r in responses)

        # Check reasonable performance (adjust threshold as needed)
        avg_time_per_request = total_time / len(responses)
        assert avg_time_per_request < 2.0  # Less than 2 seconds per request

    def test_data_consistency_across_operations(self, client, sample_session_id):
        """Test data consistency across different operations."""
        # Create initial version
        edit_response = client.post(
            "/edit",
            json={
                "session_id": sample_session_id,
                "text": "Initial text for consistency testing.",
                "edit_type": "comprehensive",
            },
        )
        assert edit_response.status_code == 200

        initial_data = edit_response.json()

        # Get version history
        history_response = client.get(f"/versions/{sample_session_id}")
        assert history_response.status_code == 200

        history = history_response.json()
        assert len(history["versions"]) == 1
        assert history["versions"][0]["version_id"] == initial_data["version_id"]

        # Edit again
        second_edit_response = client.post(
            "/edit",
            json={
                "session_id": sample_session_id,
                "text": "Second text for consistency testing.",
                "edit_type": "comprehensive",
            },
        )
        assert second_edit_response.status_code == 200

        # Check updated history
        updated_history_response = client.get(f"/versions/{sample_session_id}")
        assert updated_history_response.status_code == 200

        updated_history = updated_history_response.json()
        assert len(updated_history["versions"]) == 2
        assert updated_history["total_versions"] == 2
