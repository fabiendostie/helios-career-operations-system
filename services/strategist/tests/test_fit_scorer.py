"""Tests for fit scoring algorithm."""

import pytest
from unittest.mock import Mock

from src.core.fit_scorer import FitScorer, AspirationProfile, FitScoreDetails
from src.models.skill_vector import CandidateProfile
from src.models.role_taxonomy import (
    JobRole, RIASECCode, CareerAnchor, IndustryCategory, ExperienceLevel
)
from src.core.config import StrategistConfig


class TestFitScorer:
    """Test class for FitScorer."""
    
    @pytest.fixture
    def config(self):
        """Config fixture with default weights."""
        return StrategistConfig(
            skill_weight=0.65,
            aspiration_weight=0.35
        )
    
    @pytest.fixture
    def fit_scorer(self, config):
        """FitScorer fixture."""
        return FitScorer(config)
    
    @pytest.fixture
    def sample_candidate_profile(self):
        """Sample candidate profile for testing."""
        return CandidateProfile(
            user_id="test_user",
            skills=["Python", "Machine Learning", "Data Analysis"],
            accomplishments=["Built ML model", "Improved accuracy by 20%"],
            interests=["AI Research", "Innovation"],
            aggregated_vector=[0.1] * 384,  # Mock 384-dimensional vector
            vector_dimension=384,
            generation_timestamp=1609459200.0
        )
    
    @pytest.fixture
    def sample_job_role(self):
        """Sample job role for testing."""
        return JobRole(
            role_id="test_role",
            title="Data Scientist",
            alternative_titles=["ML Engineer"],
            description="Analyzes data and builds predictive models",
            industry_categories=[IndustryCategory.TECHNOLOGY],
            experience_level=ExperienceLevel.MID,
            required_skill_keywords=["Python", "Machine Learning", "Statistics"],
            preferred_skill_keywords=["SQL", "R", "TensorFlow"],
            associated_riasec_codes=[RIASECCode.INVESTIGATIVE, RIASECCode.REALISTIC],
            associated_career_anchors=[CareerAnchor.TECHNICAL_COMPETENCE, CareerAnchor.PURE_CHALLENGE],
            growth_trajectory=["Senior Data Scientist"],
            median_salary_range={"min": 90000, "max": 150000},
            remote_work_compatibility=0.8
        )
    
    @pytest.fixture
    def sample_aspiration_profile(self):
        """Sample aspiration profile for testing."""
        return AspirationProfile(
            riasec_codes=[RIASECCode.INVESTIGATIVE, RIASECCode.ARTISTIC],
            career_anchors=[CareerAnchor.TECHNICAL_COMPETENCE, CareerAnchor.PURE_CHALLENGE],
            interests=["Machine Learning", "AI Research", "Innovation"],
            motivators=["Problem Solving", "Technical Excellence"],
            confidence_level=0.8
        )
    
    def test_initialization_with_config(self, config):
        """Test FitScorer initialization with config."""
        scorer = FitScorer(config)
        
        assert scorer.skill_weight == 0.65
        assert scorer.aspiration_weight == 0.35
        assert scorer.config == config
    
    def test_initialization_with_default_config(self):
        """Test FitScorer initialization with default config."""
        scorer = FitScorer()
        
        # Should use default config values
        assert scorer.skill_weight > 0
        assert scorer.aspiration_weight > 0
        assert scorer.skill_weight + scorer.aspiration_weight == 1.0
    
    def test_weight_normalization(self):
        """Test that weights are normalized if they don't sum to 1.0."""
        config = StrategistConfig(skill_weight=0.8, aspiration_weight=0.4)  # Sum = 1.2
        scorer = FitScorer(config)
        
        # Weights should be normalized
        assert abs(scorer.skill_weight + scorer.aspiration_weight - 1.0) < 0.001
        assert abs(scorer.skill_weight - (0.8 / 1.2)) < 0.001
        assert abs(scorer.aspiration_weight - (0.4 / 1.2)) < 0.001
    
    def test_calculate_skill_similarity_identical_vectors(self, fit_scorer):
        """Test skill similarity with identical vectors."""
        vector1 = [1.0, 0.0, 0.0]
        vector2 = [1.0, 0.0, 0.0]
        
        similarity = fit_scorer._calculate_skill_similarity(vector1, vector2)
        assert similarity == 1.0
    
    def test_calculate_skill_similarity_orthogonal_vectors(self, fit_scorer):
        """Test skill similarity with orthogonal vectors."""
        vector1 = [1.0, 0.0]
        vector2 = [0.0, 1.0]
        
        similarity = fit_scorer._calculate_skill_similarity(vector1, vector2)
        assert similarity == 0.0
    
    def test_calculate_skill_similarity_dimension_mismatch(self, fit_scorer):
        """Test skill similarity with mismatched vector dimensions."""
        vector1 = [1.0, 0.0]
        vector2 = [1.0, 0.0, 0.0]  # Different dimension
        
        similarity = fit_scorer._calculate_skill_similarity(vector1, vector2)
        assert similarity == 0.0
    
    def test_calculate_skill_similarity_zero_magnitude(self, fit_scorer):
        """Test skill similarity with zero-magnitude vectors."""
        vector1 = [0.0, 0.0, 0.0]
        vector2 = [1.0, 0.0, 0.0]
        
        similarity = fit_scorer._calculate_skill_similarity(vector1, vector2)
        assert similarity == 0.0
    
    def test_calculate_riasec_alignment_perfect_match(self, fit_scorer):
        """Test RIASEC alignment with perfect match."""
        user_riasec = [RIASECCode.INVESTIGATIVE, RIASECCode.REALISTIC]
        role_riasec = [RIASECCode.INVESTIGATIVE, RIASECCode.REALISTIC]
        
        alignment = fit_scorer._calculate_riasec_alignment(user_riasec, role_riasec)
        assert alignment == 1.0
    
    def test_calculate_riasec_alignment_partial_match(self, fit_scorer):
        """Test RIASEC alignment with partial match."""
        user_riasec = [RIASECCode.INVESTIGATIVE, RIASECCode.ARTISTIC]
        role_riasec = [RIASECCode.INVESTIGATIVE, RIASECCode.REALISTIC]
        
        # Jaccard similarity: 1 intersection / 3 union = 0.33
        alignment = fit_scorer._calculate_riasec_alignment(user_riasec, role_riasec)
        assert abs(alignment - 0.3333333333333333) < 0.001
    
    def test_calculate_riasec_alignment_no_match(self, fit_scorer):
        """Test RIASEC alignment with no match."""
        user_riasec = [RIASECCode.ARTISTIC]
        role_riasec = [RIASECCode.CONVENTIONAL]
        
        alignment = fit_scorer._calculate_riasec_alignment(user_riasec, role_riasec)
        assert alignment == 0.0
    
    def test_calculate_riasec_alignment_empty_lists(self, fit_scorer):
        """Test RIASEC alignment with empty lists."""
        alignment = fit_scorer._calculate_riasec_alignment([], [RIASECCode.INVESTIGATIVE])
        assert alignment == 0.0
        
        alignment = fit_scorer._calculate_riasec_alignment([RIASECCode.INVESTIGATIVE], [])
        assert alignment == 0.0
    
    def test_calculate_career_anchor_alignment_perfect_match(self, fit_scorer):
        """Test career anchor alignment with perfect match."""
        user_anchors = [CareerAnchor.TECHNICAL_COMPETENCE, CareerAnchor.PURE_CHALLENGE]
        role_anchors = [CareerAnchor.TECHNICAL_COMPETENCE, CareerAnchor.PURE_CHALLENGE]
        
        alignment = fit_scorer._calculate_career_anchor_alignment(user_anchors, role_anchors)
        assert alignment == 1.0
    
    def test_calculate_career_anchor_alignment_partial_match(self, fit_scorer):
        """Test career anchor alignment with partial match."""
        user_anchors = [CareerAnchor.TECHNICAL_COMPETENCE, CareerAnchor.LIFESTYLE]
        role_anchors = [CareerAnchor.TECHNICAL_COMPETENCE, CareerAnchor.PURE_CHALLENGE]
        
        # Jaccard similarity: 1 intersection / 3 union = 0.33
        alignment = fit_scorer._calculate_career_anchor_alignment(user_anchors, role_anchors)
        assert abs(alignment - 0.3333333333333333) < 0.001
    
    def test_count_skill_overlap(self, fit_scorer, sample_candidate_profile, sample_job_role):
        """Test counting skill overlap between candidate and role."""
        overlap_count = fit_scorer._count_skill_overlap(
            sample_candidate_profile.skills, 
            sample_job_role
        )
        
        # Should find overlap: "Python", "Machine Learning"
        assert overlap_count == 2
    
    def test_find_riasec_matches(self, fit_scorer, sample_job_role):
        """Test finding RIASEC matches."""
        user_riasec = [RIASECCode.INVESTIGATIVE, RIASECCode.ARTISTIC]
        
        matches = fit_scorer._find_riasec_matches(user_riasec, sample_job_role)
        
        assert "Investigative" in matches
        assert "Artistic" not in matches  # Not in role's RIASEC codes
        assert len(matches) == 1
    
    def test_find_career_anchor_matches(self, fit_scorer, sample_job_role):
        """Test finding career anchor matches."""
        user_anchors = [CareerAnchor.TECHNICAL_COMPETENCE, CareerAnchor.LIFESTYLE]
        
        matches = fit_scorer._find_career_anchor_matches(user_anchors, sample_job_role)
        
        assert "Technical Competence" in matches
        assert "Lifestyle" not in matches  # Not in role's career anchors
        assert len(matches) == 1
    
    def test_calculate_fit_score_integration(self, fit_scorer, sample_candidate_profile, 
                                           sample_job_role, sample_aspiration_profile):
        """Test complete fit score calculation."""
        role_vector = [0.2] * 384  # Mock role vector with some similarity
        
        fit_details = fit_scorer.calculate_fit_score(
            sample_candidate_profile, 
            sample_job_role, 
            role_vector,
            sample_aspiration_profile
        )
        
        assert isinstance(fit_details, FitScoreDetails)
        assert 0.0 <= fit_details.skill_match_score <= 1.0
        assert 0.0 <= fit_details.aspiration_alignment_score <= 1.0
        assert 0.0 <= fit_details.weighted_fit_score <= 1.0
        assert fit_details.skill_overlap_count >= 0
        assert isinstance(fit_details.riasec_matches, list)
        assert isinstance(fit_details.career_anchor_matches, list)
        assert len(fit_details.explanation) > 0
    
    def test_extract_aspiration_profile_basic(self, fit_scorer):
        """Test extracting aspiration profile from master career data."""
        master_career_data = {
            "holistic_profile": {
                "aspirations": ["Become ML Engineer", "Work in AI"],
                "motivators": ["Innovation", "Problem Solving"]
            },
            "skills_inventory": {
                "programming": ["Python", "Java"]
            },
            "work_experience": [
                {"skills_demonstrated": ["Machine Learning", "Data Analysis"]}
            ]
        }
        
        aspiration_profile = fit_scorer.extract_aspiration_profile(master_career_data)
        
        assert isinstance(aspiration_profile, AspirationProfile)
        assert len(aspiration_profile.riasec_codes) > 0
        assert len(aspiration_profile.career_anchors) > 0
        assert "Become ML Engineer" in aspiration_profile.interests
        assert "Innovation" in aspiration_profile.motivators
        assert 0.0 < aspiration_profile.confidence_level <= 1.0
    
    def test_infer_riasec_codes_technical_skills(self, fit_scorer):
        """Test RIASEC code inference for technical skills."""
        master_career_data = {
            "skills_inventory": {
                "programming": ["Python", "Java", "Software Development"]
            }
        }
        
        riasec_codes = fit_scorer._infer_riasec_codes(master_career_data)
        
        assert RIASECCode.INVESTIGATIVE in riasec_codes
    
    def test_infer_riasec_codes_management_skills(self, fit_scorer):
        """Test RIASEC code inference for management skills."""
        master_career_data = {
            "skills_inventory": {
                "leadership": ["Management", "Leadership", "Strategy"]
            }
        }
        
        riasec_codes = fit_scorer._infer_riasec_codes(master_career_data)
        
        assert RIASECCode.ENTERPRISING in riasec_codes
    
    def test_infer_career_anchors_technical_focus(self, fit_scorer):
        """Test career anchor inference for technical focus."""
        master_career_data = {
            "holistic_profile": {
                "motivators": ["technical expertise", "skills development"],
                "aspirations": ["become a technical specialist"]
            }
        }
        
        career_anchors = fit_scorer._infer_career_anchors(master_career_data)
        
        assert CareerAnchor.TECHNICAL_COMPETENCE in career_anchors
    
    def test_infer_career_anchors_leadership_focus(self, fit_scorer):
        """Test career anchor inference for leadership focus."""
        master_career_data = {
            "holistic_profile": {
                "motivators": ["leadership", "team management"],
                "aspirations": ["become a manager"]
            }
        }
        
        career_anchors = fit_scorer._infer_career_anchors(master_career_data)
        
        assert CareerAnchor.GENERAL_MANAGERIAL in career_anchors
    
    def test_generate_score_explanation_high_score(self, fit_scorer, sample_candidate_profile, 
                                                  sample_job_role, sample_aspiration_profile):
        """Test explanation generation for high fit score."""
        explanation = fit_scorer._generate_score_explanation(
            skill_score=0.9, 
            aspiration_score=0.8, 
            weighted_score=0.87,
            candidate_profile=sample_candidate_profile,
            role=sample_job_role,
            aspiration_profile=sample_aspiration_profile
        )
        
        assert "excellent match" in explanation
        assert "90%" in explanation
        assert "80%" in explanation
    
    def test_generate_score_explanation_low_score(self, fit_scorer, sample_candidate_profile, 
                                                 sample_job_role, sample_aspiration_profile):
        """Test explanation generation for low fit score."""
        explanation = fit_scorer._generate_score_explanation(
            skill_score=0.2, 
            aspiration_score=0.3, 
            weighted_score=0.24,
            candidate_profile=sample_candidate_profile,
            role=sample_job_role,
            aspiration_profile=sample_aspiration_profile
        )
        
        assert "weak match" in explanation
        assert "20%" in explanation
        assert "30%" in explanation
    
    def test_calculate_interest_alignment(self, fit_scorer, sample_job_role):
        """Test interest alignment calculation."""
        user_interests = ["machine learning", "data analysis", "AI research"]
        
        alignment_score = fit_scorer._calculate_interest_alignment(user_interests, sample_job_role)
        
        assert 0.0 <= alignment_score <= 1.0
        # Should have some alignment since role is about data analysis and ML