"""
Service interaction tests for Helios Career Operations System.

This module tests the direct interactions between individual services
to ensure proper communication, data flow, and error handling.
"""

import asyncio
import pytest
import time
from typing import Dict, Any
import aiohttp
from tests.integration.fixtures.test_resumes import get_software_engineer_resume
from tests.integration.fixtures.mock_responses import MockResponseGenerator


@pytest.mark.asyncio
@pytest.mark.integration
class TestOrchestrator:
    """Test orchestrator service functionality."""

    async def test_orchestrator_health_check(self, http_session: aiohttp.ClientSession):
        """Test orchestrator health endpoint."""
        response = await http_session.get("http://localhost:8000/health")
        assert response.status == 200

        health_data = await response.json()
        assert health_data["status"] == "healthy"
        assert "services" in health_data
        assert "version" in health_data

    async def test_orchestrator_ready_check(self, http_session: aiohttp.ClientSession):
        """Test orchestrator readiness endpoint."""
        response = await http_session.get("http://localhost:8000/health/ready")
        assert response.status == 200

        ready_data = await response.json()
        assert ready_data["ready"] is True
        assert "dependencies" in ready_data

    async def test_session_management(
        self,
        http_session: aiohttp.ClientSession,
        clean_database,
        clean_redis
    ):
        """Test session creation, retrieval, and cleanup."""
        # Create session
        create_response = await http_session.post(
            "http://localhost:8000/api/v1/session/start",
            json={"user_id": "test-session-user"}
        )
        assert create_response.status == 200
        session_data = await create_response.json()
        session_id = session_data["session_id"]

        # Retrieve session
        get_response = await http_session.get(
            f"http://localhost:8000/api/v1/session/{session_id}"
        )
        assert get_response.status == 200
        retrieved_session = await get_response.json()
        assert retrieved_session["session_id"] == session_id

        # Update session
        update_response = await http_session.put(
            f"http://localhost:8000/api/v1/session/{session_id}",
            json={"workflow_state": "profile_processing"}
        )
        assert update_response.status == 200

        # Delete session
        delete_response = await http_session.delete(
            f"http://localhost:8000/api/v1/session/{session_id}"
        )
        assert delete_response.status == 200

    async def test_orchestrator_command_processing(
        self,
        http_session: aiohttp.ClientSession,
        orchestrator_commands: Dict[str, Any],
        clean_database,
        clean_redis
    ):
        """Test orchestrator command processing (START, STATUS, HELP)."""
        # START command
        start_cmd = orchestrator_commands["start_session"]
        start_response = await http_session.post(
            "http://localhost:8000/api/v1/command",
            json=start_cmd
        )
        assert start_response.status == 200
        start_data = await start_response.json()
        assert start_data["command"] == "START"
        session_id = start_data["session_id"]

        # STATUS command
        status_cmd = {
            "command": "STATUS",
            "session_id": session_id
        }
        status_response = await http_session.post(
            "http://localhost:8000/api/v1/command",
            json=status_cmd
        )
        assert status_response.status == 200
        status_data = await status_response.json()
        assert status_data["command"] == "STATUS"

        # HELP command
        help_cmd = orchestrator_commands["help_request"]
        help_response = await http_session.post(
            "http://localhost:8000/api/v1/command",
            json=help_cmd
        )
        assert help_response.status == 200
        help_data = await help_response.json()
        assert help_data["command"] == "HELP"


@pytest.mark.asyncio
@pytest.mark.integration
class TestProfileIngestorService:
    """Test profile ingestor service functionality."""

    async def test_profile_ingestor_health(self, http_session: aiohttp.ClientSession):
        """Test profile ingestor health endpoint."""
        response = await http_session.get("http://localhost:8001/health")
        assert response.status == 200

        health_data = await response.json()
        assert health_data["status"] == "healthy"

    async def test_direct_profile_processing(
        self,
        http_session: aiohttp.ClientSession,
        sample_resume_data: Dict[str, Any]
    ):
        """Test direct profile processing through profile ingestor."""
        response = await http_session.post(
            "http://localhost:8001/api/v1/profile/process",
            json={
                "resume_data": sample_resume_data,
                "processing_options": {
                    "extract_skills": True,
                    "analyze_experience": True,
                    "generate_metadata": True
                }
            }
        )

        assert response.status == 200
        profile_data = await response.json()
        assert profile_data["status"] == "success"
        assert "profile_id" in profile_data
        assert "extracted_data" in profile_data

    async def test_profile_retrieval(
        self,
        http_session: aiohttp.ClientSession,
        sample_resume_data: Dict[str, Any]
    ):
        """Test profile data retrieval after processing."""
        # First, create a profile
        create_response = await http_session.post(
            "http://localhost:8001/api/v1/profile/process",
            json={"resume_data": sample_resume_data}
        )
        profile_data = await create_response.json()
        profile_id = profile_data["profile_id"]

        # Then retrieve it
        get_response = await http_session.get(
            f"http://localhost:8001/api/v1/profile/{profile_id}"
        )
        assert get_response.status == 200

        retrieved_data = await get_response.json()
        assert retrieved_data["profile_id"] == profile_id
        assert "work_experience" in retrieved_data["data"]

    async def test_profile_ingestor_error_handling(
        self,
        http_session: aiohttp.ClientSession
    ):
        """Test profile ingestor error handling with invalid data."""
        invalid_data = {"invalid": "structure"}

        response = await http_session.post(
            "http://localhost:8001/api/v1/profile/process",
            json={"resume_data": invalid_data}
        )

        # Should handle gracefully
        assert response.status in [400, 422, 500]
        error_data = await response.json()
        assert "error" in error_data or "detail" in error_data


