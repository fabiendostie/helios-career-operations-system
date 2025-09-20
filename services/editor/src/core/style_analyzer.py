"""Style analysis for text improvement."""

import logging
import re
from typing import List, Dict, Set

from .config import settings
from ..models.text_analysis import StyleIssue, IssueSeverity

logger = logging.getLogger(__name__)


class StyleAnalyzer:
    """Analyzer for text style and writing quality."""

    def __init__(self):
        """Initialize the style analyzer."""
        self.weak_words = self._load_weak_words()
        self.filler_words = self._load_filler_words()
        self.action_verbs = self._load_action_verbs()
        self.passive_indicators = self._load_passive_indicators()

    def _load_weak_words(self) -> Set[str]:
        """Load weak words that should be avoided."""
        return {
            'things', 'stuff', 'very', 'really', 'quite', 'rather',
            'somewhat', 'fairly', 'pretty', 'kind of', 'sort of',
            'a lot', 'lots of', 'many', 'various', 'several',
            'numerous', 'multiple', 'different', 'good', 'bad',
            'nice', 'fine', 'okay', 'alright'
        }

    def _load_filler_words(self) -> Set[str]:
        """Load filler words that add no value."""
        return {
            'actually', 'basically', 'essentially', 'literally',
            'obviously', 'clearly', 'definitely', 'certainly',
            'absolutely', 'totally', 'completely', 'exactly',
            'just', 'simply', 'really', 'very', 'quite'
        }

    def _load_action_verbs(self) -> Set[str]:
        """Load strong action verbs for replacements."""
        return {
            'achieved', 'accelerated', 'accomplished', 'adapted',
            'administered', 'advanced', 'analyzed', 'applied',
            'architected', 'assembled', 'built', 'calculated',
            'collaborated', 'communicated', 'compiled', 'completed',
            'computed', 'conceived', 'conducted', 'constructed',
            'created', 'debugged', 'demonstrated', 'designed',
            'developed', 'devised', 'directed', 'discovered',
            'engineered', 'enhanced', 'established', 'evaluated',
            'executed', 'expanded', 'facilitated', 'formulated',
            'generated', 'guided', 'implemented', 'improved',
            'increased', 'initiated', 'innovated', 'integrated',
            'introduced', 'launched', 'led', 'managed', 'optimized',
            'organized', 'programmed', 'reduced', 'refined',
            'resolved', 'spearheaded', 'streamlined', 'supervised',
            'transformed', 'upgraded'
        }

    def _load_passive_indicators(self) -> List[str]:
        """Load patterns that indicate passive voice."""
        return [
            r'\bwas\s+\w+ed\b',
            r'\bwere\s+\w+ed\b',
            r'\bbeing\s+\w+ed\b',
            r'\bbeen\s+\w+ed\b',
            r'\bis\s+\w+ed\b',
            r'\bare\s+\w+ed\b',
            r'\bwill\s+be\s+\w+ed\b',
            r'\bhas\s+been\s+\w+ed\b',
            r'\bhave\s+been\s+\w+ed\b'
        ]

    def analyze_style(self, text: str, language: str = "en") -> List[StyleIssue]:
        """Analyze text for style issues."""
        if not text or text.strip() == "":
            return []

        if not settings.STYLE_CHECK_ENABLED:
            return []

        issues = []

        # Check for various style issues
        issues.extend(self._check_weak_words(text))
        issues.extend(self._check_filler_words(text))
        issues.extend(self._check_passive_voice(text))
        issues.extend(self._check_weak_phrases(text))
        issues.extend(self._check_redundancy(text))
        issues.extend(self._check_sentence_variety(text))
        issues.extend(self._check_professional_tone(text))

        return issues

    def _check_weak_words(self, text: str) -> List[StyleIssue]:
        """Check for weak words that dilute impact."""
        issues = []

        for weak_word in self.weak_words:
            pattern = r'\b' + re.escape(weak_word) + r'\b'
            for match in re.finditer(pattern, text, re.IGNORECASE):
                suggestions = self._suggest_strong_alternatives(weak_word)

                issue = StyleIssue(
                    start_pos=match.start(),
                    end_pos=match.end(),
                    message=f"'{match.group()}' is a weak word that dilutes impact",
                    issue_type="weak_word",
                    severity=IssueSeverity.MEDIUM,
                    suggestions=suggestions,
                    improvement_reason="Replace with more specific or impactful language"
                )
                issues.append(issue)

        return issues

    def _check_filler_words(self, text: str) -> List[StyleIssue]:
        """Check for filler words that add no value."""
        issues = []

        for filler in self.filler_words:
            pattern = r'\b' + re.escape(filler) + r'\b'
            for match in re.finditer(pattern, text, re.IGNORECASE):
                issue = StyleIssue(
                    start_pos=match.start(),
                    end_pos=match.end(),
                    message=f"'{match.group()}' is a filler word that adds no value",
                    issue_type="filler_word",
                    severity=IssueSeverity.LOW,
                    suggestions=[""],  # Suggest removal
                    improvement_reason="Remove unnecessary filler words for cleaner prose"
                )
                issues.append(issue)

        return issues

    def _check_passive_voice(self, text: str) -> List[StyleIssue]:
        """Check for passive voice constructions."""
        issues = []

        for pattern in self.passive_indicators:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                # Get context to suggest active alternative
                start = max(0, match.start() - 20)
                end = min(len(text), match.end() + 20)
                context = text[start:end]

                suggestions = self._suggest_active_voice(match.group(), context)

                issue = StyleIssue(
                    start_pos=match.start(),
                    end_pos=match.end(),
                    message=f"Passive voice: '{match.group()}'",
                    issue_type="passive_voice",
                    severity=IssueSeverity.MEDIUM,
                    suggestions=suggestions,
                    improvement_reason="Active voice is more direct and engaging"
                )
                issues.append(issue)

        return issues

    def _check_weak_phrases(self, text: str) -> List[StyleIssue]:
        """Check for weak phrases that should be strengthened."""
        weak_phrases = {
            'responsible for': ['managed', 'led', 'oversaw', 'directed'],
            'helped with': ['contributed to', 'assisted in', 'supported'],
            'worked on': ['developed', 'created', 'built', 'designed'],
            'in charge of': ['managed', 'supervised', 'led'],
            'did': ['executed', 'performed', 'completed', 'accomplished'],
            'made': ['created', 'developed', 'built', 'generated'],
            'got': ['achieved', 'obtained', 'secured', 'earned'],
            'used': ['utilized', 'employed', 'leveraged', 'applied']
        }

        issues = []

        for weak_phrase, alternatives in weak_phrases.items():
            pattern = r'\b' + re.escape(weak_phrase) + r'\b'
            for match in re.finditer(pattern, text, re.IGNORECASE):
                issue = StyleIssue(
                    start_pos=match.start(),
                    end_pos=match.end(),
                    message=f"'{match.group()}' is a weak phrase",
                    issue_type="weak_phrase",
                    severity=IssueSeverity.HIGH,
                    suggestions=alternatives[:3],  # Top 3 alternatives
                    improvement_reason="Use stronger, more specific action words"
                )
                issues.append(issue)

        return issues

    def _check_redundancy(self, text: str) -> List[StyleIssue]:
        """Check for redundant phrases."""
        redundant_phrases = {
            'advance planning': ['planning'],
            'end result': ['result'],
            'future plans': ['plans'],
            'past history': ['history'],
            'basic fundamentals': ['fundamentals', 'basics'],
            'close proximity': ['proximity'],
            'completely filled': ['filled'],
            'exactly the same': ['identical'],
            'first priority': ['priority'],
            'free gift': ['gift'],
            'new innovation': ['innovation'],
            'personal opinion': ['opinion'],
            'true facts': ['facts'],
            'unexpected surprise': ['surprise']
        }

        issues = []

        for redundant, alternatives in redundant_phrases.items():
            pattern = r'\b' + re.escape(redundant) + r'\b'
            for match in re.finditer(pattern, text, re.IGNORECASE):
                issue = StyleIssue(
                    start_pos=match.start(),
                    end_pos=match.end(),
                    message=f"'{match.group()}' is redundant",
                    issue_type="redundancy",
                    severity=IssueSeverity.MEDIUM,
                    suggestions=alternatives,
                    improvement_reason="Remove redundancy for cleaner writing"
                )
                issues.append(issue)

        return issues

    def _check_sentence_variety(self, text: str) -> List[StyleIssue]:
        """Check for lack of sentence variety."""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if len(sentences) < 3:
            return []

        issues = []

        # Check for repetitive sentence starts
        sentence_starts = []
        for sentence in sentences:
            words = sentence.split()
            if words:
                start = words[0].lower()
                sentence_starts.append(start)

        # Find repetitive starts
        start_counts = {}
        for start in sentence_starts:
            start_counts[start] = start_counts.get(start, 0) + 1

        for start, count in start_counts.items():
            if count >= 3:  # Three or more sentences starting the same way
                # Find first occurrence to place the issue
                for i, sentence in enumerate(sentences):
                    words = sentence.split()
                    if words and words[0].lower() == start:
                        # Find position in original text
                        sentence_start = text.find(sentence)
                        if sentence_start >= 0:
                            issue = StyleIssue(
                                start_pos=sentence_start,
                                end_pos=sentence_start + len(words[0]),
                                message=f"Multiple sentences start with '{start}' - vary sentence structure",
                                issue_type="sentence_variety",
                                severity=IssueSeverity.LOW,
                                suggestions=["Consider varying sentence structure"],
                                improvement_reason="Varied sentence structure improves readability"
                            )
                            issues.append(issue)
                            break

        return issues

    def _check_professional_tone(self, text: str) -> List[StyleIssue]:
        """Check for unprofessional language."""
        unprofessional_words = {
            'awesome': ['excellent', 'outstanding', 'exceptional'],
            'cool': ['impressive', 'effective', 'valuable'],
            'crazy': ['remarkable', 'significant', 'substantial'],
            'insane': ['extraordinary', 'exceptional', 'remarkable'],
            'sick': ['excellent', 'impressive', 'outstanding'],
            'dope': ['excellent', 'effective', 'valuable'],
            'lit': ['excellent', 'outstanding', 'impressive'],
            'fire': ['excellent', 'outstanding', 'exceptional']
        }

        issues = []

        for unprofessional, alternatives in unprofessional_words.items():
            pattern = r'\b' + re.escape(unprofessional) + r'\b'
            for match in re.finditer(pattern, text, re.IGNORECASE):
                issue = StyleIssue(
                    start_pos=match.start(),
                    end_pos=match.end(),
                    message=f"'{match.group()}' may be too casual for professional writing",
                    issue_type="tone",
                    severity=IssueSeverity.MEDIUM,
                    suggestions=alternatives,
                    improvement_reason="Use more professional language"
                )
                issues.append(issue)

        return issues

    def _suggest_strong_alternatives(self, weak_word: str) -> List[str]:
        """Suggest stronger alternatives for weak words."""
        alternatives = {
            'things': ['items', 'elements', 'components', 'aspects'],
            'stuff': ['materials', 'items', 'elements', 'components'],
            'very': ['extremely', 'highly', 'significantly'],
            'really': ['significantly', 'substantially', 'considerably'],
            'good': ['excellent', 'effective', 'valuable', 'beneficial'],
            'bad': ['ineffective', 'problematic', 'detrimental'],
            'big': ['substantial', 'significant', 'major', 'extensive'],
            'small': ['minor', 'minimal', 'limited', 'modest'],
            'many': ['numerous', 'multiple', 'several'],
            'a lot': ['significantly', 'substantially', 'considerably']
        }

        return alternatives.get(weak_word.lower(), ['more specific term'])

    def _suggest_active_voice(self, passive_phrase: str, context: str) -> List[str]:
        """Suggest active voice alternatives for passive constructions."""
        # Basic suggestions - could be enhanced with NLP
        if 'was' in passive_phrase.lower():
            return ['[subject] + [action verb]']
        elif 'were' in passive_phrase.lower():
            return ['[subjects] + [action verb]']
        elif 'being' in passive_phrase.lower():
            return ['[subject] + [present action verb]']

        return ['Use active voice']

    def calculate_style_score(self, text: str) -> float:
        """Calculate overall style score for the text."""
        issues = self.analyze_style(text)

        if not issues:
            return 100.0

        # Weight issues by severity
        severity_weights = {
            IssueSeverity.LOW: 1,
            IssueSeverity.MEDIUM: 3,
            IssueSeverity.HIGH: 5,
            IssueSeverity.CRITICAL: 10
        }

        total_penalty = sum(severity_weights.get(issue.severity, 3) for issue in issues)

        # Calculate score (100 - penalties, minimum 0)
        score = max(0, 100 - total_penalty)

        return score