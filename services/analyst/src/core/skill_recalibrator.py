"""Skill recalibration engine implementing the Skill Framing Matrix."""

import logging
from typing import Dict, List, Any, Tuple
from collections import Counter
from enum import Enum

from src.models.ner_entities import ResumeDeconstruction, EntityType
from src.models.market_data import MarketAnalysisResult


logger = logging.getLogger(__name__)


class SkillQuadrant(str, Enum):
    """Skill Framing Matrix quadrants."""

    LEVERAGE = "leverage"  # High Proficiency, High Market Demand
    UPSKILL = "upskill"  # Low Proficiency, High Market Demand
    MAINTAIN = "maintain"  # High Proficiency, Low Market Demand
    DE_EMPHASIZE = "de_emphasize"  # Low Proficiency, Low Market Demand


class SkillClassification:
    """Individual skill classification result."""

    def __init__(
        self,
        skill: str,
        proficiency_score: float,
        market_demand_score: float,
        quadrant: SkillQuadrant,
        evidence_count: int,
        market_frequency: int,
        recommendations: List[str],
    ):
        self.skill = skill
        self.proficiency_score = proficiency_score
        self.market_demand_score = market_demand_score
        self.quadrant = quadrant
        self.evidence_count = evidence_count
        self.market_frequency = market_frequency
        self.recommendations = recommendations


class SkillFramingMatrix:
    """Complete skill framing matrix result."""

    def __init__(
        self,
        leverage_skills: List[SkillClassification],
        upskill_skills: List[SkillClassification],
        maintain_skills: List[SkillClassification],
        de_emphasize_skills: List[SkillClassification],
        matrix_insights: Dict[str, Any],
        skill_gap_analysis: Dict[str, Any],
        development_roadmap: List[Dict[str, Any]],
    ):
        self.leverage_skills = leverage_skills
        self.upskill_skills = upskill_skills
        self.maintain_skills = maintain_skills
        self.de_emphasize_skills = de_emphasize_skills
        self.matrix_insights = matrix_insights
        self.skill_gap_analysis = skill_gap_analysis
        self.development_roadmap = development_roadmap


