"""Test career path inference engine."""

import pytest

from src.core.career_inferencer import CareerInferencer, CareerHorizon, PathType
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
from src.models.ats_scoring import ATSScore, CriteriaScore, ScoringCriteria, ScoreLevel
from src.core.skill_recalibrator import (
    SkillFramingMatrix,
    SkillClassification,
    SkillQuadrant,
)
from datetime import date


@pytest.fixture
def career_inferencer():
    """Create CareerInferencer instance."""
    return CareerInferencer()


@pytest.fixture
def sample_resume_senior():
    """Sample resume for senior-level professional."""
    entities = [
        ExtractedEntity(
            text="Python", label=EntityType.SKILL, start=0, end=6, confidence=0.9
        ),
        ExtractedEntity(
            text="led", label=EntityType.ACTION_VERB, start=10, end=13, confidence=0.8
        ),
        ExtractedEntity(
            text="team",
            label=EntityType.RESPONSIBILITY,
            start=14,
            end=18,
            confidence=0.7,
        ),
    ]

    section = ProcessedSection(
        section_name="work_experience_senior_engineer",
        raw_text="Led team of 5 developers using Python and Django, senior engineer role for 3 years",
        entities=entities,
        language="en",
    )

    return ResumeDeconstruction(
        sections=[section],
        entity_summary={
            EntityType.SKILL: 1,
            EntityType.ACTION_VERB: 1,
            EntityType.RESPONSIBILITY: 1,
        },
        language_distribution={"en": 100.0},
        processing_time_seconds=1.0,
        quality_metrics={},
    )


@pytest.fixture
def sample_market_analysis_multi_level():
    """Sample market analysis with jobs at multiple levels."""
    jobs = [
        MarketJob(
            job_id="job_001",
            role_title="Senior Python Developer",
            company_name="TechCorp",
            location="Remote",
            remote_policy=RemotePolicy.REMOTE,
            post_date=date(2025, 1, 1),
            required_skills=["Python", "Django", "AWS"],
            level=JobLevel.SENIOR,
            full_description_text="Senior Python developer position",
        ),
        MarketJob(
            job_id="job_002",
            role_title="Staff Engineer",
            company_name="BigTech Inc",
            location="San Francisco",
            remote_policy=RemotePolicy.HYBRID,
            post_date=date(2025, 1, 2),
            required_skills=["Python", "System Design", "Leadership"],
            level=JobLevel.STAFF,
            full_description_text="Staff engineer role with technical leadership",
        ),
        MarketJob(
            job_id="job_003",
            role_title="ML Engineer",
            company_name="AIStartup",
            location="Remote",
            remote_policy=RemotePolicy.REMOTE,
            post_date=date(2025, 1, 3),
            required_skills=["Python", "Machine Learning", "TensorFlow"],
            level=JobLevel.SENIOR,
            full_description_text="Machine learning engineer position",
        ),
    ]

    job_matches = [
        JobMatch(
            job=jobs[0],
            similarity_score=0.8,
            matched_skills=["Python", "Django"],
            missing_skills=["AWS"],
            match_details={},
        ),
        JobMatch(
            job=jobs[1],
            similarity_score=0.6,
            matched_skills=["Python"],
            missing_skills=["System Design", "Leadership"],
            match_details={},
        ),
        JobMatch(
            job=jobs[2],
            similarity_score=0.7,
            matched_skills=["Python"],
            missing_skills=["Machine Learning", "TensorFlow"],
            match_details={},
        ),
    ]

    return MarketAnalysisResult(
        job_matches=job_matches,
        market_insights={"average_similarity_score": 0.7},
        compensation_analysis={},
        skill_demand_analysis={},
        location_analysis={},
        recommendations=[],
        processing_metadata={},
    )


