"""Career path inference engine with horizon modeling and report generation."""

import logging
import time
from typing import Dict, List, Any
from datetime import datetime, timezone
from enum import Enum

from src.models.ner_entities import ResumeDeconstruction
from src.models.market_data import MarketAnalysisResult, JobLevel
from src.models.ats_scoring import ATSScore
from src.core.skill_recalibrator import SkillFramingMatrix


logger = logging.getLogger(__name__)


class CareerHorizon(str, Enum):
    """Career planning horizons."""

    HORIZON_1 = "horizon_1"  # 0-6 months: Immediate opportunities
    HORIZON_2 = "horizon_2"  # 6-18 months: Skill development & transition
    HORIZON_3 = "horizon_3"  # 18+ months: Strategic positioning & leadership


class PathType(str, Enum):
    """Career path types."""

    LATERAL_MOVE = "lateral_move"  # Same level, different focus
    VERTICAL_PROMOTION = "vertical_promotion"  # Higher level, same domain
    CAREER_PIVOT = "career_pivot"  # Different domain/industry
    SPECIALIZATION = "specialization"  # Deeper expertise in current area


class CareerPath:
    """Individual career path recommendation."""

    def __init__(
        self,
        path_id: str,
        title: str,
        path_type: PathType,
        horizon: CareerHorizon,
        target_roles: List[str],
        skill_requirements: List[str],
        preparation_timeline: str,
        confidence_score: float,
        market_opportunity: str,
        rationale: str,
        action_steps: List[str],
    ):
        self.path_id = path_id
        self.title = title
        self.path_type = path_type
        self.horizon = horizon
        self.target_roles = target_roles
        self.skill_requirements = skill_requirements
        self.preparation_timeline = preparation_timeline
        self.confidence_score = confidence_score
        self.market_opportunity = market_opportunity
        self.rationale = rationale
        self.action_steps = action_steps


class CareerAnalysisReport:
    """Comprehensive career analysis report."""

    def __init__(
        self,
        career_paths: List[CareerPath],
        current_positioning: Dict[str, Any],
        market_readiness: Dict[str, Any],
        competitive_advantages: List[str],
        development_priorities: List[str],
        timeline_recommendations: Dict[str, Any],
        executive_summary: str,
        processing_metadata: Dict[str, Any],
    ):
        self.career_paths = career_paths
        self.current_positioning = current_positioning
        self.market_readiness = market_readiness
        self.competitive_advantages = competitive_advantages
        self.development_priorities = development_priorities
        self.timeline_recommendations = timeline_recommendations
        self.executive_summary = executive_summary
        self.processing_metadata = processing_metadata


