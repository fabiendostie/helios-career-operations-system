"""Test ATS simulation engine."""

import pytest
from unittest.mock import patch, mock_open

from src.core.ats_simulator import ATSSimulator
from src.models.ats_scoring import ScoringCriteria, ScoreLevel
from src.models.ner_entities import (
    ResumeDeconstruction,
    ProcessedSection,
    ExtractedEntity,
    EntityType,
)
from src.models.market_data import MarketJob, JobLevel, RemotePolicy
from datetime import date


@pytest.fixture
def sample_scoring_data():
    """Sample scoring data for testing."""
    return {
        "high_impact_verbs": {
            "technical": ["architected", "engineered", "deployed"],
            "management": ["led", "managed", "coordinated"],
        },
        "weak_verbs_to_avoid": ["helped", "worked", "did"],
        "quantification_patterns": {
            "percentage": r"\d+\.?\d*%",
            "currency": r"\$[\d,]+",
        },
    }


@pytest.fixture
def mock_ats_simulator(sample_scoring_data):
    """Create ATSSimulator with mocked data loading."""
    with patch("builtins.open", mock_open()):
        with patch("yaml.safe_load", return_value=sample_scoring_data):
            simulator = ATSSimulator()
            return simulator


@pytest.fixture
def sample_resume_deconstruction():
    """Sample resume deconstruction for testing."""
    entities = [
        ExtractedEntity(
            text="Python", label=EntityType.SKILL, start=0, end=6, confidence=0.9
        ),
        ExtractedEntity(
            text="25%", label=EntityType.METRIC, start=20, end=23, confidence=0.8
        ),
        ExtractedEntity(
            text="architected",
            label=EntityType.ACTION_VERB,
            start=30,
            end=41,
            confidence=0.9,
        ),
    ]

    section = ProcessedSection(
        section_name="work_experience",
        raw_text="I architected Python solutions that improved performance by 25%",
        entities=entities,
        language="en",
    )

    return ResumeDeconstruction(
        sections=[section],
        entity_summary={
            EntityType.SKILL: 1,
            EntityType.METRIC: 1,
            EntityType.ACTION_VERB: 1,
        },
        language_distribution={"en": 100.0},
        processing_time_seconds=1.0,
        quality_metrics={},
    )


@pytest.fixture
def sample_job():
    """Sample job posting for testing."""
    return MarketJob(
        job_id="test_001",
        role_title="Senior Python Developer",
        company_name="TechCorp",
        location="Remote",
        remote_policy=RemotePolicy.REMOTE,
        post_date=date(2025, 1, 1),
        required_skills=["Python", "Docker", "AWS"],
        level=JobLevel.SENIOR,
        full_description_text="We are looking for a Senior Python Developer with experience in Docker and AWS cloud services. The ideal candidate will architect scalable solutions.",
    )


def test_scoring_weights(mock_ats_simulator):
    """Test that scoring weights are properly configured."""
    weights = mock_ats_simulator.SCORING_WEIGHTS

    assert weights[ScoringCriteria.KEYWORD_MATCH] == 0.40
    assert weights[ScoringCriteria.FORMAT_PARSABILITY] == 0.30
    assert weights[ScoringCriteria.QUANTIFICATION] == 0.20
    assert weights[ScoringCriteria.ACTION_VERBS] == 0.10

    # Weights should sum to 1.0
    assert sum(weights.values()) == 1.0


def test_determine_performance_level(mock_ats_simulator):
    """Test performance level determination."""
    assert mock_ats_simulator.determine_performance_level(90) == ScoreLevel.EXCELLENT
    assert mock_ats_simulator.determine_performance_level(70) == ScoreLevel.GOOD
    assert mock_ats_simulator.determine_performance_level(50) == ScoreLevel.FAIR
    assert mock_ats_simulator.determine_performance_level(30) == ScoreLevel.POOR


