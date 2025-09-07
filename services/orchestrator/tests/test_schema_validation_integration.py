"""Tests for schema validation integration in service coordinator."""

import pytest
from unittest.mock import AsyncMock, Mock
from datetime import datetime

from src.core.service_coordinator import ServiceCoordinator, ServiceCoordinationError
from src.core.schema_validator import SchemaValidator
from src.models.session import SessionState, CurrentStep


@pytest.fixture
def mock_session_manager():
    """Create mock session manager."""
    manager = AsyncMock()
    manager.create_session.return_value = Mock(session_id="schema-test-session")
    manager.get_session.return_value = Mock(
        session_id="schema-test-session",
        state=SessionState.COMPLETED,
        current_step=CurrentStep.REVIEW,
        master_career_database={},
        updated_at=datetime.utcnow()
    )
    manager.update_session.return_value = Mock(session_id="schema-test-session")
    return manager


@pytest.fixture
def mock_profile_ingestor():
    """Create mock profile ingestor with valid schema data."""
    client = AsyncMock()
    client.ingest_resume.return_value = {
        "success": True,
        "master_career_database": {
            "work_experience": [
                {
                    "job_title": "Senior Software Engineer",
                    "company": "TechCorp Inc",
                    "duration": "3 years",
                    "start_date": "2021-01-15",
                    "end_date": "2024-01-15",
                    "location": "San Francisco, CA",
                    "accomplishments": [
                        "Led development of scalable API handling 1M+ requests/day",
                        "Reduced system latency by 40% through optimization",
                        "Managed team of 5 engineers"
                    ],
                    "responsibilities": [
                        "System architecture design",
                        "Code review and mentoring",
                        "Performance optimization"
                    ],
                    "skills_used": ["Python", "FastAPI", "PostgreSQL", "Redis"],
                    "metrics": {"team_size": 5, "performance_improvement": 40}
                }
            ],
            "projects": [
                {
                    "name": "AI-Powered Customer Service Bot",
                    "description": "Developed intelligent chatbot with 95% accuracy",
                    "duration": "6 months",
                    "technologies": ["Python", "Transformers", "FastAPI", "Docker"],
                    "outcomes": [
                        "Reduced customer support tickets by 60%",
                        "Improved customer satisfaction score from 3.2 to 4.7"
                    ],
                    "role": "Lead Developer",
                    "team_size": 3,
                    "url": "https://github.com/company/chatbot"
                }
            ],
            "skills_inventory": {
                "technical": ["Python", "FastAPI", "PostgreSQL", "Redis", "Docker"],
                "soft_skills": ["Leadership", "Communication", "Problem Solving"],
                "languages": ["Python", "JavaScript", "SQL"],
                "frameworks": ["FastAPI", "React", "Django"],
                "databases": ["PostgreSQL", "Redis", "MongoDB"],
                "cloud": ["AWS", "Docker", "Kubernetes"],
                "tools": ["Git", "Jira", "VS Code"],
                "certifications": ["AWS Certified Solutions Architect"]
            },
            "strategic_metadata": {
                "job_title_variations": [
                    "Senior Software Engineer",
                    "Senior Backend Developer", 
                    "Lead Software Engineer"
                ],
                "core_competencies": [
                    "Full-stack development",
                    "System architecture",
                    "Team leadership",
                    "Performance optimization"
                ],
                "career_level": "senior",
                "industry_experience": ["Technology", "SaaS", "Fintech"],
                "top_accomplishments": [
                    "Led API development handling 1M+ requests/day",
                    "Reduced system latency by 40%",
                    "Built AI chatbot reducing support tickets by 60%"
                ],
                "leadership_experience": True
            },
            "holistic_profile": {
                "transversal_projects": [
                    {
                        "name": "Cross-platform Mobile App",
                        "description": "Led development spanning web and mobile teams",
                        "impact": "Unified user experience across platforms"
                    }
                ],
                "career_aspirations": [
                    "Technical Leadership Role",
                    "Principal Engineer Position",
                    "CTO Track"
                ],
                "motivators": [
                    "Technical challenges",
                    "Team mentoring", 
                    "Innovation",
                    "Impact at scale"
                ],
                "preferred_work_environment": "Hybrid - collaborative with flexibility",
                "geographic_preferences": ["San Francisco Bay Area", "Remote-friendly"],
                "salary_expectations": {
                    "min": 180000,
                    "max": 250000,
                    "currency": "USD",
                    "benefits_priority": ["equity", "learning_budget", "flexible_time"]
                }
            },
            "created_at": "2024-01-15T10:30:00Z",
            "updated_at": "2024-01-15T15:45:00Z",
            "version": "1.0",
            "source": "resume_pdf_upload"
        }
    }
    client.health_check.return_value = {"status": "healthy"}
    return client


