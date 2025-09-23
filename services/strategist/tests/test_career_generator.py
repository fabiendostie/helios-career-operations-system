"""Tests for CareerGenerator class."""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, Mock, patch
from typing import Dict, Any, List

from src.core.career_generator import CareerGenerator
from src.models.career_path import CareerPathRequest, TransitionDifficulty
from src.models.role_taxonomy import JobRole, RIASECCode, CareerAnchor, IndustryCategory, ExperienceLevel
from src.core.config import StrategistConfig


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    return StrategistConfig(
        embedding_model="test-model",
        max_career_paths=3,
        skill_weight=0.65,
        aspiration_weight=0.35
    )


@pytest.fixture
def sample_master_career_data():
    """Sample master career database for testing."""
    return {
        "user_id": "test_user_123",
        "skills_inventory": {
            "technical": ["Python", "SQL", "Machine Learning"],
            "soft": ["Communication", "Problem Solving"]
        },
        "work_experience": [
            {
                "title": "Data Analyst",
                "accomplishments": ["Built ML model that increased accuracy by 20%"],
                "skills_demonstrated": ["Python", "Data Analysis", "SQL"]
            }
        ],
        "projects": [
            {
                "name": "ML Classification Project",
                "description": "Built classification model for customer segmentation",
                "technologies_used": ["Python", "scikit-learn", "pandas"]
            }
        ],
        "holistic_profile": {
            "aspirations": ["Work with cutting-edge AI technology", "Lead technical teams"],
            "motivators": ["Technical challenges", "Innovation", "Growth"]
        }
    }


@pytest.fixture
def sample_job_role():
    """Sample job role for testing."""
    return JobRole(
        role_id="test_role_001",
        title="Senior Data Scientist",
        description="Lead data science projects and mentor junior team members",
        industry_categories=[IndustryCategory.TECHNOLOGY],
        experience_level=ExperienceLevel.SENIOR,
        required_skill_keywords=["Python", "Machine Learning", "Statistics", "Leadership"],
        preferred_skill_keywords=["TensorFlow", "Deep Learning", "MLOps"],
        associated_riasec_codes=[RIASECCode.INVESTIGATIVE, RIASECCode.ENTERPRISING],
        associated_career_anchors=[CareerAnchor.TECHNICAL_COMPETENCE, CareerAnchor.PURE_CHALLENGE],
        median_salary_range={"min": 120000, "max": 160000},
        remote_work_compatibility=0.9
    )


