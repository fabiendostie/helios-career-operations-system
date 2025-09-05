"""Tests for skill vectorization system."""

import pytest
import numpy as np
from unittest.mock import Mock, AsyncMock, patch

from src.core.skill_vectorizer import SkillVectorizer
from src.models.skill_vector import SkillEmbedding, SkillVector, CandidateProfile


class TestSkillVectorizer:
    """Test class for SkillVectorizer."""
    
    @pytest.fixture
    def vectorizer(self):
        """Create vectorizer fixture with mocked model."""
        vectorizer = SkillVectorizer("test-model")
        
        # Mock the sentence transformer model
        mock_model = Mock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_model.encode.return_value = np.random.rand(1, 384)  # Mock embedding
        
        vectorizer.model = mock_model
        vectorizer.skill_space.dimension = 384
        vectorizer.initialized = True  # Mark as initialized to skip initialization
        
        return vectorizer
    
    def test_preprocess_text(self):
        """Test text preprocessing functionality."""
        vectorizer = SkillVectorizer()
        
        # Test basic preprocessing
        result = vectorizer._preprocess_text("  Python Programming  ")
        assert result == "python programming"
        
        # Test special character handling
        result = vectorizer._preprocess_text("C++ & Java Development!")
        assert result == "c++ java development "
        
        # Test multiple spaces
        result = vectorizer._preprocess_text("Machine    Learning")
        assert result == "machine learning"
    
    def test_extract_skills_from_text(self):
        """Test skill extraction from text."""
        vectorizer = SkillVectorizer()
        
        # Test comma-separated skills
        skills = vectorizer._extract_skills_from_text("Python, Java, JavaScript")
        assert skills == ["Python", "Java", "JavaScript"]
        
        # Test semicolon-separated skills
        skills = vectorizer._extract_skills_from_text("SQL; MongoDB; Redis")
        assert skills == ["SQL", "MongoDB", "Redis"]
        
        # Test single skill
        skills = vectorizer._extract_skills_from_text("Machine Learning")
        assert skills == ["Machine Learning"]
        
        # Test empty and short skills filtering
        skills = vectorizer._extract_skills_from_text("Python, , x, JavaScript")
        assert "x" not in skills
        assert "" not in skills
    
    @pytest.mark.asyncio
    async def test_generate_skill_embeddings(self, vectorizer):
        """Test skill embedding generation."""
        skills = ["Python", "Machine Learning", "SQL"]
        
        embeddings = await vectorizer.generate_skill_embeddings(skills)
        
        assert len(embeddings) == 3
        for embedding in embeddings:
            assert isinstance(embedding, SkillEmbedding)
            assert embedding.text in skills
            assert len(embedding.embedding) == 384
            assert "model" in embedding.metadata
    
    @pytest.mark.asyncio
    async def test_generate_skill_embeddings_caching(self, vectorizer):
        """Test that skill embeddings are cached properly."""
        skills = ["Python", "Python"]  # Duplicate skill
        
        embeddings = await vectorizer.generate_skill_embeddings(skills)
        
        # Both should return the same cached result
        assert len(embeddings) == 2
        assert vectorizer.get_cache_stats()["cached_skills"] >= 1
        
        # Verify model.encode was called only once due to caching
        assert vectorizer.model.encode.call_count == 1
    
    @pytest.mark.asyncio
    async def test_generate_candidate_vector(self, vectorizer):
        """Test candidate profile vector generation."""
        master_career_data = {
            "user_id": "test_user",
            "skills_inventory": {
                "programming": ["Python", "Java"],
                "databases": {"SQL": {}, "MongoDB": {}}
            },
            "work_experience": [
                {
                    "title": "Software Engineer",
                    "skills_demonstrated": ["Python", "React"],
                    "accomplishments": ["Built scalable API", "Improved performance by 40%"]
                }
            ],
            "projects": [
                {
                    "name": "ML Project",
                    "description": "Machine learning model for predictions",
                    "technologies_used": ["Python", "scikit-learn"]
                }
            ],
            "holistic_profile": {
                "aspirations": ["Become ML Engineer", "Work in AI"],
                "motivators": ["Innovation", "Problem Solving"]
            }
        }
        
        candidate_profile = await vectorizer.generate_candidate_vector(master_career_data)
        
        assert isinstance(candidate_profile, CandidateProfile)
        assert candidate_profile.user_id == "test_user"
        assert len(candidate_profile.skills) > 0
        assert len(candidate_profile.accomplishments) > 0
        assert len(candidate_profile.interests) > 0
        assert len(candidate_profile.aggregated_vector) == 384
        assert candidate_profile.vector_dimension == 384
    
    def test_extract_candidate_skills(self):
        """Test skill extraction from master career data."""
        vectorizer = SkillVectorizer()
        master_career_data = {
            "skills_inventory": {
                "programming": ["Python", "Java"],
                "databases": {"SQL": {}, "MongoDB": {}}
            },
            "work_experience": [
                {"skills_demonstrated": ["React", "Node.js"]}
            ],
            "projects": [
                {"technologies_used": ["Docker", "Kubernetes"]}
            ]
        }
        
        skills = vectorizer._extract_candidate_skills(master_career_data)
        
        # Check that all skills are extracted and duplicates are removed
        expected_skills = {"Python", "Java", "SQL", "MongoDB", "React", "Node.js", "Docker", "Kubernetes"}
        assert set(skills) == expected_skills
    
    def test_extract_candidate_accomplishments(self):
        """Test accomplishment extraction from master career data."""
        vectorizer = SkillVectorizer()
        master_career_data = {
            "work_experience": [
                {"accomplishments": ["Built API", "Improved performance"]},
                {"accomplishments": "Led team of 5 developers"}
            ],
            "projects": [
                {"description": "Machine learning project for fraud detection"}
            ]
        }
        
        accomplishments = vectorizer._extract_candidate_accomplishments(master_career_data)
        
        assert len(accomplishments) >= 3
        assert "Built API" in accomplishments
        assert "Led team of 5 developers" in accomplishments
        assert "Machine learning project for fraud detection" in accomplishments
    
    def test_extract_candidate_interests(self):
        """Test interest extraction from master career data."""
        vectorizer = SkillVectorizer()
        master_career_data = {
            "holistic_profile": {
                "aspirations": ["Become ML Engineer", "Work in AI"],
                "motivators": "Innovation and Problem Solving"
            }
        }
        
        interests = vectorizer._extract_candidate_interests(master_career_data)
        
        assert "Become ML Engineer" in interests
        assert "Work in AI" in interests
        assert "Innovation and Problem Solving" in interests
    
    def test_combine_candidate_text(self):
        """Test combining candidate information into text."""
        vectorizer = SkillVectorizer()
        skills = ["Python", "Machine Learning"]
        accomplishments = ["Built ML model", "Improved accuracy by 20%"]
        interests = ["AI Research", "Innovation"]
        
        combined_text = vectorizer._combine_candidate_text(skills, accomplishments, interests)
        
        assert "Skills: Python, Machine Learning" in combined_text
        assert "Accomplishments:" in combined_text
        assert "Interests: AI Research, Innovation" in combined_text
    
    def test_calculate_similarity(self):
        """Test cosine similarity calculation."""
        vectorizer = SkillVectorizer()
        # Test identical vectors
        vector1 = [1.0, 0.0, 0.0]
        vector2 = [1.0, 0.0, 0.0]
        similarity = vectorizer.calculate_similarity(vector1, vector2)
        assert similarity == 1.0
        
        # Test orthogonal vectors
        vector1 = [1.0, 0.0]
        vector2 = [0.0, 1.0]
        similarity = vectorizer.calculate_similarity(vector1, vector2)
        assert similarity == 0.0
        
        # Test different dimension vectors (should raise error)
        with pytest.raises(ValueError):
            vectorizer.calculate_similarity([1.0, 0.0], [1.0, 0.0, 0.0])
    
    @pytest.mark.asyncio
    async def test_find_similar_skills(self, vectorizer):
        """Test finding similar skills."""
        query_vector = [1.0, 0.0, 0.0]
        
        skill_database = [
            SkillVector(skill_name="Python", vector=[1.0, 0.0, 0.0]),
            SkillVector(skill_name="Java", vector=[0.8, 0.6, 0.0]),
            SkillVector(skill_name="JavaScript", vector=[0.0, 1.0, 0.0])
        ]
        
        results = await vectorizer.find_similar_skills(query_vector, skill_database, top_k=2)
        
        assert len(results) == 2
        assert results[0].item_id == "Python"  # Most similar
        assert results[0].similarity_score > results[1].similarity_score
    
    def test_get_cache_stats(self):
        """Test cache statistics."""
        vectorizer = SkillVectorizer()
        # Add some items to cache
        vectorizer._skill_cache["python"] = np.random.rand(384)
        vectorizer._skill_cache["java"] = np.random.rand(384)
        
        stats = vectorizer.get_cache_stats()
        
        assert stats["cached_skills"] == 2
        assert stats["cache_memory_estimate"] > 0
    
    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test vectorizer initialization."""
        with patch('src.core.skill_vectorizer.SentenceTransformer') as mock_st:
            mock_model = Mock()
            mock_model.get_sentence_embedding_dimension.return_value = 384
            mock_model.encode.return_value = np.array([[0.1] * 384])  # Return proper numpy array
            mock_st.return_value = mock_model
            
            vectorizer = SkillVectorizer("test-model")
            await vectorizer.initialize()
            
            assert vectorizer.model is not None
            assert vectorizer.skill_space.dimension == 384
    
    @pytest.mark.asyncio
    async def test_uninitialized_model_error(self):
        """Test that uninitialized model raises appropriate errors."""
        vectorizer = SkillVectorizer()
        
        with pytest.raises(RuntimeError, match="Model not initialized"):
            await vectorizer.generate_skill_embeddings(["Python"])
        
        with pytest.raises(RuntimeError, match="Model not initialized"):
            await vectorizer.generate_candidate_vector({})