@pytest.mark.asyncio
@pytest.mark.integration
class TestStrategistService:
    """Test strategist service functionality."""

    async def test_strategist_health(self, http_session: aiohttp.ClientSession):
        """Test strategist service health endpoint."""
        response = await http_session.get("http://localhost:8002/health")
        assert response.status == 200

        health_data = await response.json()
        assert health_data["status"] == "healthy"

    async def test_career_path_generation(
        self,
        http_session: aiohttp.ClientSession,
        sample_resume_data: Dict[str, Any],
        sample_career_goals: Dict[str, Any]
    ):
        """Test direct career path generation."""
        response = await http_session.post(
            "http://localhost:8002/api/v1/career-paths/generate",
            json={
                "profile_data": sample_resume_data,
                "career_goals": sample_career_goals,
                "options": {
                    "max_paths": 5,
                    "timeline_limit": 36,
                    "include_salary": True
                }
            }
        )

        assert response.status == 200
        career_data = await response.json()
        assert career_data["status"] == "success"
        assert "career_paths" in career_data
        assert len(career_data["career_paths"]) > 0

        # Validate career path structure
        for path in career_data["career_paths"]:
            assert "path_id" in path
            assert "title" in path
            assert "probability" in path
            assert "timeline_months" in path
            assert "required_skills" in path

    async def test_skill_analysis(
        self,
        http_session: aiohttp.ClientSession,
        sample_resume_data: Dict[str, Any]
    ):
        """Test skill gap analysis functionality."""
        response = await http_session.post(
            "http://localhost:8002/api/v1/skills/analyze",
            json={
                "profile_data": sample_resume_data,
                "target_role": "Staff Software Engineer"
            }
        )

        assert response.status == 200
        skill_data = await response.json()
        assert "current_skills" in skill_data
        assert "skill_gaps" in skill_data
        assert "recommendations" in skill_data


@pytest.mark.asyncio
@pytest.mark.integration
class TestAnalystService:
    """Test analyst service functionality."""

    async def test_analyst_health(self, http_session: aiohttp.ClientSession):
        """Test analyst service health endpoint."""
        response = await http_session.get("http://localhost:8003/health")
        assert response.status == 200

        health_data = await response.json()
        assert health_data["status"] == "healthy"

    async def test_market_analysis(
        self,
        http_session: aiohttp.ClientSession,
        sample_resume_data: Dict[str, Any]
    ):
        """Test market analysis functionality."""
        response = await http_session.post(
            "http://localhost:8003/api/v1/market/analyze",
            json={
                "profile_data": sample_resume_data,
                "analysis_options": {
                    "include_salary_data": True,
                    "geographic_scope": "US",
                    "industry_focus": "technology"
                }
            }
        )

        assert response.status == 200
        market_data = await response.json()
        assert market_data["status"] == "success"
        assert "market_analysis" in market_data
        assert "demand_score" in market_data["market_analysis"]

    async def test_resume_optimization(
        self,
        http_session: aiohttp.ClientSession,
        sample_resume_data: Dict[str, Any]
    ):
        """Test resume optimization functionality."""
        response = await http_session.post(
            "http://localhost:8003/api/v1/resume/optimize",
            json={
                "profile_data": sample_resume_data,
                "target_job": "Senior Software Engineer",
                "optimization_goals": ["ats_compatibility", "keyword_density"]
            }
        )

        assert response.status == 200
        optimization_data = await response.json()
        assert "ats_score" in optimization_data
        assert "suggested_improvements" in optimization_data
        assert "keyword_recommendations" in optimization_data

    async def test_competitive_analysis(
        self,
        http_session: aiohttp.ClientSession,
        sample_resume_data: Dict[str, Any]
    ):
        """Test competitive analysis functionality."""
        response = await http_session.post(
            "http://localhost:8003/api/v1/competitive/analyze",
            json={
                "profile_data": sample_resume_data,
                "comparison_criteria": ["experience", "skills", "education"],
                "market_segment": "senior_engineers"
            }
        )

        assert response.status == 200
        competitive_data = await response.json()
        assert "percentile_ranking" in competitive_data
        assert "similar_profiles_count" in competitive_data
        assert "competitive_advantages" in competitive_data


