"""
Data validation integration tests for Helios Career Operations System.

This module tests data validation, transformation, and integrity
across service boundaries and workflow stages.
"""

import pytest
import time
from typing import Dict, Any, List
import aiohttp
from tests.integration.fixtures.test_resumes import (
    get_software_engineer_resume,
    get_data_scientist_resume,
    get_product_manager_resume,
    get_invalid_resume_data
)


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.data_validation
class TestDataValidation:
    """Test data validation across the complete workflow."""

    async def test_valid_profile_data_processing(
        self,
        http_session: aiohttp.ClientSession,
        clean_database,
        clean_redis
    ):
        """Test processing of valid profile data through all services."""
        valid_resumes = [
            get_software_engineer_resume(),
            get_data_scientist_resume(),
            get_product_manager_resume()
        ]

        for resume_data in valid_resumes:
            # Start session
            session_response = await http_session.post(
                "http://localhost:8000/api/v1/session/start",
                json={"user_id": f"validation-user-{int(time.time())}"}
            )
            session_id = (await session_response.json())["session_id"]

            # Process profile
            profile_response = await http_session.post(
                "http://localhost:8000/api/v1/profile/process",
                json={
                    "session_id": session_id,
                    "resume_data": resume_data
                }
            )

            assert profile_response.status == 200
            profile_data = await profile_response.json()

            # Validate response structure
            assert "profile_id" in profile_data
            assert "status" in profile_data
            assert profile_data["status"] == "success"

            # Validate extracted data completeness
            if "extracted_data" in profile_data:
                extracted = profile_data["extracted_data"]
                assert "personal_info" in extracted
                assert "work_experience" in extracted
                assert "skills_inventory" in extracted

                # Validate personal info was preserved
                original_name = resume_data["personal_info"]["name"]
                extracted_name = extracted["personal_info"]["name"]
                assert original_name == extracted_name

    async def test_invalid_profile_data_handling(
        self,
        http_session: aiohttp.ClientSession,
        clean_database,
        clean_redis
    ):
        """Test handling of invalid profile data."""
        invalid_data_sets = get_invalid_resume_data()

        for invalid_data in invalid_data_sets:
            # Start session
            session_response = await http_session.post(
                "http://localhost:8000/api/v1/session/start",
                json={"user_id": f"invalid-user-{int(time.time())}"}
            )
            session_id = (await session_response.json())["session_id"]

            # Submit invalid data
            profile_response = await http_session.post(
                "http://localhost:8000/api/v1/profile/process",
                json={
                    "session_id": session_id,
                    "resume_data": invalid_data
                }
            )

            # Should handle gracefully with error status
            assert profile_response.status in [400, 422, 500]
            error_data = await profile_response.json()

            # Verify error structure
            assert "error" in error_data or "detail" in error_data
            if "error" in error_data:
                assert isinstance(error_data["error"], str)

    async def test_data_schema_validation(
        self,
        http_session: aiohttp.ClientSession,
        sample_resume_data: Dict[str, Any],
        clean_database,
        clean_redis
    ):
        """Test that data maintains correct schema through transformations."""
        # Start session and process profile
        session_response = await http_session.post(
            "http://localhost:8000/api/v1/session/start",
            json={"user_id": "schema-test-user"}
        )
        session_id = (await session_response.json())["session_id"]

        profile_response = await http_session.post(
            "http://localhost:8000/api/v1/profile/process",
            json={
                "session_id": session_id,
                "resume_data": sample_resume_data
            }
        )

        assert profile_response.status == 200
        profile_data = await profile_response.json()
        profile_id = profile_data["profile_id"]

        # Get profile data directly from service
        direct_profile = await http_session.get(
            f"http://localhost:8001/api/v1/profile/{profile_id}"
        )
        assert direct_profile.status == 200
        profile_content = await direct_profile.json()

        # Validate schema compliance
        self._validate_profile_schema(profile_content)

        # Generate career paths and validate schema
        career_response = await http_session.post(
            "http://localhost:8000/api/v1/career-paths/generate",
            json={
                "session_id": session_id,
                "profile_id": profile_id,
                "career_goals": {"target_roles": ["Senior Engineer"]}
            }
        )

        assert career_response.status == 200
        career_data = await career_response.json()
        self._validate_career_paths_schema(career_data)

        # Generate market analysis and validate schema
        market_response = await http_session.post(
            "http://localhost:8000/api/v1/analysis/market",
            json={
                "session_id": session_id,
                "profile_id": profile_id
            }
        )

        assert market_response.status == 200
        market_data = await market_response.json()
        self._validate_market_analysis_schema(market_data)

    async def test_data_integrity_across_services(
        self,
        http_session: aiohttp.ClientSession,
        sample_resume_data: Dict[str, Any],
        clean_database,
        clean_redis
    ):
        """Test data integrity is maintained across service calls."""
        # Process profile and track data at each stage
        session_response = await http_session.post(
            "http://localhost:8000/api/v1/session/start",
            json={"user_id": "integrity-test-user"}
        )
        session_id = (await session_response.json())["session_id"]

        # Stage 1: Profile processing
        profile_response = await http_session.post(
            "http://localhost:8000/api/v1/profile/process",
            json={
                "session_id": session_id,
                "resume_data": sample_resume_data
            }
        )
        profile_data = await profile_response.json()
        profile_id = profile_data["profile_id"]

        # Verify core data preservation
        original_name = sample_resume_data["personal_info"]["name"]
        original_email = sample_resume_data["personal_info"]["email"]
        original_skills = sample_resume_data["skills_inventory"]["programming_languages"]

        # Get processed profile
        processed_profile = await http_session.get(
            f"http://localhost:8001/api/v1/profile/{profile_id}"
        )
        processed_data = await processed_profile.json()

        # Verify critical data wasn't corrupted
        assert processed_data["data"]["personal_info"]["name"] == original_name
        assert processed_data["data"]["personal_info"]["email"] == original_email

        # Skills should be preserved (possibly enhanced)
        processed_skills = processed_data["data"]["skills_inventory"]["programming_languages"]
        for skill in original_skills:
            assert skill in processed_skills, f"Original skill '{skill}' was lost during processing"

        # Stage 2: Career path generation
        career_response = await http_session.post(
            "http://localhost:8000/api/v1/career-paths/generate",
            json={
                "session_id": session_id,
                "profile_id": profile_id,
                "career_goals": {"target_roles": ["Senior Software Engineer"]}
            }
        )
        career_data = await career_response.json()

        # Verify career paths reference relevant skills from profile
        career_skills = set()
        for path in career_data["career_paths"]:
            career_skills.update(path.get("required_skills", []))

        # Should have some connection to original skills
        original_skill_set = set(original_skills)
        assert len(career_skills) > 0, "No skills found in career paths"

        # Stage 3: Market analysis
        market_response = await http_session.post(
            "http://localhost:8000/api/v1/analysis/market",
            json={
                "session_id": session_id,
                "profile_id": profile_id
            }
        )
        market_data = await market_response.json()

        # Verify market analysis is relevant to profile
        if "recommended_skills" in market_data.get("market_analysis", {}):
            recommended_skills = set(market_data["market_analysis"]["recommended_skills"])
            assert len(recommended_skills) > 0, "No recommended skills in market analysis"

        # Verify resume optimization references original data
        if "resume_optimization" in market_data:
            ats_score = market_data["resume_optimization"].get("ats_score", 0)
            assert ats_score > 0, "ATS score should be positive"

    async def test_concurrent_data_processing(
        self,
        http_session: aiohttp.ClientSession,
        clean_database,
        clean_redis
    ):
        """Test data integrity with concurrent requests."""
        import asyncio

        async def process_user_profile(user_id: int):
            """Process a single user profile."""
            resume_data = get_software_engineer_resume()
            resume_data["personal_info"]["name"] = f"Test User {user_id}"
            resume_data["personal_info"]["email"] = f"user{user_id}@example.com"

            # Create session
            session_response = await http_session.post(
                "http://localhost:8000/api/v1/session/start",
                json={"user_id": f"concurrent-user-{user_id}"}
            )
            session_data = await session_response.json()
            session_id = session_data["session_id"]

            # Process profile
            profile_response = await http_session.post(
                "http://localhost:8000/api/v1/profile/process",
                json={
                    "session_id": session_id,
                    "resume_data": resume_data
                }
            )

            assert profile_response.status == 200
            profile_data = await profile_response.json()

            # Verify user-specific data wasn't mixed up
            if "extracted_data" in profile_data:
                extracted_name = profile_data["extracted_data"]["personal_info"]["name"]
                assert extracted_name == f"Test User {user_id}", f"Data mixing detected for user {user_id}"

            return profile_data

        # Process multiple users concurrently
        concurrent_users = 5
        tasks = [process_user_profile(i) for i in range(concurrent_users)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Verify all succeeded and data wasn't mixed
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) == concurrent_users, "Some concurrent requests failed"

    def _validate_profile_schema(self, profile_data: Dict[str, Any]):
        """Validate profile data schema."""
        assert "profile_id" in profile_data
        assert "data" in profile_data

        data = profile_data["data"]
        assert "personal_info" in data
        assert "work_experience" in data
        assert "skills_inventory" in data

        # Validate personal info
        personal_info = data["personal_info"]
        assert "name" in personal_info
        assert "email" in personal_info

        # Validate work experience
        work_exp = data["work_experience"]
        assert isinstance(work_exp, list)
        for exp in work_exp:
            assert "company" in exp
            assert "position" in exp
            assert "start_date" in exp

        # Validate skills inventory
        skills = data["skills_inventory"]
        assert isinstance(skills, dict)
        for skill_category in skills.values():
            assert isinstance(skill_category, list)

    def _validate_career_paths_schema(self, career_data: Dict[str, Any]):
        """Validate career paths data schema."""
        assert "status" in career_data
        assert "career_paths" in career_data

        paths = career_data["career_paths"]
        assert isinstance(paths, list)
        assert len(paths) > 0

        for path in paths:
            assert "path_id" in path
            assert "title" in path
            assert "probability" in path
            assert "timeline_months" in path
            assert isinstance(path["probability"], (int, float))
            assert isinstance(path["timeline_months"], int)
            assert 0 <= path["probability"] <= 1

    def _validate_market_analysis_schema(self, market_data: Dict[str, Any]):
        """Validate market analysis data schema."""
        assert "status" in market_data

        if "market_analysis" in market_data:
            analysis = market_data["market_analysis"]
            assert "demand_score" in analysis
            assert isinstance(analysis["demand_score"], (int, float))
            assert 0 <= analysis["demand_score"] <= 1

        if "resume_optimization" in market_data:
            optimization = market_data["resume_optimization"]
            assert "ats_score" in optimization
            assert isinstance(optimization["ats_score"], (int, float))
            assert optimization["ats_score"] >= 0


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.data_validation
class TestDataTransformations:
    """Test data transformations between services."""

    async def test_profile_to_career_data_transformation(
        self,
        http_session: aiohttp.ClientSession,
        sample_resume_data: Dict[str, Any],
        clean_database,
        clean_redis
    ):
        """Test data transformation from profile to career analysis."""
        # Create profile
        session_response = await http_session.post(
            "http://localhost:8000/api/v1/session/start",
            json={"user_id": "transform-test-user"}
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

        # Get detailed profile data
        detailed_profile = await http_session.get(
            f"http://localhost:8001/api/v1/profile/{profile_id}"
        )
        detailed_data = await detailed_profile.json()

        # Generate career paths
        career_response = await http_session.post(
            "http://localhost:8000/api/v1/career-paths/generate",
            json={
                "session_id": session_id,
                "profile_id": profile_id,
                "career_goals": {"target_roles": ["Senior Software Engineer"]}
            }
        )
        career_data = await career_response.json()

        # Verify transformation logic
        original_experience = detailed_data["data"]["work_experience"]
        career_paths = career_data["career_paths"]

        # Career paths should reflect experience level
        total_experience_years = len(original_experience) * 2  # Rough estimate

        for path in career_paths:
            timeline_months = path["timeline_months"]

            # More experienced candidates should have shorter timelines to senior roles
            if total_experience_years >= 5:
                assert timeline_months <= 24, "Experienced candidates should have shorter progression timelines"

            # Required skills should build on existing skills
            existing_skills = set()
            for skill_list in detailed_data["data"]["skills_inventory"].values():
                if isinstance(skill_list, list):
                    existing_skills.update(skill_list)

            required_skills = set(path.get("required_skills", []))
            # Some overlap expected but not required (could be growth areas)
            assert len(required_skills) > 0, "Career path should specify required skills"

    async def test_profile_to_market_data_transformation(
        self,
        http_session: aiohttp.ClientSession,
        sample_resume_data: Dict[str, Any],
        clean_database,
        clean_redis
    ):
        """Test data transformation from profile to market analysis."""
        # Create and process profile
        session_response = await http_session.post(
            "http://localhost:8000/api/v1/session/start",
            json={"user_id": "market-transform-user"}
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

        # Generate market analysis
        market_response = await http_session.post(
            "http://localhost:8000/api/v1/analysis/market",
            json={
                "session_id": session_id,
                "profile_id": profile_id
            }
        )
        market_data = await market_response.json()

        # Verify market analysis reflects profile characteristics
        if "market_analysis" in market_data:
            analysis = market_data["market_analysis"]

            # Demand score should be reasonable for software engineers
            demand_score = analysis.get("demand_score", 0)
            assert 0.5 <= demand_score <= 1.0, "Software engineers should have good market demand"

            # Recommended skills should be relevant
            if "recommended_skills" in analysis:
                recommended = analysis["recommended_skills"]
                tech_skills = {"Python", "JavaScript", "Java", "AWS", "Docker", "Kubernetes", "React"}
                recommended_set = set(recommended)

                # Should recommend at least some tech skills
                overlap = tech_skills.intersection(recommended_set)
                assert len(overlap) > 0, "Should recommend relevant tech skills"

        # Verify resume optimization is profile-specific
        if "resume_optimization" in market_data:
            optimization = market_data["resume_optimization"]

            # ATS score should be reasonable for a structured resume
            ats_score = optimization.get("ats_score", 0)
            assert ats_score > 50, "Well-structured resume should have decent ATS score"

            # Should have specific suggestions
            improvements = optimization.get("suggested_improvements", [])
            assert len(improvements) > 0, "Should provide specific improvement suggestions"