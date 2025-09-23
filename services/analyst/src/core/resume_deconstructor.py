"""Resume deconstruction engine with NLP processing and NER extraction."""

import logging
import time
from typing import Dict, List, Any, Optional
import re

import spacy
from spacy.matcher import Matcher
from sentence_transformers import SentenceTransformer
import numpy as np

from src.models.ner_entities import (
    ResumeDeconstruction,
    ProcessedSection,
    ExtractedEntity,
    EntityType,
)
from src.core.config import settings


logger = logging.getLogger(__name__)


class ResumeDeconstructor:
    """Resume deconstruction engine with multilingual NLP processing."""

    def __init__(self):
        """Initialize NLP models and processing components."""
        self.nlp_models = {}
        self.sentence_model = None
        self.matcher = None
        self._load_models()
        self._setup_matchers()

    def _load_models(self) -> None:
        """Load spaCy models and Sentence-BERT."""
        try:
            # Load spaCy models with fallback
            try:
                self.nlp_models["en"] = spacy.load(settings.SPACY_MODEL_EN)
            except OSError:
                logger.warning(
                    f"spaCy model {settings.SPACY_MODEL_EN} not found. Downloading..."
                )
                import subprocess

                subprocess.run(
                    ["python", "-m", "spacy", "download", settings.SPACY_MODEL_EN],
                    check=False,
                )
                try:
                    self.nlp_models["en"] = spacy.load(settings.SPACY_MODEL_EN)
                except OSError:
                    logger.warning(
                        f"Could not load {settings.SPACY_MODEL_EN}, using blank model"
                    )
                    self.nlp_models["en"] = spacy.blank("en")

            try:
                self.nlp_models["fr"] = spacy.load(settings.SPACY_MODEL_FR)
            except OSError:
                logger.warning(
                    f"spaCy model {settings.SPACY_MODEL_FR} not found. Downloading..."
                )
                import subprocess

                subprocess.run(
                    ["python", "-m", "spacy", "download", settings.SPACY_MODEL_FR],
                    check=False,
                )
                try:
                    self.nlp_models["fr"] = spacy.load(settings.SPACY_MODEL_FR)
                except OSError:
                    logger.warning(
                        f"Could not load {settings.SPACY_MODEL_FR}, using blank model"
                    )
                    self.nlp_models["fr"] = spacy.blank("fr")

            # Load Sentence-BERT model with fallback
            try:
                self.sentence_model = SentenceTransformer("all-MiniLM-L6-v2")
                logger.info("Sentence-BERT model loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load Sentence-BERT model: {str(e)}")
                logger.warning("Resume semantic embeddings will be unavailable")
                self.sentence_model = None

            logger.info("NLP models loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load NLP models: {str(e)}")
            logger.warning("Service starting in degraded mode - limited NLP functionality")
            # Don't raise - allow service to start in degraded mode

    def _setup_matchers(self) -> None:
        """Setup spaCy matchers for professional entities."""
        try:
            if "en" in self.nlp_models and self.nlp_models["en"]:
                self.matcher = Matcher(self.nlp_models["en"].vocab)
            else:
                logger.warning("English model not available - pattern matching disabled")
                self.matcher = None
                return

            # Action verb patterns
            action_patterns = [
                [{"POS": "VERB", "TAG": {"IN": ["VBD", "VBN"]}}],
                [{"LEMMA": {"IN": self._get_high_impact_verbs()}}],
            ]
            self.matcher.add("ACTION_VERB", action_patterns)

            # Metric patterns (numbers with units/percentages)
            metric_patterns = [
                [
                    {"LIKE_NUM": True},
                    {
                        "TEXT": {
                            "REGEX": r"%|percent|seconds?|minutes?|hours?|days?|weeks?|months?|years?"
                        }
                    },
                ],
                [{"TEXT": {"REGEX": r"\$"}}, {"LIKE_NUM": True}],
                [
                    {"LIKE_NUM": True},
                    {"TEXT": {"REGEX": r"[KMB]|thousand|million|billion"}},
                ],
            ]
            self.matcher.add("METRIC", metric_patterns)

        except Exception as e:
            logger.error(f"Failed to setup matchers: {str(e)}")
            self.matcher = None

    def _get_high_impact_verbs(self) -> List[str]:
        """Get list of high-impact action verbs."""
        return [
            # Technical
            "architect",
            "engineer",
            "deploy",
            "refactor",
            "automate",
            "implement",
            "develop",
            "design",
            "optimize",
            "scale",
            # Management
            "orchestrate",
            "govern",
            "mentor",
            "pilot",
            "lead",
            "manage",
            "coordinate",
            "supervise",
            "direct",
            "oversee",
            # Growth/Sales
            "accelerate",
            "evangelize",
            "penetrate",
            "negotiate",
            "capture",
            "drive",
            "increase",
            "expand",
            "grow",
            "boost",
            # Analysis
            "synthesize",
            "model",
            "forecast",
            "quantify",
            "infer",
            "analyze",
            "evaluate",
            "assess",
            "measure",
            "track",
        ]

    def detect_language(self, text: str) -> str:
        """Detect primary language of text."""
        try:
            import langdetect

            detected = langdetect.detect(text)
            return "fr" if detected == "fr" else "en"
        except Exception:
            # Fallback to English
            return "en"

    def extract_entities(self, text: str, language: str) -> List[ExtractedEntity]:
        """Extract professional entities from text."""
        if language not in self.nlp_models:
            language = "en"  # Fallback

        nlp = self.nlp_models[language]
        doc = nlp(text)
        entities = []

        # Extract using spaCy NER
        for ent in doc.ents:
            entity_type = self._classify_entity(ent.text, ent.label_)
            if entity_type:
                entities.append(
                    ExtractedEntity(
                        text=ent.text,
                        label=entity_type,
                        start=ent.start_char,
                        end=ent.end_char,
                        confidence=0.8,  # Base confidence for spaCy entities
                        context=self._get_entity_context(
                            text, ent.start_char, ent.end_char
                        ),
                    )
                )

        # Extract using custom patterns (if matcher is available)
        if self.matcher:
            matches = self.matcher(doc)
            for match_id, start, end in matches:
                span = doc[start:end]
                label_name = nlp.vocab.strings[match_id]

                if label_name in EntityType.__members__:
                    entities.append(
                        ExtractedEntity(
                            text=span.text,
                            label=EntityType(label_name),
                            start=span.start_char,
                            end=span.end_char,
                            confidence=0.9,  # Higher confidence for pattern matches
                            context=self._get_entity_context(
                                text, span.start_char, span.end_char
                            ),
                        )
                    )

        # Extract skills using custom logic
        skill_entities = self._extract_skills(text, doc)
        entities.extend(skill_entities)

        return self._deduplicate_entities(entities)

    def _classify_entity(self, text: str, spacy_label: str) -> Optional[EntityType]:
        """Classify spaCy entity into professional type."""
        # Map spaCy labels to our entity types
        label_mapping = {
            "ORG": EntityType.TOOL,  # Organizations often tools/platforms
            "PRODUCT": EntityType.TOOL,  # Products are tools
            "MONEY": EntityType.METRIC,  # Money amounts are metrics
            "PERCENT": EntityType.METRIC,  # Percentages are metrics
            "DATE": EntityType.METRIC,  # Dates can be metrics (duration)
        }
        return label_mapping.get(spacy_label)

    def _extract_skills(self, text: str, doc) -> List[ExtractedEntity]:
        """Extract technical and soft skills using domain knowledge."""
        skills = []

        # Technical skills patterns
        tech_patterns = [
            r"\b(?:Python|Java|JavaScript|React|Docker|Kubernetes|AWS|Azure|GCP)\b",
            r"\b(?:Machine Learning|ML|AI|Deep Learning|NLP|Computer Vision)\b",
            r"\b(?:SQL|NoSQL|PostgreSQL|MongoDB|Redis|Elasticsearch)\b",
            r"\b(?:Agile|Scrum|DevOps|CI\/CD|Git|GitHub|GitLab)\b",
        ]

        for pattern in tech_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                skills.append(
                    ExtractedEntity(
                        text=match.group(),
                        label=EntityType.SKILL,
                        start=match.start(),
                        end=match.end(),
                        confidence=0.85,
                        context=self._get_entity_context(
                            text, match.start(), match.end()
                        ),
                    )
                )

        return skills

    def _get_entity_context(
        self, text: str, start: int, end: int, context_size: int = 50
    ) -> str:
        """Get surrounding context for an entity."""
        context_start = max(0, start - context_size)
        context_end = min(len(text), end + context_size)
        return text[context_start:context_end].strip()

    def _deduplicate_entities(
        self, entities: List[ExtractedEntity]
    ) -> List[ExtractedEntity]:
        """Remove duplicate entities based on text and position overlap."""
        if not entities:
            return entities

        # Sort by start position
        entities = sorted(entities, key=lambda e: (e.start, e.end))

        deduplicated = []
        for entity in entities:
            # Check for overlap with existing entities
            overlaps = any(
                e.start <= entity.start < e.end
                or e.start < entity.end <= e.end
                or (entity.start <= e.start and entity.end >= e.end)
                for e in deduplicated
            )

            if not overlaps:
                deduplicated.append(entity)

        return deduplicated

    def generate_semantic_embeddings(
        self, accomplishments: List[str]
    ) -> Dict[str, List[float]]:
        """Generate Sentence-BERT embeddings for accomplishment statements."""
        if not accomplishments or not self.sentence_model:
            return {}

        try:
            embeddings = self.sentence_model.encode(accomplishments)
            return {
                accomplishments[i]: embeddings[i].tolist()
                for i in range(len(accomplishments))
            }
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {str(e)}")
            return {}

    def process_resume_sections(
        self, career_data: Dict[str, Any]
    ) -> ResumeDeconstruction:
        """Process all resume sections and extract entities."""
        start_time = time.time()

        sections = []
        all_entities = []
        language_counts = {"en": 0, "fr": 0}
        accomplishments = []

        # Process work experience
        for exp in career_data.get("work_experience", []):
            for accomplishment in exp.get("accomplishments", []):
                text = accomplishment.get("description", "")
                if text:
                    accomplishments.append(text)

                    language = self.detect_language(text)
                    language_counts[language] += 1

                    entities = self.extract_entities(text, language)
                    all_entities.extend(entities)

                    sections.append(
                        ProcessedSection(
                            section_name=f"work_experience_{exp.get('role', 'unknown')}",
                            raw_text=text,
                            entities=entities,
                            language=language,
                            processing_metadata={
                                "entity_count": len(entities),
                                "confidence_avg": np.mean(
                                    [e.confidence for e in entities]
                                )
                                if entities
                                else 0.0,
                            },
                        )
                    )

        # Process projects
        for project in career_data.get("projects", []):
            text = project.get("description", "")
            if text:
                language = self.detect_language(text)
                language_counts[language] += 1

                entities = self.extract_entities(text, language)
                all_entities.extend(entities)

                sections.append(
                    ProcessedSection(
                        section_name=f"project_{project.get('name', 'unknown')}",
                        raw_text=text,
                        entities=entities,
                        language=language,
                    )
                )

        # Calculate statistics
        entity_summary = {}
        for entity_type in EntityType:
            entity_summary[entity_type] = len(
                [e for e in all_entities if e.label == entity_type]
            )

        total_langs = sum(language_counts.values())
        language_distribution = {
            lang: (count / total_langs * 100) if total_langs > 0 else 0.0
            for lang, count in language_counts.items()
        }

        # Generate semantic embeddings
        semantic_embeddings = self.generate_semantic_embeddings(accomplishments)

        processing_time = time.time() - start_time

        # Quality metrics
        quality_metrics = {
            "total_entities": len(all_entities),
            "avg_confidence": np.mean([e.confidence for e in all_entities])
            if all_entities
            else 0.0,
            "entity_density": len(all_entities) / len(sections) if sections else 0.0,
            "multilingual_support": len(
                [lang for lang, pct in language_distribution.items() if pct > 0]
            ),
        }

        return ResumeDeconstruction(
            sections=sections,
            entity_summary=entity_summary,
            language_distribution=language_distribution,
            semantic_embeddings=semantic_embeddings,
            processing_time_seconds=processing_time,
            quality_metrics=quality_metrics,
        )