@pytest.fixture
def sample_skill_matrix():
    """Sample skill framing matrix."""
    leverage_skills = [
        SkillClassification(
            skill="Python",
            proficiency_score=0.9,
            market_demand_score=0.8,
            quadrant=SkillQuadrant.LEVERAGE,
            evidence_count=5,
            market_frequency=3,
            recommendations=[],
        ),
        SkillClassification(
            skill="Django",
            proficiency_score=0.8,
            market_demand_score=0.6,
            quadrant=SkillQuadrant.LEVERAGE,
            evidence_count=3,
            market_frequency=2,
            recommendations=[],
        ),
    ]

    upskill_skills = [
        SkillClassification(
            skill="AWS",
            proficiency_score=0.3,
            market_demand_score=0.8,
            quadrant=SkillQuadrant.UPSKILL,
            evidence_count=1,
            market_frequency=2,
            recommendations=[],
        )
    ]

    return SkillFramingMatrix(
        leverage_skills=leverage_skills,
        upskill_skills=upskill_skills,
        maintain_skills=[],
        de_emphasize_skills=[],
        matrix_insights={
            "total_skills_analyzed": 3,
            "quadrant_distribution": {
                "leverage": 2,
                "upskill": 1,
                "maintain": 0,
                "de_emphasize": 0,
            },
        },
        skill_gap_analysis={},
        development_roadmap=[],
    )


@pytest.fixture
def sample_ats_score():
    """Sample ATS score."""
    criteria_scores = [
        CriteriaScore(
            criteria=ScoringCriteria.KEYWORD_MATCH,
            score=0.8,
            weight=0.4,
            weighted_score=0.32,
            details={},
            recommendations=[],
        )
    ]

    return ATSScore(
        overall_score=0.75,
        percentage_score=75,
        performance_level=ScoreLevel.GOOD,
        criteria_scores=criteria_scores,
        summary={},
        optimization_recommendations=[],
        ats_readiness_feedback={},
    )


def test_infer_current_level(career_inferencer, sample_resume_senior):
    """Test current career level inference."""
    level = career_inferencer.infer_current_level(sample_resume_senior)
    assert level == JobLevel.SENIOR


def test_generate_lateral_paths(
    career_inferencer, sample_market_analysis_multi_level, sample_skill_matrix
):
    """Test lateral career path generation."""
    current_skills = ["Python", "Django"]
    paths = career_inferencer.generate_lateral_paths(
        current_skills, sample_market_analysis_multi_level, sample_skill_matrix
    )

    assert isinstance(paths, list)
    # Should find opportunities based on similar skills
    for path in paths:
        assert path.path_type == PathType.LATERAL_MOVE
        assert path.horizon == CareerHorizon.HORIZON_1


def test_generate_vertical_paths(
    career_inferencer, sample_skill_matrix, sample_market_analysis_multi_level
):
    """Test vertical promotion path generation."""
    current_level = JobLevel.SENIOR
    paths = career_inferencer.generate_vertical_paths(
        current_level, sample_skill_matrix, sample_market_analysis_multi_level
    )

    assert isinstance(paths, list)
    for path in paths:
        assert path.path_type == PathType.VERTICAL_PROMOTION
        assert path.target_roles  # Should have target roles


def test_generate_pivot_paths(
    career_inferencer, sample_skill_matrix, sample_market_analysis_multi_level
):
    """Test career pivot path generation."""
    paths = career_inferencer.generate_pivot_paths(
        sample_skill_matrix, sample_market_analysis_multi_level
    )

    assert isinstance(paths, list)
    for path in paths:
        assert path.path_type == PathType.CAREER_PIVOT
        assert path.horizon == CareerHorizon.HORIZON_2


def test_generate_specialization_paths(
    career_inferencer, sample_skill_matrix, sample_market_analysis_multi_level
):
    """Test specialization path generation."""
    paths = career_inferencer.generate_specialization_paths(
        sample_skill_matrix, sample_market_analysis_multi_level
    )

    assert isinstance(paths, list)
    for path in paths:
        assert path.path_type == PathType.SPECIALIZATION
        assert path.horizon == CareerHorizon.HORIZON_3