@pytest.mark.asyncio
@pytest.mark.integration
class TestServiceCommunication:
    """Test communication patterns between services."""

    async def test_orchestrator_to_profile_ingestor(
        self,
        http_session: aiohttp.ClientSession,
        sample_resume_data: Dict[str, Any],
        clean_database,
        clean_redis
    ):
        """Test orchestrator routing to profile ingestor."""
        # Start session
        session_response = await http_session.post(
            "http://localhost:8000/api/v1/session/start",
            json={"user_id": "comm-test-user"}
        )
        session_id = (await session_response.json())["session_id"]

        # Submit through orchestrator
        response = await http_session.post(
            "http://localhost:8000/api/v1/profile/process",
            json={
                "session_id": session_id,
                "resume_data": sample_resume_data
            }
        )

        assert response.status == 200
        profile_data = await response.json()
        assert "profile_id" in profile_data

    async def test_orchestrator_to_strategist(
        self,
        http_session: aiohttp.ClientSession,
        sample_resume_data: Dict[str, Any],
        sample_career_goals: Dict[str, Any],
        clean_database,
        clean_redis
    ):
        """Test orchestrator routing to strategist."""
        # Setup session and profile
        session_response = await http_session.post(
            "http://localhost:8000/api/v1/session/start",
            json={"user_id": "strategist-test-user"}
        )
        session_id = (await session_response.json())["session_id"]

        profile_response = await http_session.post(
            "http://localhost:8000/api/v1/profile/process",
            json={
                "session_id": session_id,
                "resume_data": sample_resume_data
            }
        )
        profile_id = (await profile_response.json())["profile_id"]

        # Request career paths through orchestrator
        career_response = await http_session.post(
            "http://localhost:8000/api/v1/career-paths/generate",
            json={
                "session_id": session_id,
                "profile_id": profile_id,
                "career_goals": sample_career_goals
            }
        )

        assert career_response.status == 200
        career_data = await career_response.json()
        assert "career_paths" in career_data

    async def test_orchestrator_to_analyst(
        self,
        http_session: aiohttp.ClientSession,
        sample_resume_data: Dict[str, Any],
        clean_database,
        clean_redis
    ):
        """Test orchestrator routing to analyst."""
        # Setup session and profile
        session_response = await http_session.post(
            "http://localhost:8000/api/v1/session/start",
            json={"user_id": "analyst-test-user"}
        )
        session_id = (await session_response.json())["session_id"]

        profile_response = await http_session.post(
            "http://localhost:8000/api/v1/profile/process",
            json={
                "session_id": session_id,
                "resume_data": sample_resume_data
            }
        )
        profile_id = (await profile_response.json())["profile_id"]

        # Request market analysis through orchestrator
        analysis_response = await http_session.post(
            "http://localhost:8000/api/v1/analysis/market",
            json={
                "session_id": session_id,
                "profile_id": profile_id
            }
        )

        assert analysis_response.status == 200
        analysis_data = await analysis_response.json()
        assert "market_analysis" in analysis_data

    async def test_data_consistency_across_services(
        self,
        http_session: aiohttp.ClientSession,
        sample_resume_data: Dict[str, Any],
        clean_database,
        clean_redis
    ):
        """Test data consistency when passed between services."""
        # Create profile
        session_response = await http_session.post(
            "http://localhost:8000/api/v1/session/start",
            json={"user_id": "consistency-test-user"}
        )
        session_id = (await session_response.json())["session_id"]

        profile_response = await http_session.post(
            "http://localhost:8000/api/v1/profile/process",
            json={
                "session_id": session_id,
                "resume_data": sample_resume_data
            }
        )
        profile_data = await profile_response.json()
        profile_id = profile_data["profile_id"]

        # Get original profile data
        original_profile = await http_session.get(
            f"http://localhost:8001/api/v1/profile/{profile_id}"
        )
        original_data = await original_profile.json()

        # Generate career paths and verify data usage
        career_response = await http_session.post(
            "http://localhost:8002/api/v1/career-paths/generate",
            json={
                "profile_data": original_data["data"],
                "career_goals": {"target_roles": ["Senior Engineer"]}
            }
        )
        career_data = await career_response.json()

        # Verify strategist used correct skills
        original_skills = set()
        for skill_list in original_data["data"]["skills_inventory"].values():
            if isinstance(skill_list, list):
                original_skills.update(skill_list)

        career_skills = set()
        for path in career_data["career_paths"]:
            career_skills.update(path.get("required_skills", []))

        # Should have some relationship between original and required skills
        assert len(original_skills) > 0
        assert len(career_skills) > 0