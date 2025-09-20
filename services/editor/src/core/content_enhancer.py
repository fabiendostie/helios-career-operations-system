"""Content enhancement for professional writing."""

import logging
import re

logger = logging.getLogger(__name__)


class ContentEnhancer:
    """Enhances content for professional impact and clarity."""

    def __init__(self):
        """Initialize the content enhancer."""
        self.industry_keywords = self._load_industry_keywords()
        self.quantification_patterns = self._load_quantification_patterns()
        self.impact_verbs = self._load_impact_verbs()

    def _load_industry_keywords(self) -> dict[str, list[str]]:
        """Load industry-specific keywords and terminology."""
        return {
            "technology": [
                "software",
                "development",
                "programming",
                "coding",
                "debugging",
                "architecture",
                "framework",
                "database",
                "API",
                "microservices",
                "cloud",
                "DevOps",
                "CI/CD",
                "agile",
                "scrum",
                "testing",
                "deployment",
                "scalability",
                "performance",
                "security",
                "algorithms",
                "data structures",
                "machine learning",
                "AI",
                "full-stack",
                "front-end",
                "back-end",
                "mobile",
                "web",
            ],
            "finance": [
                "portfolio",
                "investment",
                "analysis",
                "risk management",
                "financial modeling",
                "valuation",
                "compliance",
                "audit",
                "budgeting",
                "forecasting",
                "ROI",
                "KPI",
                "metrics",
                "capital",
                "equity",
                "debt",
                "derivatives",
                "trading",
            ],
            "marketing": [
                "campaign",
                "strategy",
                "branding",
                "digital marketing",
                "content marketing",
                "SEO",
                "SEM",
                "social media",
                "analytics",
                "conversion",
                "engagement",
                "lead generation",
                "customer acquisition",
                "retention",
                "segmentation",
            ],
            "healthcare": [
                "patient care",
                "clinical",
                "medical",
                "diagnosis",
                "treatment",
                "therapy",
                "healthcare",
                "compliance",
                "quality assurance",
                "safety",
                "regulations",
            ],
            "education": [
                "curriculum",
                "pedagogy",
                "assessment",
                "learning outcomes",
                "instruction",
                "educational technology",
                "student engagement",
            ],
        }

    def _load_quantification_patterns(self) -> list[str]:
        """Load patterns for quantifiable achievements."""
        return [
            r"increased\s+\w+(?:\s+\w+)*",
            r"improved\s+\w+(?:\s+\w+)*",
            r"reduced\s+\w+(?:\s+\w+)*",
            r"optimized\s+\w+(?:\s+\w+)*",
            r"enhanced\s+\w+(?:\s+\w+)*",
            r"streamlined\s+\w+(?:\s+\w+)*",
            r"accelerated\s+\w+(?:\s+\w+)*",
            r"expanded\s+\w+(?:\s+\w+)*",
            r"grew\s+\w+(?:\s+\w+)*",
            r"boosted\s+\w+(?:\s+\w+)*",
            r"delivered\s+\w+(?:\s+\w+)*",
            r"achieved\s+\w+(?:\s+\w+)*",
        ]

    def _load_impact_verbs(self) -> dict[str, list[str]]:
        """Load high-impact action verbs by category."""
        return {
            "leadership": [
                "led",
                "directed",
                "managed",
                "supervised",
                "coordinated",
                "orchestrated",
                "spearheaded",
                "championed",
                "guided",
                "mentored",
                "facilitated",
                "drove",
                "initiated",
            ],
            "achievement": [
                "achieved",
                "accomplished",
                "delivered",
                "exceeded",
                "surpassed",
                "attained",
                "secured",
                "earned",
                "won",
                "captured",
                "generated",
                "produced",
            ],
            "improvement": [
                "improved",
                "enhanced",
                "optimized",
                "refined",
                "upgraded",
                "modernized",
                "streamlined",
                "revitalized",
                "transformed",
                "revolutionized",
                "innovated",
                "pioneered",
            ],
            "creation": [
                "created",
                "developed",
                "built",
                "designed",
                "engineered",
                "constructed",
                "established",
                "founded",
                "launched",
                "introduced",
                "implemented",
                "deployed",
            ],
            "analysis": [
                "analyzed",
                "evaluated",
                "assessed",
                "investigated",
                "researched",
                "examined",
                "studied",
                "reviewed",
                "audited",
                "diagnosed",
                "identified",
                "discovered",
            ],
        }

    def enhance_content(
        self, text: str, industry: str | None = None, role: str | None = None
    ) -> tuple[str, list[dict]]:
        """Enhance content for professional impact."""
        enhanced_text = text
        enhancements = []

        # Apply various enhancement techniques
        enhanced_text, verb_enhancements = self._enhance_action_verbs(enhanced_text)
        enhancements.extend(verb_enhancements)

        enhanced_text, quant_enhancements = self._suggest_quantification(enhanced_text)
        enhancements.extend(quant_enhancements)

        if industry:
            enhanced_text, industry_enhancements = self._add_industry_context(
                enhanced_text, industry
            )
            enhancements.extend(industry_enhancements)

        enhanced_text, impact_enhancements = self._enhance_impact_statements(
            enhanced_text
        )
        enhancements.extend(impact_enhancements)

        enhanced_text, clarity_enhancements = self._improve_clarity(enhanced_text)
        enhancements.extend(clarity_enhancements)

        return enhanced_text, enhancements

    def _enhance_action_verbs(self, text: str) -> tuple[str, list[dict]]:
        """Replace weak verbs with stronger action verbs."""
        enhancements = []
        enhanced_text = text

        weak_to_strong = {
            "did": ["executed", "performed", "accomplished", "completed"],
            "made": ["created", "developed", "built", "generated"],
            "worked on": ["developed", "created", "built", "designed"],
            "helped": ["assisted", "supported", "contributed to", "facilitated"],
            "used": ["utilized", "leveraged", "employed", "applied"],
            "got": ["achieved", "obtained", "secured", "earned"],
            "handled": ["managed", "oversaw", "administered", "coordinated"],
            "dealt with": ["managed", "resolved", "addressed", "handled"],
        }

        for weak, strong_options in weak_to_strong.items():
            pattern = r"\b" + re.escape(weak) + r"\b"
            matches = list(re.finditer(pattern, enhanced_text, re.IGNORECASE))

            for match in matches:
                enhancement = {
                    "type": "action_verb",
                    "start_pos": match.start(),
                    "end_pos": match.end(),
                    "original": match.group(),
                    "suggestions": strong_options,
                    "reason": "Replace with stronger action verb for more impact",
                }
                enhancements.append(enhancement)

                # Apply the first suggestion
                enhanced_text = (
                    enhanced_text[: match.start()]
                    + strong_options[0]
                    + enhanced_text[match.end() :]
                )

        return enhanced_text, enhancements

    def _suggest_quantification(self, text: str) -> tuple[str, list[dict]]:
        """Suggest adding quantification to achievements."""
        enhancements = []

        for pattern in self.quantification_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)

            for match in matches:
                # Check if already quantified
                following_text = text[match.end() : match.end() + 50]
                if re.search(
                    r"\b\d+(?:[\.,]\d+)?(?:%|percent|k|thousand|million|billion)?\b",
                    following_text,
                ):
                    continue  # Already quantified

                enhancement = {
                    "type": "quantification",
                    "start_pos": match.start(),
                    "end_pos": match.end(),
                    "original": match.group(),
                    "suggestions": [
                        f"{match.group()} by X%",
                        f"{match.group()} by X units",
                        f"{match.group()} from X to Y",
                    ],
                    "reason": "Add specific metrics to strengthen impact",
                }
                enhancements.append(enhancement)

        return text, enhancements  # Return original text with suggestions

    def _add_industry_context(self, text: str, industry: str) -> tuple[str, list[dict]]:
        """Add industry-specific terminology and context."""
        enhancements = []
        enhanced_text = text

        if industry.lower() not in self.industry_keywords:
            return text, enhancements

        # TODO: Use industry keywords for content enhancement
        # keywords = self.industry_keywords[industry.lower()]

        # Replace generic terms with industry-specific ones
        generic_replacements = {
            "technology": {
                "computer things": "software applications",
                "computer stuff": "technical systems",
                "IT work": "software development",
                "technical work": "software engineering",
                "coding work": "software development",
                "computer projects": "software projects",
            },
            "finance": {
                "money work": "financial analysis",
                "number work": "financial modeling",
                "calculations": "financial calculations",
            },
            "marketing": {
                "promotion work": "marketing campaigns",
                "advertising work": "marketing strategy",
            },
        }

        if industry.lower() in generic_replacements:
            replacements = generic_replacements[industry.lower()]

            for generic, specific in replacements.items():
                pattern = r"\b" + re.escape(generic) + r"\b"
                matches = list(re.finditer(pattern, enhanced_text, re.IGNORECASE))

                for match in matches:
                    enhancement = {
                        "type": "industry_context",
                        "start_pos": match.start(),
                        "end_pos": match.end(),
                        "original": match.group(),
                        "suggestions": [specific],
                        "reason": f"Use {industry}-specific terminology",
                    }
                    enhancements.append(enhancement)

                    enhanced_text = re.sub(
                        pattern, specific, enhanced_text, flags=re.IGNORECASE, count=1
                    )

        return enhanced_text, enhancements

    def _enhance_impact_statements(self, text: str) -> tuple[str, list[dict]]:
        """Enhance statements to show greater impact."""
        enhancements = []
        enhanced_text = text

        # Patterns for impact enhancement
        impact_patterns = {
            r"\bcontributed to\b": [
                "directly contributed to",
                "significantly contributed to",
                "played a key role in",
            ],
            r"\bparticipated in\b": [
                "actively participated in",
                "contributed to",
                "played a role in",
            ],
            r"\binvolved in\b": [
                "actively involved in",
                "played a key role in",
                "contributed significantly to",
            ],
            r"\bhelped\b": [
                "assisted in",
                "supported",
                "contributed to",
                "facilitated",
            ],
        }

        for pattern, replacements in impact_patterns.items():
            matches = list(re.finditer(pattern, enhanced_text, re.IGNORECASE))

            for match in matches:
                enhancement = {
                    "type": "impact_statement",
                    "start_pos": match.start(),
                    "end_pos": match.end(),
                    "original": match.group(),
                    "suggestions": replacements,
                    "reason": "Strengthen impact statement",
                }
                enhancements.append(enhancement)

                # Apply the first replacement
                enhanced_text = (
                    enhanced_text[: match.start()]
                    + replacements[0]
                    + enhanced_text[match.end() :]
                )

        return enhanced_text, enhancements

    def _improve_clarity(self, text: str) -> tuple[str, list[dict]]:
        """Improve clarity and conciseness."""
        enhancements = []
        enhanced_text = text

        # Remove redundant phrases
        redundant_phrases = {
            "in order to": "to",
            "due to the fact that": "because",
            "in spite of the fact that": "although",
            "at this point in time": "now",
            "during the course of": "during",
            "in the event that": "if",
            "with regard to": "regarding",
            "in terms of": "regarding",
            "as a matter of fact": "",
            "it is important to note that": "",
            "it should be mentioned that": "",
        }

        for redundant, replacement in redundant_phrases.items():
            pattern = r"\b" + re.escape(redundant) + r"\b"
            matches = list(re.finditer(pattern, enhanced_text, re.IGNORECASE))

            for match in matches:
                enhancement = {
                    "type": "clarity",
                    "start_pos": match.start(),
                    "end_pos": match.end(),
                    "original": match.group(),
                    "suggestions": [replacement] if replacement else ["remove"],
                    "reason": "Improve clarity and conciseness",
                }
                enhancements.append(enhancement)

                enhanced_text = re.sub(
                    pattern, replacement, enhanced_text, flags=re.IGNORECASE, count=1
                )

        return enhanced_text, enhancements

    def analyze_achievement_strength(self, text: str) -> dict[str, float]:
        """Analyze the strength of achievement statements."""
        achievements = re.findall(
            r"(?:achieved|accomplished|delivered|increased|improved|reduced|optimized|enhanced|streamlined|accelerated|expanded|grew|boosted)[^.!?]*[.!?]",
            text,
            re.IGNORECASE,
        )

        scores = {
            "quantified_ratio": 0.0,
            "action_verb_strength": 0.0,
            "impact_clarity": 0.0,
            "overall_strength": 0.0,
        }

        if not achievements:
            return scores

        quantified_count = 0
        strong_verb_count = 0

        for achievement in achievements:
            # Check for quantification
            if re.search(
                r"\b\d+(?:[\.,]\d+)?(?:%|percent|k|thousand|million|billion)?\b",
                achievement,
            ):
                quantified_count += 1

            # Check for strong action verbs
            all_impact_verbs = []
            for category_verbs in self.impact_verbs.values():
                all_impact_verbs.extend(category_verbs)

            for verb in all_impact_verbs:
                if verb in achievement.lower():
                    strong_verb_count += 1
                    break

        scores["quantified_ratio"] = quantified_count / len(achievements)
        scores["action_verb_strength"] = strong_verb_count / len(achievements)
        scores["impact_clarity"] = (quantified_count + strong_verb_count) / (
            2 * len(achievements)
        )
        scores["overall_strength"] = sum(scores.values()) / 3

        return scores

    def suggest_power_words(self, context: str, category: str = "general") -> list[str]:
        """Suggest power words based on context and category."""
        if category in self.impact_verbs:
            return self.impact_verbs[category][:5]  # Top 5 suggestions

        # General power words
        return [
            "achieved",
            "delivered",
            "improved",
            "optimized",
            "enhanced",
            "streamlined",
            "accelerated",
            "expanded",
            "generated",
            "exceeded",
        ]
