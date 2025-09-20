"""
End-to-end integration tests for the complete Helios Career Operations System workflow.

This module tests the complete workflow from initial session creation through
profile ingestion, career path generation, and market analysis.
"""

import asyncio
import time
from typing import Any

import aiohttp
import pytest


@pytest.mark.asyncio
@pytest.mark.integration
class TestEndToEndWorkflow:
    """Test complete workflow from session start to final analysis."""

    async def test_complete_workflow_happy_path(
        self,
        http_session: aiohttp.ClientSession,
        sample_resume_data: dict[str, Any],
        sample_career_goals: dict[str, Any],
        clean_database,
        clean_redis,
        performance_thresholds: dict[str, float],
    ):
        """Test complete happy path workflow with real services."""
        workflow_start_time = time.time()

        # Step 1: Start session with orchestrator
        session_response = await self._start_session(http_session)
        assert session_response["status"] == "success"
        session_id = session_response["session_id"]

        # Step 2: Submit profile data to orchestrator
        profile_response = await self._submit_profile(
            http_session, session_id, sample_resume_data
        )
        assert profile_response["status"] == "success"
        profile_id = profile_response["profile_id"]

        # Step 3: Request career path generation
        career_paths_response = await self._generate_career_paths(
            http_session, session_id, profile_id, sample_career_goals
        )
        assert career_paths_response["status"] == "success"
        assert len(career_paths_response["career_paths"]) > 0

        # Step 4: Request market analysis
        market_analysis_response = await self._analyze_market(
            http_session, session_id, profile_id
        )
        assert market_analysis_response["status"] == "success"
        assert "market_analysis" in market_analysis_response
        assert "resume_optimization" in market_analysis_response

        # Step 5: Get final session status
        final_status = await self._get_session_status(http_session, session_id)
        assert final_status["status"] == "completed"
        assert final_status["workflow_progress"] == 100

        # Verify performance
        total_workflow_time = time.time() - workflow_start_time
        assert total_workflow_time < performance_thresholds["end_to_end_workflow_time"]

        # Verify data integrity across services
        await self._verify_data_integrity(
            http_session,
            session_id,
            profile_id,
            sample_resume_data,
            career_paths_response,
            market_analysis_response,
        )

    async def test_workflow_with_orchestrator_commands(
        self,
        http_session: aiohttp.ClientSession,
        orchestrator_commands: dict[str, Any],
        clean_database,
        clean_redis,
    ):
        """Test orchestrator command handling (START, STATUS, HELP)."""
        # Test START command
        start_cmd = orchestrator_commands["start_session"]
        start_response = await http_session.post(
            "http://localhost:8000/api/v1/command", json=start_cmd
        )
        assert start_response.status == 200
        start_data = await start_response.json()
        assert start_data["command"] == "START"
        session_id = start_data["session_id"]

        # Test STATUS command
        status_cmd = orchestrator_commands["status_check"]
        status_cmd["session_id"] = session_id
        status_response = await http_session.post(
            "http://localhost:8000/api/v1/command", json=status_cmd
        )
        assert status_response.status == 200
        status_data = await status_response.json()
        assert status_data["command"] == "STATUS"
        assert status_data["session_id"] == session_id

        # Test HELP command
        help_cmd = orchestrator_commands["help_request"]
        help_response = await http_session.post(
            "http://localhost:8000/api/v1/command", json=help_cmd
        )
        assert help_response.status == 200
        help_data = await help_response.json()
        assert help_data["command"] == "HELP"
        assert "help_content" in help_data

    async def test_service_communication_flow(
        self,
        http_session: aiohttp.ClientSession,
        sample_resume_data: dict[str, Any],
        clean_database,
        clean_redis,
    ):
        """Test communication flow between all services."""
        # Start session
        session_response = await self._start_session(http_session)
        session_id = session_response["session_id"]

        # Test orchestrator -> profile-ingestor communication
        profile_response = await http_session.post(
            "http://localhost:8000/api/v1/profile/process",
            json={"session_id": session_id, "resume_data": sample_resume_data},
        )
        assert profile_response.status == 200
        profile_data = await profile_response.json()
        profile_id = profile_data["profile_id"]

        # Verify profile-ingestor processed data
        ingestor_response = await http_session.get(
            f"http://localhost:8001/api/v1/profile/{profile_id}"
        )
        assert ingestor_response.status == 200

        # Test orchestrator -> strategist communication
        strategist_response = await http_session.post(
            "http://localhost:8000/api/v1/career-paths/generate",
            json={
                "session_id": session_id,
                "profile_id": profile_id,
                "career_goals": {"target_roles": ["Software Engineer"]},
            },
        )
        assert strategist_response.status == 200

        # Test orchestrator -> analyst communication
        analyst_response = await http_session.post(
            "http://localhost:8000/api/v1/analysis/market",
            json={"session_id": session_id, "profile_id": profile_id},
        )
        assert analyst_response.status == 200

    async def test_data_flow_validation(
        self,
        http_session: aiohttp.ClientSession,
        sample_resume_data: dict[str, Any],
        clean_database,
        clean_redis,
    ):
        """Test data consistency across service boundaries."""
        # Create profile and track data transformations
        session_response = await self._start_session(http_session)
        session_id = session_response["session_id"]

        # Submit original data
        profile_response = await self._submit_profile(
            http_session, session_id, sample_resume_data
        )
        profile_id = profile_response["profile_id"]

        # Verify profile-ingestor output format
        ingestor_data = await http_session.get(
            f"http://localhost:8001/api/v1/profile/{profile_id}/raw"
        )
        ingestor_json = await ingestor_data.json()

        # Validate required fields are present
        assert "work_experience" in ingestor_json
        assert "skills_inventory" in ingestor_json
        assert "strategic_metadata" in ingestor_json

        # Generate career paths and verify data usage
        career_response = await self._generate_career_paths(
            http_session, session_id, profile_id, {"target_roles": ["Senior Engineer"]}
        )

        # Verify strategist used profile data correctly
        assert len(career_response["career_paths"]) > 0
        for path in career_response["career_paths"]:
            assert "required_skills" in path
            assert "timeline_months" in path
            assert "probability" in path

        # Generate market analysis and verify data integration
        market_response = await self._analyze_market(
            http_session, session_id, profile_id
        )

        # Verify analyst integrated both profile and career data
        assert "market_analysis" in market_response
        assert "resume_optimization" in market_response
        assert market_response["resume_optimization"]["ats_score"] > 0

    # Helper methods
    async def _start_session(
        self, http_session: aiohttp.ClientSession
    ) -> dict[str, Any]:
        """Start a new session with the orchestrator."""
        response = await http_session.post(
            "http://localhost:8000/api/v1/session/start",
            json={
                "user_id": f"test-user-{int(time.time())}",
                "config": {"timeout_minutes": 60},
            },
        )
        assert response.status == 200
        return await response.json()

    async def _submit_profile(
        self,
        http_session: aiohttp.ClientSession,
        session_id: str,
        resume_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Submit profile data through orchestrator."""
        response = await http_session.post(
            "http://localhost:8000/api/v1/profile/process",
            json={"session_id": session_id, "resume_data": resume_data},
        )
        assert response.status == 200
        return await response.json()

    async def _generate_career_paths(
        self,
        http_session: aiohttp.ClientSession,
        session_id: str,
        profile_id: str,
        career_goals: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate career paths through orchestrator."""
        response = await http_session.post(
            "http://localhost:8000/api/v1/career-paths/generate",
            json={
                "session_id": session_id,
                "profile_id": profile_id,
                "career_goals": career_goals,
            },
        )
        assert response.status == 200
        return await response.json()

    async def _analyze_market(
        self, http_session: aiohttp.ClientSession, session_id: str, profile_id: str
    ) -> dict[str, Any]:
        """Analyze market through orchestrator."""
        response = await http_session.post(
            "http://localhost:8000/api/v1/analysis/market",
            json={"session_id": session_id, "profile_id": profile_id},
        )
        assert response.status == 200
        return await response.json()

    async def _get_session_status(
        self, http_session: aiohttp.ClientSession, session_id: str
    ) -> dict[str, Any]:
        """Get session status from orchestrator."""
        response = await http_session.get(
            f"http://localhost:8000/api/v1/session/{session_id}/status"
        )
        assert response.status == 200
        return await response.json()

    async def _verify_data_integrity(
        self,
        http_session: aiohttp.ClientSession,
        session_id: str,
        profile_id: str,
        original_data: dict[str, Any],
        career_data: dict[str, Any],
        market_data: dict[str, Any],
    ):
        """Verify data integrity across all services."""
        # Verify original skills are preserved and enhanced
        original_skills = set(
            original_data["skills_inventory"]["programming_languages"]
        )

        # Check career paths reference relevant skills
        career_skills = set()
        for path in career_data["career_paths"]:
            career_skills.update(path.get("required_skills", []))

        # Should have some overlap with original skills
        skill_overlap = original_skills.intersection(career_skills)
        assert (
            len(skill_overlap) > 0
        ), "No skill overlap between profile and career paths"

        # Verify market analysis is relevant to profile
        recommended_skills = set(market_data["market_analysis"]["recommended_skills"])
        assert len(recommended_skills) > 0, "No recommended skills in market analysis"

        # Verify session maintains consistent state
        session_status = await self._get_session_status(http_session, session_id)
        assert session_status["profile_id"] == profile_id
        assert len(session_status["workflow_history"]) >= 4  # At least 4 workflow steps


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.error_handling
class TestErrorHandlingWorkflows:
    """Test error handling across the complete workflow."""

    async def test_profile_ingestor_error_handling(
        self, http_session: aiohttp.ClientSession, clean_database, clean_redis
    ):
        """Test error handling when profile ingestor fails."""
        session_response = await http_session.post(
            "http://localhost:8000/api/v1/session/start",
            json={"user_id": "test-error-user"},
        )
        session_id = (await session_response.json())["session_id"]

        # Submit invalid resume data
        invalid_data = {"invalid": "data structure"}
        response = await http_session.post(
            "http://localhost:8000/api/v1/profile/process",
            json={"session_id": session_id, "resume_data": invalid_data},
        )

        # Should handle error gracefully
        assert response.status in [400, 422]
        error_data = await response.json()
        assert "error" in error_data or "detail" in error_data

    async def test_service_unavailable_handling(
        self, http_session: aiohttp.ClientSession, clean_database, clean_redis
    ):
        """Test handling when downstream services are unavailable."""
        # This test would require temporarily stopping services
        # For now, test timeout handling

        session_response = await http_session.post(
            "http://localhost:8000/api/v1/session/start",
            json={"user_id": "test-timeout-user"},
        )
        session_id = (await session_response.json())["session_id"]

        # Test with very short timeout
        try:
            response = await http_session.post(
                "http://localhost:8000/api/v1/career-paths/generate",
                json={
                    "session_id": session_id,
                    "profile_id": "non-existent",
                    "career_goals": {},
                },
                timeout=aiohttp.ClientTimeout(total=1),
            )
        except TimeoutError:
            # Expected for this test case
            pass

    async def test_data_validation_errors(
        self, http_session: aiohttp.ClientSession, clean_database, clean_redis
    ):
        """Test data validation error handling."""
        session_response = await http_session.post(
            "http://localhost:8000/api/v1/session/start",
            json={"user_id": "test-validation-user"},
        )
        session_id = (await session_response.json())["session_id"]

        # Test missing required fields
        incomplete_data = {
            "personal_info": {"name": "Test User"}
            # Missing work_experience, skills, etc.
        }

        response = await http_session.post(
            "http://localhost:8000/api/v1/profile/process",
            json={"session_id": session_id, "resume_data": incomplete_data},
        )

        # Should return validation error
        assert response.status in [400, 422]
        error_data = await response.json()
        assert (
            "validation" in str(error_data).lower()
            or "required" in str(error_data).lower()
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.performance
class TestPerformanceWorkflows:
    """Test performance characteristics of the complete workflow."""

    async def test_single_user_performance(
        self,
        http_session: aiohttp.ClientSession,
        sample_resume_data: dict[str, Any],
        performance_thresholds: dict[str, float],
        clean_database,
        clean_redis,
    ):
        """Test performance with single user workflow."""
        start_time = time.time()

        # Session creation performance
        session_start = time.time()
        session_response = await http_session.post(
            "http://localhost:8000/api/v1/session/start",
            json={"user_id": "perf-test-user"},
        )
        session_time = time.time() - session_start
        assert session_time < performance_thresholds["orchestrator_response_time"]

        session_id = (await session_response.json())["session_id"]

        # Profile processing performance
        profile_start = time.time()
        await http_session.post(
            "http://localhost:8000/api/v1/profile/process",
            json={"session_id": session_id, "resume_data": sample_resume_data},
        )
        profile_time = time.time() - profile_start
        assert profile_time < performance_thresholds["profile_processing_time"]

        total_time = time.time() - start_time
        assert total_time < performance_thresholds["end_to_end_workflow_time"]

    async def test_concurrent_users_performance(
        self,
        http_session: aiohttp.ClientSession,
        sample_resume_data: dict[str, Any],
        load_test_config: dict[str, Any],
        clean_database,
        clean_redis,
    ):
        """Test performance with multiple concurrent users."""
        concurrent_users = load_test_config["concurrent_users"]
        requests_per_user = load_test_config["requests_per_user"]

        async def user_workflow(user_id: int):
            """Simulate a single user workflow."""
            session_response = await http_session.post(
                "http://localhost:8000/api/v1/session/start",
                json={"user_id": f"load-test-user-{user_id}"},
            )
            session_data = await session_response.json()
            session_id = session_data["session_id"]

            for request_num in range(requests_per_user):
                await http_session.post(
                    "http://localhost:8000/api/v1/profile/process",
                    json={"session_id": session_id, "resume_data": sample_resume_data},
                )

        # Run concurrent user workflows
        start_time = time.time()
        tasks = [user_workflow(i) for i in range(concurrent_users)]
        await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time

        # Verify performance under load
        assert total_time < load_test_config["test_duration"]

        # Calculate throughput
        total_requests = concurrent_users * requests_per_user
        throughput = total_requests / total_time
        assert throughput > 1.0  # At least 1 request per second
