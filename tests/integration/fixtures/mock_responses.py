"""
Mock API responses for integration testing.

This module provides standardized mock responses for all Helios services
to enable testing of integration workflows without external dependencies.
"""

import time
import uuid
from typing import Any


class MockResponseGenerator:
    """Generate consistent mock responses for testing."""

    @staticmethod
    def profile_ingestor_success_response(
        profile_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate successful profile ingestor response."""
        profile_id = str(uuid.uuid4())
        return {
            "status": "success",
            "profile_id": profile_id,
            "processing_time": 2.3,
            "data": {
                "skills_extracted": len(
                    profile_data.get("skills_inventory", {}).get(
                        "programming_languages", []
                    )
                ),
                "experience_years": MockResponseGenerator._calculate_experience_years(
                    profile_data
                ),
                "education_level": MockResponseGenerator._determine_education_level(
                    profile_data
                ),
                "work_experience_count": len(profile_data.get("work_experience", [])),
                "projects_count": len(profile_data.get("projects", [])),
                "certifications_count": len(profile_data.get("certifications", [])),
                "completeness_score": 0.95,
                "ats_compatibility": 0.87,
            },
            "extracted_data": {
                "personal_info": profile_data.get("personal_info", {}),
                "work_experience": profile_data.get("work_experience", []),
                "projects": profile_data.get("projects", []),
                "skills_inventory": profile_data.get("skills_inventory", {}),
                "education": profile_data.get("education", []),
                "certifications": profile_data.get("certifications", []),
            },
            "metadata": {
                "processing_timestamp": time.time(),
                "version": "1.0.0",
                "extraction_method": "nlp_enhanced",
            },
        }

    @staticmethod
    def profile_ingestor_error_response(
        error_type: str = "parsing_failed",
    ) -> dict[str, Any]:
        """Generate error response from profile ingestor."""
        error_responses = {
            "parsing_failed": {
                "status": "error",
                "error_code": "PARSING_FAILED",
                "message": "Unable to extract meaningful data from resume",
                "details": "Insufficient structured content found in uploaded document",
            },
            "invalid_format": {
                "status": "error",
                "error_code": "INVALID_FORMAT",
                "message": "Unsupported file format",
                "details": "Only PDF, DOCX, TXT, and JSON formats are supported",
            },
            "processing_timeout": {
                "status": "error",
                "error_code": "PROCESSING_TIMEOUT",
                "message": "Document processing timed out",
                "details": "Document too large or complex for processing within time limit",
            },
        }
        return error_responses.get(error_type, error_responses["parsing_failed"])

    @staticmethod
    def strategist_success_response(
        profile_data: dict[str, Any], career_goals: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate successful strategist response."""
        skills = profile_data.get("skills_inventory", {})
        experience_years = MockResponseGenerator._calculate_experience_years(
            profile_data
        )

        career_paths = MockResponseGenerator._generate_career_paths(
            skills, experience_years, career_goals
        )

        return {
            "status": "success",
            "career_paths": career_paths,
            "analysis": {
                "current_level": MockResponseGenerator._determine_current_level(
                    experience_years
                ),
                "skill_gaps": MockResponseGenerator._identify_skill_gaps(
                    skills, career_goals
                ),
                "market_alignment": 0.82,
                "growth_potential": 0.78,
            },
            "recommendations": {
                "priority_skills": [
                    "System Design",
                    "Leadership",
                    "Cloud Architecture",
                ],
                "learning_path": "Focus on distributed systems and team leadership",
                "timeline_estimate": "12-18 months for next level progression",
            },
            "processing_time": 1.8,
            "metadata": {
                "model_version": "2.1.0",
                "confidence_threshold": 0.75,
                "paths_generated": len(career_paths),
            },
        }

    @staticmethod
    def strategist_error_response(
        error_type: str = "insufficient_data",
    ) -> dict[str, Any]:
        """Generate error response from strategist."""
        error_responses = {
            "insufficient_data": {
                "status": "error",
                "error_code": "INSUFFICIENT_DATA",
                "message": "Profile lacks sufficient experience data for path generation",
                "details": "Minimum 1 year of work experience required for career path analysis",
            },
            "model_unavailable": {
                "status": "error",
                "error_code": "MODEL_UNAVAILABLE",
                "message": "Career prediction model temporarily unavailable",
                "details": "ML model is being updated, please try again later",
            },
            "invalid_goals": {
                "status": "error",
                "error_code": "INVALID_CAREER_GOALS",
                "message": "Career goals are too vague or unrealistic",
                "details": "Please provide more specific target roles and timeline",
            },
        }
        return error_responses.get(error_type, error_responses["insufficient_data"])

    @staticmethod
    def analyst_success_response(profile_data: dict[str, Any]) -> dict[str, Any]:
        """Generate successful analyst response."""
        skills = profile_data.get("skills_inventory", {})

        return {
            "status": "success",
            "market_analysis": {
                "demand_score": 0.89,
                "competition_level": "moderate",
                "salary_trends": "increasing",
                "growth_outlook": "strong",
                "hot_skills": [
                    "Kubernetes",
                    "Machine Learning",
                    "System Design",
                    "TypeScript",
                ],
                "market_size": {
                    "total_jobs": 45000,
                    "matching_profile": 12500,
                    "growth_rate": 0.15,
                },
                "geographic_insights": {
                    "top_locations": ["San Francisco", "Seattle", "New York", "Austin"],
                    "remote_availability": 0.65,
                    "relocation_likelihood": 0.45,
                },
            },
            "resume_optimization": {
                "ats_score": 78,
                "keyword_density": 0.15,
                "improvement_areas": [
                    "Add more quantified achievements",
                    "Include industry-specific keywords",
                    "Optimize section ordering",
                    "Enhance technical skills presentation",
                ],
                "suggested_keywords": [
                    "microservices",
                    "cloud-native",
                    "DevOps",
                    "API design",
                ],
                "competitiveness_score": 0.84,
                "recommendations": {
                    "title_optimization": "Consider 'Senior Software Engineer' or 'Technical Lead'",
                    "skills_to_highlight": ["Python", "AWS", "Docker", "React"],
                    "experience_focus": "Emphasize scalability and team leadership experience",
                },
            },
            "competitive_analysis": {
                "percentile_ranking": 75,
                "similar_profiles": 1250,
                "success_factors": [
                    "Strong technical depth",
                    "Leadership experience",
                    "Cloud expertise",
                    "Open source contributions",
                ],
            },
            "processing_time": 3.2,
            "metadata": {
                "analysis_date": time.time(),
                "data_sources": ["job_boards", "salary_surveys", "market_reports"],
                "confidence_level": 0.87,
            },
        }

    @staticmethod
    def analyst_error_response(
        error_type: str = "market_data_unavailable",
    ) -> dict[str, Any]:
        """Generate error response from analyst."""
        error_responses = {
            "market_data_unavailable": {
                "status": "error",
                "error_code": "MARKET_DATA_UNAVAILABLE",
                "message": "Market analysis temporarily unavailable",
                "details": "External data sources are currently unreachable",
            },
            "profile_incomplete": {
                "status": "error",
                "error_code": "PROFILE_INCOMPLETE",
                "message": "Profile lacks sufficient data for market analysis",
                "details": "Work experience and skills data required for meaningful analysis",
            },
            "analysis_failed": {
                "status": "error",
                "error_code": "ANALYSIS_FAILED",
                "message": "Market analysis processing failed",
                "details": "Internal error during competitive analysis computation",
            },
        }
        return error_responses.get(
            error_type, error_responses["market_data_unavailable"]
        )

    @staticmethod
    def orchestrator_session_response(user_id: str) -> dict[str, Any]:
        """Generate orchestrator session start response."""
        session_id = str(uuid.uuid4())
        return {
            "status": "success",
            "session_id": session_id,
            "user_id": user_id,
            "created_at": time.time(),
            "expires_at": time.time() + 3600,  # 1 hour
            "workflow_state": "initialized",
            "services_available": ["profile-ingestor", "strategist", "analyst"],
            "configuration": {
                "timeout_minutes": 60,
                "language": "en",
                "version": "1.0.0",
            },
        }

    @staticmethod
    def orchestrator_status_response(
        session_id: str, workflow_progress: int = 0
    ) -> dict[str, Any]:
        """Generate orchestrator status response."""
        stages = [
            "profile_ingestion",
            "career_analysis",
            "market_analysis",
            "recommendations",
        ]
        completed_stages = (
            stages[: workflow_progress // 25] if workflow_progress > 0 else []
        )

        return {
            "status": "active" if workflow_progress < 100 else "completed",
            "session_id": session_id,
            "workflow_progress": workflow_progress,
            "current_stage": (
                stages[len(completed_stages)]
                if len(completed_stages) < len(stages)
                else "completed"
            ),
            "completed_stages": completed_stages,
            "services_status": {
                "profile-ingestor": "healthy",
                "strategist": "healthy",
                "analyst": "healthy",
            },
            "processing_times": {
                "total_elapsed": 45.2,
                "profile_processing": 12.3,
                "career_analysis": 18.7,
                "market_analysis": 14.2,
            },
            "data_summary": {
                "profile_created": workflow_progress >= 25,
                "career_paths_generated": workflow_progress >= 50,
                "market_analysis_completed": workflow_progress >= 75,
                "recommendations_ready": workflow_progress >= 100,
            },
        }

    @staticmethod
    def orchestrator_help_response(topic: str = "general") -> dict[str, Any]:
        """Generate orchestrator help response."""
        help_content = {
            "general": {
                "title": "Helios Career Operations System Help",
                "description": "AI-powered career intelligence platform",
                "available_commands": ["START", "STATUS", "HELP", "STOP"],
                "workflow_overview": "Profile → Analysis → Recommendations → Optimization",
            },
            "career_analysis": {
                "title": "Career Path Analysis",
                "description": "Generate personalized career progression paths",
                "required_data": ["work_experience", "skills", "career_goals"],
                "output": "Ranked career paths with timelines and requirements",
            },
            "market_analysis": {
                "title": "Market Analysis & Resume Optimization",
                "description": "Analyze market demand and optimize resume for ATS",
                "features": ["salary_trends", "skill_demand", "ats_optimization"],
                "metrics": ["demand_score", "competitiveness", "keyword_density"],
            },
        }

        return {
            "command": "HELP",
            "topic": topic,
            "help_content": help_content.get(topic, help_content["general"]),
            "timestamp": time.time(),
        }

    # Helper methods
    @staticmethod
    def _calculate_experience_years(profile_data: dict[str, Any]) -> float:
        """Calculate total years of experience from work history."""
        work_experience = profile_data.get("work_experience", [])
        if not work_experience:
            return 0.0

        # Simple calculation - could be more sophisticated
        return len(work_experience) * 2.5  # Assume average 2.5 years per role

    @staticmethod
    def _determine_education_level(profile_data: dict[str, Any]) -> str:
        """Determine highest education level."""
        education = profile_data.get("education", [])
        if not education:
            return "unknown"

        degrees = [edu.get("degree", "").lower() for edu in education]
        if any("phd" in degree or "doctorate" in degree for degree in degrees):
            return "doctorate"
        elif any("master" in degree or "mba" in degree for degree in degrees):
            return "masters"
        elif any("bachelor" in degree for degree in degrees):
            return "bachelors"
        else:
            return "other"

    @staticmethod
    def _determine_current_level(experience_years: float) -> str:
        """Determine current career level based on experience."""
        if experience_years < 2:
            return "junior"
        elif experience_years < 5:
            return "mid"
        elif experience_years < 8:
            return "senior"
        else:
            return "staff/principal"

    @staticmethod
    def _generate_career_paths(
        skills: dict[str, Any], experience_years: float, career_goals: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Generate realistic career paths based on profile."""
        base_paths = [
            {
                "path_id": str(uuid.uuid4()),
                "title": "Senior to Staff Engineer Track",
                "probability": 0.85,
                "timeline_months": 18,
                "required_skills": ["System Design", "Leadership", "Microservices"],
                "salary_range": {"min": 180000, "max": 250000, "currency": "USD"},
                "companies": ["Google", "Microsoft", "Amazon", "Meta"],
                "description": "Progression to senior individual contributor role with system ownership",
            },
            {
                "path_id": str(uuid.uuid4()),
                "title": "Technical Lead/Engineering Manager",
                "probability": 0.72,
                "timeline_months": 24,
                "required_skills": [
                    "Team Leadership",
                    "Project Management",
                    "Technical Strategy",
                ],
                "salary_range": {"min": 200000, "max": 280000, "currency": "USD"},
                "companies": ["Stripe", "Airbnb", "Uber", "Netflix"],
                "description": "Transition to leadership role managing engineering teams",
            },
            {
                "path_id": str(uuid.uuid4()),
                "title": "Principal Engineer/Architect",
                "probability": 0.68,
                "timeline_months": 30,
                "required_skills": [
                    "Architecture Design",
                    "Cross-team Influence",
                    "Technical Vision",
                ],
                "salary_range": {"min": 250000, "max": 350000, "currency": "USD"},
                "companies": ["Netflix", "Shopify", "Databricks", "Snowflake"],
                "description": "Senior technical leadership with company-wide technical influence",
            },
        ]

        # Adjust based on experience level
        if experience_years < 3:
            base_paths[0]["title"] = "Junior to Mid-level Engineer"
            base_paths[0]["timeline_months"] = 12
            base_paths[0]["salary_range"] = {
                "min": 90000,
                "max": 140000,
                "currency": "USD",
            }

        return base_paths

    @staticmethod
    def _identify_skill_gaps(
        current_skills: dict[str, Any], career_goals: dict[str, Any]
    ) -> list[str]:
        """Identify skills gaps for career progression."""
        current_techs = set()
        for skill_category in current_skills.values():
            if isinstance(skill_category, list):
                current_techs.update(skill_category)

        target_skills = {
            "System Design",
            "Leadership",
            "Cloud Architecture",
            "Kubernetes",
            "Machine Learning",
            "Distributed Systems",
        }

        return list(target_skills - current_techs)
