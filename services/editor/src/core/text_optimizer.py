"""Text optimization engine for comprehensive text improvement."""

import logging
import re
import time

import spacy
import textstat

from ..models.edit_request import EditRequest, EditResponse, EditSuggestion, EditType
from ..models.text_analysis import ContentAnalysis, ReadabilityMetrics, TextAnalysis
from .config import settings
from .content_enhancer import ContentEnhancer
from .grammar_checker import GrammarChecker
from .style_analyzer import StyleAnalyzer
from .version_control import VersionController

logger = logging.getLogger(__name__)


class TextOptimizer:
    """Main text optimization engine."""

    def __init__(self):
        """Initialize the text optimizer."""
        self.grammar_checker = GrammarChecker()
        self.style_analyzer = StyleAnalyzer()
        self.content_enhancer = ContentEnhancer()
        self.version_controller = VersionController()

        # Load NLP models
        self._load_models()

    def _load_models(self):
        """Load required NLP models."""
        try:
            self.nlp_en = spacy.load(settings.SPACY_MODEL_EN)
            logger.info(f"Loaded English model: {settings.SPACY_MODEL_EN}")
        except OSError:
            logger.warning(
                f"Could not load {settings.SPACY_MODEL_EN}, using basic model"
            )
            self.nlp_en = None

        try:
            self.nlp_fr = spacy.load(settings.SPACY_MODEL_FR)
            logger.info(f"Loaded French model: {settings.SPACY_MODEL_FR}")
        except OSError:
            logger.warning(f"Could not load {settings.SPACY_MODEL_FR}")
            self.nlp_fr = None

    def analyze_text(self, text: str, language: str = "en") -> TextAnalysis:
        """Analyze text for grammar, style, and content issues."""
        if not text or text.strip() == "":
            raise ValueError("Text cannot be empty")

        start_time = time.time()

        # Grammar analysis
        grammar_issues = self.grammar_checker.check_grammar(text, language)

        # Style analysis
        style_issues = self.style_analyzer.analyze_style(text, language)

        # Readability metrics
        readability = self._calculate_readability_metrics(text)

        # Content analysis
        content_analysis = self._analyze_content(text, language)

        # Calculate quality scores
        grammar_score = max(0, 100 - len(grammar_issues) * 5)
        style_score = max(0, 100 - len(style_issues) * 3)
        content_score = self._calculate_content_score(content_analysis)
        overall_score = (grammar_score + style_score + content_score) / 3

        analysis_time = time.time() - start_time

        return TextAnalysis(
            text=text,
            language=language,
            grammar_issues=grammar_issues,
            style_issues=style_issues,
            readability=readability,
            content_analysis=content_analysis,
            overall_quality_score=overall_score,
            grammar_score=grammar_score,
            style_score=style_score,
            content_score=content_score,
            analysis_time=analysis_time,
        )

    def optimize_text(self, request: EditRequest) -> EditResponse:
        """Optimize text based on the edit request."""
        if not request.text or request.text.strip() == "":
            raise ValueError("Text cannot be empty")

        if len(request.text) > settings.MAX_TEXT_LENGTH:
            raise ValueError("Text too long")

        start_time = time.time()

        # Analyze the original text
        analysis = self.analyze_text(request.text, request.language)

        # Apply optimizations based on edit type
        optimized_text = request.text
        suggestions = []

        grammar_fixes = 0
        style_improvements = 0
        content_enhancements = 0

        if request.edit_type in [EditType.GRAMMAR, EditType.COMPREHENSIVE]:
            optimized_text, grammar_suggestions = self._apply_grammar_fixes(
                optimized_text, analysis.grammar_issues
            )
            suggestions.extend(grammar_suggestions)
            grammar_fixes = len(grammar_suggestions)

        if request.edit_type in [
            EditType.STYLE,
            EditType.COMPREHENSIVE,
            EditType.TONE_ADJUSTMENT,
        ]:
            optimized_text, style_suggestions = self._apply_style_improvements(
                optimized_text, analysis.style_issues, request.tone
            )
            suggestions.extend(style_suggestions)
            style_improvements = len(style_suggestions)

        if request.edit_type in [EditType.CONTENT_ENHANCEMENT, EditType.COMPREHENSIVE]:
            optimized_text, content_suggestions = self._apply_content_enhancements(
                optimized_text, request.industry, request.role
            )
            suggestions.extend(content_suggestions)
            content_enhancements = len(content_suggestions)

        if request.edit_type == EditType.QUANTIFICATION:
            optimized_text, quant_suggestions = self._apply_quantification(
                optimized_text
            )
            suggestions.extend(quant_suggestions)
            content_enhancements += len(quant_suggestions)

        # Calculate readability score for optimized text
        readability_score = textstat.flesch_reading_ease(optimized_text)

        # Handle version control
        version_id = None
        version_number = 1

        if request.track_changes:
            version = self.version_controller.create_version(
                session_id=request.session_id,
                text=optimized_text,
                edit_type=request.edit_type.value,
                comment=request.version_comment,
            )
            version_id = version.version_id
            version_number = version.version_number

        processing_time = time.time() - start_time

        return EditResponse(
            session_id=request.session_id,
            original_text=request.text,
            edited_text=optimized_text,
            suggestions=suggestions,
            readability_score=readability_score,
            grammar_issues_fixed=grammar_fixes,
            style_improvements=style_improvements,
            content_enhancements=content_enhancements,
            version_id=version_id,
            version_number=version_number,
            processing_time=processing_time,
        )

    def _calculate_readability_metrics(self, text: str) -> ReadabilityMetrics:
        """Calculate readability metrics for text."""
        return ReadabilityMetrics(
            flesch_reading_ease=textstat.flesch_reading_ease(text),
            flesch_kincaid_grade=textstat.flesch_kincaid_grade(text),
            gunning_fog=textstat.gunning_fog(text),
            automated_readability_index=textstat.automated_readability_index(text),
            coleman_liau_index=textstat.coleman_liau_index(text),
            sentence_count=textstat.sentence_count(text),
            word_count=len(text.split()),
            character_count=len(text),
            syllable_count=textstat.syllable_count(text),
            avg_sentence_length=textstat.avg_sentence_length(text),
            avg_syllables_per_word=textstat.avg_syllables_per_word(text),
        )

    def _analyze_content(self, text: str, language: str) -> ContentAnalysis:
        """Analyze content quality and structure."""
        # TODO: Use spaCy for advanced analysis when available
        # nlp = self.nlp_en if language == "en" else self.nlp_fr
        # if nlp:
        #     doc = nlp(text)
        # else:
        #     doc = None

        # Count quantified achievements (numbers, percentages)
        quantified_pattern = (
            r"\b\d+(?:[\.,]\d+)?(?:%|percent|k|thousand|million|billion)?\b"
        )
        quantified_achievements = len(
            re.findall(quantified_pattern, text, re.IGNORECASE)
        )

        # Count action verbs (basic implementation)
        action_verbs = self._count_action_verbs(text)

        # Count passive voice instances
        passive_voice_count = self._count_passive_voice(text)

        # Count weak words
        weak_words = self._count_weak_words(text)

        # Identify industry keywords (basic implementation)
        industry_keywords = self._extract_industry_keywords(text)

        # Structure analysis
        bullet_points = text.count("•") + text.count("-") + text.count("*")
        paragraphs = len([p for p in text.split("\n\n") if p.strip()])
        headings = len(re.findall(r"^#+\s", text, re.MULTILINE))

        # Basic tone analysis
        tone_scores = self._analyze_tone(text)
        formality_score = self._calculate_formality_score(text)

        return ContentAnalysis(
            quantified_achievements=quantified_achievements,
            action_verbs_count=action_verbs,
            passive_voice_count=passive_voice_count,
            weak_words_count=weak_words,
            industry_keywords=industry_keywords,
            technical_terms=[],  # TODO: Implement technical term extraction
            jargon_count=0,  # TODO: Implement jargon detection
            bullet_points=bullet_points,
            paragraphs=max(1, paragraphs),
            headings=headings,
            tone_scores=tone_scores,
            formality_score=formality_score,
        )

    def _count_action_verbs(self, text: str) -> int:
        """Count strong action verbs in text."""
        action_verbs = {
            "achieved",
            "accelerated",
            "accomplished",
            "advanced",
            "analyzed",
            "built",
            "created",
            "designed",
            "developed",
            "engineered",
            "implemented",
            "improved",
            "increased",
            "led",
            "managed",
            "optimized",
            "organized",
            "reduced",
            "resolved",
            "streamlined",
        }

        words = text.lower().split()
        return sum(1 for word in words if word.strip(".,!?;:") in action_verbs)

    def _count_passive_voice(self, text: str) -> int:
        """Count passive voice instances."""
        passive_patterns = [
            r"\bwas\s+\w+ed\b",
            r"\bwere\s+\w+ed\b",
            r"\bbeing\s+\w+ed\b",
            r"\bbeen\s+\w+ed\b",
        ]

        count = 0
        for pattern in passive_patterns:
            count += len(re.findall(pattern, text, re.IGNORECASE))

        return count

    def _count_weak_words(self, text: str) -> int:
        """Count weak words and phrases."""
        weak_phrases = {
            "responsible for",
            "helped with",
            "assisted in",
            "worked on",
            "involved in",
            "participated in",
            "contributed to",
            "did",
            "made",
            "got",
            "things",
            "stuff",
            "various",
            "several",
        }

        text_lower = text.lower()
        return sum(1 for phrase in weak_phrases if phrase in text_lower)

    def _extract_industry_keywords(self, text: str) -> list[str]:
        """Extract industry-specific keywords."""
        # Basic implementation - can be enhanced with industry-specific dictionaries
        tech_keywords = {
            "api",
            "database",
            "algorithm",
            "framework",
            "software",
            "development",
            "programming",
            "system",
            "application",
            "architecture",
            "cloud",
            "microservices",
            "devops",
        }

        words = set(word.lower().strip(".,!?;:") for word in text.split())
        return list(words.intersection(tech_keywords))

    def _analyze_tone(self, text: str) -> dict[str, float]:
        """Analyze tone of the text."""
        # Basic tone analysis - can be enhanced with ML models
        formal_indicators = ["furthermore", "moreover", "therefore", "consequently"]
        casual_indicators = ["really", "pretty", "quite", "sort of", "kind of"]

        text_lower = text.lower()
        formal_count = sum(
            1 for indicator in formal_indicators if indicator in text_lower
        )
        casual_count = sum(
            1 for indicator in casual_indicators if indicator in text_lower
        )

        total_words = len(text.split())

        return {
            "formal": formal_count / max(1, total_words) * 100,
            "casual": casual_count / max(1, total_words) * 100,
        }

    def _calculate_formality_score(self, text: str) -> float:
        """Calculate formality score (0-1)."""
        # Basic implementation
        formal_words = ["utilize", "demonstrate", "facilitate", "implement"]
        casual_words = ["use", "show", "help", "do"]

        text_lower = text.lower()
        formal_count = sum(1 for word in formal_words if word in text_lower)
        casual_count = sum(1 for word in casual_words if word in text_lower)

        if formal_count + casual_count == 0:
            return 0.5

        return formal_count / (formal_count + casual_count)

    def _calculate_content_score(self, content: ContentAnalysis) -> float:
        """Calculate content quality score."""
        score = 50  # Base score

        # Add points for good practices
        score += min(20, content.quantified_achievements * 5)
        score += min(15, content.action_verbs_count * 2)
        score += min(10, len(content.industry_keywords) * 3)

        # Subtract points for issues
        score -= min(20, content.weak_words_count * 3)
        score -= min(15, content.passive_voice_count * 2)

        return max(0, min(100, score))

    def _apply_grammar_fixes(
        self, text: str, grammar_issues
    ) -> tuple[str, list[EditSuggestion]]:
        """Apply grammar fixes to text."""
        suggestions = []
        fixed_text = text

        # Sort issues by position (reverse order to maintain positions)
        sorted_issues = sorted(grammar_issues, key=lambda x: x.start_pos, reverse=True)

        for issue in sorted_issues:
            if issue.suggestions:
                suggestion = EditSuggestion(
                    start_pos=issue.start_pos,
                    end_pos=issue.end_pos,
                    original_text=text[issue.start_pos : issue.end_pos],
                    suggested_text=issue.suggestions[0],
                    reason=issue.message,
                    confidence=0.8,
                    edit_type=EditType.GRAMMAR,
                )
                suggestions.append(suggestion)

                # Apply the fix
                fixed_text = (
                    fixed_text[: issue.start_pos]
                    + issue.suggestions[0]
                    + fixed_text[issue.end_pos :]
                )

        return fixed_text, suggestions

    def _apply_style_improvements(
        self, text: str, style_issues, tone: str | None
    ) -> tuple[str, list[EditSuggestion]]:
        """Apply style improvements to text."""
        suggestions = []
        improved_text = text

        # Apply style issue fixes
        sorted_issues = sorted(style_issues, key=lambda x: x.start_pos, reverse=True)

        for issue in sorted_issues:
            if issue.suggestions:
                suggestion = EditSuggestion(
                    start_pos=issue.start_pos,
                    end_pos=issue.end_pos,
                    original_text=text[issue.start_pos : issue.end_pos],
                    suggested_text=issue.suggestions[0],
                    reason=issue.improvement_reason,
                    confidence=0.7,
                    edit_type=EditType.STYLE,
                )
                suggestions.append(suggestion)

                improved_text = (
                    improved_text[: issue.start_pos]
                    + issue.suggestions[0]
                    + improved_text[issue.end_pos :]
                )

        # Apply tone adjustments
        if tone == "professional":
            improved_text = self._make_more_professional(improved_text)

        return improved_text, suggestions

    def _apply_content_enhancements(
        self, text: str, industry: str | None, role: str | None
    ) -> tuple[str, list[EditSuggestion]]:
        """Apply content enhancements."""
        suggestions = []
        enhanced_text = text

        # Replace weak phrases with stronger alternatives
        weak_replacements = {
            "responsible for": "managed",
            "helped with": "contributed to",
            "worked on": "developed",
            "did": "executed",
            "made": "created",
        }

        for weak, strong in weak_replacements.items():
            if weak in enhanced_text.lower():
                pattern = re.compile(re.escape(weak), re.IGNORECASE)
                match = pattern.search(enhanced_text)
                if match:
                    suggestion = EditSuggestion(
                        start_pos=match.start(),
                        end_pos=match.end(),
                        original_text=match.group(),
                        suggested_text=strong,
                        reason="Replace weak phrase with stronger action verb",
                        confidence=0.9,
                        edit_type=EditType.CONTENT_ENHANCEMENT,
                    )
                    suggestions.append(suggestion)
                    enhanced_text = pattern.sub(strong, enhanced_text, count=1)

        return enhanced_text, suggestions

    def _apply_quantification(self, text: str) -> tuple[str, list[EditSuggestion]]:
        """Suggest quantification for achievements."""
        suggestions = []

        # Find achievements that could be quantified
        achievement_patterns = [
            r"increased\s+\w+",
            r"improved\s+\w+",
            r"reduced\s+\w+",
            r"optimized\s+\w+",
        ]

        for pattern in achievement_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                suggestion = EditSuggestion(
                    start_pos=match.start(),
                    end_pos=match.end(),
                    original_text=match.group(),
                    suggested_text=f"{match.group()} by X%",
                    reason="Add quantification to strengthen impact",
                    confidence=0.6,
                    edit_type=EditType.QUANTIFICATION,
                )
                suggestions.append(suggestion)

        return text, suggestions

    def _make_more_professional(self, text: str) -> str:
        """Make text more professional in tone."""
        casual_to_professional = {
            "really": "significantly",
            "pretty": "quite",
            "stuff": "materials",
            "things": "items",
            "got": "obtained",
            "did": "executed",
        }

        professional_text = text
        for casual, professional in casual_to_professional.items():
            professional_text = re.sub(
                r"\b" + re.escape(casual) + r"\b",
                professional,
                professional_text,
                flags=re.IGNORECASE,
            )

        return professional_text