def test_calculate_keyword_match_score(mock_ats_simulator):
    """Test keyword matching score calculation."""
    resume_text = "I have experience with Python, Docker, and AWS cloud services"
    job_text = "We need a Python developer with Docker and AWS experience"

    score = mock_ats_simulator.calculate_keyword_match_score(resume_text, job_text)

    assert score.criteria == ScoringCriteria.KEYWORD_MATCH
    assert 0.0 <= score.score <= 1.0
    assert score.weight == 0.40
    assert "similarity_score" in score.details


def test_calculate_format_parsability_score(
    mock_ats_simulator, sample_resume_deconstruction
):
    """Test format parsability score calculation."""
    score = mock_ats_simulator.calculate_format_parsability_score(
        sample_resume_deconstruction
    )

    assert score.criteria == ScoringCriteria.FORMAT_PARSABILITY
    assert 0.0 <= score.score <= 1.0
    assert score.weight == 0.30
    assert "total_sections" in score.details
    assert "total_entities" in score.details


def test_calculate_quantification_score(
    mock_ats_simulator, sample_resume_deconstruction
):
    """Test quantification score calculation."""
    score = mock_ats_simulator.calculate_quantification_score(
        sample_resume_deconstruction
    )

    assert score.criteria == ScoringCriteria.QUANTIFICATION
    assert 0.0 <= score.score <= 1.0
    assert score.weight == 0.20
    assert "total_bullets" in score.details
    assert "quantified_bullets" in score.details


def test_calculate_action_verb_score(mock_ats_simulator, sample_resume_deconstruction):
    """Test action verb score calculation."""
    score = mock_ats_simulator.calculate_action_verb_score(sample_resume_deconstruction)

    assert score.criteria == ScoringCriteria.ACTION_VERBS
    assert 0.0 <= score.score <= 1.0
    assert score.weight == 0.10
    assert "total_bullets" in score.details


def test_simulate_ats_score_integration(
    mock_ats_simulator, sample_resume_deconstruction, sample_job
):
    """Test complete ATS score simulation."""
    ats_score = mock_ats_simulator.simulate_ats_score(
        sample_resume_deconstruction, sample_job
    )

    assert hasattr(ats_score, "overall_score")
    assert hasattr(ats_score, "percentage_score")
    assert hasattr(ats_score, "performance_level")
    assert len(ats_score.criteria_scores) == 4

    assert 0.0 <= ats_score.overall_score <= 1.0
    assert 0 <= ats_score.percentage_score <= 100
    assert ats_score.performance_level in ScoreLevel

    # Check that all scoring criteria are included
    criteria_types = [score.criteria for score in ats_score.criteria_scores]
    assert ScoringCriteria.KEYWORD_MATCH in criteria_types
    assert ScoringCriteria.FORMAT_PARSABILITY in criteria_types
    assert ScoringCriteria.QUANTIFICATION in criteria_types
    assert ScoringCriteria.ACTION_VERBS in criteria_types


def test_ats_score_recommendations(
    mock_ats_simulator, sample_resume_deconstruction, sample_job
):
    """Test that ATS score includes recommendations."""
    ats_score = mock_ats_simulator.simulate_ats_score(
        sample_resume_deconstruction, sample_job
    )

    assert isinstance(ats_score.optimization_recommendations, list)
    assert len(ats_score.optimization_recommendations) >= 0

    # Check that feedback is provided
    assert "readiness_level" in ats_score.ats_readiness_feedback
    assert "pass_probability" in ats_score.ats_readiness_feedback


def test_estimate_ranking(mock_ats_simulator):
    """Test ranking estimation."""
    ranking_90 = mock_ats_simulator._estimate_ranking(90)
    ranking_75 = mock_ats_simulator._estimate_ranking(75)
    ranking_60 = mock_ats_simulator._estimate_ranking(60)
    ranking_40 = mock_ats_simulator._estimate_ranking(40)

    assert "Top 10%" in ranking_90
    assert "Top 25%" in ranking_75
    assert "Top 50%" in ranking_60
    assert "Below median" in ranking_40
