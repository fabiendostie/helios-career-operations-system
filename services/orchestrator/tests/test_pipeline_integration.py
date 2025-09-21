"""Integration tests for the complete pipeline orchestration."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime
import json

from src.core.service_coordinator import ServiceCoordinator, ServiceCoordinationError
from src.models.session import SessionState, CurrentStep


@pytest.fixture
def mock_session_manager():
    """Create mock session manager."""
    manager = AsyncMock()
    manager.create_session.return_value = Mock(session_id="test-session-123")
    manager.get_session.return_value = Mock(
        session_id="test-session-123",
        state=SessionState.COMPLETED,
        current_step=CurrentStep.REVIEW,
        master_career_database={"test": "data"},
        updated_at=datetime.utcnow()
    )
    manager.update_session.return_value = Mock(session_id="test-session-123")
    return manager


@pytest.fixture
def mock_profile_ingestor():
    """Create mock profile ingestor client."""
    client = AsyncMock()
    client.ingest_resume.return_value = {
        "success": True,
        "master_career_database": {
            "work_experience": [
                {
                    "job_title": "Software Engineer",
                    "company": "TechCorp",
                    "duration": "2 years",
                    "accomplishments": ["Built scalable APIs", "Led team of 5"]
                }
            ],
            "projects": [
                {
                    "name": "AI Chat System",
                    "description": "Developed AI-powered customer service bot"
                }
            ],
            "skills_inventory": {
                "technical": ["Python", "FastAPI", "PostgreSQL"],
                "soft_skills": ["Leadership", "Communication"]
            }
        }
    }
    client.health_check.return_value = {"status": "healthy"}
    return client


@pytest.fixture
def mock_strategist():
    """Create mock strategist client."""
    client = AsyncMock()
    client.generate_career_paths.return_value = {
        "success": True,
        "career_paths": {
            "recommended_paths": [
                {
                    "path_id": "senior_engineer",
                    "title": "Senior Software Engineer",
                    "fit_score": 0.92,
                    "transition_difficulty": "low",
                    "learning_time_months": 6
                },
                {
                    "path_id": "tech_lead",
                    "title": "Technical Lead",
                    "fit_score": 0.85,
                    "transition_difficulty": "medium",
                    "learning_time_months": 12
                }
            ],
            "analysis": {
                "current_level": "mid_level",
                "strength_areas": ["technical_skills", "project_management"],
                "growth_areas": ["system_architecture", "team_leadership"]
            }
        }
    }
    client.health_check.return_value = {"status": "healthy"}
    return client


@pytest.fixture
def mock_analyst():
    """Create mock analyst client."""
    client = AsyncMock()
    client.analyze_market_position.return_value = {
        "success": True,
        "analysis": {
            "market_demand": {
                "software_engineer": {
                    "demand_score": 0.88,
                    "salary_range": {"min": 80000, "max": 150000},
                    "job_openings": 1250
                }
            },
            "skill_gaps": [
                {
                    "skill": "Kubernetes",
                    "importance": 0.75,
                    "current_level": 0.2,
                    "target_level": 0.8
                }
            ],
            "resume_optimization": {
                "ats_score": 0.73,
                "recommendations": [
                    "Add more quantifiable achievements",
                    "Include relevant keywords for target roles"
                ]
            }
        }
    }
    client.health_check.return_value = {"status": "healthy"}
    return client


@pytest.fixture
def service_coordinator(mock_session_manager, mock_profile_ingestor, mock_strategist, mock_analyst):
    """Create service coordinator with mocked dependencies."""
    return ServiceCoordinator(
        session_manager=mock_session_manager,
        profile_ingestor=mock_profile_ingestor,
        strategist=mock_strategist,
        analyst=mock_analyst
    )


class TestPipelineIntegration:
    """Test complete pipeline integration."""

    @pytest.mark.asyncio
    async def test_full_pipeline_execution_success(self, service_coordinator):
        """Test successful execution of complete pipeline."""
        # Execute pipeline with mock resume path
        results = await service_coordinator.execute_full_pipeline(
            session_id="test-session-123",
            resume_path="/path/to/resume.pdf"
        )

        # Verify results structure
        assert "session_id" in results
        assert "timestamp" in results
        assert "profile_data" in results
        assert "career_strategies" in results
        assert "market_analysis" in results
        assert results["pipeline_status"] == "completed"

        # Verify profile data
        profile_data = results["profile_data"]
        assert "work_experience" in profile_data
        assert "skills_inventory" in profile_data
        assert len(profile_data["work_experience"]) > 0

        # Verify career strategies
        strategies = results["career_strategies"]
        assert "recommended_paths" in strategies
        assert len(strategies["recommended_paths"]) == 2
        assert strategies["recommended_paths"][0]["fit_score"] == 0.92

        # Verify market analysis
        analysis = results["market_analysis"]
        assert "market_demand" in analysis
        assert "skill_gaps" in analysis
        assert "resume_optimization" in analysis

    @pytest.mark.asyncio
    async def test_pipeline_with_direct_career_data(self, service_coordinator):
        """Test pipeline execution with direct career data input."""
        career_data = {
            "work_experience": [
                {
                    "job_title": "Data Scientist",
                    "company": "DataCorp",
                    "accomplishments": ["Built ML models with 95% accuracy"],
                    "responsibilities": ["Data analysis", "Model development"],
                    "skills_used": ["Python", "Machine Learning", "SQL"]
                }
            ],
            "projects": [
                {
                    "name": "Customer Churn Prediction",
                    "description": "Developed ML model to predict customer churn",
                    "technologies": ["Python", "scikit-learn"]
                }
            ],
            "skills_inventory": {
                "technical": ["Python", "Machine Learning", "SQL"],
                "soft_skills": ["Communication", "Problem Solving"],
                "languages": ["Python", "R"],
                "frameworks": ["scikit-learn", "pandas"]
            },
            "strategic_metadata": {
                "core_competencies": ["Data Science", "Machine Learning"],
                "job_title_variations": ["Data Scientist", "ML Engineer"]
            },
            "holistic_profile": {
                "career_aspirations": ["Senior Data Scientist", "ML Lead"],
                "motivators": ["Data insights", "Innovation"]
            }
        }

        results = await service_coordinator.execute_full_pipeline(
            session_id="test-session-123",
            career_data=career_data
        )

        assert results["pipeline_status"] == "completed"
        assert results["profile_data"] == career_data

    @pytest.mark.asyncio
    async def test_pipeline_failure_handling(self, service_coordinator, mock_profile_ingestor):
        """Test pipeline failure handling."""
        # Mock profile ingestor to fail
        mock_profile_ingestor.ingest_resume.return_value = {
            "success": False,
            "error": "Resume file not found"
        }

        with pytest.raises(ServiceCoordinationError) as exc_info:
            await service_coordinator.execute_full_pipeline(
                session_id="test-session-123",
                resume_path="/invalid/path.pdf"
            )

        assert "Profile ingestion failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_pipeline_status_tracking(self, service_coordinator, mock_session_manager):
        """Test pipeline status tracking."""
        # Get pipeline status
        status = await service_coordinator.get_pipeline_status("test-session-123")

        assert "session_id" in status
        assert "state" in status
        assert "current_step" in status
        assert "progress" in status
        assert status["progress"] == 1.0  # REVIEW step = 100%

    @pytest.mark.asyncio
    async def test_service_health_check(self, service_coordinator):
        """Test health check for all coordinated services."""
        health_status = await service_coordinator.health_check_all_services()

        assert "overall_status" in health_status
        assert "services" in health_status
        assert "timestamp" in health_status

        services = health_status["services"]
        assert "profile_ingestor" in services
        assert "strategist" in services
        assert "analyst" in services

        # All services should be healthy
        assert health_status["overall_status"] == "healthy"
        for service in services.values():
            assert service["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_service_health_check_degraded(self, service_coordinator, mock_strategist):
        """Test health check when one service is unhealthy."""
        # Mock strategist to be unhealthy
        mock_strategist.health_check.side_effect = Exception("Connection timeout")

        health_status = await service_coordinator.health_check_all_services()

        assert health_status["overall_status"] == "degraded"
        assert health_status["services"]["strategist"]["status"] == "unhealthy"
        assert "Connection timeout" in health_status["services"]["strategist"]["error"]

    def test_progress_calculation(self, service_coordinator):
        """Test progress calculation for different steps."""
        assert service_coordinator._calculate_progress(CurrentStep.START) == 0.0
        assert service_coordinator._calculate_progress(CurrentStep.INGEST) == 0.25
        assert service_coordinator._calculate_progress(CurrentStep.DISCOVER) == 0.5
        assert service_coordinator._calculate_progress(CurrentStep.ANALYZE) == 0.75
        assert service_coordinator._calculate_progress(CurrentStep.BUILD) == 0.9
        assert service_coordinator._calculate_progress(CurrentStep.REVIEW) == 1.0


class TestDataFlowValidation:
    """Test data flow through Master Career Database schema."""

    @pytest.mark.asyncio
    async def test_master_career_database_schema_validation(self, service_coordinator):
        """Test that data flows correctly through Master Career Database schema."""
        # Execute pipeline and validate schema compliance
        results = await service_coordinator.execute_full_pipeline(
            session_id="test-session-123",
            resume_path="/path/to/resume.pdf"
        )

        profile_data = results["profile_data"]

        # Validate required schema fields
        required_fields = ["work_experience", "projects", "skills_inventory"]
        for field in required_fields:
            assert field in profile_data, f"Missing required field: {field}"

        # Validate work experience structure
        if profile_data["work_experience"]:
            experience = profile_data["work_experience"][0]
            expected_exp_fields = ["job_title", "company", "duration", "accomplishments"]
            for field in expected_exp_fields:
                assert field in experience, f"Missing work experience field: {field}"

        # Validate skills inventory structure
        skills = profile_data["skills_inventory"]
        assert isinstance(skills, dict), "Skills inventory should be a dictionary"

        # Validate career strategies structure
        strategies = results["career_strategies"]
        assert "recommended_paths" in strategies
        if strategies["recommended_paths"]:
            path = strategies["recommended_paths"][0]
            expected_path_fields = ["path_id", "title", "fit_score", "transition_difficulty"]
            for field in expected_path_fields:
                assert field in path, f"Missing career path field: {field}"

        # Validate market analysis structure
        analysis = results["market_analysis"]
        expected_analysis_fields = ["market_demand", "skill_gaps", "resume_optimization"]
        for field in expected_analysis_fields:
            assert field in analysis, f"Missing analysis field: {field}"

    @pytest.mark.asyncio
    async def test_data_transformation_between_services(self, service_coordinator):
        """Test data transformation and compatibility between services."""
        results = await service_coordinator.execute_full_pipeline(
            session_id="test-session-123",
            resume_path="/path/to/resume.pdf"
        )

        # Verify that profile data from Profile Ingestor
        # is compatible with Strategist input format
        profile_data = results["profile_data"]
        assert "skills_inventory" in profile_data
        assert isinstance(profile_data["skills_inventory"], dict)

        # Verify that career strategies from Strategist
        # are compatible with Analyst input format
        strategies = results["career_strategies"]
        assert "recommended_paths" in strategies
        assert isinstance(strategies["recommended_paths"], list)

        # Verify final consolidated data structure
        assert results["pipeline_status"] == "completed"
        assert "timestamp" in results

        # All services should have contributed data
        assert len(results["profile_data"]) > 0
        assert len(results["career_strategies"]) > 0
        assert len(results["market_analysis"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
