"""Tests for text optimization engine."""

import pytest
from unittest.mock import Mock, patch

from src.core.text_optimizer import TextOptimizer
from src.models.edit_request import EditType, EditRequest
from src.models.text_analysis import TextAnalysis, ReadabilityMetrics, ContentAnalysis


class TestTextOptimizer:
    """Test cases for TextOptimizer."""

    @pytest.fixture
    def optimizer(self):
        """Create TextOptimizer instance."""
        return TextOptimizer()

    @pytest.fixture
    def sample_text(self):
        """Sample text for testing."""
        return (
            "I worked at a company where I did many things. "
            "I helped with projects. I was responsible for tasks. "
            "The results were good and people liked my work."
        )

    @pytest.fixture
    def sample_edit_request(self, sample_text):
        """Sample edit request."""
        return EditRequest(
            session_id="test-session",
            text=sample_text,
            edit_type=EditType.COMPREHENSIVE,
            industry="technology",
            role="software engineer"
        )

    def test_optimizer_initialization(self, optimizer):
        """Test that optimizer initializes correctly."""
        assert optimizer is not None
        assert hasattr(optimizer, 'optimize_text')
        assert hasattr(optimizer, 'analyze_text')

    def test_analyze_text_basic(self, optimizer, sample_text):
        """Test basic text analysis."""
        analysis = optimizer.analyze_text(sample_text)

        assert isinstance(analysis, TextAnalysis)
        assert analysis.text == sample_text
        assert analysis.language == "en"
        assert 0 <= analysis.overall_quality_score <= 100
        assert 0 <= analysis.grammar_score <= 100
        assert 0 <= analysis.style_score <= 100
        assert 0 <= analysis.content_score <= 100

    def test_analyze_text_readability_metrics(self, optimizer, sample_text):
        """Test that readability metrics are calculated."""
        analysis = optimizer.analyze_text(sample_text)

        readability = analysis.readability
        assert isinstance(readability, ReadabilityMetrics)
        assert readability.word_count > 0
        assert readability.sentence_count > 0
        assert readability.character_count > 0
        assert readability.flesch_reading_ease >= 0

    def test_analyze_text_content_analysis(self, optimizer, sample_text):
        """Test content analysis features."""
        analysis = optimizer.analyze_text(sample_text)

        content = analysis.content_analysis
        assert isinstance(content, ContentAnalysis)
        # Should detect weak language like "did many things", "helped with"
        assert content.weak_words_count > 0
        assert content.action_verbs_count >= 0

    def test_optimize_text_grammar(self, optimizer, sample_edit_request):
        """Test grammar optimization."""
        sample_edit_request.edit_type = EditType.GRAMMAR

        result = optimizer.optimize_text(sample_edit_request)

        assert result.original_text == sample_edit_request.text
        assert result.edited_text != sample_edit_request.text
        assert result.grammar_issues_fixed > 0
        assert len(result.suggestions) > 0

    def test_optimize_text_style(self, optimizer, sample_edit_request):
        """Test style optimization."""
        sample_edit_request.edit_type = EditType.STYLE

        result = optimizer.optimize_text(sample_edit_request)

        assert result.style_improvements > 0
        # Should improve weak language
        assert "did many things" not in result.edited_text.lower()

    def test_optimize_text_content_enhancement(self, optimizer, sample_edit_request):
        """Test content enhancement."""
        sample_edit_request.edit_type = EditType.CONTENT_ENHANCEMENT

        result = optimizer.optimize_text(sample_edit_request)

        assert result.content_enhancements > 0
        # Should add more specific, action-oriented language
        assert result.edited_text != result.original_text

    def test_optimize_text_quantification(self, optimizer):
        """Test achievement quantification."""
        text = "I increased sales and improved customer satisfaction."
        request = EditRequest(
            session_id="test",
            text=text,
            edit_type=EditType.QUANTIFICATION
        )

        result = optimizer.optimize_text(request)

        # Should suggest adding numbers/percentages
        assert any("%" in suggestion.suggested_text or
                  any(char.isdigit() for char in suggestion.suggested_text)
                  for suggestion in result.suggestions)

    def test_optimize_text_tone_adjustment(self, optimizer, sample_edit_request):
        """Test tone adjustment."""
        sample_edit_request.edit_type = EditType.TONE_ADJUSTMENT
        sample_edit_request.tone = "professional"

        result = optimizer.optimize_text(sample_edit_request)

        # Should make language more professional
        assert "responsible for" not in result.edited_text.lower()
        assert result.style_improvements > 0

    def test_optimize_text_comprehensive(self, optimizer, sample_edit_request):
        """Test comprehensive optimization."""
        sample_edit_request.edit_type = EditType.COMPREHENSIVE

        result = optimizer.optimize_text(sample_edit_request)

        # Should include all types of improvements
        assert result.grammar_issues_fixed >= 0
        assert result.style_improvements > 0
        assert result.content_enhancements > 0
        assert len(result.suggestions) > 0

    def test_optimize_text_industry_context(self, optimizer):
        """Test industry-specific optimization."""
        text = "I worked on computer things and helped users."
        request = EditRequest(
            session_id="test",
            text=text,
            edit_type=EditType.CONTENT_ENHANCEMENT,
            industry="technology",
            role="software developer"
        )

        result = optimizer.optimize_text(request)

        # Should use industry-specific terms
        edited_lower = result.edited_text.lower()
        assert any(tech_term in edited_lower for tech_term in
                  ["software", "applications", "systems", "development"])

    def test_optimize_text_preserves_meaning(self, optimizer, sample_edit_request):
        """Test that optimization preserves original meaning."""
        result = optimizer.optimize_text(sample_edit_request)

        # Original and edited should have similar length (not drastically different)
        original_words = len(sample_edit_request.text.split())
        edited_words = len(result.edited_text.split())

        # Should not change length by more than 50%
        assert 0.5 <= edited_words / original_words <= 2.0

    def test_optimize_text_with_version_tracking(self, optimizer, sample_edit_request):
        """Test optimization with version tracking enabled."""
        sample_edit_request.track_changes = True
        sample_edit_request.version_comment = "Initial optimization"

        result = optimizer.optimize_text(sample_edit_request)

        assert result.version_id is not None
        assert result.version_number == 1

    def test_analyze_text_empty_input(self, optimizer):
        """Test analysis with empty text."""
        with pytest.raises(ValueError, match="Text cannot be empty"):
            optimizer.analyze_text("")

    def test_optimize_text_empty_input(self, optimizer):
        """Test optimization with empty text."""
        request = EditRequest(session_id="test", text="")

        with pytest.raises(ValueError, match="Text cannot be empty"):
            optimizer.optimize_text(request)

    def test_optimize_text_too_long(self, optimizer):
        """Test optimization with text that's too long."""
        long_text = "word " * 50000  # Exceeds MAX_TEXT_LENGTH
        request = EditRequest(session_id="test", text=long_text)

        with pytest.raises(ValueError, match="Text too long"):
            optimizer.optimize_text(request)

    @patch('src.core.text_optimizer.language_tool_python')
    def test_grammar_check_with_language_tool(self, mock_lt, optimizer, sample_text):
        """Test grammar checking integration."""
        mock_tool = Mock()
        mock_lt.LanguageTool.return_value = mock_tool
        mock_tool.check.return_value = [
            Mock(offset=0, errorLength=5, message="Test error",
                 replacements=['fixed'], ruleId='TEST_RULE')
        ]

        analysis = optimizer.analyze_text(sample_text)

        assert len(analysis.grammar_issues) > 0
        mock_tool.check.assert_called_once()

    def test_readability_score_calculation(self, optimizer):
        """Test readability score calculation."""
        simple_text = "The cat sat on the mat. It was happy."
        complex_text = "The feline positioned itself upon the textile floor covering, experiencing contentment."

        simple_analysis = optimizer.analyze_text(simple_text)
        complex_analysis = optimizer.analyze_text(complex_text)

        # Simple text should have better readability
        assert simple_analysis.readability.flesch_reading_ease > complex_analysis.readability.flesch_reading_ease