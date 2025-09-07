"""Test resume deconstruction engine."""

import pytest
from unittest.mock import Mock, patch

from src.core.resume_deconstructor import ResumeDeconstructor
from src.models.ner_entities import EntityType, ExtractedEntity


@pytest.fixture
def mock_nlp_models():
    """Mock spaCy models to avoid loading during tests."""
    # Mock all the imports and classes at the module level
    with (
        patch("src.core.resume_deconstructor.spacy.load") as mock_load,
        patch("src.core.resume_deconstructor.Matcher") as mock_matcher_class,
        patch("src.core.resume_deconstructor.SentenceTransformer") as mock_st,
    ):
        # Create properly configured mock models
        mock_en = Mock()
        mock_fr = Mock()

        # Mock vocab with proper attributes
        mock_vocab_en = Mock()
        mock_vocab_fr = Mock()
        mock_vocab_en.strings = Mock()
        mock_vocab_fr.strings = Mock()

        # Configure models
        mock_en.vocab = mock_vocab_en
        mock_fr.vocab = mock_vocab_fr
        mock_en.return_value = Mock(ents=[])  # Empty entities list for docs
        mock_fr.return_value = Mock(ents=[])

        # Configure spacy.load to return appropriate model
        mock_load.side_effect = (
            lambda model: mock_en if model == "en_core_web_sm" else mock_fr
        )

        # Mock Matcher class to return a mock instance
        mock_matcher_instance = Mock()
        mock_matcher_class.return_value = mock_matcher_instance

        # Mock SentenceTransformer
        mock_st.return_value = Mock()

        yield mock_load


@pytest.fixture
def deconstructor(mock_nlp_models):
    """Create ResumeDeconstructor instance with mocked models."""
    return ResumeDeconstructor()


def test_detect_language(deconstructor):
    """Test language detection."""
    with patch("langdetect.detect") as mock_detect:
        mock_detect.return_value = "en"
        assert deconstructor.detect_language("Hello world") == "en"

        mock_detect.return_value = "fr"
        assert deconstructor.detect_language("Bonjour monde") == "fr"

        # Test fallback
        mock_detect.side_effect = Exception("Detection failed")
        assert deconstructor.detect_language("Unknown text") == "en"


def test_get_high_impact_verbs(deconstructor):
    """Test high-impact verb list."""
    verbs = deconstructor._get_high_impact_verbs()

    assert isinstance(verbs, list)
    assert len(verbs) > 20
    assert "architect" in verbs
    assert "manage" in verbs
    assert "analyze" in verbs


def test_get_entity_context(deconstructor):
    """Test entity context extraction."""
    text = "I developed a Python application that increased sales by 25%"
    context = deconstructor._get_entity_context(
        text, 12, 18, context_size=10
    )  # "Python"

    assert "Python" in context
    assert len(context) <= 30  # Should be around context_size * 2 + entity length


def test_deduplicate_entities(deconstructor):
    """Test entity deduplication."""
    entities = [
        ExtractedEntity(
            text="Python", label=EntityType.SKILL, start=0, end=6, confidence=0.8
        ),
        ExtractedEntity(
            text="Python", label=EntityType.SKILL, start=0, end=6, confidence=0.9
        ),  # Duplicate
        ExtractedEntity(
            text="Java", label=EntityType.SKILL, start=10, end=14, confidence=0.8
        ),
    ]

    deduplicated = deconstructor._deduplicate_entities(entities)
    assert len(deduplicated) == 2
    assert all(e.text in ["Python", "Java"] for e in deduplicated)


def test_process_resume_sections_structure(deconstructor):
    """Test processing resume sections structure."""
    career_data = {
        "work_experience": [
            {
                "role": "Software Engineer",
                "accomplishments": [
                    {
                        "description": "Developed Python applications using Docker and AWS"
                    }
                ],
            }
        ],
        "projects": [
            {
                "name": "ML Pipeline",
                "description": "Built machine learning pipeline with 95% accuracy",
            }
        ],
    }

    with patch.object(deconstructor, "extract_entities") as mock_extract:
        with patch.object(deconstructor, "detect_language", return_value="en"):
            with patch.object(
                deconstructor, "generate_semantic_embeddings", return_value={}
            ):
                mock_extract.return_value = [
                    ExtractedEntity(
                        text="Python",
                        label=EntityType.SKILL,
                        start=0,
                        end=6,
                        confidence=0.8,
                    )
                ]

                result = deconstructor.process_resume_sections(career_data)

                assert len(result.sections) == 2  # 1 work exp + 1 project
                assert EntityType.SKILL in result.entity_summary
                assert "en" in result.language_distribution
                assert result.processing_time_seconds >= 0


def test_extract_skills_patterns(deconstructor):
    """Test skill extraction patterns."""
    text = "I have experience with Python, React, Docker, and AWS cloud services"

    # Mock the doc parameter since we're testing regex patterns
    mock_doc = Mock()

    skills = deconstructor._extract_skills(text, mock_doc)

    skill_texts = [skill.text for skill in skills]
    assert "Python" in skill_texts
    assert "React" in skill_texts
    assert "Docker" in skill_texts
    assert "AWS" in skill_texts