class CareerInferencer:
    """Career path inference engine with comprehensive analysis."""

    def __init__(self):
        """Initialize career inference engine."""
        self.level_progression = {
            JobLevel.ENTRY: [JobLevel.MID, JobLevel.SENIOR],
            JobLevel.MID: [JobLevel.SENIOR, JobLevel.STAFF],
            JobLevel.SENIOR: [JobLevel.STAFF, JobLevel.PRINCIPAL, JobLevel.DIRECTOR],
            JobLevel.STAFF: [JobLevel.PRINCIPAL, JobLevel.DIRECTOR],
            JobLevel.PRINCIPAL: [JobLevel.DIRECTOR],
            JobLevel.DIRECTOR: [],
        }

    def infer_current_level(
        self, resume_deconstruction: ResumeDeconstruction
    ) -> JobLevel:
        """Infer current career level from resume."""
        level_indicators = {
            JobLevel.DIRECTOR: ["director", "head of", "vp", "vice president", "chief"],
            JobLevel.PRINCIPAL: ["principal", "distinguished", "architect"],
            JobLevel.STAFF: ["staff", "lead", "senior lead"],
            JobLevel.SENIOR: ["senior", "sr.", "lead"],
            JobLevel.MID: ["mid", "ii", "2"],
            JobLevel.ENTRY: ["junior", "entry", "associate", "jr."],
        }

        # Extract all text for analysis
        all_text = " ".join(
            [section.raw_text.lower() for section in resume_deconstruction.sections]
        )

        # Check for level indicators
        for level, indicators in level_indicators.items():
            if any(indicator in all_text for indicator in indicators):
                return level

        # Default inference based on experience depth
        work_experience_sections = [
            s
            for s in resume_deconstruction.sections
            if "work_experience" in s.section_name
        ]

        if len(work_experience_sections) >= 5:
            return JobLevel.SENIOR
        elif len(work_experience_sections) >= 3:
            return JobLevel.MID
        else:
            return JobLevel.ENTRY

    def generate_lateral_paths(
        self,
        current_skills: List[str],
        market_analysis: MarketAnalysisResult,
        skill_matrix: SkillFramingMatrix,
    ) -> List[CareerPath]:
        """Generate lateral career move opportunities."""
        paths = []

        # Find roles with similar skill requirements but different focus areas
        leverage_skills = [s.skill for s in skill_matrix.leverage_skills]

        role_clusters = {}
        for job_match in market_analysis.job_matches[:10]:
            job = job_match.job
            role_base = (
                job.role_title.lower()
                .replace("senior", "")
                .replace("jr", "")
                .replace("junior", "")
                .strip()
            )

            if role_base not in role_clusters:
                role_clusters[role_base] = []
            role_clusters[role_base].append(job)

        for role_type, jobs in role_clusters.items():
            if len(jobs) >= 2:  # Multiple opportunities
                common_skills = []
                for job in jobs[:3]:
                    common_skills.extend(job.required_skills)

                skill_overlap = len(set(leverage_skills) & set(common_skills))

                if skill_overlap >= 3:
                    paths.append(
                        CareerPath(
                            path_id=f"lateral_{role_type.replace(' ', '_')}",
                            title=f"{role_type.title()} Specialist",
                            path_type=PathType.LATERAL_MOVE,
                            horizon=CareerHorizon.HORIZON_1,
                            target_roles=[job.role_title for job in jobs[:3]],
                            skill_requirements=list(set(common_skills))[:5],
                            preparation_timeline="0-3 months",
                            confidence_score=min(0.8, skill_overlap / 5.0),
                            market_opportunity=f"{len(jobs)} opportunities identified",
                            rationale=f"Strong skill alignment ({skill_overlap} matching skills) with immediate market opportunities",
                            action_steps=[
                                "Tailor resume to emphasize relevant experience",
                                "Network with professionals in this specialization",
                                "Apply to identified opportunities",
                            ],
                        )
                    )

        return paths[:3]  # Top 3 lateral opportunities

    def generate_vertical_paths(
        self,
        current_level: JobLevel,
        skill_matrix: SkillFramingMatrix,
        market_analysis: MarketAnalysisResult,
    ) -> List[CareerPath]:
        """Generate vertical promotion opportunities."""
        paths = []

        next_levels = self.level_progression.get(current_level, [])
        leverage_skills = [s.skill for s in skill_matrix.leverage_skills]

        for next_level in next_levels:
            # Find roles at the next level
            matching_roles = []
            for job_match in market_analysis.job_matches:
                if job_match.job.level == next_level:
                    matching_roles.append(job_match.job)

            if matching_roles:
                # Analyze skill requirements for promotion
                promotion_skills = []
                for role in matching_roles[:3]:
                    promotion_skills.extend(role.required_skills)

                skill_gap = len(set(promotion_skills) - set(leverage_skills))
                readiness_score = max(
                    0.1, 1.0 - (skill_gap / max(len(promotion_skills), 1))
                )

                timeline = "3-6 months" if readiness_score > 0.7 else "6-12 months"
                horizon = (
                    CareerHorizon.HORIZON_1
                    if readiness_score > 0.7
                    else CareerHorizon.HORIZON_2
                )

                paths.append(
                    CareerPath(
                        path_id=f"vertical_{next_level}",
                        title=f"Promotion to {next_level.title()} Level",
                        path_type=PathType.VERTICAL_PROMOTION,
                        horizon=horizon,
                        target_roles=[role.role_title for role in matching_roles[:3]],
                        skill_requirements=list(set(promotion_skills))[:5],
                        preparation_timeline=timeline,
                        confidence_score=readiness_score,
                        market_opportunity=f"{len(matching_roles)} roles at {next_level} level",
                        rationale=f"Natural progression from {current_level} with {readiness_score:.1%} skill alignment",
                        action_steps=[
                            "Develop leadership and management skills",
                            "Take on more strategic projects",
                            "Seek mentorship from current leaders",
                            "Build visibility through internal initiatives",
                        ],
                    )
                )

        return paths

    def generate_pivot_paths(
        self, skill_matrix: SkillFramingMatrix, market_analysis: MarketAnalysisResult
    ) -> List[CareerPath]:
        """Generate career pivot opportunities."""
        paths = []

        # Identify transferable skills
        leverage_skills = skill_matrix.leverage_skills

        # Look for roles that value current leverage skills but in different domains
        domain_opportunities = {}

        for job_match in market_analysis.job_matches:
            job = job_match.job
            industry = job.company_name  # Simplified industry detection

            if industry not in domain_opportunities:
                domain_opportunities[industry] = []
            domain_opportunities[industry].append(job)

        for industry, jobs in domain_opportunities.items():
            if len(jobs) >= 2:  # Multiple opportunities in this domain
                # Calculate transferability score
                industry_skills = []
                for job in jobs:
                    industry_skills.extend(job.required_skills)

                transferable_skills = [
                    skill
                    for skill in leverage_skills
                    if any(
                        skill.skill.lower() in req_skill.lower()
                        for req_skill in industry_skills
                    )
                ]

                if len(transferable_skills) >= 2:
                    paths.append(
                        CareerPath(
                            path_id=f"pivot_{industry.lower().replace(' ', '_')}",
                            title=f"Transition to {industry}",
                            path_type=PathType.CAREER_PIVOT,
                            horizon=CareerHorizon.HORIZON_2,
                            target_roles=[job.role_title for job in jobs[:2]],
                            skill_requirements=[
                                skill.skill for skill in transferable_skills[:3]
                            ],
                            preparation_timeline="6-12 months",
                            confidence_score=len(transferable_skills) / 5.0,
                            market_opportunity=f"{len(jobs)} opportunities in {industry}",
                            rationale=f"Transferable skills ({len(transferable_skills)} leverage skills applicable)",
                            action_steps=[
                                f"Research {industry} industry trends",
                                "Network with professionals in target industry",
                                "Consider industry-specific certifications",
                                "Highlight transferable skills in applications",
                            ],
                        )
                    )

        return paths[:2]  # Top 2 pivot opportunities

    def generate_specialization_paths(
        self, skill_matrix: SkillFramingMatrix, market_analysis: MarketAnalysisResult
    ) -> List[CareerPath]:
        """Generate specialization/expertise paths."""
        paths = []

        # Identify areas where candidate has strong leverage skills
        top_leverage_skills = skill_matrix.leverage_skills[:5]

        for skill_classification in top_leverage_skills:
            skill = skill_classification.skill

            # Find specialist roles for this skill
            specialist_roles = []
            for job_match in market_analysis.job_matches:
                job = job_match.job
                if skill.lower() in job.role_title.lower() or any(
                    skill.lower() in req_skill.lower()
                    for req_skill in job.required_skills
                ):
                    specialist_roles.append(job)

            if len(specialist_roles) >= 2:
                paths.append(
                    CareerPath(
                        path_id=f"specialize_{skill.lower().replace(' ', '_')}",
                        title=f"{skill} Specialist/Expert",
                        path_type=PathType.SPECIALIZATION,
                        horizon=CareerHorizon.HORIZON_3,
                        target_roles=[role.role_title for role in specialist_roles[:3]],
                        skill_requirements=[skill]
                        + [
                            s for s in specialist_roles[0].required_skills if s != skill
                        ][:3],
                        preparation_timeline="12-18 months",
                        confidence_score=skill_classification.proficiency_score,
                        market_opportunity=f"{len(specialist_roles)} specialist opportunities",
                        rationale=f"Deep expertise in {skill} (proficiency: {skill_classification.proficiency_score:.1%})",
                        action_steps=[
                            f"Pursue advanced {skill} certifications",
                            f"Contribute to {skill} open source projects",
                            f"Speak at {skill} conferences or meetups",
                            f"Mentor others in {skill} development",
                        ],
                    )
                )

        return paths[:2]  # Top 2 specialization paths

    def assess_current_positioning(
        self,
        resume_deconstruction: ResumeDeconstruction,
        skill_matrix: SkillFramingMatrix,
        ats_score: ATSScore,
    ) -> Dict[str, Any]:
        """Assess current market positioning."""
        return {
            "inferred_level": self.infer_current_level(resume_deconstruction).value,
            "skill_portfolio_strength": len(skill_matrix.leverage_skills),
            "ats_readiness": ats_score.performance_level.value,
            "ats_score_percentage": ats_score.percentage_score,
            "skill_quadrant_distribution": skill_matrix.matrix_insights[
                "quadrant_distribution"
            ],
            "total_experience_indicators": len(
                [
                    s
                    for s in resume_deconstruction.sections
                    if "work_experience" in s.section_name
                ]
            ),
            "multilingual_capability": len(
                [
                    lang
                    for lang, pct in resume_deconstruction.language_distribution.items()
                    if pct > 10
                ]
            ),
        }

    def assess_market_readiness(
        self,
        skill_matrix: SkillFramingMatrix,
        ats_score: ATSScore,
        market_analysis: MarketAnalysisResult,
    ) -> Dict[str, Any]:
        """Assess readiness for market opportunities."""
        # Calculate overall readiness score
        skill_strength = len(skill_matrix.leverage_skills) / max(
            1, skill_matrix.matrix_insights["total_skills_analyzed"]
        )
        ats_readiness = ats_score.overall_score
        market_fit = market_analysis.market_insights.get(
            "average_similarity_score", 0.0
        )

        overall_readiness = (skill_strength + ats_readiness + market_fit) / 3

        return {
            "overall_readiness_score": overall_readiness,
            "readiness_level": self._classify_readiness(overall_readiness),
            "skill_portfolio_strength": skill_strength,
            "ats_compatibility": ats_readiness,
            "market_alignment": market_fit,
            "immediate_opportunities": len(
                [
                    match
                    for match in market_analysis.job_matches
                    if match.similarity_score > 0.6
                ]
            ),
            "skill_gaps": len(skill_matrix.upskill_skills),
            "competitive_position": "Strong"
            if overall_readiness > 0.7
            else "Moderate"
            if overall_readiness > 0.5
            else "Developing",
        }

    def _classify_readiness(self, score: float) -> str:
        """Classify market readiness level."""
        if score >= 0.8:
            return "Market Ready"
        elif score >= 0.6:
            return "Nearly Ready"
        elif score >= 0.4:
            return "Developing"
        else:
            return "Preparation Needed"

    def generate_executive_summary(
        self,
        career_paths: List[CareerPath],
        current_positioning: Dict[str, Any],
        market_readiness: Dict[str, Any],
    ) -> str:
        """Generate executive summary of career analysis."""
        readiness_level = market_readiness["readiness_level"]
        current_level = current_positioning["inferred_level"]
        top_path = career_paths[0] if career_paths else None

        summary = "**Career Analysis Summary**\n\n"
        summary += f"Current Position: {current_level.title()} level professional with {current_positioning['skill_portfolio_strength']} leverage skills.\n"
        summary += f"Market Readiness: {readiness_level} ({market_readiness['overall_readiness_score']:.1%} overall score).\n"
        summary += f"ATS Compatibility: {current_positioning['ats_readiness'].title()} ({current_positioning['ats_score_percentage']}%).\n\n"

        if top_path:
            summary += f"**Recommended Next Step**: {top_path.title} ({top_path.horizon.replace('_', ' ').title()})\n"
            summary += f"Confidence: {top_path.confidence_score:.1%} | Timeline: {top_path.preparation_timeline}\n\n"

        summary += "**Key Insights**:\n"
        summary += f"- {len(career_paths)} viable career paths identified\n"
        summary += f"- {market_readiness['immediate_opportunities']} immediate opportunities available\n"
        summary += (
            f"- {market_readiness['skill_gaps']} skills identified for development\n"
        )

        return summary

    def infer_career_paths(
        self,
        resume_deconstruction: ResumeDeconstruction,
        market_analysis: MarketAnalysisResult,
        skill_matrix: SkillFramingMatrix,
        ats_score: ATSScore,
    ) -> CareerAnalysisReport:
        """Generate comprehensive career path analysis and recommendations."""
        start_time = time.time()

        # Infer current level
        current_level = self.infer_current_level(resume_deconstruction)

        # Extract current skills
        current_skills = [
            s.skill for s in skill_matrix.leverage_skills + skill_matrix.upskill_skills
        ]

        # Generate different types of career paths
        all_paths = []

        # Lateral moves (immediate opportunities)
        lateral_paths = self.generate_lateral_paths(
            current_skills, market_analysis, skill_matrix
        )
        all_paths.extend(lateral_paths)

        # Vertical promotions
        vertical_paths = self.generate_vertical_paths(
            current_level, skill_matrix, market_analysis
        )
        all_paths.extend(vertical_paths)

        # Career pivots
        pivot_paths = self.generate_pivot_paths(skill_matrix, market_analysis)
        all_paths.extend(pivot_paths)

        # Specializations
        specialization_paths = self.generate_specialization_paths(
            skill_matrix, market_analysis
        )
        all_paths.extend(specialization_paths)

        # Sort paths by confidence score and relevance
        all_paths.sort(
            key=lambda p: (p.confidence_score, len(p.target_roles)), reverse=True
        )

        # Assess current positioning
        current_positioning = self.assess_current_positioning(
            resume_deconstruction, skill_matrix, ats_score
        )

        # Assess market readiness
        market_readiness = self.assess_market_readiness(
            skill_matrix, ats_score, market_analysis
        )

        # Identify competitive advantages
        competitive_advantages = [
            f"Strong proficiency in {skill.skill}"
            for skill in skill_matrix.leverage_skills[:3]
        ]
        if current_positioning["multilingual_capability"] > 1:
            competitive_advantages.append("Multilingual capability")
        if current_positioning["ats_score_percentage"] >= 70:
            competitive_advantages.append("ATS-optimized resume")

        # Development priorities
        development_priorities = [
            skill.skill for skill in skill_matrix.upskill_skills[:5]
        ]

        # Timeline recommendations
        timeline_recommendations = {
            "immediate_actions": [
                path.title
                for path in all_paths
                if path.horizon == CareerHorizon.HORIZON_1
            ],
            "short_term_goals": [
                path.title
                for path in all_paths
                if path.horizon == CareerHorizon.HORIZON_2
            ],
            "long_term_vision": [
                path.title
                for path in all_paths
                if path.horizon == CareerHorizon.HORIZON_3
            ],
        }

        # Generate executive summary
        executive_summary = self.generate_executive_summary(
            all_paths, current_positioning, market_readiness
        )

        processing_time = time.time() - start_time

        return CareerAnalysisReport(
            career_paths=all_paths[:10],  # Top 10 paths
            current_positioning=current_positioning,
            market_readiness=market_readiness,
            competitive_advantages=competitive_advantages,
            development_priorities=development_priorities,
            timeline_recommendations=timeline_recommendations,
            executive_summary=executive_summary,
            processing_metadata={
                "processing_time_seconds": processing_time,
                "total_paths_generated": len(all_paths),
                "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