def test_assess_current_positioning(
    career_inferencer, sample_resume_senior, sample_skill_matrix, sample_ats_score
):
    """Test current positioning assessment."""
    positioning = career_inferencer.assess_current_positioning(
        sample_resume_senior, sample_skill_matrix, sample_ats_score
    )

    assert "inferred_level" in positioning
    assert "skill_portfolio_strength" in positioning
    assert "ats_readiness" in positioning
    assert "ats_score_percentage" in positioning
    assert positioning["inferred_level"] == "senior"
    assert positioning["skill_portfolio_strength"] > 0


def test_assess_market_readiness(
    career_inferencer,
    sample_skill_matrix,
    sample_ats_score,
    sample_market_analysis_multi_level,
):
    """Test market readiness assessment."""
    readiness = career_inferencer.assess_market_readiness(
        sample_skill_matrix, sample_ats_score, sample_market_analysis_multi_level
    )

    assert "overall_readiness_score" in readiness
    assert "readiness_level" in readiness
    assert "skill_portfolio_strength" in readiness
    assert "immediate_opportunities" in readiness
    assert 0.0 <= readiness["overall_readiness_score"] <= 1.0


def test_classify_readiness(career_inferencer):
    """Test readiness level classification."""
    assert career_inferencer._classify_readiness(0.9) == "Market Ready"
    assert career_inferencer._classify_readiness(0.7) == "Nearly Ready"
    assert career_inferencer._classify_readiness(0.5) == "Developing"
    assert career_inferencer._classify_readiness(0.3) == "Preparation Needed"


def test_generate_executive_summary(career_inferencer):
    """Test executive summary generation."""
    from src.core.career_inferencer import CareerPath

    career_paths = [
        CareerPath(
            path_id="test_path",
            title="Senior Developer",
            path_type=PathType.LATERAL_MOVE,
            horizon=CareerHorizon.HORIZON_1,
            target_roles=["Senior Developer"],
            skill_requirements=["Python"],
            preparation_timeline="0-3 months",
            confidence_score=0.8,
            market_opportunity="High",
            rationale="Test path",
            action_steps=["Apply"],
        )
    ]

    current_positioning = {
        "inferred_level": "senior",
        "skill_portfolio_strength": 5,
        "ats_readiness": "good",
        "ats_score_percentage": 75,
    }

    market_readiness = {
        "readiness_level": "Nearly Ready",
        "overall_readiness_score": 0.7,
        "immediate_opportunities": 3,
        "skill_gaps": 2,
    }

    summary = career_inferencer.generate_executive_summary(
        career_paths, current_positioning, market_readiness
    )

    assert isinstance(summary, str)
    assert "Career Analysis Summary" in summary
    assert "senior" in summary.lower()
    assert "nearly ready" in summary.lower()


def test_infer_career_paths_integration(
    career_inferencer,
    sample_resume_senior,
    sample_market_analysis_multi_level,
    sample_skill_matrix,
    sample_ats_score,
):
    """Test complete career path inference integration."""
    report = career_inferencer.infer_career_paths(
        sample_resume_senior,
        sample_market_analysis_multi_level,
        sample_skill_matrix,
        sample_ats_score,
    )

    # Check report structure
    assert hasattr(report, "career_paths")
    assert hasattr(report, "current_positioning")
    assert hasattr(report, "market_readiness")
    assert hasattr(report, "competitive_advantages")
    assert hasattr(report, "development_priorities")
    assert hasattr(report, "timeline_recommendations")
    assert hasattr(report, "executive_summary")
    assert hasattr(report, "processing_metadata")

    # Check content quality
    assert len(report.career_paths) > 0
    assert isinstance(report.current_positioning, dict)
    assert isinstance(report.market_readiness, dict)
    assert isinstance(report.competitive_advantages, list)
    assert isinstance(report.development_priorities, list)
    assert isinstance(report.executive_summary, str)

    # Check timeline recommendations structure
    assert "immediate_actions" in report.timeline_recommendations
    assert "short_term_goals" in report.timeline_recommendations
    assert "long_term_vision" in report.timeline_recommendations

    # Verify processing metadata
    assert "processing_time_seconds" in report.processing_metadata
    assert "total_paths_generated" in report.processing_metadata
    assert report.processing_metadata["processing_time_seconds"] >= 0