class TestCareerGenerator:
    """Test cases for CareerGenerator."""

    @pytest.fixture
    def career_generator(self, mock_config):
        """Create career generator instance for testing."""
        generator = CareerGenerator(mock_config)

        # Mock the dependencies
        generator.vectorizer = AsyncMock()
        generator.taxonomy_manager = MagicMock()
        generator.fit_scorer = MagicMock()
        generator._initialized = True

        return generator

    def test_init(self, mock_config):
        """Test career generator initialization."""
        generator = CareerGenerator(mock_config)

        assert generator.config == mock_config
        assert not generator._initialized
        assert isinstance(generator._role_vectors_cache, dict)

    @pytest.mark.asyncio
    async def test_initialize_success(self, mock_config):
        """Test successful initialization of career generator."""
        generator = CareerGenerator(mock_config)

        # Mock the dependencies
        generator.vectorizer = AsyncMock()
        generator.taxonomy_manager = AsyncMock()
        generator._role_vectors_cache = {}

        # Mock the taxonomy manager roles as a regular dict (not AsyncMock)
        generator.taxonomy_manager.roles = {"role1": Mock()}

        # Mock the initialize methods
        generator.vectorizer.initialize = AsyncMock()
        generator.taxonomy_manager.load_taxonomy = AsyncMock()
        generator.taxonomy_manager.generate_role_vectors = AsyncMock(return_value={"role1": [0.1, 0.2, 0.3]})

        # Mock cache manager to None to avoid Redis path
        generator.vectorizer.cache_manager = None

        await generator.initialize()

        assert generator._initialized
        generator.vectorizer.initialize.assert_called_once()
        generator.taxonomy_manager.load_taxonomy.assert_called_once()
        generator.taxonomy_manager.generate_role_vectors.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_failure(self, mock_config):
        """Test initialization failure handling."""
        generator = CareerGenerator(mock_config)

        # Mock failure in vectorizer initialization
        generator.vectorizer = AsyncMock()
        generator.vectorizer.initialize = AsyncMock(side_effect=Exception("Model loading failed"))

        with pytest.raises(Exception, match="Model loading failed"):
            await generator.initialize()

        assert not generator._initialized

    @pytest.mark.asyncio
    async def test_generate_career_paths_success(self, career_generator, sample_master_career_data, sample_job_role):
        """Test successful career path generation."""
        # Setup mocks
        mock_candidate_profile = MagicMock()
        mock_candidate_profile.skills = ["Python", "SQL"]

        mock_aspiration_profile = MagicMock()
        mock_fit_details = MagicMock()
        mock_fit_details.weighted_fit_score = 0.85
        mock_fit_details.skill_match_score = 0.80
        mock_fit_details.aspiration_alignment_score = 0.75
        mock_fit_details.explanation = "Good match based on skills and interests"
        mock_fit_details.skill_overlap_count = 3
        mock_fit_details.riasec_matches = ["Investigative"]
        mock_fit_details.career_anchor_matches = ["Technical Competence"]

        career_generator.vectorizer.generate_candidate_vector.return_value = mock_candidate_profile
        career_generator.fit_scorer.extract_aspiration_profile.return_value = mock_aspiration_profile
        career_generator.fit_scorer.calculate_fit_score.return_value = mock_fit_details
        career_generator.taxonomy_manager.get_all_roles.return_value = [sample_job_role]
        career_generator._role_vectors_cache = {sample_job_role.role_id: [0.1, 0.2, 0.3]}

        request = CareerPathRequest(
            user_id="test_user",
            master_career_database=sample_master_career_data,
            max_recommendations=3
        )

        response = await career_generator.generate_career_paths(request)

        assert response.user_id == "test_user"
        assert len(response.career_target_profiles) == 1
        assert response.career_target_profiles[0].fit_score == 0.85
        assert response.processing_time_ms > 0

    @pytest.mark.asyncio
    async def test_generate_career_paths_not_initialized(self, mock_config, sample_master_career_data):
        """Test error when generator not initialized."""
        generator = CareerGenerator(mock_config)
        # Don't initialize

        request = CareerPathRequest(
            user_id="test_user",
            master_career_database=sample_master_career_data
        )

        with pytest.raises(RuntimeError, match="CareerGenerator not initialized"):
            await generator.generate_career_paths(request)

    def test_filter_roles_basic(self, career_generator, sample_job_role):
        """Test basic role filtering."""
        mock_fit_details = MagicMock()
        mock_fit_details.weighted_fit_score = 0.75

        role_scores = [(sample_job_role, mock_fit_details)]
        request = CareerPathRequest(user_id="test", master_career_database={})

        filtered = career_generator._filter_roles(role_scores, request)

        assert len(filtered) == 1
        assert filtered[0] == (sample_job_role, mock_fit_details)

    def test_filter_roles_low_score(self, career_generator, sample_job_role):
        """Test filtering out roles with low fit scores."""
        mock_fit_details = MagicMock()
        mock_fit_details.weighted_fit_score = 0.2  # Below threshold

        role_scores = [(sample_job_role, mock_fit_details)]
        request = CareerPathRequest(user_id="test", master_career_database={})

        filtered = career_generator._filter_roles(role_scores, request)

        assert len(filtered) == 0

    def test_filter_roles_industry_preference(self, career_generator, sample_job_role):
        """Test filtering by industry preferences."""
        mock_fit_details = MagicMock()
        mock_fit_details.weighted_fit_score = 0.75

        role_scores = [(sample_job_role, mock_fit_details)]
        request = CareerPathRequest(
            user_id="test",
            master_career_database={},
            preferred_industries=["Finance"]  # Role is in Technology
        )

        filtered = career_generator._filter_roles(role_scores, request)

        assert len(filtered) == 0

    def test_filter_roles_salary_requirements(self, career_generator, sample_job_role):
        """Test filtering by salary requirements."""
        mock_fit_details = MagicMock()
        mock_fit_details.weighted_fit_score = 0.75

        role_scores = [(sample_job_role, mock_fit_details)]
        request = CareerPathRequest(
            user_id="test",
            master_career_database={},
            salary_requirements={"min": 200000, "max": 300000}  # Above role range
        )

        filtered = career_generator._filter_roles(role_scores, request)

        assert len(filtered) == 0

    def test_rank_roles(self, career_generator):
        """Test role ranking by fit score."""
        # Create roles with different scores
        role1 = MagicMock()
        role2 = MagicMock()

        fit_details1 = MagicMock()
        fit_details1.weighted_fit_score = 0.6

        fit_details2 = MagicMock()
        fit_details2.weighted_fit_score = 0.8

        role_scores = [(role1, fit_details1), (role2, fit_details2)]

        ranked = career_generator._rank_roles(role_scores, max_recommendations=2)

        # Should be sorted by score (highest first)
        assert len(ranked) == 2
        assert ranked[0][1].weighted_fit_score == 0.8  # Higher score first
        assert ranked[1][1].weighted_fit_score == 0.6

    def test_assess_transition_difficulty_easy(self, career_generator):
        """Test transition difficulty assessment for easy transition."""
        mock_fit_details = MagicMock()
        mock_fit_details.skill_match_score = 0.8

        skill_gaps = []  # No critical gaps

        difficulty = career_generator._assess_transition_difficulty(mock_fit_details, skill_gaps)

        assert difficulty == TransitionDifficulty.EASY

    def test_assess_transition_difficulty_challenging(self, career_generator):
        """Test transition difficulty assessment for challenging transition."""
        mock_fit_details = MagicMock()
        mock_fit_details.skill_match_score = 0.4

        # Create critical skill gaps
        skill_gaps = []
        for i in range(5):
            gap = MagicMock()
            gap.priority.value = "critical"
            skill_gaps.append(gap)

        difficulty = career_generator._assess_transition_difficulty(mock_fit_details, skill_gaps)

        assert difficulty == TransitionDifficulty.CHALLENGING

    def test_estimate_learning_time(self, career_generator):
        """Test learning time estimation for different skills."""
        # Programming language
        time1 = career_generator._estimate_learning_time("Python")
        assert "2-4 months" in time1

        # Tool/Software
        time2 = career_generator._estimate_learning_time("Excel")
        assert "weeks" in time2

        # Management skill
        time3 = career_generator._estimate_learning_time("Leadership")
        assert "months" in time3

    def test_suggest_learning_resources(self, career_generator):
        """Test learning resource suggestions."""
        # Python resources
        resources = career_generator._suggest_learning_resources("Python")
        assert "Python.org tutorials" in resources
        assert "Real Python" in resources

        # SQL resources
        resources = career_generator._suggest_learning_resources("SQL")
        assert "SQLBolt" in resources

        # Management resources
        resources = career_generator._suggest_learning_resources("Management")
        assert "Harvard Business Review" in resources

    def test_calculate_confidence_level(self, career_generator):
        """Test confidence level calculation."""
        mock_fit_details = MagicMock()
        mock_fit_details.weighted_fit_score = 0.8
        mock_fit_details.aspiration_alignment_score = 0.7

        # No critical gaps
        skill_gaps = []

        confidence = career_generator._calculate_confidence_level(mock_fit_details, skill_gaps)

        assert 0.1 <= confidence <= 1.0
        assert confidence > 0.8  # Should be high with good fit and no gaps

    def test_estimate_transition_time(self, career_generator):
        """Test transition time estimation."""
        # Easy transition
        time1 = career_generator._estimate_transition_time([], TransitionDifficulty.EASY)
        assert "3-6 months" == time1

        # Very challenging transition
        time2 = career_generator._estimate_transition_time([], TransitionDifficulty.VERY_CHALLENGING)
        assert "18+" in time2


if __name__ == "__main__":
    pytest.main([__file__])
