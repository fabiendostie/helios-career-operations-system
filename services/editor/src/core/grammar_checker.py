"""Grammar checking functionality using LanguageTool."""

import logging

try:
    import language_tool_python
except ImportError:
    language_tool_python = None

from ..models.text_analysis import GrammarIssue, IssueSeverity
from .config import settings

logger = logging.getLogger(__name__)


class GrammarChecker:
    """Grammar checker using LanguageTool."""

    def __init__(self):
        """Initialize the grammar checker."""
        self.tools = {}
        self._initialize_tools()

    def _initialize_tools(self):
        """Initialize LanguageTool instances for different languages."""
        if not language_tool_python:
            logger.warning(
                "LanguageTool not available. Grammar checking will be limited."
            )
            return

        try:
            # Initialize English tool
            self.tools["en"] = language_tool_python.LanguageTool("en-US")
            logger.info("Initialized English LanguageTool")

            # Initialize French tool if needed
            if settings.SPACY_MODEL_FR:
                self.tools["fr"] = language_tool_python.LanguageTool("fr")
                logger.info("Initialized French LanguageTool")

        except Exception as e:
            logger.error(f"Failed to initialize LanguageTool: {e}")

    def check_grammar(self, text: str, language: str = "en") -> list[GrammarIssue]:
        """Check grammar in the given text."""
        if not text or text.strip() == "":
            return []

        if not settings.GRAMMAR_CHECK_ENABLED:
            return []

        # Use LanguageTool if available
        if language_tool_python and language in self.tools:
            return self._check_with_languagetool(text, language)

        # Fallback to basic checks
        return self._basic_grammar_check(text)

    def _check_with_languagetool(self, text: str, language: str) -> list[GrammarIssue]:
        """Check grammar using LanguageTool."""
        try:
            tool = self.tools[language]
            matches = tool.check(text)

            issues = []
            for match in matches:
                severity = self._determine_severity(match)

                issue = GrammarIssue(
                    start_pos=match.offset,
                    end_pos=match.offset + match.errorLength,
                    message=match.message,
                    rule_id=match.ruleId,
                    severity=severity,
                    suggestions=match.replacements[:3],  # Limit to top 3 suggestions
                    category=getattr(match, "category", "Grammar"),
                )
                issues.append(issue)

            return issues

        except Exception as e:
            logger.error(f"Error checking grammar with LanguageTool: {e}")
            return self._basic_grammar_check(text)

    def _basic_grammar_check(self, text: str) -> list[GrammarIssue]:
        """Basic grammar checking without external tools."""
        issues = []

        # Check for common grammar mistakes
        issues.extend(self._check_subject_verb_agreement(text))
        issues.extend(self._check_common_misspellings(text))
        issues.extend(self._check_apostrophes(text))

        return issues

    def _check_subject_verb_agreement(self, text: str) -> list[GrammarIssue]:
        """Check for basic subject-verb agreement issues."""
        import re

        issues = []

        # Pattern for "This are" - should be "This is"
        pattern = r"\bThis\s+are\b"
        for match in re.finditer(pattern, text, re.IGNORECASE):
            issue = GrammarIssue(
                start_pos=match.start(),
                end_pos=match.end(),
                message="Subject-verb disagreement. 'This' should be followed by 'is', not 'are'.",
                rule_id="BASIC_SUBJECT_VERB",
                severity=IssueSeverity.HIGH,
                suggestions=["This is"],
                category="Grammar",
            )
            issues.append(issue)

        # Pattern for "These is" - should be "These are"
        pattern = r"\bThese\s+is\b"
        for match in re.finditer(pattern, text, re.IGNORECASE):
            issue = GrammarIssue(
                start_pos=match.start(),
                end_pos=match.end(),
                message="Subject-verb disagreement. 'These' should be followed by 'are', not 'is'.",
                rule_id="BASIC_SUBJECT_VERB",
                severity=IssueSeverity.HIGH,
                suggestions=["These are"],
                category="Grammar",
            )
            issues.append(issue)

        return issues

    def _check_common_misspellings(self, text: str) -> list[GrammarIssue]:
        """Check for common misspellings."""
        import re

        issues = []

        # Common misspellings
        misspellings = {
            r"\bgrammer\b": ("grammar", "Incorrect spelling"),
            r"\bspeling\b": ("spelling", "Incorrect spelling"),
            r"\beror\b": ("error", "Incorrect spelling"),
            r"\beroor\b": ("error", "Incorrect spelling"),
            r"\berors\b": ("errors", "Incorrect spelling"),
            r"\bmispelled\b": ("misspelled", "Incorrect spelling"),
            r"\brecieve\b": ("receive", "Incorrect spelling"),
            r"\bacheive\b": ("achieve", "Incorrect spelling"),
        }

        for pattern, (correction, message) in misspellings.items():
            for match in re.finditer(pattern, text, re.IGNORECASE):
                # Preserve original case
                original = match.group()
                if original.isupper():
                    suggestion = correction.upper()
                elif original[0].isupper():
                    suggestion = correction.capitalize()
                else:
                    suggestion = correction

                issue = GrammarIssue(
                    start_pos=match.start(),
                    end_pos=match.end(),
                    message=message,
                    rule_id="BASIC_SPELLING",
                    severity=IssueSeverity.MEDIUM,
                    suggestions=[suggestion],
                    category="Spelling",
                )
                issues.append(issue)

        return issues

    def _check_apostrophes(self, text: str) -> list[GrammarIssue]:
        """Check for incorrect apostrophe usage."""
        import re

        issues = []

        # Check for incorrect possessive apostrophes
        # Pattern for "word's" where it should be "words" (plural, not possessive)
        incorrect_possessives = [
            r"\bmistake\'s\b",  # "mistake's" in "many mistake's"
            r"\bsentence\'s\b",  # Similar pattern
        ]

        for pattern in incorrect_possessives:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                # Remove apostrophe and 's'
                word = match.group()[:-2]
                suggestion = word + "s" if not word.endswith("s") else word

                issue = GrammarIssue(
                    start_pos=match.start(),
                    end_pos=match.end(),
                    message="Incorrect apostrophe usage. This appears to be a plural, not possessive.",
                    rule_id="BASIC_APOSTROPHE",
                    severity=IssueSeverity.MEDIUM,
                    suggestions=[suggestion],
                    category="Punctuation",
                )
                issues.append(issue)

        return issues

    def _determine_severity(self, match) -> IssueSeverity:
        """Determine severity of a grammar issue."""
        # Map LanguageTool categories to severity levels
        category = getattr(match, "category", "").lower()
        rule_id = getattr(match, "ruleId", "").lower()

        if "spelling" in category or "typo" in rule_id:
            return IssueSeverity.HIGH

        if "grammar" in category:
            return IssueSeverity.HIGH

        if "style" in category or "redundancy" in category:
            return IssueSeverity.MEDIUM

        if "punctuation" in category:
            return IssueSeverity.MEDIUM

        # Default to medium severity
        return IssueSeverity.MEDIUM

    def suggest_corrections(self, text: str, issue: GrammarIssue) -> list[str]:
        """Get correction suggestions for a specific issue."""
        return issue.suggestions

    def check_grammar_batch(
        self, texts: list[str], language: str = "en"
    ) -> list[list[GrammarIssue]]:
        """Check grammar for multiple texts in batch."""
        results = []
        for text in texts:
            issues = self.check_grammar(text, language)
            results.append(issues)
        return results

    def __del__(self):
        """Clean up LanguageTool instances."""
        if hasattr(self, "tools"):
            for tool in self.tools.values():
                try:
                    if hasattr(tool, "close"):
                        tool.close()
                except Exception:
                    pass  # Ignore cleanup errors
