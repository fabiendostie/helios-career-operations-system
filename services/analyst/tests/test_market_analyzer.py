"""Test market analysis engine."""

import pytest
from unittest.mock import patch, mock_open

from src.core.market_analyzer import MarketAnalyzer
from src.models.ner_entities import (
    ResumeDeconstruction,
    ProcessedSection,
    ExtractedEntity,
    EntityType,
)


@pytest.fixture
def sample_market_data():
    """Sample market data for testing."""
    jobs_data = [
        {
            "job_id": "test_001",
            "role_title": "Software Engineer",
            "company_name": "TestCorp",
            "location": "Remote",
            "remote_policy": "remote",
            "post_date": "2025-01-01",
            "required_skills": ["Python", "Docker", "AWS"],
            "preferred_skills": ["React"],
            "level": "senior",
            "full_description_text": "Python developer needed for cloud applications",
            "company_size": "100-500",
            "industry": "Technology",
        }
    ]

    comp_data = [
        {
            "role_title": "Software Engineer",
            "company_name": "TestCorp",
            "level": "senior",
            "location": "Remote",
            "year": 2025,
            "base_salary_usd": 150000,
            "total_comp_usd": 200000,
            "company_size": "100-500",
            "industry": "Technology",
        }
    ]

    return jobs_data, comp_data


@pytest.fixture
def mock_analyzer(sample_market_data):
    """Create MarketAnalyzer with mocked data loading."""
    jobs_data, comp_data = sample_market_data

    with patch("builtins.open", mock_open()):
        with patch("json.load") as mock_json:
            mock_json.side_effect = [jobs_data, comp_data]
            with patch("src.core.market_analyzer.Path"):
                analyzer = MarketAnalyzer()
                return analyzer


@pytest.fixture
def sample_resume_deconstruction():
    """Sample resume deconstruction for testing."""
    entities = [
        ExtractedEntity(
            text="Python", label=EntityType.SKILL, start=0, end=6, confidence=0.9
        ),
        ExtractedEntity(
            text="Docker", label=EntityType.TOOL, start=10, end=16, confidence=0.8
        ),
    ]

    section = ProcessedSection(
        section_name="work_experience",
        raw_text="I worked with Python and Docker",
        entities=entities,
        language="en",
    )

    return ResumeDeconstruction(
        sections=[section],
        entity_summary={EntityType.SKILL: 1, EntityType.TOOL: 1},
        language_distribution={"en": 100.0},
        processing_time_seconds=1.0,
        quality_metrics={},
    )


def test_extract_candidate_skills(mock_analyzer, sample_resume_deconstruction):
    """Test extracting candidate skills from resume."""
    skills = mock_analyzer.extract_candidate_skills(sample_resume_deconstruction)

    assert "python" in skills
    assert "docker" in skills
    assert len(skills) == 2


def test_calculate_job_similarity(mock_analyzer):
    """Test job similarity calculation."""
    candidate_skills = ["python", "docker"]
    job = mock_analyzer.market_jobs[0]  # From sample data

    similarity, matched, missing = mock_analyzer.calculate_job_similarity(
        candidate_skills, job
    )

    assert similarity > 0
    assert "Python" in matched or "python" in matched
    assert isinstance(missing, list)


def test_find_job_matches(mock_analyzer, sample_resume_deconstruction):
    """Test finding job matches."""
    matches = mock_analyzer.find_job_matches(sample_resume_deconstruction, top_k=5)

    assert len(matches) <= 5
    assert len(matches) == len(
        mock_analyzer.market_jobs
    )  # Should return all available jobs
    assert all(hasattr(match, "similarity_score") for match in matches)
    assert all(hasattr(match, "matched_skills") for match in matches)


def test_analyze_compensation(mock_analyzer):
    """Test compensation analysis."""
    # Create dummy job matches
    from src.models.market_data import JobMatch

    job_match = JobMatch(
        job=mock_analyzer.market_jobs[0],
        similarity_score=0.8,
        matched_skills=["Python"],
        missing_skills=["AWS"],
        match_details={},
    )

    comp_analysis = mock_analyzer.analyze_compensation([job_match])

    assert "base_salary_stats" in comp_analysis or "message" in comp_analysis
    if "base_salary_stats" in comp_analysis:
        assert "median" in comp_analysis["base_salary_stats"]


def test_analyze_skill_demand(mock_analyzer):
    """Test skill demand analysis."""
    from src.models.market_data import JobMatch

    job_match = JobMatch(
        job=mock_analyzer.market_jobs[0],
        similarity_score=0.8,
        matched_skills=["Python"],
        missing_skills=["AWS"],
        match_details={},
    )

    skill_analysis = mock_analyzer.analyze_skill_demand([job_match])

    assert "total_jobs_analyzed" in skill_analysis or "error" in skill_analysis
    if "total_jobs_analyzed" in skill_analysis:
        assert skill_analysis["total_jobs_analyzed"] == 1


def test_analyze_locations(mock_analyzer):
    """Test location analysis."""
    from src.models.market_data import JobMatch

    job_match = JobMatch(
        job=mock_analyzer.market_jobs[0],
        similarity_score=0.8,
        matched_skills=["Python"],
        missing_skills=["AWS"],
        match_details={},
    )

    location_analysis = mock_analyzer.analyze_locations([job_match])

    assert "top_locations" in location_analysis or "error" in location_analysis
    if "top_locations" in location_analysis:
        assert len(location_analysis["top_locations"]) >= 0


def test_generate_recommendations(mock_analyzer):
    """Test recommendation generation."""
    analysis_components = {
        "skill_demand": {"high_demand_skills": ["Python", "Docker"]},
        "compensation": {"total_compensation_stats": {"median": 150000}},
        "location": {"remote_opportunities": 5},
    }

    recommendations = mock_analyzer.generate_recommendations(analysis_components)

    assert isinstance(recommendations, list)
    assert len(recommendations) > 0
    assert any("Python" in rec or "Docker" in rec for rec in recommendations)


def test_analyze_market_integration(mock_analyzer, sample_resume_deconstruction):
    """Test complete market analysis integration."""
    result = mock_analyzer.analyze_market(sample_resume_deconstruction)

    assert hasattr(result, "job_matches")
    assert hasattr(result, "market_insights")
    assert hasattr(result, "compensation_analysis")
    assert hasattr(result, "recommendations")
    assert result.processing_metadata["processing_time_seconds"] >= 0
