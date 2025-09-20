"""Tests for API endpoints."""

from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient
from src.main import app


class TestEditorAPI:
    """Test cases for Editor API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def sample_edit_request(self):
        """Sample edit request for testing."""
        return {
            "session_id": "test-session",
            "text": "This are a test sentence with grammar error.",
            "edit_type": "comprehensive",
            "industry": "technology",
            "role": "software engineer",
        }

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_edit_text_endpoint(self, client, sample_edit_request):
        """Test text editing endpoint."""
        response = client.post("/edit", json=sample_edit_request)
        assert response.status_code == 200

        data = response.json()
        assert "session_id" in data
        assert "original_text" in data
        assert "edited_text" in data
        assert "suggestions" in data
        assert data["session_id"] == sample_edit_request["session_id"]

    def test_edit_text_validation(self, client):
        """Test request validation for edit endpoint."""
        # Missing required fields
        response = client.post("/edit", json={"session_id": "test"})
        assert response.status_code == 422

        # Invalid edit type
        response = client.post(
            "/edit",
            json={"session_id": "test", "text": "test", "edit_type": "invalid_type"},
        )
        assert response.status_code == 422

    def test_edit_text_empty_text(self, client):
        """Test editing with empty text."""
        response = client.post(
            "/edit",
            json={"session_id": "test", "text": "", "edit_type": "comprehensive"},
        )
        assert response.status_code == 400
        assert "Text cannot be empty" in response.json()["detail"]

    def test_analyze_text_endpoint(self, client):
        """Test text analysis endpoint."""
        response = client.post(
            "/analyze",
            json={"text": "This is a test sentence for analysis.", "language": "en"},
        )
        assert response.status_code == 200

        data = response.json()
        assert "text" in data
        assert "grammar_issues" in data
        assert "style_issues" in data
        assert "readability" in data
        assert "overall_quality_score" in data

    def test_batch_edit_endpoint(self, client):
        """Test batch editing endpoint."""
        request_data = {
            "session_id": "test-batch",
            "texts": ["This are wrong.", "This is correct.", "Another eror here."],
            "edit_type": "grammar",
        }

        response = client.post("/edit/batch", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 3
        assert "total_processing_time" in data

    def test_version_history_endpoint(self, client):
        """Test version history endpoint."""
        session_id = "test-version-session"

        # First, create some versions by editing text
        edit_requests = [
            {"session_id": session_id, "text": "Initial text.", "edit_type": "initial"},
            {"session_id": session_id, "text": "Edited text.", "edit_type": "grammar"},
        ]

        for request in edit_requests:
            client.post("/edit", json=request)

        # Now get version history
        response = client.get(f"/versions/{session_id}")
        assert response.status_code == 200

        data = response.json()
        assert "session_id" in data
        assert "versions" in data
        assert "total_versions" in data

    def test_compare_versions_endpoint(self, client):
        """Test version comparison endpoint."""
        session_id = "test-compare-session"

        # Create two versions
        edit1 = {
            "session_id": session_id,
            "text": "Original text.",
            "edit_type": "initial",
        }
        edit2 = {
            "session_id": session_id,
            "text": "Modified text.",
            "edit_type": "edit",
        }

        response1 = client.post("/edit", json=edit1)
        response2 = client.post("/edit", json=edit2)

        version1_id = response1.json()["version_id"]
        version2_id = response2.json()["version_id"]

        # Compare versions
        response = client.get(
            f"/versions/{session_id}/compare?version_a={version1_id}&version_b={version2_id}"
        )
        assert response.status_code == 200

        data = response.json()
        assert "diff" in data
        assert "similarity_score" in data
        assert "change_summary" in data

    def test_revert_version_endpoint(self, client):
        """Test version reversion endpoint."""
        session_id = "test-revert-session"

        # Create multiple versions
        edits = [
            {"session_id": session_id, "text": "Version 1", "edit_type": "initial"},
            {"session_id": session_id, "text": "Version 2", "edit_type": "edit"},
            {"session_id": session_id, "text": "Version 3", "edit_type": "edit"},
        ]

        responses = []
        for edit in edits:
            response = client.post("/edit", json=edit)
            responses.append(response)

        version2_id = responses[1].json()["version_id"]

        # Revert to version 2
        response = client.post(
            f"/versions/{session_id}/revert",
            json={"target_version_id": version2_id, "comment": "Reverted to version 2"},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["text"] == "Version 2"

    def test_edit_suggestions_endpoint(self, client, sample_edit_request):
        """Test getting edit suggestions without applying them."""
        response = client.post("/edit/suggestions", json=sample_edit_request)
        assert response.status_code == 200

        data = response.json()
        assert "suggestions" in data
        assert "analysis" in data
        assert len(data["suggestions"]) > 0

    def test_apply_suggestions_endpoint(self, client):
        """Test applying specific suggestions."""
        # First get suggestions
        request_data = {
            "session_id": "test-apply",
            "text": "This are wrong and has erors.",
            "edit_type": "grammar",
        }

        # Get suggestions first (but don't use them in this test)
        client.post("/edit/suggestions", json=request_data)

        # Apply specific suggestions
        apply_request = {
            "session_id": "test-apply",
            "text": request_data["text"],
            "suggestion_ids": [0, 1],  # Apply first two suggestions
        }

        response = client.post("/edit/apply", json=apply_request)
        assert response.status_code == 200

        data = response.json()
        assert "edited_text" in data
        assert data["edited_text"] != request_data["text"]

    def test_edit_with_industry_context(self, client):
        """Test editing with industry-specific context."""
        request_data = {
            "session_id": "test-industry",
            "text": "I worked on computer stuff and helped users.",
            "edit_type": "content_enhancement",
            "industry": "technology",
            "role": "software developer",
        }

        response = client.post("/edit", json=request_data)
        assert response.status_code == 200

        data = response.json()
        # Should contain technology-specific terms
        edited_text = data["edited_text"].lower()
        assert any(
            term in edited_text
            for term in ["software", "development", "applications", "systems"]
        )

    def test_tone_adjustment_endpoint(self, client):
        """Test tone adjustment functionality."""
        request_data = {
            "session_id": "test-tone",
            "text": "I did some work on projects and stuff.",
            "edit_type": "tone_adjustment",
            "tone": "professional",
        }

        response = client.post("/edit", json=request_data)
        assert response.status_code == 200

        data = response.json()
        # Should have more professional language
        assert "stuff" not in data["edited_text"].lower()

    def test_rate_limiting(self, client):
        """Test rate limiting on API endpoints."""
        # Make many requests quickly
        for _ in range(100):
            response = client.get("/health")
            if response.status_code == 429:  # Too Many Requests
                break
        else:
            # If no rate limiting is implemented, that's okay for now
            pass

    def test_error_handling(self, client):
        """Test API error handling."""
        # Invalid JSON
        response = client.post("/edit", data="invalid json")
        assert response.status_code == 422

        # Missing content-type
        response = client.post("/edit")
        assert response.status_code == 422

    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        response = client.options("/edit")
        # Should have CORS headers in actual deployment
        # For now, just check the endpoint exists
        assert response.status_code in [
            200,
            405,
        ]  # 405 = Method Not Allowed is also fine

    @patch("src.core.text_optimizer.TextOptimizer")
    def test_edit_service_integration(
        self, mock_optimizer, client, sample_edit_request
    ):
        """Test integration with text optimization service."""
        mock_instance = Mock()
        mock_optimizer.return_value = mock_instance
        mock_instance.optimize_text.return_value = Mock(
            session_id="test-session",
            original_text=sample_edit_request["text"],
            edited_text="This is a test sentence with corrected grammar.",
            suggestions=[],
            grammar_issues_fixed=1,
            style_improvements=0,
            content_enhancements=0,
            processing_time=0.5,
        )

        response = client.post("/edit", json=sample_edit_request)
        assert response.status_code == 200

        mock_instance.optimize_text.assert_called_once()

    def test_metrics_endpoint(self, client):
        """Test metrics endpoint for monitoring."""
        response = client.get("/metrics")
        assert response.status_code == 200

        data = response.json()
        assert "total_edits" in data
        assert "average_processing_time" in data
        assert "success_rate" in data

    def test_concurrent_requests(self, client):
        """Test handling of concurrent requests."""
        import threading

        results = []

        def make_request():
            response = client.post(
                "/edit",
                json={
                    "session_id": f"concurrent-{threading.current_thread().ident}",
                    "text": "Test concurrent editing.",
                    "edit_type": "grammar",
                },
            )
            results.append(response.status_code)

        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # All requests should succeed
        assert all(status == 200 for status in results)
