"""Test skill recalibration engine."""

import pytest

from src.core.skill_recalibrator import SkillRecalibrator, SkillQuadrant
from src.models.ner_entities import (
    ResumeDeconstruction,
    ProcessedSection,
    ExtractedEntity,
    EntityType,
)
from src.models.market_data import (
    MarketAnalysisResult,
    JobMatch,
    MarketJob,
    JobLevel,
    RemotePolicy,
)
from datetime import date


@pytest.fixture
def skill_recalibrator():
    """Create SkillRecalibrator instance."""
    return SkillRecalibrator()


@pytest.fixture
def sample_resume_with_skills():
    """Sample resume with various skills."""
    entities = [
        ExtractedEntity(
            text="Python", label=EntityType.SKILL, start=0, end=6, confidence=0.9
        ),
        ExtractedEntity(
            text="Docker", label=EntityType.TOOL, start=10, end=16, confidence=0.8
        ),
        ExtractedEntity(
            text="Leadership", label=EntityType.SKILL, start=20, end=30, confidence=0.7
        ),
    ]

    section1 = ProcessedSection(
        section_name="work_experience_senior_dev",
        raw_text="Led team using Python and Docker for microservices development",
        entities=entities,
        language="en",
    )

    section2 = ProcessedSection(
        section_name="project_ml_pipeline",
        raw_text="Built Python machine learning pipeline with Docker deployment",
        entities=[
            ExtractedEntity(
                text="Python", label=EntityType.SKILL, start=6, end=12, confidence=0.9
            ),
            ExtractedEntity(
                text="Machine Learning",
                label=EntityType.SKILL,
                start=13,
                end=29,
                confidence=0.8,
            ),
        ],
        language="en",
    )

    return ResumeDeconstruction(
        sections=[section1, section2],
        entity_summary={EntityType.SKILL: 4, EntityType.TOOL: 1},
        language_distribution={"en": 100.0},
        processing_time_seconds=1.0,
        quality_metrics={},
    )


@pytest.fixture
def sample_market_analysis():
    """Sample market analysis with job matches."""
    job1 = MarketJob(
        job_id="job_001",
        role_title="Senior Python Developer",
        company_name="TechCorp",
        location="Remote",
        remote_policy=RemotePolicy.REMOTE,
        post_date=date(2025, 1, 1),
        required_skills=["Python", "Docker", "AWS"],
        preferred_skills=["React"],
        level=JobLevel.SENIOR,
        full_description_text="Python developer needed",
    )

    job2 = MarketJob(
        job_id="job_002",
        role_title="ML Engineer",
        company_name="DataCorp",
        location="San Francisco",
        remote_policy=RemotePolicy.HYBRID,
        post_date=date(2025, 1, 2),
        required_skills=["Python", "Machine Learning", "TensorFlow"],
        preferred_skills=["Docker"],
        level=JobLevel.MID,
        full_description_text="ML engineer position",
    )

    job_matches = [
        JobMatch(
            job=job1,
            similarity_score=0.8,
            matched_skills=["Python", "Docker"],
            missing_skills=["AWS"],
            match_details={},
        ),
        JobMatch(
            job=job2,
            similarity_score=0.7,
            matched_skills=["Python", "Machine Learning"],
            missing_skills=["TensorFlow"],
            match_details={},
        ),
    ]

    return MarketAnalysisResult(
        job_matches=job_matches,
        market_insights={},
        compensation_analysis={},
        skill_demand_analysis={},
        location_analysis={},
        recommendations=[],
        processing_metadata={},
    )


def test_calculate_proficiency_score(skill_recalibrator, sample_resume_with_skills):
    """Test proficiency score calculation."""
    # Test skill with multiple mentions
    python_score, python_evidence = skill_recalibrator.calculate_proficiency_score(
        "Python", sample_resume_with_skills
    )

    assert 0.0 <= python_score <= 1.0
    assert python_evidence >= 2  # Should find Python in multiple sections

    # Test skill with single mention
    docker_score, docker_evidence = skill_recalibrator.calculate_proficiency_score(
        "Docker", sample_resume_with_skills
    )

    assert 0.0 <= docker_score <= 1.0
    assert docker_evidence >= 1

    # Test non-existent skill
    unknown_score, unknown_evidence = skill_recalibrator.calculate_proficiency_score(
        "UnknownSkill", sample_resume_with_skills
    )

    assert unknown_score == 0.0
    assert unknown_evidence == 0


def test_calculate_market_demand_score(skill_recalibrator, sample_market_analysis):
    """Test market demand score calculation."""
    # Test high-demand skill
    python_score, python_mentions = skill_recalibrator.calculate_market_demand_score(
        "Python", sample_market_analysis
    )

    assert 0.0 <= python_score <= 1.0
    assert python_mentions >= 1  # Python appears in multiple jobs

    # Test moderate demand skill
    docker_score, docker_mentions = skill_recalibrator.calculate_market_demand_score(
        "Docker", sample_market_analysis
    )

    assert 0.0 <= docker_score <= 1.0

    # Test low/no demand skill
    unknown_score, unknown_mentions = skill_recalibrator.calculate_market_demand_score(
        "UnknownSkill", sample_market_analysis
    )

    assert unknown_score == 0.0
    assert unknown_mentions == 0


