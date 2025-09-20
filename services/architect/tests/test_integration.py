"""Integration tests for the Architect service."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from src.core.document_generator import DocumentGenerator
from src.main import create_app


class TestArchitectServiceIntegration:
    """Integration tests for the complete Architect service."""

    @pytest.fixture
    def app(self):
        """Create test FastAPI app."""
        return create_app()

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def sample_career_data(self):
        """Sample career data for integration testing."""
        return {
            "candidate_name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "555-123-4567",
            "location": "New York, NY",
            "linkedin": "linkedin.com/in/johndoe",
            "work_experience": [
                {
                    "role_title": "Senior Software Engineer",
                    "company_name": "TechCorp",
                    "start_date": "2020-01",
                    "end_date": "Present",
                    "accomplishments": [
                        "Led development of microservices architecture serving 1M+ users",
                        "Improved system performance by 40% through optimization",
                        "Mentored team of 5 junior developers",
                    ],
                    "skills_used": ["Python", "AWS", "Docker", "Kubernetes"],
                },
                {
                    "role_title": "Software Engineer",
                    "company_name": "StartupCorp",
                    "start_date": "2018-06",
                    "end_date": "2020-01",
                    "accomplishments": [
                        "Built full-stack web application from scratch",
                        "Implemented CI/CD pipeline reducing deployment time by 60%",
                    ],
                    "skills_used": ["JavaScript", "React", "Node.js", "MongoDB"],
                },
            ],
            "education": [
                {
                    "degree": "Bachelor of Science in Computer Science",
                    "institution": "State University",
                    "year": "2018",
                }
            ],
            "skills_inventory": {
                "technical_skills": {
                    "programming": ["Python", "JavaScript", "Java"],
                    "frameworks": ["React", "Django", "FastAPI"],
                    "tools": ["Docker", "Kubernetes", "AWS", "Git"],
                },
                "soft_skills": ["Leadership", "Communication", "Problem Solving"],
            },
            "strategic_metadata": {
                "core_competencies": [
                    "Software Architecture",
                    "Team Leadership",
                    "Cloud Computing",
                ],
                "quantified_achievements": [
                    "improved system performance by 40%",
                    "led team of 5 developers",
                    "reduced deployment time by 60%",
                ],
            },
        }

    @pytest.mark.asyncio
    async def test_document_generator_integration(self, sample_career_data):
        """Test complete document generation workflow."""
        # Initialize document generator
        generator = DocumentGenerator()

        # Test HTML generation
        html_result = await generator.generate_document(
            template_name="t_shaped_classic",
            career_data=sample_career_data,
            output_format="html",
            document_type="resume",
        )

        assert html_result["content"] is not None
        assert html_result["mime_type"] == "text/html"
        assert "metadata" in html_result
        assert html_result["metadata"]["template_name"] == "t_shaped_classic"

        # Test PDF generation (with fallback)
        pdf_result = await generator.generate_document(
            template_name="t_shaped_classic",
            career_data=sample_career_data,
            output_format="pdf",
            document_type="resume",
        )

        assert pdf_result["content"] is not None
        assert pdf_result["mime_type"] == "application/pdf"
        assert len(pdf_result["content"]) > 0

        # Test Markdown generation
        md_result = await generator.generate_document(
            template_name="t_shaped_classic",
            career_data=sample_career_data,
            output_format="markdown",
            document_type="resume",
        )

        assert md_result["content"] is not None
        assert md_result["mime_type"] == "text/markdown"

    def test_health_endpoint(self, client):
        """Test health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "timestamp" in data

    def test_template_listing_endpoint(self, client):
        """Test template listing endpoint."""
        response = client.get("/generate/templates")
        assert response.status_code == 200
        data = response.json()
        assert "templates" in data
        assert "total_count" in data

    @patch("src.api.generation.get_session_data")
    def test_resume_generation_endpoint(
        self, mock_get_session, client, sample_career_data
    ):
        """Test resume generation API endpoint."""
        # Mock session data retrieval
        mock_get_session.return_value = sample_career_data

        request_data = {
            "session_id": "test-session-123",
            "document_type": "resume",
            "template_name": "t_shaped_classic",
            "output_format": "html",
        }

        response = client.post("/generate/resume", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "content" in data
        assert data["mime_type"] == "text/html"

    @patch("src.api.generation.get_session_data")
    def test_cover_letter_generation_endpoint(
        self, mock_get_session, client, sample_career_data
    ):
        """Test cover letter generation API endpoint."""
        # Mock session data retrieval
        mock_get_session.return_value = sample_career_data

        request_data = {
            "session_id": "test-session-123",
            "document_type": "cover_letter",
            "template_name": "pain_promise",
            "output_format": "html",
            "job_requirements": {
                "role_title": "Senior Software Engineer",
                "company": "BigTech Corp",
                "required_skills": ["Python", "AWS", "Leadership"],
            },
        }

        response = client.post("/generate/cover-letter", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "content" in data

    def test_bulk_generation_endpoint(self, client, sample_career_data):
        """Test bulk document generation endpoint."""
        with patch("src.api.generation.get_session_data") as mock_get_session:
            mock_get_session.return_value = sample_career_data

            request_data = {
                "session_id": "test-session-123",
                "parallel_processing": True,
                "generations": [
                    {
                        "session_id": "test-session-123",
                        "document_type": "resume",
                        "template_name": "t_shaped_classic",
                        "output_format": "html",
                    },
                    {
                        "session_id": "test-session-123",
                        "document_type": "resume",
                        "template_name": "t_shaped_modern",
                        "output_format": "pdf",
                    },
                ],
            }

            response = client.post("/generate/bulk", json=request_data)
            assert response.status_code == 200

            data = response.json()
            assert "results" in data
            assert "success_count" in data
            assert "total_time" in data

    def test_download_endpoint(self, client, sample_career_data):
        """Test document download endpoint."""
        with patch("src.api.generation.get_session_data") as mock_get_session:
            mock_get_session.return_value = sample_career_data

            response = client.get(
                "/generate/download/test-session-123/html?template_name=t_shaped_classic"
            )
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/html; charset=utf-8"

    @pytest.mark.asyncio
    async def test_template_engine_integration(self, sample_career_data):
        """Test template engine with real templates."""
        from src.core.template_engine import TemplateEngine

        engine = TemplateEngine()

        # Test resume template rendering
        html_content = await engine.render_resume_template(
            template_name="t_shaped_classic", career_data=sample_career_data
        )

        assert html_content is not None
        assert isinstance(html_content, str)
        assert len(html_content) > 0
        assert "John Doe" in html_content
        assert "Senior Software Engineer" in html_content

        # Test cover letter template rendering
        job_requirements = {
            "role_title": "Senior Software Engineer",
            "company": "BigTech Corp",
        }

        cover_letter_content = await engine.render_cover_letter_template(
            template_name="pain_promise",
            career_data=sample_career_data,
            job_requirements=job_requirements,
        )

        assert cover_letter_content is not None
        assert isinstance(cover_letter_content, str)
        assert "BigTech Corp" in cover_letter_content

    def test_error_handling(self, client):
        """Test error handling for invalid requests."""
        # Test invalid session ID
        request_data = {
            "session_id": "invalid-session",
            "document_type": "resume",
            "template_name": "t_shaped_classic",
            "output_format": "html",
        }

        with patch("src.api.generation.get_session_data") as mock_get_session:
            mock_get_session.side_effect = Exception("Session not found")

            response = client.post("/generate/resume", json=request_data)
            assert response.status_code == 500

        # Test invalid template
        request_data["template_name"] = "invalid_template"
        response = client.post("/generate/resume", json=request_data)
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_performance_monitoring(self, sample_career_data):
        """Test performance monitoring and logging."""
        generator = DocumentGenerator()

        # Test memory monitoring
        from src.core.document_generator import monitor_memory_usage

        memory_ok = await monitor_memory_usage()
        assert isinstance(memory_ok, bool)

        # Test template caching
        engine = generator.template_engine
        cache_stats = engine._memory_engine.get_cache_stats()
        assert isinstance(cache_stats, dict)

        # Test generation timing
        result = await generator.generate_document(
            template_name="t_shaped_classic",
            career_data=sample_career_data,
            output_format="html",
            document_type="resume",
        )

        assert "generation_time" in result["metadata"]
        assert result["metadata"]["generation_time"] > 0


class TestArchitectServiceAPI:
    """Test API-specific functionality."""

    @pytest.fixture
    def app(self):
        """Create test FastAPI app."""
        return create_app()

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)

    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        response = client.options("/health")
        assert "access-control-allow-origin" in response.headers

    def test_correlation_id_header(self, client):
        """Test correlation ID is added to responses."""
        response = client.get("/health", headers={"X-Correlation-ID": "test-123"})
        assert response.headers.get("X-Correlation-ID") == "test-123"

    def test_metrics_endpoint(self, client):
        """Test Prometheus metrics endpoint."""
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "architect_requests_total" in response.text

    def test_openapi_docs(self, client):
        """Test OpenAPI documentation."""
        response = client.get("/docs")
        # Note: docs might be disabled in production
        assert response.status_code in [200, 404]

        response = client.get("/openapi.json")
        if response.status_code == 200:
            data = response.json()
            assert "openapi" in data
            assert data["info"]["title"] == "Helios ARCHITECT Service"