@pytest.fixture
def mock_strategist():
    """Create mock strategist with valid career paths data."""
    client = AsyncMock()
    client.generate_career_paths.return_value = {
        "success": True,
        "career_paths": {
            "recommended_paths": [
                {
                    "path_id": "principal_engineer",
                    "title": "Principal Software Engineer",
                    "fit_score": 0.94,
                    "transition_difficulty": "medium",
                    "learning_time_months": 8,
                    "required_skills": ["System Design", "Architecture", "Technical Leadership"],
                    "skill_gaps": ["Distributed Systems", "Cloud Architecture"]
                },
                {
                    "path_id": "engineering_manager",
                    "title": "Engineering Manager",
                    "fit_score": 0.87,
                    "transition_difficulty": "low",
                    "learning_time_months": 4,
                    "required_skills": ["People Management", "Strategic Planning", "Project Management"],
                    "skill_gaps": ["Budget Management", "Hiring"]
                }
            ],
            "analysis": {
                "current_level": "senior_engineer",
                "strength_areas": [
                    "technical_implementation",
                    "system_optimization", 
                    "team_leadership"
                ],
                "growth_areas": [
                    "strategic_planning",
                    "distributed_systems",
                    "cloud_architecture"
                ]
            }
        }
    }
    client.health_check.return_value = {"status": "healthy"}
    return client


@pytest.fixture
def mock_analyst():
    """Create mock analyst with valid market analysis data."""
    client = AsyncMock()
    client.analyze_market_position.return_value = {
        "success": True,
        "analysis": {
            "market_demand": {
                "principal_engineer": {
                    "demand_score": 0.91,
                    "salary_range": {"min": 200000, "max": 320000},
                    "job_openings": 450,
                    "growth_rate": 0.15
                },
                "engineering_manager": {
                    "demand_score": 0.86,
                    "salary_range": {"min": 180000, "max": 280000},
                    "job_openings": 380,
                    "growth_rate": 0.12
                }
            },
            "skill_gaps": [
                {
                    "skill": "Distributed Systems",
                    "importance": 0.85,
                    "current_level": 0.3,
                    "target_level": 0.8,
                    "learning_resources": ["System Design Course", "Distributed Systems Book"]
                },
                {
                    "skill": "Cloud Architecture",
                    "importance": 0.78,
                    "current_level": 0.4,
                    "target_level": 0.9,
                    "learning_resources": ["AWS Architecture Certification", "GCP Training"]
                }
            ],
            "resume_optimization": {
                "ats_score": 0.82,
                "recommendations": [
                    "Add more quantifiable achievements with specific metrics",
                    "Include cloud architecture keywords for target roles",
                    "Highlight distributed systems experience",
                    "Emphasize leadership and mentoring accomplishments"
                ],
                "keyword_analysis": {
                    "missing_keywords": ["microservices", "kubernetes", "distributed", "scalability"],
                    "well_represented": ["python", "api", "leadership", "optimization"]
                }
            }
        }
    }
    client.health_check.return_value = {"status": "healthy"}
    return client


@pytest.fixture
def service_coordinator_with_validation(mock_session_manager, mock_profile_ingestor, 
                                       mock_strategist, mock_analyst):
    """Create service coordinator with schema validation."""
    return ServiceCoordinator(
        session_manager=mock_session_manager,
        profile_ingestor=mock_profile_ingestor,
        strategist=mock_strategist,
        analyst=mock_analyst
    )


