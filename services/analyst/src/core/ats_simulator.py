"""ATS simulation engine with weighted scoring criteria."""

import logging
import re
import yaml
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.models.ats_scoring import ATSScore, CriteriaScore, ScoringCriteria, ScoreLevel
from src.models.ner_entities import ResumeDeconstruction, EntityType
from src.models.market_data import MarketJob


logger = logging.getLogger(__name__)


class ATSSimulator:
    """ATS simulation engine with comprehensive scoring."""

    # Scoring weights as per requirements
    SCORING_WEIGHTS = {
        ScoringCriteria.KEYWORD_MATCH: 0.40,  # 40%
        ScoringCriteria.FORMAT_PARSABILITY: 0.30,  # 30%
        ScoringCriteria.QUANTIFICATION: 0.20,  # 20%
        ScoringCriteria.ACTION_VERBS: 0.10,  # 10%
    }

    def __init__(self):
        """Initialize ATS simulator with scoring data."""
        self.high_impact_verbs = {}
        self.weak_verbs = []
        self.quantification_patterns = {}
        self.tfidf_vectorizer = TfidfVectorizer(
            stop_words="english", max_features=1000, ngram_range=(1, 2)
        )
        self._load_scoring_data()

    def _load_scoring_data(self) -> None:
        """Load high-impact verbs and scoring patterns."""
        try:
            data_dir = Path(__file__).parent.parent / "data"

            with open(data_dir / "high_impact_verbs.yaml", "r") as f:
                data = yaml.safe_load(f)

                self.high_impact_verbs = data.get("high_impact_verbs", {})
                self.weak_verbs = data.get("weak_verbs_to_avoid", [])
                self.quantification_patterns = data.get("quantification_patterns", {})

            logger.info("ATS scoring data loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load ATS scoring data: {str(e)}")
            # Fallback to basic patterns
            self.quantification_patterns = {
                "percentage": r"\d+\.?\d*%",
                "currency": r"\$[\d,]+",
                "numbers_with_units": r"\d+\s*(K|M|B|thousand|million|billion)",
            }

    def calculate_keyword_match_score(
        self, resume_text: str, job_description: str
    ) -> CriteriaScore:
        """Calculate keyword match score using cosine similarity (40% weight)."""
        try:
            # Prepare texts
            texts = [resume_text, job_description]
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(texts)

            # Calculate cosine similarity
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]

            # Get top matching keywords
            feature_names = self.tfidf_vectorizer.get_feature_names_out()
            resume_tfidf = tfidf_matrix[0].toarray()[0]
            job_tfidf = tfidf_matrix[1].toarray()[0]

            # Find common high-scoring terms
            common_terms = []
            for i, (resume_score, job_score) in enumerate(zip(resume_tfidf, job_tfidf)):
                if resume_score > 0 and job_score > 0:
                    common_terms.append(
                        (feature_names[i], min(resume_score, job_score))
                    )

            common_terms = sorted(common_terms, key=lambda x: x[1], reverse=True)[:10]

            details = {
                "similarity_score": float(similarity),
                "total_resume_terms": int(np.sum(resume_tfidf > 0)),
                "total_job_terms": int(np.sum(job_tfidf > 0)),
                "common_terms": [term for term, score in common_terms],
                "top_matching_keywords": common_terms[:5],
            }

            # Generate recommendations
            recommendations = []
            if similarity < 0.6:
                recommendations.extend(
                    [
                        "Include more keywords from the job description in your resume",
                        "Use industry-specific terminology that matches the job posting",
                        "Mirror the language and phrases used in the job requirements",
                    ]
                )

            return CriteriaScore(
                criteria=ScoringCriteria.KEYWORD_MATCH,
                score=float(similarity),
                weight=self.SCORING_WEIGHTS[ScoringCriteria.KEYWORD_MATCH],
                weighted_score=float(similarity)
                * self.SCORING_WEIGHTS[ScoringCriteria.KEYWORD_MATCH],
                details=details,
                recommendations=recommendations,
            )

        except Exception as e:
            logger.error(f"Error calculating keyword match score: {str(e)}")
            return CriteriaScore(
                criteria=ScoringCriteria.KEYWORD_MATCH,
                score=0.0,
                weight=self.SCORING_WEIGHTS[ScoringCriteria.KEYWORD_MATCH],
                weighted_score=0.0,
                details={"error": str(e)},
                recommendations=["Unable to calculate keyword match score"],
            )

    def calculate_format_parsability_score(
        self, resume_deconstruction: ResumeDeconstruction
    ) -> CriteriaScore:
        """Calculate format parsability score based on NER extraction success (30% weight)."""
        try:
            total_sections = len(resume_deconstruction.sections)
            total_entities = sum(
                len(section.entities) for section in resume_deconstruction.sections
            )

            if total_sections == 0:
                parsability_score = 0.0
            else:
                # Base score on entity extraction success
                avg_entities_per_section = total_entities / total_sections

                # Normalize to 0-1 scale (assume 10+ entities per section is excellent)
                parsability_score = min(avg_entities_per_section / 10.0, 1.0)

                # Bonus for good confidence scores
                all_confidences = []
                for section in resume_deconstruction.sections:
                    all_confidences.extend([e.confidence for e in section.entities])

                if all_confidences:
                    avg_confidence = np.mean(all_confidences)
                    parsability_score = (parsability_score + avg_confidence) / 2

            details = {
                "total_sections": total_sections,
                "total_entities": total_entities,
                "avg_entities_per_section": avg_entities_per_section
                if total_sections > 0
                else 0,
                "avg_confidence": float(np.mean(all_confidences))
                if all_confidences
                else 0.0,
                "entity_types_found": list(resume_deconstruction.entity_summary.keys()),
                "language_support": resume_deconstruction.language_distribution,
            }

            # Generate recommendations
            recommendations = []
            if parsability_score < 0.7:
                recommendations.extend(
                    [
                        "Use standard section headers (Experience, Education, Skills)",
                        "Avoid complex formatting, tables, or graphics",
                        "Use bullet points for accomplishments and responsibilities",
                        "Ensure consistent formatting throughout the document",
                    ]
                )

            if avg_entities_per_section < 5:
                recommendations.append(
                    "Include more specific details, skills, and quantifiable achievements"
                )

            return CriteriaScore(
                criteria=ScoringCriteria.FORMAT_PARSABILITY,
                score=float(parsability_score),
                weight=self.SCORING_WEIGHTS[ScoringCriteria.FORMAT_PARSABILITY],
                weighted_score=float(parsability_score)
                * self.SCORING_WEIGHTS[ScoringCriteria.FORMAT_PARSABILITY],
                details=details,
                recommendations=recommendations,
            )

        except Exception as e:
            logger.error(f"Error calculating parsability score: {str(e)}")
            return CriteriaScore(
                criteria=ScoringCriteria.FORMAT_PARSABILITY,
                score=0.0,
                weight=self.SCORING_WEIGHTS[ScoringCriteria.FORMAT_PARSABILITY],
                weighted_score=0.0,
                details={"error": str(e)},
                recommendations=["Unable to calculate format parsability score"],
            )

    def calculate_quantification_score(
        self, resume_deconstruction: ResumeDeconstruction
    ) -> CriteriaScore:
        """Calculate quantification score based on METRIC entity presence (20% weight)."""
        try:
            total_bullets = 0
            quantified_bullets = 0
            quantification_examples = []

            for section in resume_deconstruction.sections:
                # Count bullet points (assume each section is a bullet or accomplishment)
                total_bullets += 1

                # Check for METRIC entities
                metric_entities = [
                    e for e in section.entities if e.label == EntityType.METRIC
                ]
                if metric_entities:
                    quantified_bullets += 1
                    quantification_examples.extend(
                        [e.text for e in metric_entities[:2]]
                    )

                # Also check for quantification patterns in text
                text = section.raw_text
                for pattern_name, pattern in self.quantification_patterns.items():
                    if re.search(pattern, text, re.IGNORECASE):
                        if (
                            quantified_bullets == total_bullets - 1
                        ):  # If not already counted
                            quantified_bullets += 1
                        break

            # Calculate score
            quantification_score = (
                (quantified_bullets / total_bullets) if total_bullets > 0 else 0.0
            )

            details = {
                "total_bullets": total_bullets,
                "quantified_bullets": quantified_bullets,
                "quantification_percentage": quantification_score * 100,
                "metric_entities_found": sum(
                    len([e for e in section.entities if e.label == EntityType.METRIC])
                    for section in resume_deconstruction.sections
                ),
                "quantification_examples": quantification_examples[:5],
            }

            # Generate recommendations
            recommendations = []
            if quantification_score < 0.5:
                recommendations.extend(
                    [
                        "Add specific numbers, percentages, and metrics to your accomplishments",
                        "Quantify the impact of your work (e.g., 'Increased sales by 25%')",
                        "Include timeframes for your achievements (e.g., 'within 3 months')",
                        "Use dollar amounts, percentages, or other measurable outcomes",
                    ]
                )

            return CriteriaScore(
                criteria=ScoringCriteria.QUANTIFICATION,
                score=float(quantification_score),
                weight=self.SCORING_WEIGHTS[ScoringCriteria.QUANTIFICATION],
                weighted_score=float(quantification_score)
                * self.SCORING_WEIGHTS[ScoringCriteria.QUANTIFICATION],
                details=details,
                recommendations=recommendations,
            )

        except Exception as e:
            logger.error(f"Error calculating quantification score: {str(e)}")
            return CriteriaScore(
                criteria=ScoringCriteria.QUANTIFICATION,
                score=0.0,
                weight=self.SCORING_WEIGHTS[ScoringCriteria.QUANTIFICATION],
                weighted_score=0.0,
                details={"error": str(e)},
                recommendations=["Unable to calculate quantification score"],
            )

    def calculate_action_verb_score(
        self, resume_deconstruction: ResumeDeconstruction
    ) -> CriteriaScore:
        """Calculate action verb score using high-impact verb classification (10% weight)."""
        try:
            # Flatten all high-impact verbs from categories
            all_high_impact_verbs = []
            for category, verbs in self.high_impact_verbs.items():
                all_high_impact_verbs.extend([verb.lower() for verb in verbs])

            total_bullets = 0
            high_impact_verb_count = 0
            weak_verb_count = 0
            action_verb_examples = []

            for section in resume_deconstruction.sections:
                text = section.raw_text.lower()
                total_bullets += 1

                # Check for high-impact verbs in text
                section_has_high_impact = False
                section_has_weak = False

                for verb in all_high_impact_verbs:
                    if verb in text:
                        if not section_has_high_impact:
                            high_impact_verb_count += 1
                            section_has_high_impact = True
                            action_verb_examples.append(verb)
                        break

                # Check for weak verbs
                for weak_verb in self.weak_verbs:
                    if weak_verb.lower() in text:
                        section_has_weak = True
                        break

                if section_has_weak:
                    weak_verb_count += 1

            # Calculate score
            if total_bullets == 0:
                action_verb_score = 0.0
            else:
                base_score = high_impact_verb_count / total_bullets
                # Penalty for weak verbs
                weak_penalty = (weak_verb_count / total_bullets) * 0.3
                action_verb_score = max(0.0, base_score - weak_penalty)

            details = {
                "total_bullets": total_bullets,
                "high_impact_verb_count": high_impact_verb_count,
                "weak_verb_count": weak_verb_count,
                "action_verb_percentage": action_verb_score * 100,
                "action_verb_examples": action_verb_examples[:5],
                "weak_verbs_found": weak_verb_count,
            }

            # Generate recommendations
            recommendations = []
            if action_verb_score < 0.6:
                recommendations.extend(
                    [
                        "Start bullet points with strong action verbs (e.g., 'Architected', 'Optimized', 'Led')",
                        f"Avoid weak verbs like: {', '.join(self.weak_verbs[:5])}",
                        "Use past tense action verbs for previous roles",
                        "Choose verbs that demonstrate impact and leadership",
                    ]
                )

            if high_impact_verb_count < total_bullets * 0.5:
                recommendations.append(
                    "Replace generic verbs with more impactful alternatives"
                )

            return CriteriaScore(
                criteria=ScoringCriteria.ACTION_VERBS,
                score=float(action_verb_score),
                weight=self.SCORING_WEIGHTS[ScoringCriteria.ACTION_VERBS],
                weighted_score=float(action_verb_score)
                * self.SCORING_WEIGHTS[ScoringCriteria.ACTION_VERBS],
                details=details,
                recommendations=recommendations,
            )

        except Exception as e:
            logger.error(f"Error calculating action verb score: {str(e)}")
            return CriteriaScore(
                criteria=ScoringCriteria.ACTION_VERBS,
                score=0.0,
                weight=self.SCORING_WEIGHTS[ScoringCriteria.ACTION_VERBS],
                weighted_score=0.0,
                details={"error": str(e)},
                recommendations=["Unable to calculate action verb score"],
            )

    def determine_performance_level(self, percentage_score: int) -> ScoreLevel:
        """Determine performance level based on percentage score."""
        if percentage_score >= 80:
            return ScoreLevel.EXCELLENT
        elif percentage_score >= 60:
            return ScoreLevel.GOOD
        elif percentage_score >= 40:
            return ScoreLevel.FAIR
        else:
            return ScoreLevel.POOR

    def simulate_ats_score(
        self, resume_deconstruction: ResumeDeconstruction, target_job: MarketJob
    ) -> ATSScore:
        """Simulate comprehensive ATS scoring for a resume against a job."""
        try:
            # Extract resume text for keyword matching
            resume_text = " ".join(
                [section.raw_text for section in resume_deconstruction.sections]
            )
            job_description = target_job.full_description_text

            # Calculate individual criteria scores
            criteria_scores = []

            # 1. Keyword Match (40%)
            keyword_score = self.calculate_keyword_match_score(
                resume_text, job_description
            )
            criteria_scores.append(keyword_score)

            # 2. Format Parsability (30%)
            parsability_score = self.calculate_format_parsability_score(
                resume_deconstruction
            )
            criteria_scores.append(parsability_score)

            # 3. Quantification (20%)
            quantification_score = self.calculate_quantification_score(
                resume_deconstruction
            )
            criteria_scores.append(quantification_score)

            # 4. Action Verbs (10%)
            action_verb_score = self.calculate_action_verb_score(resume_deconstruction)
            criteria_scores.append(action_verb_score)

            # Calculate overall weighted score
            overall_score = sum(score.weighted_score for score in criteria_scores)
            percentage_score = int(overall_score * 100)
            performance_level = self.determine_performance_level(percentage_score)

            # Generate summary statistics
            summary = {
                "total_weighted_score": overall_score,
                "individual_scores": {
                    score.criteria: score.score for score in criteria_scores
                },
                "weights_applied": {
                    score.criteria: score.weight for score in criteria_scores
                },
                "strongest_area": max(criteria_scores, key=lambda x: x.score).criteria,
                "weakest_area": min(criteria_scores, key=lambda x: x.score).criteria,
            }

            # Compile optimization recommendations
            all_recommendations = []
            for score in criteria_scores:
                all_recommendations.extend(score.recommendations)

            # Add overall recommendations based on performance level
            if performance_level == ScoreLevel.POOR:
                all_recommendations.extend(
                    [
                        "Consider significant resume restructuring for better ATS compatibility",
                        "Focus on the weakest scoring areas first for maximum impact",
                    ]
                )
            elif performance_level == ScoreLevel.FAIR:
                all_recommendations.append(
                    "Good foundation, focus on improving keyword matching and quantification"
                )

            # ATS readiness feedback
            ats_feedback = {
                "readiness_level": performance_level.value,
                "pass_probability": "High"
                if percentage_score >= 70
                else "Medium"
                if percentage_score >= 50
                else "Low",
                "key_strengths": [
                    score.criteria for score in criteria_scores if score.score >= 0.7
                ],
                "improvement_areas": [
                    score.criteria for score in criteria_scores if score.score < 0.5
                ],
                "estimated_ranking": self._estimate_ranking(percentage_score),
            }

            return ATSScore(
                overall_score=overall_score,
                percentage_score=percentage_score,
                performance_level=performance_level,
                criteria_scores=criteria_scores,
                summary=summary,
                optimization_recommendations=list(set(all_recommendations)),
                ats_readiness_feedback=ats_feedback,
            )

        except Exception as e:
            logger.error(f"Error simulating ATS score: {str(e)}")
            raise

    def _estimate_ranking(self, percentage_score: int) -> str:
        """Estimate ranking among applicants based on ATS score."""
        if percentage_score >= 85:
            return "Top 10% of applicants"
        elif percentage_score >= 70:
            return "Top 25% of applicants"
        elif percentage_score >= 55:
            return "Top 50% of applicants"
        else:
            return "Below median applicant score"
