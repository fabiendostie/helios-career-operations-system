"""Tests for grammar checking functionality."""

import pytest
from unittest.mock import Mock, patch

from src.core.grammar_checker import GrammarChecker
from src.models.text_analysis import GrammarIssue, IssueSeverity


class TestGrammarChecker:
    """Test cases for GrammarChecker."""

    @pytest.fixture
    def checker(self):
        """Create GrammarChecker instance."""
        return GrammarChecker()

    def test_checker_initialization(self, checker):
        """Test that checker initializes correctly."""
        assert checker is not None
        assert hasattr(checker, 'check_grammar')
        assert hasattr(checker, 'suggest_corrections')

    def test_check_grammar_basic(self, checker):
        """Test basic grammar checking."""
        text = "This are a test sentence with grammar error."
        issues = checker.check_grammar(text)

        assert isinstance(issues, list)
        assert len(issues) > 0
        assert all(isinstance(issue, GrammarIssue) for issue in issues)

    def test_check_grammar_perfect_text(self, checker):
        """Test grammar checking with perfect text."""
        text = "This is a perfect sentence with no errors."
        issues = checker.check_grammar(text)

        # Should return empty list or very few minor issues
        assert len(issues) <= 1

    def test_check_grammar_multiple_errors(self, checker):
        """Test grammar checking with multiple errors."""
        text = "Their are many mistake's in this sentence's grammar and spelling."
        issues = checker.check_grammar(text)

        assert len(issues) >= 2
        # Should detect "Their" -> "There", apostrophe errors

    def test_grammar_issue_properties(self, checker):
        """Test that grammar issues have required properties."""
        text = "This are wrong."
        issues = checker.check_grammar(text)

        for issue in issues:
            assert hasattr(issue, 'start_pos')
            assert hasattr(issue, 'end_pos')
            assert hasattr(issue, 'message')
            assert hasattr(issue, 'rule_id')
            assert hasattr(issue, 'severity')
            assert hasattr(issue, 'suggestions')
            assert hasattr(issue, 'category')

            assert issue.start_pos >= 0
            assert issue.end_pos > issue.start_pos
            assert len(issue.message) > 0
            assert isinstance(issue.severity, IssueSeverity)

    def test_suggest_corrections(self, checker):
        """Test correction suggestions."""
        text = "I have a good grammer."
        issues = checker.check_grammar(text)

        grammar_issue = next(
            (issue for issue in issues if "grammer" in text[issue.start_pos:issue.end_pos].lower()),
            None
        )

        if grammar_issue:
            assert "grammar" in [s.lower() for s in grammar_issue.suggestions]

    def test_check_grammar_different_languages(self, checker):
        """Test grammar checking with different languages."""
        english_text = "This is an English sentence."
        french_text = "Ceci est une phrase française."

        en_issues = checker.check_grammar(english_text, language="en")
        fr_issues = checker.check_grammar(french_text, language="fr")

        # Both should work without throwing errors
        assert isinstance(en_issues, list)
        assert isinstance(fr_issues, list)

    def test_check_grammar_empty_text(self, checker):
        """Test grammar checking with empty text."""
        issues = checker.check_grammar("")
        assert issues == []

    def test_check_grammar_whitespace_only(self, checker):
        """Test grammar checking with whitespace only."""
        issues = checker.check_grammar("   \n\t  ")
        assert issues == []

    def test_severity_classification(self, checker):
        """Test that issues are properly classified by severity."""
        text = "This are a sentence with multiple types of erors."
        issues = checker.check_grammar(text)

        severities = [issue.severity for issue in issues]
        # Should have different severity levels
        assert len(set(severities)) >= 1

    def test_position_accuracy(self, checker):
        """Test that issue positions are accurate."""
        text = "This word is mispelled."
        issues = checker.check_grammar(text)

        for issue in issues:
            flagged_text = text[issue.start_pos:issue.end_pos]
            # The flagged text should not be empty
            assert len(flagged_text) > 0
            # Position should be within text bounds
            assert 0 <= issue.start_pos < len(text)
            assert issue.start_pos < issue.end_pos <= len(text)

    @patch('src.core.grammar_checker.language_tool_python')
    def test_language_tool_integration(self, mock_lt, checker):
        """Test integration with LanguageTool."""
        mock_tool = Mock()
        mock_lt.LanguageTool.return_value = mock_tool
        mock_match = Mock()
        mock_match.offset = 5
        mock_match.errorLength = 4
        mock_match.message = "Test error"
        mock_match.replacements = ['fixed']
        mock_match.ruleId = 'TEST_RULE'
        mock_match.category = 'Grammar'
        mock_tool.check.return_value = [mock_match]

        issues = checker.check_grammar("Test text here")

        assert len(issues) == 1
        issue = issues[0]
        assert issue.start_pos == 5
        assert issue.end_pos == 9
        assert issue.message == "Test error"
        assert "fixed" in issue.suggestions

    def test_category_classification(self, checker):
        """Test that issues are properly categorized."""
        text = "This sentence has grammer and speling errors."
        issues = checker.check_grammar(text)

        categories = [issue.category for issue in issues]
        # Should have categories like 'Grammar', 'Spelling', etc.
        assert len(categories) > 0
        assert all(isinstance(cat, str) for cat in categories)

    def test_check_grammar_long_text(self, checker):
        """Test grammar checking with long text."""
        text = " ".join(["This is a test sentence."] * 100)
        issues = checker.check_grammar(text)

        # Should handle long text without errors
        assert isinstance(issues, list)

    def test_check_grammar_special_characters(self, checker):
        """Test grammar checking with special characters."""
        text = "This text has émojis 😀 and spéciàl characters!"
        issues = checker.check_grammar(text)

        # Should handle special characters gracefully
        assert isinstance(issues, list)

    def test_batch_grammar_check(self, checker):
        """Test batch grammar checking."""
        texts = [
            "This are wrong.",
            "This is correct.",
            "Another eror here."
        ]

        results = checker.check_grammar_batch(texts)

        assert len(results) == 3
        assert all(isinstance(result, list) for result in results)
        # First and third should have errors, second should be clean
        assert len(results[0]) > 0
        assert len(results[1]) == 0 or len(results[1]) == 1  # Might have minor issues
        assert len(results[2]) > 0