class TestSchemaValidationIntegration:
    """Test schema validation integration in service coordinator."""
    
    @pytest.mark.asyncio
    async def test_full_pipeline_with_valid_schema(self, service_coordinator_with_validation):
        """Test complete pipeline with valid Master Career Database schema."""
        # Execute pipeline with comprehensive test data
        results = await service_coordinator_with_validation.execute_full_pipeline(
            session_id="schema-test-session",
            resume_path="/path/to/test/resume.pdf"
        )
        
        # Verify pipeline completion
        assert results["pipeline_status"] == "completed"
        assert "schema_validation" in results
        
        # Verify schema validation passed
        schema_validation = results["schema_validation"]
        assert schema_validation["is_valid"] is True
        assert "report" in schema_validation
        
        # Verify comprehensive data structure
        profile_data = results["profile_data"]
        
        # Verify Master Career Database schema compliance
        assert "work_experience" in profile_data
        assert "projects" in profile_data
        assert "skills_inventory" in profile_data
        assert "strategic_metadata" in profile_data
        assert "holistic_profile" in profile_data
        
        # Verify work experience structure
        work_exp = profile_data["work_experience"][0]
        required_exp_fields = [
            "job_title", "company", "duration", "accomplishments", 
            "responsibilities", "skills_used", "metrics"
        ]
        for field in required_exp_fields:
            assert field in work_exp, f"Missing work experience field: {field}"
        
        # Verify skills inventory completeness
        skills_inventory = profile_data["skills_inventory"]
        skill_categories = [
            "technical", "soft_skills", "languages", "frameworks",
            "databases", "cloud", "tools", "certifications"
        ]
        for category in skill_categories:
            assert category in skills_inventory
            assert isinstance(skills_inventory[category], list)
        
        # Verify strategic metadata
        strategic_meta = profile_data["strategic_metadata"]
        assert "core_competencies" in strategic_meta
        assert "job_title_variations" in strategic_meta
        assert "career_level" in strategic_meta
        assert strategic_meta["career_level"] == "senior"
        
        # Verify holistic profile
        holistic_profile = profile_data["holistic_profile"]
        assert "career_aspirations" in holistic_profile
        assert "motivators" in holistic_profile
        assert len(holistic_profile["career_aspirations"]) >= 3
        
        # Verify career strategies structure
        strategies = results["career_strategies"]
        assert "recommended_paths" in strategies
        assert len(strategies["recommended_paths"]) >= 2
        
        path = strategies["recommended_paths"][0]
        expected_path_fields = [
            "path_id", "title", "fit_score", "transition_difficulty",
            "required_skills", "skill_gaps"
        ]
        for field in expected_path_fields:
            assert field in path, f"Missing career path field: {field}"
        
        # Verify market analysis structure
        analysis = results["market_analysis"]
        expected_analysis_fields = ["market_demand", "skill_gaps", "resume_optimization"]
        for field in expected_analysis_fields:
            assert field in analysis, f"Missing analysis field: {field}"
        
        # Verify skill gaps analysis
        skill_gaps = analysis["skill_gaps"]
        assert len(skill_gaps) >= 2
        gap = skill_gaps[0]
        assert all(field in gap for field in ["skill", "importance", "current_level", "target_level"])
        
        # Verify resume optimization
        resume_opt = analysis["resume_optimization"]
        assert "ats_score" in resume_opt
        assert "recommendations" in resume_opt
        assert resume_opt["ats_score"] > 0.5  # Should be reasonable score
    
    @pytest.mark.asyncio
    async def test_schema_validation_report_generation(self, service_coordinator_with_validation):
        """Test schema validation report generation with detailed metrics."""
        results = await service_coordinator_with_validation.execute_full_pipeline(
            session_id="schema-test-session",
            resume_path="/path/to/test/resume.pdf"
        )
        
        # Extract schema validation report
        schema_report = results["schema_validation"]["report"]
        
        # Verify report structure
        assert "validation_summary" in schema_report
        assert "data_metrics" in schema_report
        assert "recommendations" in schema_report
        
        # Verify validation summary
        validation_summary = schema_report["validation_summary"]
        assert validation_summary["is_valid"] is True
        assert "validation_timestamp" in validation_summary
        
        # Verify data metrics
        data_metrics = schema_report["data_metrics"]
        assert data_metrics["work_experience_entries"] >= 1
        assert data_metrics["project_entries"] >= 1
        assert data_metrics["total_skills"] >= 15  # Should have substantial skills
        assert data_metrics["has_strategic_metadata"] is True
        assert data_metrics["has_holistic_profile"] is True
        
        # Verify recommendations exist (should be minimal for good data)
        recommendations = schema_report["recommendations"]
        assert isinstance(recommendations, list)
    
    @pytest.mark.asyncio 
    async def test_pipeline_data_flow_validation(self, service_coordinator_with_validation):
        """Test comprehensive pipeline data flow validation."""
        results = await service_coordinator_with_validation.execute_full_pipeline(
            session_id="schema-test-session", 
            resume_path="/path/to/test/resume.pdf"
        )
        
        # Verify that data flows correctly between services
        profile_data = results["profile_data"]
        strategies = results["career_strategies"]
        analysis = results["market_analysis"]
        
        # Verify Profile Ingestor output feeds into Strategist
        assert "skills_inventory" in profile_data
        skills_from_profile = profile_data["skills_inventory"]["technical"]
        assert len(skills_from_profile) > 0
        
        # Verify Strategist uses profile data
        recommended_paths = strategies["recommended_paths"]
        assert len(recommended_paths) > 0
        
        # Verify Analyst references both profile and strategy data
        skill_gaps = analysis["skill_gaps"]
        market_demand = analysis["market_demand"]
        
        # Should have skill gaps identified based on career paths
        assert len(skill_gaps) > 0
        
        # Should have market analysis for recommended career paths
        path_titles = [path["path_id"] for path in recommended_paths]
        for path_id in path_titles:
            # Market demand should reference the career paths
            if path_id in market_demand:
                demand_data = market_demand[path_id]
                assert "demand_score" in demand_data
                assert "salary_range" in demand_data
    
    @pytest.mark.asyncio
    async def test_invalid_schema_handling(self, service_coordinator_with_validation, 
                                         mock_profile_ingestor):
        """Test handling of invalid schema data - should fail pipeline."""
        # Mock profile ingestor to return completely invalid data (empty skills)
        mock_profile_ingestor.ingest_resume.return_value = {
            "success": True,
            "master_career_database": {
                # Completely empty data that should trigger errors
                "work_experience": [],
                "projects": [],
                "skills_inventory": {"technical": []},  # Completely empty - triggers error
                "strategic_metadata": {},
                "holistic_profile": {}
            }
        }
        
        # Execute pipeline - should fail due to invalid schema
        with pytest.raises(ServiceCoordinationError) as exc_info:
            await service_coordinator_with_validation.execute_full_pipeline(
                session_id="schema-test-session",
                resume_path="/path/to/invalid/resume.pdf"
            )
        
        # Should fail with schema validation error
        assert "Pipeline data flow validation failed" in str(exc_info.value)
        assert "Skills inventory is completely empty" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_minimal_valid_schema_handling(self, service_coordinator_with_validation, 
                                                mock_profile_ingestor):
        """Test handling of minimal but valid schema data - should complete with warnings."""
        # Mock profile ingestor to return minimal but valid data
        mock_profile_ingestor.ingest_resume.return_value = {
            "success": True,
            "master_career_database": {
                # Minimal but valid data - has some skills
                "work_experience": [
                    {
                        "job_title": "Software Developer",
                        "company": "TechCorp",
                        "accomplishments": [],
                        "responsibilities": []
                    }
                ],
                "projects": [],
                "skills_inventory": {
                    "technical": ["Python", "JavaScript"],  # Has some skills
                    "soft_skills": ["Communication"]
                },
                "strategic_metadata": {
                    "core_competencies": ["Programming"]
                },
                "holistic_profile": {
                    "career_aspirations": ["Senior Developer"]
                }
            }
        }
        
        # Execute pipeline - should complete with warnings
        results = await service_coordinator_with_validation.execute_full_pipeline(
            session_id="schema-test-session",
            resume_path="/path/to/minimal/resume.pdf"
        )
        
        # Pipeline should complete despite warnings
        assert results["pipeline_status"] == "completed"
        
        # Schema validation should show warnings but be valid
        schema_validation = results["schema_validation"]
        assert schema_validation["is_valid"] is True
        
        schema_report = schema_validation["report"]
        assert len(schema_report["warnings"]) > 0  # Should have warnings
        assert "recommendations" in schema_report
        assert len(schema_report["recommendations"]) > 0  # Should suggest improvements


if __name__ == "__main__":
    pytest.main([__file__, "-v"])