def test_classify_skill_quadrant(skill_recalibrator):
    """Test skill quadrant classification."""
    # Test LEVERAGE (high proficiency, high demand)
    assert (
        skill_recalibrator.classify_skill_quadrant(0.8, 0.7) == SkillQuadrant.LEVERAGE
    )

    # Test UPSKILL (low proficiency, high demand)
    assert skill_recalibrator.classify_skill_quadrant(0.3, 0.7) == SkillQuadrant.UPSKILL

    # Test MAINTAIN (high proficiency, low demand)
    assert (
        skill_recalibrator.classify_skill_quadrant(0.8, 0.3) == SkillQuadrant.MAINTAIN
    )

    # Test DE_EMPHASIZE (low proficiency, low demand)
    assert (
        skill_recalibrator.classify_skill_quadrant(0.3, 0.3)
        == SkillQuadrant.DE_EMPHASIZE
    )


def test_generate_skill_recommendations(skill_recalibrator):
    """Test skill recommendation generation."""
    # Test LEVERAGE recommendations
    leverage_recs = skill_recalibrator.generate_skill_recommendations(
        "Python", SkillQuadrant.LEVERAGE, 0.8, 0.7
    )
    assert len(leverage_recs) > 0
    assert any("highlight" in rec.lower() for rec in leverage_recs)

    # Test UPSKILL recommendations
    upskill_recs = skill_recalibrator.generate_skill_recommendations(
        "AWS", SkillQuadrant.UPSKILL, 0.3, 0.7
    )
    assert len(upskill_recs) > 0
    assert any(
        "learn" in rec.lower() or "course" in rec.lower() for rec in upskill_recs
    )

    # Test MAINTAIN recommendations
    maintain_recs = skill_recalibrator.generate_skill_recommendations(
        "jQuery", SkillQuadrant.MAINTAIN, 0.8, 0.3
    )
    assert len(maintain_recs) > 0
    assert any(
        "maintain" in rec.lower() or "current" in rec.lower() for rec in maintain_recs
    )

    # Test DE_EMPHASIZE recommendations
    deemphasize_recs = skill_recalibrator.generate_skill_recommendations(
        "Flash", SkillQuadrant.DE_EMPHASIZE, 0.3, 0.2
    )
    assert len(deemphasize_recs) > 0
    assert any(
        "de-prioritize" in rec.lower() or "focus" in rec.lower()
        for rec in deemphasize_recs
    )


def test_extract_all_skills(
    skill_recalibrator, sample_resume_with_skills, sample_market_analysis
):
    """Test skill extraction from resume and market data."""
    skills = skill_recalibrator.extract_all_skills(
        sample_resume_with_skills, sample_market_analysis
    )

    assert isinstance(skills, list)
    assert len(skills) > 0

    # Should include skills from resume
    skill_names = [skill.lower() for skill in skills]
    assert "python" in skill_names
    assert "docker" in skill_names

    # Should include skills from market data
    assert any("aws" in skill.lower() for skill in skills)


def test_analyze_skill_gaps(skill_recalibrator, sample_market_analysis):
    """Test skill gap analysis."""
    # Create mock skill classifications
    from src.core.skill_recalibrator import SkillClassification

    leverage_skills = [
        SkillClassification(
            skill="Python",
            proficiency_score=0.8,
            market_demand_score=0.9,
            quadrant=SkillQuadrant.LEVERAGE,
            evidence_count=5,
            market_frequency=2,
            recommendations=[],
        )
    ]

    upskill_skills = [
        SkillClassification(
            skill="AWS",
            proficiency_score=0.3,
            market_demand_score=0.6,
            quadrant=SkillQuadrant.UPSKILL,
            evidence_count=1,
            market_frequency=1,
            recommendations=[],
        )
    ]

    gap_analysis = skill_recalibrator.analyze_skill_gaps(
        leverage_skills, upskill_skills, sample_market_analysis
    )

    assert "missing_high_demand_skills" in gap_analysis
    assert "skills_ready_for_advancement" in gap_analysis
    assert "total_skills_analyzed" in gap_analysis
    assert gap_analysis["total_skills_analyzed"] == 2


def test_recalibrate_skills_integration(
    skill_recalibrator, sample_resume_with_skills, sample_market_analysis
):
    """Test complete skill recalibration integration."""
    matrix = skill_recalibrator.recalibrate_skills(
        sample_resume_with_skills, sample_market_analysis
    )

    # Check structure
    assert hasattr(matrix, "leverage_skills")
    assert hasattr(matrix, "upskill_skills")
    assert hasattr(matrix, "maintain_skills")
    assert hasattr(matrix, "de_emphasize_skills")
    assert hasattr(matrix, "matrix_insights")
    assert hasattr(matrix, "skill_gap_analysis")
    assert hasattr(matrix, "development_roadmap")

    # Check insights structure
    assert "total_skills_analyzed" in matrix.matrix_insights
    assert "quadrant_distribution" in matrix.matrix_insights

    # Check that skills are classified
    total_skills = (
        len(matrix.leverage_skills)
        + len(matrix.upskill_skills)
        + len(matrix.maintain_skills)
        + len(matrix.de_emphasize_skills)
    )
    assert total_skills > 0

    # Check development roadmap
    assert isinstance(matrix.development_roadmap, list)


def test_is_technical_skill(skill_recalibrator):
    """Test technical skill identification."""
    assert skill_recalibrator._is_technical_skill("Python") is True
    assert skill_recalibrator._is_technical_skill("JavaScript") is True
    assert skill_recalibrator._is_technical_skill("Docker") is True
    assert skill_recalibrator._is_technical_skill("Leadership") is False
    assert skill_recalibrator._is_technical_skill("Communication") is False