class SkillRecalibrator:
    """Skill recalibration engine using the 2x2 Skill Framing Matrix."""

    # Thresholds for quadrant classification
    HIGH_PROFICIENCY_THRESHOLD = 0.6
    HIGH_DEMAND_THRESHOLD = 0.5

    def __init__(self):
        """Initialize skill recalibrator."""
        pass

    def calculate_proficiency_score(
        self, skill: str, resume_deconstruction: ResumeDeconstruction
    ) -> Tuple[float, int]:
        """Calculate candidate proficiency score for a skill."""
        evidence_count = 0
        context_quality_score = 0.0

        skill_lower = skill.lower()

        for section in resume_deconstruction.sections:
            # Count direct skill mentions
            for entity in section.entities:
                if (
                    entity.label in [EntityType.SKILL, EntityType.TOOL]
                    and skill_lower in entity.text.lower()
                ):
                    evidence_count += 1

                    # Higher quality evidence from work experience vs other sections
                    if "work_experience" in section.section_name:
                        context_quality_score += 1.0
                    elif "project" in section.section_name:
                        context_quality_score += 0.8
                    else:
                        context_quality_score += 0.5

            # Check for skill mentions in raw text
            section_text = section.raw_text.lower()
            if skill_lower in section_text:
                # Count occurrences but cap at 3 per section to avoid over-counting
                occurrences = min(section_text.count(skill_lower), 3)
                evidence_count += occurrences

                if "work_experience" in section.section_name:
                    context_quality_score += occurrences * 0.5
                else:
                    context_quality_score += occurrences * 0.3

        # Calculate proficiency score (0.0 to 1.0)
        if evidence_count == 0:
            proficiency_score = 0.0
        else:
            # Base score from evidence count (normalized)
            base_score = min(evidence_count / 10.0, 0.8)  # Cap at 0.8 from count alone

            # Quality bonus from context
            quality_bonus = min(context_quality_score / 20.0, 0.3)  # Up to 0.3 bonus

            proficiency_score = min(base_score + quality_bonus, 1.0)

        return proficiency_score, evidence_count

    def calculate_market_demand_score(
        self, skill: str, market_analysis: MarketAnalysisResult
    ) -> Tuple[float, int]:
        """Calculate market demand score for a skill."""
        total_jobs = len(market_analysis.job_matches)
        skill_mentions = 0

        skill_lower = skill.lower()

        for job_match in market_analysis.job_matches:
            job = job_match.job
            all_job_skills = [
                s.lower() for s in job.required_skills + job.preferred_skills
            ]

            # Check if skill is mentioned in job requirements
            if any(
                skill_lower in job_skill or job_skill in skill_lower
                for job_skill in all_job_skills
            ):
                skill_mentions += 1

        # Calculate demand score (0.0 to 1.0)
        demand_score = (skill_mentions / total_jobs) if total_jobs > 0 else 0.0

        return demand_score, skill_mentions

    def classify_skill_quadrant(
        self, proficiency_score: float, demand_score: float
    ) -> SkillQuadrant:
        """Classify skill into appropriate quadrant based on scores."""
        high_proficiency = proficiency_score >= self.HIGH_PROFICIENCY_THRESHOLD
        high_demand = demand_score >= self.HIGH_DEMAND_THRESHOLD

        if high_proficiency and high_demand:
            return SkillQuadrant.LEVERAGE
        elif not high_proficiency and high_demand:
            return SkillQuadrant.UPSKILL
        elif high_proficiency and not high_demand:
            return SkillQuadrant.MAINTAIN
        else:
            return SkillQuadrant.DE_EMPHASIZE

    def generate_skill_recommendations(
        self,
        skill: str,
        quadrant: SkillQuadrant,
        proficiency_score: float,
        demand_score: float,
    ) -> List[str]:
        """Generate actionable recommendations for skill development."""
        recommendations = []

        if quadrant == SkillQuadrant.LEVERAGE:
            recommendations.extend(
                [
                    f"Highlight your {skill} expertise prominently in your resume",
                    f"Consider pursuing advanced certifications or specializations in {skill}",
                    f"Mentor others in {skill} to demonstrate leadership",
                    f"Look for senior roles that emphasize {skill} expertise",
                ]
            )

        elif quadrant == SkillQuadrant.UPSKILL:
            recommendations.extend(
                [
                    f"Prioritize learning {skill} - high market demand with growth potential",
                    f"Take online courses or bootcamps to develop {skill} proficiency",
                    f"Start a personal project using {skill} to build experience",
                    f"Network with professionals who specialize in {skill}",
                ]
            )

        elif quadrant == SkillQuadrant.MAINTAIN:
            recommendations.extend(
                [
                    f"Keep {skill} skills current but don't over-invest time",
                    f"Use {skill} experience to differentiate yourself in niche markets",
                    f"Consider how {skill} complements high-demand skills",
                    "Maintain proficiency through periodic practice or refreshers",
                ]
            )

        else:  # DE_EMPHASIZE
            recommendations.extend(
                [
                    f"De-prioritize {skill} in favor of higher-demand skills",
                    f"Consider if {skill} has transferable elements to other technologies",
                    f"Remove outdated {skill} references from your resume",
                    "Focus learning time on skills in the UPSKILL quadrant",
                ]
            )

        return recommendations

    def extract_all_skills(
        self,
        resume_deconstruction: ResumeDeconstruction,
        market_analysis: MarketAnalysisResult,
    ) -> List[str]:
        """Extract comprehensive skill list from resume and market data."""
        skills = set()

        # Extract from resume
        for section in resume_deconstruction.sections:
            for entity in section.entities:
                if entity.label in [EntityType.SKILL, EntityType.TOOL]:
                    skills.add(entity.text.strip())

        # Extract from market data
        for job_match in market_analysis.job_matches:
            skills.update(job_match.job.required_skills)
            skills.update(job_match.job.preferred_skills)

        # Clean and normalize
        cleaned_skills = []
        for skill in skills:
            cleaned_skill = skill.strip()
            if len(cleaned_skill) > 1 and cleaned_skill.lower() not in [
                "and",
                "or",
                "with",
            ]:
                cleaned_skills.append(cleaned_skill)

        return list(set(cleaned_skills))

    def analyze_skill_gaps(
        self,
        leverage_skills: List[SkillClassification],
        upskill_skills: List[SkillClassification],
        market_analysis: MarketAnalysisResult,
    ) -> Dict[str, Any]:
        """Analyze skill gaps and provide strategic insights."""
        # Top skills in high demand that candidate lacks
        high_demand_skills = []
        for job_match in market_analysis.job_matches[:5]:  # Top 5 matches
            high_demand_skills.extend(job_match.job.required_skills)

        demand_counter = Counter(high_demand_skills)

        candidate_skills = set(
            [skill.skill.lower() for skill in leverage_skills + upskill_skills]
        )

        missing_high_demand = []
        for skill, frequency in demand_counter.most_common(10):
            if skill.lower() not in candidate_skills:
                missing_high_demand.append(
                    {
                        "skill": skill,
                        "market_frequency": frequency,
                        "priority": "High" if frequency >= 3 else "Medium",
                    }
                )

        # Skills ready for advancement (high proficiency, growing demand)
        advancement_ready = [
            skill
            for skill in leverage_skills
            if skill.proficiency_score > 0.8 and skill.market_demand_score > 0.3
        ]

        return {
            "missing_high_demand_skills": missing_high_demand[:5],
            "skills_ready_for_advancement": [s.skill for s in advancement_ready],
            "total_skills_analyzed": len(leverage_skills) + len(upskill_skills),
            "skill_portfolio_balance": {
                "technical_skills": len(
                    [s for s in leverage_skills if self._is_technical_skill(s.skill)]
                ),
                "soft_skills": len(
                    [
                        s
                        for s in leverage_skills
                        if not self._is_technical_skill(s.skill)
                    ]
                ),
            },
        }

    def _is_technical_skill(self, skill: str) -> bool:
        """Determine if a skill is technical vs soft skill."""
        technical_indicators = [
            "python",
            "java",
            "javascript",
            "react",
            "angular",
            "vue",
            "docker",
            "kubernetes",
            "aws",
            "azure",
            "gcp",
            "sql",
            "postgresql",
            "mongodb",
            "redis",
            "git",
            "github",
            "jenkins",
            "terraform",
        ]

        skill_lower = skill.lower()
        return any(indicator in skill_lower for indicator in technical_indicators)

    def create_development_roadmap(
        self,
        upskill_skills: List[SkillClassification],
        skill_gap_analysis: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Create prioritized skill development roadmap."""
        roadmap = []

        # High priority: Missing high-demand skills
        for missing_skill in skill_gap_analysis.get("missing_high_demand_skills", []):
            if missing_skill.get("priority") == "High":
                roadmap.append(
                    {
                        "skill": missing_skill["skill"],
                        "priority": "High",
                        "timeline": "0-3 months",
                        "rationale": f"High market demand ({missing_skill['market_frequency']} mentions in top jobs)",
                        "suggested_actions": [
                            "Complete online course or certification",
                            "Build a portfolio project",
                            "Practice through coding challenges or tutorials",
                        ],
                    }
                )

        # Medium priority: Current upskill opportunities
        upskill_sorted = sorted(
            upskill_skills, key=lambda x: x.market_demand_score, reverse=True
        )
        for skill in upskill_sorted[:3]:
            roadmap.append(
                {
                    "skill": skill.skill,
                    "priority": "Medium",
                    "timeline": "3-6 months",
                    "rationale": f"Moderate proficiency, good market demand ({skill.market_demand_score:.1%})",
                    "suggested_actions": [
                        "Deepen existing knowledge through advanced courses",
                        "Apply skills in current work projects",
                        "Seek mentorship or pair programming opportunities",
                    ],
                }
            )

        return roadmap[:5]  # Top 5 priorities

    def recalibrate_skills(
        self,
        resume_deconstruction: ResumeDeconstruction,
        market_analysis: MarketAnalysisResult,
    ) -> SkillFramingMatrix:
        """Perform complete skill recalibration using the Skill Framing Matrix."""
        # Extract all relevant skills
        all_skills = self.extract_all_skills(resume_deconstruction, market_analysis)

        # Classify each skill
        skill_classifications = []
        for skill in all_skills:
            proficiency_score, evidence_count = self.calculate_proficiency_score(
                skill, resume_deconstruction
            )
            demand_score, market_frequency = self.calculate_market_demand_score(
                skill, market_analysis
            )

            quadrant = self.classify_skill_quadrant(proficiency_score, demand_score)
            recommendations = self.generate_skill_recommendations(
                skill, quadrant, proficiency_score, demand_score
            )

            classification = SkillClassification(
                skill=skill,
                proficiency_score=proficiency_score,
                market_demand_score=demand_score,
                quadrant=quadrant,
                evidence_count=evidence_count,
                market_frequency=market_frequency,
                recommendations=recommendations,
            )
            skill_classifications.append(classification)

        # Group by quadrant
        leverage_skills = [
            s for s in skill_classifications if s.quadrant == SkillQuadrant.LEVERAGE
        ]
        upskill_skills = [
            s for s in skill_classifications if s.quadrant == SkillQuadrant.UPSKILL
        ]
        maintain_skills = [
            s for s in skill_classifications if s.quadrant == SkillQuadrant.MAINTAIN
        ]
        de_emphasize_skills = [
            s for s in skill_classifications if s.quadrant == SkillQuadrant.DE_EMPHASIZE
        ]

        # Sort each quadrant by relevance
        leverage_skills.sort(
            key=lambda x: (x.proficiency_score + x.market_demand_score) / 2,
            reverse=True,
        )
        upskill_skills.sort(key=lambda x: x.market_demand_score, reverse=True)
        maintain_skills.sort(key=lambda x: x.proficiency_score, reverse=True)
        de_emphasize_skills.sort(
            key=lambda x: x.proficiency_score + x.market_demand_score, reverse=True
        )

        # Generate matrix insights
        matrix_insights = {
            "total_skills_analyzed": len(all_skills),
            "quadrant_distribution": {
                "leverage": len(leverage_skills),
                "upskill": len(upskill_skills),
                "maintain": len(maintain_skills),
                "de_emphasize": len(de_emphasize_skills),
            },
            "top_leverage_skills": [s.skill for s in leverage_skills[:5]],
            "priority_upskill_skills": [s.skill for s in upskill_skills[:5]],
            "portfolio_strength": len(leverage_skills) / len(all_skills)
            if all_skills
            else 0.0,
        }

        # Analyze skill gaps
        skill_gap_analysis = self.analyze_skill_gaps(
            leverage_skills, upskill_skills, market_analysis
        )

        # Create development roadmap
        development_roadmap = self.create_development_roadmap(
            upskill_skills, skill_gap_analysis
        )

        return SkillFramingMatrix(
            leverage_skills=leverage_skills,
            upskill_skills=upskill_skills,
            maintain_skills=maintain_skills,
            de_emphasize_skills=de_emphasize_skills,
            matrix_insights=matrix_insights,
            skill_gap_analysis=skill_gap_analysis,
            development_roadmap=development_roadmap,
        )
