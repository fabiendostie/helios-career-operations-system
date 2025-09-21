"""Dynamic content selection system using ANALYST recommendations."""

import asyncio
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum

import structlog

from .config import get_settings

logger = structlog.get_logger(__name__)


class SkillQuadrant(str, Enum):
    """Skill quadrant classification from ANALYST service."""
    LEVERAGE = "leverage"      # Strong skills to emphasize
    UPSKILL = "upskill"       # Skills being developed
    MAINTAIN = "maintain"     # Stable core skills
    DE_EMPHASIZE = "de_emphasize"  # Skills to reduce focus on


class ContentPriority(str, Enum):
    """Content priority levels."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    EXCLUDE = "exclude"


@dataclass
class SkillRecommendation:
    """Skill recommendation from ANALYST service."""
    skill: str
    quadrant: SkillQuadrant
    relevance_score: float
    confidence: float
    evidence_count: int
    market_demand: Optional[float] = None


@dataclass
class ContentRecommendation:
    """Content recommendation for document generation."""
    content_type: str  # 'accomplishment', 'skill', 'experience', 'project'
    content_id: str
    priority: ContentPriority
    relevance_score: float
    reasoning: str
    customization_notes: List[str]


@dataclass
class AnalystRecommendations:
    """Parsed recommendations from ANALYST service."""
    skill_recalibration: Dict[SkillQuadrant, List[SkillRecommendation]]
    ats_keywords: List[str]
    impact_metrics: List[str]
    action_verbs: List[str]
    industry_keywords: List[str]
    content_priorities: Dict[str, ContentPriority]
    target_role_alignment: Dict[str, float]


class ContentSelector:
    """Intelligent content selection based on ANALYST recommendations."""

    def __init__(self):
        self.settings = get_settings()

    async def select_resume_content(
        self,
        master_career_db: Dict[str, Any],
        analyst_recommendations: Optional[Dict[str, Any]] = None,
        job_requirements: Optional[Dict[str, Any]] = None,
        template_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Select optimal content for resume based on ANALYST recommendations.

        Args:
            master_career_db: Complete career data from Profile Ingestor
            analyst_recommendations: ANALYST service recommendations
            job_requirements: Job-specific requirements
            template_preferences: Template customization preferences

        Returns:
            Optimized content structure for resume generation
        """
        try:
            logger.info("Starting intelligent content selection for resume")

            # Parse ANALYST recommendations
            parsed_recommendations = self._parse_analyst_recommendations(
                analyst_recommendations or {}
            )

            # Extract base content from career data
            work_experience = master_career_db.get('work_experience', [])
            skills_inventory = master_career_db.get('skills_inventory', {})
            projects = master_career_db.get('projects', [])
            strategic_metadata = master_career_db.get('strategic_metadata', {})

            # Select and optimize work experience
            optimized_experience = await self._select_work_experience(
                work_experience,
                parsed_recommendations,
                job_requirements
            )

            # Select and prioritize skills
            optimized_skills = await self._select_skills(
                skills_inventory,
                parsed_recommendations,
                job_requirements
            )

            # Select relevant projects
            selected_projects = await self._select_projects(
                projects,
                parsed_recommendations,
                job_requirements
            )

            # Create T-shaped summary content
            t_shaped_content = await self._create_t_shaped_summary(
                master_career_db,
                parsed_recommendations,
                job_requirements
            )

            # Create optimized content structure
            optimized_content = {
                **master_career_db,  # Keep base data
                'work_experience': optimized_experience,
                'skills_inventory': optimized_skills,
                'projects': selected_projects,
                **t_shaped_content,  # T-shaped specific fields
                '_content_metadata': {
                    'selection_strategy': 'analyst_optimized',
                    'recommendations_applied': bool(analyst_recommendations),
                    'job_targeted': bool(job_requirements),
                    'optimization_timestamp': asyncio.get_event_loop().time()
                }
            }

            logger.info(
                "Content selection completed",
                experience_count=len(optimized_experience),
                skills_categories=len(optimized_skills.get('technical_skills', {})),
                projects_count=len(selected_projects)
            )

            return optimized_content

        except Exception as e:
            logger.error("Content selection failed", error=str(e), exc_info=True)
            # Fallback to original content
            return master_career_db

    async def select_cover_letter_content(
        self,
        master_career_db: Dict[str, Any],
        job_requirements: Dict[str, Any],
        analyst_recommendations: Optional[Dict[str, Any]] = None,
        company_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Select and customize content for Pain & Promise cover letter.

        Args:
            master_career_db: Complete career data
            job_requirements: Target job requirements
            analyst_recommendations: ANALYST service recommendations
            company_data: Company research data

        Returns:
            Optimized content for cover letter generation
        """
        try:
            logger.info(
                "Starting content selection for cover letter",
                company=job_requirements.get('company', 'Unknown')
            )

            parsed_recommendations = self._parse_analyst_recommendations(
                analyst_recommendations or {}
            )

            # Extract the most relevant achievement for Promise paragraph
            top_achievement = await self._select_top_achievement(
                master_career_db,
                job_requirements,
                parsed_recommendations
            )

            # Identify pain points and connection strategies
            pain_promise_content = await self._create_pain_promise_content(
                master_career_db,
                job_requirements,
                company_data,
                parsed_recommendations
            )

            # Create customized content
            optimized_content = {
                **master_career_db,
                **pain_promise_content,
                'selected_achievement': top_achievement,
                '_content_metadata': {
                    'selection_strategy': 'pain_promise_optimized',
                    'target_company': job_requirements.get('company'),
                    'target_role': job_requirements.get('role_title'),
                    'customization_level': 'high' if company_data else 'medium'
                }
            }

            logger.info("Cover letter content selection completed")
            return optimized_content

        except Exception as e:
            logger.error("Cover letter content selection failed", error=str(e))
            return master_career_db

    def _parse_analyst_recommendations(
        self,
        recommendations: Dict[str, Any]
    ) -> AnalystRecommendations:
        """Parse and structure ANALYST service recommendations."""

        # Extract skill recalibration matrix
        skill_recalibration = {}
        recalibration_data = recommendations.get('skill_recalibration', {})

        for quadrant in SkillQuadrant:
            skills_data = recalibration_data.get(quadrant.value, [])
            skill_recommendations = []

            for skill_data in skills_data:
                if isinstance(skill_data, str):
                    # Simple skill name
                    skill_recommendations.append(SkillRecommendation(
                        skill=skill_data,
                        quadrant=quadrant,
                        relevance_score=0.8,  # Default score
                        confidence=0.7,
                        evidence_count=1
                    ))
                elif isinstance(skill_data, dict):
                    # Detailed skill data
                    skill_recommendations.append(SkillRecommendation(
                        skill=skill_data.get('name', skill_data.get('skill', '')),
                        quadrant=quadrant,
                        relevance_score=skill_data.get('relevance_score', 0.8),
                        confidence=skill_data.get('confidence', 0.7),
                        evidence_count=skill_data.get('evidence_count', 1),
                        market_demand=skill_data.get('market_demand')
                    ))

            skill_recalibration[quadrant] = skill_recommendations

        # Extract other recommendations
        ats_optimization = recommendations.get('ats_optimization', {})
        content_recommendations = recommendations.get('content_recommendations', {})

        return AnalystRecommendations(
            skill_recalibration=skill_recalibration,
            ats_keywords=ats_optimization.get('keywords_to_emphasize', []),
            impact_metrics=content_recommendations.get('impact_metrics', []),
            action_verbs=content_recommendations.get('action_verbs', []),
            industry_keywords=content_recommendations.get('industry_keywords', []),
            content_priorities=recommendations.get('content_priorities', {}),
            target_role_alignment=recommendations.get('target_role_alignment', {})
        )

    async def _select_work_experience(
        self,
        work_experience: List[Dict[str, Any]],
        recommendations: AnalystRecommendations,
        job_requirements: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Select and optimize work experience entries."""

        if not work_experience:
            return []

        optimized_experience = []

        for job_entry in work_experience:
            # Copy the job entry
            optimized_job = job_entry.copy()

            # Optimize accomplishments based on recommendations
            accomplishments = job_entry.get('accomplishments', [])
            optimized_accomplishments = await self._optimize_accomplishments(
                accomplishments, recommendations, job_requirements
            )
            optimized_job['accomplishments'] = optimized_accomplishments

            # Optimize skills used based on quadrant recommendations
            skills_used = job_entry.get('skills_used', [])
            optimized_skills = await self._optimize_job_skills(
                skills_used, recommendations
            )
            optimized_job['skills_used'] = optimized_skills

            # Add relevance score for potential reordering
            relevance_score = await self._calculate_job_relevance(
                optimized_job, recommendations, job_requirements
            )
            optimized_job['_relevance_score'] = relevance_score

            optimized_experience.append(optimized_job)

        # Sort by relevance (most relevant first)
        optimized_experience.sort(
            key=lambda x: x.get('_relevance_score', 0),
            reverse=True
        )

        # Limit to most relevant positions (typically 3-5 for resume)
        max_positions = 5
        return optimized_experience[:max_positions]

    async def _optimize_accomplishments(
        self,
        accomplishments: List[str],
        recommendations: AnalystRecommendations,
        job_requirements: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Optimize accomplishment bullets based on recommendations."""

        optimized_accomplishments = []
        target_keywords = set()

        # Collect target keywords
        target_keywords.update(recommendations.ats_keywords)
        target_keywords.update(recommendations.industry_keywords)

        if job_requirements:
            target_keywords.update(job_requirements.get('required_skills', []))
            target_keywords.update(job_requirements.get('ats_keywords', []))

        for accomplishment in accomplishments:
            optimized_text = accomplishment

            # Enhance with recommended action verbs if applicable
            optimized_text = await self._enhance_with_action_verbs(
                optimized_text, recommendations.action_verbs
            )

            # Ensure impact metrics are prominent
            optimized_text = await self._enhance_impact_metrics(
                optimized_text, recommendations.impact_metrics
            )

            # Calculate relevance score
            relevance_score = await self._calculate_accomplishment_relevance(
                optimized_text, target_keywords
            )

            if relevance_score > 0.3:  # Threshold for inclusion
                optimized_accomplishments.append(optimized_text)

        # Sort by relevance and limit to top accomplishments
        accomplishments_with_scores = [
            (acc, await self._calculate_accomplishment_relevance(acc, target_keywords))
            for acc in optimized_accomplishments
        ]
        accomplishments_with_scores.sort(key=lambda x: x[1], reverse=True)

        # Return top 4-5 accomplishments
        return [acc[0] for acc in accomplishments_with_scores[:5]]

    async def _optimize_job_skills(
        self,
        skills_used: List[str],
        recommendations: AnalystRecommendations
    ) -> List[str]:
        """Optimize skills list based on quadrant recommendations."""

        optimized_skills = []
        leverage_skills = {r.skill.lower() for r in recommendations.skill_recalibration.get(SkillQuadrant.LEVERAGE, [])}
        upskill_skills = {r.skill.lower() for r in recommendations.skill_recalibration.get(SkillQuadrant.UPSKILL, [])}
        de_emphasize_skills = {r.skill.lower() for r in recommendations.skill_recalibration.get(SkillQuadrant.DE_EMPHASIZE, [])}

        # Prioritize skills based on quadrant
        skill_priority_map = {}

        for skill in skills_used:
            skill_lower = skill.lower()

            if skill_lower in leverage_skills:
                skill_priority_map[skill] = 1  # Highest priority
            elif skill_lower in upskill_skills:
                skill_priority_map[skill] = 2  # Medium priority
            elif skill_lower in de_emphasize_skills:
                skill_priority_map[skill] = 4  # Lowest priority
            else:
                skill_priority_map[skill] = 3  # Default priority

        # Sort by priority and return
        sorted_skills = sorted(skills_used, key=lambda s: skill_priority_map.get(s, 3))

        # Filter out de-emphasized skills if we have better options
        if len(sorted_skills) > 6:  # If we have many skills, be selective
            filtered_skills = [s for s in sorted_skills if skill_priority_map.get(s, 3) <= 3]
            return filtered_skills[:8]  # Limit to 8 skills

        return sorted_skills

    async def _select_skills(
        self,
        skills_inventory: Dict[str, Any],
        recommendations: AnalystRecommendations,
        job_requirements: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Select and prioritize skills based on recommendations."""

        optimized_skills = skills_inventory.copy()

        # Get skills from different quadrants
        leverage_skills = [r.skill for r in recommendations.skill_recalibration.get(SkillQuadrant.LEVERAGE, [])]
        upskill_skills = [r.skill for r in recommendations.skill_recalibration.get(SkillQuadrant.UPSKILL, [])]
        maintain_skills = [r.skill for r in recommendations.skill_recalibration.get(SkillQuadrant.MAINTAIN, [])]

        # Create prioritized core skills list for T-shaped summary
        core_skills = []

        # Add leverage skills first (highest priority)
        core_skills.extend(leverage_skills[:4])

        # Add maintain skills
        core_skills.extend([s for s in maintain_skills if s not in core_skills][:2])

        # Add upskill skills if we need more
        if len(core_skills) < 8:
            remaining_needed = 8 - len(core_skills)
            core_skills.extend([s for s in upskill_skills if s not in core_skills][:remaining_needed])

        # If still need more, add from job requirements
        if job_requirements and len(core_skills) < 8:
            required_skills = job_requirements.get('required_skills', [])
            remaining_needed = 8 - len(core_skills)
            core_skills.extend([s for s in required_skills if s not in core_skills][:remaining_needed])

        optimized_skills['core_skills'] = core_skills[:8]  # Limit to 8 for ATS optimization

        return optimized_skills

    async def _select_projects(
        self,
        projects: List[Dict[str, Any]],
        recommendations: AnalystRecommendations,
        job_requirements: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Select most relevant projects."""

        if not projects:
            return []

        # Score projects based on skill alignment and keywords
        project_scores = []

        for project in projects:
            score = 0.0

            # Score based on technologies used
            project_technologies = project.get('technologies', [])
            leverage_skills = [r.skill.lower() for r in recommendations.skill_recalibration.get(SkillQuadrant.LEVERAGE, [])]

            for tech in project_technologies:
                if tech.lower() in leverage_skills:
                    score += 0.3
                if tech.lower() in recommendations.ats_keywords:
                    score += 0.2

            # Score based on job requirements alignment
            if job_requirements:
                required_skills = [s.lower() for s in job_requirements.get('required_skills', [])]
                for tech in project_technologies:
                    if tech.lower() in required_skills:
                        score += 0.4

            # Score based on description keyword alignment
            description = project.get('description', '').lower()
            for keyword in recommendations.industry_keywords:
                if keyword.lower() in description:
                    score += 0.1

            project_scores.append((project, score))

        # Sort by score and return top 3
        project_scores.sort(key=lambda x: x[1], reverse=True)
        return [project[0] for project in project_scores[:3]]

    async def _create_t_shaped_summary(
        self,
        master_career_db: Dict[str, Any],
        recommendations: AnalystRecommendations,
        job_requirements: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create optimized T-shaped summary fields."""

        # Get core competencies from strategic metadata and recommendations
        strategic_metadata = master_career_db.get('strategic_metadata', {})
        base_competencies = strategic_metadata.get('core_competencies', [])

        # Enhance with leverage skills
        leverage_skills = [r.skill for r in recommendations.skill_recalibration.get(SkillQuadrant.LEVERAGE, [])]

        # Combine and prioritize competencies
        all_competencies = list(base_competencies)
        all_competencies.extend([skill for skill in leverage_skills if skill not in all_competencies])

        # Select top 3 for T-shaped formula
        selected_competencies = all_competencies[:3]
        if len(selected_competencies) < 3:
            # Pad with industry keywords if needed
            industry_keywords = recommendations.industry_keywords
            for keyword in industry_keywords:
                if len(selected_competencies) >= 3:
                    break
                if keyword not in selected_competencies:
                    selected_competencies.append(keyword)

        # Ensure we have 3 competencies
        while len(selected_competencies) < 3:
            selected_competencies.append("expertise")

        # Select top quantified achievement
        achievements = strategic_metadata.get('quantified_achievements', [])
        top_achievement = "delivered exceptional results"

        if achievements:
            # Find achievement with best metric alignment
            for achievement in achievements:
                if any(metric in achievement for metric in recommendations.impact_metrics):
                    top_achievement = achievement
                    break
            else:
                top_achievement = achievements[0]  # Fallback to first

        # Determine appropriate adjective based on recommendations
        years_exp = self._calculate_years_experience(master_career_db.get('work_experience', []))
        adjective = await self._select_optimal_adjective(
            years_exp, recommendations, job_requirements
        )

        return {
            'core_competency_1': selected_competencies[0],
            'core_competency_2': selected_competencies[1],
            'core_technology': selected_competencies[2],
            'top_quantified_achievement': top_achievement,
            'adjective': adjective,
            'years_experience': years_exp,
            'skill_area': selected_competencies[0]  # Primary skill area
        }

    async def _create_pain_promise_content(
        self,
        master_career_db: Dict[str, Any],
        job_requirements: Dict[str, Any],
        company_data: Optional[Dict[str, Any]],
        recommendations: AnalystRecommendations
    ) -> Dict[str, Any]:
        """Create Pain & Promise specific content with DYNAMIC company research."""

        from .research_engine import get_research_engine

        company_name = job_requirements.get('company', '')

        try:
            # Get dynamic company intelligence if company name is provided
            if company_name:
                research_engine = await get_research_engine()
                company_intelligence = await research_engine.get_company_intelligence(
                    company_name=company_name,
                    max_age_hours=4  # Very fresh company data for cover letters
                )

                # Merge with provided company_data
                if company_data:
                    company_intelligence.update(company_data)

                company_challenges = company_intelligence.get('challenges', [])
                company_challenges.extend(company_intelligence.get('recent_news', []))
                company_challenges.extend(company_intelligence.get('pain_points', []))

                # Get industry-specific intelligence
                industry = job_requirements.get('industry', '') or company_intelligence.get('industry', '')
                if industry:
                    industry_intelligence = await research_engine.get_industry_intelligence(
                        industry=industry,
                        research_depth="quick",
                        max_age_hours=12
                    )

                    # Add industry challenges to company context
                    industry_challenges = industry_intelligence.get('challenges', [])
                    company_challenges.extend(industry_challenges)
            else:
                company_challenges = []
                if company_data:
                    company_challenges.extend(company_data.get('challenges', []))
                    company_challenges.extend(company_data.get('recent_news', []))
                company_intelligence = company_data or {}

        except Exception as e:
            logger.warning(f"Failed to get dynamic company intelligence: {e}")
            # Fallback to provided company_data
            company_challenges = []
            if company_data:
                company_challenges.extend(company_data.get('challenges', []))
                company_challenges.extend(company_data.get('recent_news', []))
            company_intelligence = company_data or {}

        # Infer pain points from job requirements and research
        role_title = job_requirements.get('role_title', '')
        industry = job_requirements.get('industry', '')

        # Create intelligent pain point mapping using research data
        pain_point = await self._infer_pain_point_with_research(
            role_title, industry, company_challenges, company_intelligence
        )

        # Select best achievement to address the pain point
        work_experience = master_career_db.get('work_experience', [])
        strategic_metadata = master_career_db.get('strategic_metadata', {})

        relevant_achievement = await self._select_pain_addressing_achievement(
            work_experience, strategic_metadata, pain_point, recommendations
        )

        # Get skills that bridge to the pain point using current market intelligence
        bridge_skills = await self._select_bridge_skills_with_research(
            recommendations, job_requirements, industry
        )

        return {
            'inferred_pain_point': pain_point['description'],
            'company_challenge_context': pain_point['context'],
            'specific_challenge_detail': pain_point['specific_detail'],
            'top_quantified_achievement': relevant_achievement,
            'key_skill_1': bridge_skills[0] if bridge_skills else "expertise",
            'key_skill_2': bridge_skills[1] if len(bridge_skills) > 1 else "leadership",
            'relevant_skill_area': bridge_skills[0] if bridge_skills else "strategic implementation",
            'connection_to_pain_point': f"addressing {pain_point['category']} challenges",

            # Enhanced with research data
            'company_growth_areas': company_intelligence.get('growth_areas', []),
            'industry_trends': company_intelligence.get('hiring_trends', {}),
            '_research_enhanced': True,
            '_company_research_timestamp': company_intelligence.get('timestamp'),
        }

    async def _select_top_achievement(
        self,
        master_career_db: Dict[str, Any],
        job_requirements: Dict[str, Any],
        recommendations: AnalystRecommendations
    ) -> str:
        """Select the most impactful achievement for cover letter."""

        strategic_metadata = master_career_db.get('strategic_metadata', {})
        achievements = strategic_metadata.get('quantified_achievements', [])

        if not achievements:
            return "delivered significant results and improvements"

        # Score achievements based on impact metrics and relevance
        achievement_scores = []

        for achievement in achievements:
            score = 0.0

            # Score based on quantified metrics
            for metric in recommendations.impact_metrics:
                if metric.lower() in achievement.lower():
                    score += 0.4

            # Score based on industry keyword alignment
            for keyword in recommendations.industry_keywords:
                if keyword.lower() in achievement.lower():
                    score += 0.3

            # Score based on job requirements
            required_skills = job_requirements.get('required_skills', [])
            for skill in required_skills:
                if skill.lower() in achievement.lower():
                    score += 0.3

            achievement_scores.append((achievement, score))

        # Return highest scoring achievement
        achievement_scores.sort(key=lambda x: x[1], reverse=True)
        return achievement_scores[0][0]

    async def _calculate_job_relevance(
        self,
        job_entry: Dict[str, Any],
        recommendations: AnalystRecommendations,
        job_requirements: Optional[Dict[str, Any]] = None
    ) -> float:
        """Calculate relevance score for a job entry."""

        score = 0.0

        # Score based on skills alignment
        skills_used = job_entry.get('skills_used', [])
        leverage_skills = [r.skill.lower() for r in recommendations.skill_recalibration.get(SkillQuadrant.LEVERAGE, [])]

        for skill in skills_used:
            if skill.lower() in leverage_skills:
                score += 0.3
            if skill.lower() in recommendations.ats_keywords:
                score += 0.2

        # Score based on job requirements alignment
        if job_requirements:
            required_skills = [s.lower() for s in job_requirements.get('required_skills', [])]
            for skill in skills_used:
                if skill.lower() in required_skills:
                    score += 0.4

        # Score based on accomplishments relevance
        accomplishments = job_entry.get('accomplishments', [])
        for accomplishment in accomplishments:
            for keyword in recommendations.industry_keywords:
                if keyword.lower() in accomplishment.lower():
                    score += 0.1

        return score

    async def _calculate_accomplishment_relevance(
        self,
        accomplishment: str,
        target_keywords: Set[str]
    ) -> float:
        """Calculate relevance score for an accomplishment."""

        score = 0.0
        accomplishment_lower = accomplishment.lower()

        # Count keyword matches
        for keyword in target_keywords:
            if keyword.lower() in accomplishment_lower:
                score += 0.2

        # Bonus for quantified metrics
        import re
        if re.search(r'\d+%|\$\d+|x\d+|\d+,\d+', accomplishment):
            score += 0.3

        # Bonus for strong action verbs
        strong_verbs = ['achieved', 'improved', 'increased', 'reduced', 'delivered', 'led', 'implemented']
        for verb in strong_verbs:
            if verb in accomplishment_lower:
                score += 0.1
                break

        return min(score, 1.0)  # Cap at 1.0

    async def _enhance_with_action_verbs(
        self,
        text: str,
        recommended_verbs: List[str]
    ) -> str:
        """Enhance text with stronger action verbs if appropriate."""

        # This is a simplified implementation
        # Could be enhanced with NLP to intelligently replace weak verbs
        return text

    async def _enhance_impact_metrics(
        self,
        text: str,
        impact_metrics: List[str]
    ) -> str:
        """Ensure impact metrics are clearly presented."""

        # This is a simplified implementation
        # Could be enhanced to reformat metrics for better visibility
        return text

    async def _infer_pain_point_with_research(
        self,
        role_title: str,
        industry: str,
        company_challenges: List[str],
        company_intelligence: Dict[str, Any]
    ) -> Dict[str, str]:
        """Infer pain points enhanced with dynamic research intelligence."""

        # Start with base pain point mapping
        base_pain_point = await self._infer_pain_point(role_title, industry, company_challenges)

        # Enhance with research intelligence
        growth_areas = company_intelligence.get('growth_areas', [])
        hiring_trends = company_intelligence.get('hiring_trends', {})
        industry_challenges = company_intelligence.get('challenges', [])

        # Combine company challenges with research data
        all_challenges = company_challenges + industry_challenges

        # Refine pain point based on research
        if growth_areas and any('ai' in area.lower() or 'ml' in area.lower() for area in growth_areas):
            if 'engineer' in role_title.lower():
                base_pain_point.update({
                    'description': 'scaling AI/ML infrastructure and implementing intelligent systems',
                    'context': 'rapid AI adoption and machine learning integration demands',
                    'specific_detail': 'building robust, scalable AI-powered platforms'
                })

        elif any('scale' in challenge.lower() or 'growth' in challenge.lower() for challenge in all_challenges):
            base_pain_point.update({
                'context': f"rapid scaling challenges and {base_pain_point['context']}",
                'specific_detail': f"managing growth complexity while {base_pain_point['specific_detail']}"
            })

        return base_pain_point

    async def _infer_pain_point(
        self,
        role_title: str,
        industry: str,
        company_challenges: List[str]
    ) -> Dict[str, str]:
        """Infer likely pain points based on role and industry."""

        # Simplified pain point mapping
        role_lower = role_title.lower()
        industry_lower = industry.lower()

        if 'engineer' in role_lower or 'developer' in role_lower:
            return {
                'description': 'scaling technical infrastructure efficiently',
                'context': 'rapid growth and increasing technical demands',
                'specific_detail': 'implementing robust, scalable systems',
                'category': 'technical'
            }
        elif 'manager' in role_lower or 'director' in role_lower:
            return {
                'description': 'optimizing team performance and operational efficiency',
                'context': 'organizational growth and process optimization',
                'specific_detail': 'implementing effective leadership and process improvements',
                'category': 'operational'
            }
        else:
            return {
                'description': 'improving operational efficiency and business outcomes',
                'context': 'competitive market pressures and growth objectives',
                'specific_detail': 'implementing strategic initiatives and process improvements',
                'category': 'strategic'
            }

    async def _select_pain_addressing_achievement(
        self,
        work_experience: List[Dict[str, Any]],
        strategic_metadata: Dict[str, Any],
        pain_point: Dict[str, str],
        recommendations: AnalystRecommendations
    ) -> str:
        """Select achievement that best addresses the identified pain point."""

        achievements = strategic_metadata.get('quantified_achievements', [])

        if not achievements:
            return "delivered significant operational improvements"

        pain_category = pain_point['category']

        # Score achievements based on pain point relevance
        for achievement in achievements:
            achievement_lower = achievement.lower()

            if pain_category == 'technical' and any(word in achievement_lower for word in ['system', 'technical', 'performance', 'scale']):
                return achievement
            elif pain_category == 'operational' and any(word in achievement_lower for word in ['efficiency', 'process', 'team', 'operational']):
                return achievement
            elif pain_category == 'strategic' and any(word in achievement_lower for word in ['revenue', 'growth', 'strategic', 'business']):
                return achievement

        # Fallback to first achievement
        return achievements[0]

    async def _select_bridge_skills_with_research(
        self,
        recommendations: AnalystRecommendations,
        job_requirements: Dict[str, Any],
        industry: str
    ) -> List[str]:
        """Select bridge skills enhanced with current market intelligence."""

        # Start with base bridge skills
        base_skills = await self._select_bridge_skills(recommendations, job_requirements)

        try:
            # Get dynamic research engine for current market trends
            from .research_engine import get_research_engine
            research_engine = await get_research_engine()

            # Get skills demand intelligence for the industry
            skills_intelligence = await research_engine.get_skills_demand_intelligence(
                industry=industry,
                role_type=job_requirements.get('role_title', ''),
                max_age_hours=6  # Very fresh skills data
            )

            # Get trending skills that might bridge to the role
            trending_skills = skills_intelligence.get('high_demand_skills', [])
            emerging_skills = skills_intelligence.get('emerging_skills', [])

            # Enhance bridge skills with market-trending skills
            enhanced_skills = base_skills.copy()

            # Add trending skills that match our leverage skills
            leverage_skills = [r.skill.lower() for r in recommendations.skill_recalibration.get(SkillQuadrant.LEVERAGE, [])]

            for skill in trending_skills:
                if (skill.lower() in leverage_skills and
                    skill not in enhanced_skills and
                    len(enhanced_skills) < 3):
                    enhanced_skills.append(skill)

            # Add emerging skills if they're upskill targets
            upskill_skills = [r.skill.lower() for r in recommendations.skill_recalibration.get(SkillQuadrant.UPSKILL, [])]

            for skill in emerging_skills:
                if (skill.lower() in upskill_skills and
                    skill not in enhanced_skills and
                    len(enhanced_skills) < 3):
                    enhanced_skills.append(skill)

            return enhanced_skills[:3]

        except Exception as e:
            logger.warning(f"Failed to enhance bridge skills with research: {e}")
            return base_skills

    async def _select_bridge_skills(
        self,
        recommendations: AnalystRecommendations,
        job_requirements: Dict[str, Any]
    ) -> List[str]:
        """Select skills that bridge to job requirements."""

        bridge_skills = []

        # Get leverage skills (highest priority)
        leverage_skills = [r.skill for r in recommendations.skill_recalibration.get(SkillQuadrant.LEVERAGE, [])]
        bridge_skills.extend(leverage_skills[:2])

        # Add required skills from job
        required_skills = job_requirements.get('required_skills', [])
        for skill in required_skills:
            if skill not in bridge_skills and len(bridge_skills) < 3:
                bridge_skills.append(skill)

        # Ensure we have at least 2 skills
        if len(bridge_skills) == 0:
            bridge_skills = ["expertise", "leadership"]
        elif len(bridge_skills) == 1:
            bridge_skills.append("problem-solving")

        return bridge_skills[:3]

    async def _select_optimal_adjective(
        self,
        years_experience: int,
        recommendations: AnalystRecommendations,
        job_requirements: Optional[Dict[str, Any]] = None
    ) -> str:
        """Select optimal adjective based on experience and role."""

        # Base adjective on experience level
        if years_experience < 3:
            base_options = ["Motivated", "Dedicated", "Emerging"]
        elif years_experience < 7:
            base_options = ["Experienced", "Skilled", "Accomplished"]
        elif years_experience < 12:
            base_options = ["Senior", "Expert", "Seasoned"]
        else:
            base_options = ["Strategic", "Visionary", "Executive"]

        # Customize based on job requirements or industry
        if job_requirements:
            role_title = job_requirements.get('role_title', '').lower()

            if 'senior' in role_title or 'lead' in role_title:
                return "Strategic" if years_experience >= 7 else "Experienced"
            elif 'principal' in role_title or 'architect' in role_title:
                return "Expert" if years_experience >= 5 else "Skilled"

        return base_options[0]  # Default to first option

    def _calculate_years_experience(self, work_experience: List[Dict[str, Any]]) -> int:
        """Calculate years of experience from work history."""
        if not work_experience:
            return 0
        return min(len(work_experience) * 2, 20)  # Simplified calculation


# Dynamic industry-specific customization logic
async def customize_template_by_industry(
    template_content: Dict[str, Any],
    industry: str,
    role_level: str,
    recommendations: Optional[AnalystRecommendations] = None
) -> Dict[str, Any]:
    """
    Apply DYNAMIC industry-specific customizations using real-time research.

    Args:
        template_content: Base template content
        industry: Target industry
        role_level: Experience level (entry, mid, senior, executive)
        recommendations: ANALYST recommendations

    Returns:
        Dynamically customized template content
    """
    from .research_engine import get_research_engine

    customized_content = template_content.copy()

    try:
        # Get dynamic research engine
        research_engine = await get_research_engine()

        # Gather real-time industry intelligence
        industry_intelligence = await research_engine.get_industry_intelligence(
            industry=industry,
            research_depth="standard",
            max_age_hours=24
        )

        # Get current ATS compliance requirements
        ats_intelligence = await research_engine.get_ats_compliance_intelligence(
            max_age_hours=12
        )

        # Get skills demand intelligence
        skills_intelligence = await research_engine.get_skills_demand_intelligence(
            industry=industry,
            role_type=role_level,
            max_age_hours=6
        )

        # Apply dynamic customizations based on research
        customized_content.update({
            # Research-driven emphasis areas
            'emphasis_areas': industry_intelligence.get('emphasis_areas', [
                'performance', 'results', 'impact', 'leadership'
            ]),

            # Current terminology style
            'terminology_style': industry_intelligence.get('terminology_style', 'professional'),

            # Optimal achievement format
            'achievement_format': industry_intelligence.get('achievement_format', 'metric_driven'),

            # Trending skills to emphasize
            'trending_skills': skills_intelligence.get('high_demand_skills', []),

            # Emerging skills to include
            'emerging_skills': skills_intelligence.get('emerging_skills', []),

            # Industry keywords for ATS optimization
            'industry_keywords': industry_intelligence.get('keywords', []),

            # Current ATS requirements
            'ats_requirements': ats_intelligence.get('requirements', {}),

            # Research metadata
            '_research_metadata': {
                'industry_research_timestamp': industry_intelligence.get('research_timestamp'),
                'skills_research_timestamp': skills_intelligence.get('timestamp'),
                'ats_research_timestamp': ats_intelligence.get('last_updated'),
                'research_confidence': 'high',
                'data_freshness': 'current'
            }
        })

        # Role level adjustments (enhanced with research)
        if role_level == 'executive':
            customized_content['focus_areas'] = industry_intelligence.get('executive_focus', [
                'vision', 'transformation', 'organizational_leadership', 'strategic_results'
            ])
            customized_content['summary_style'] = 'executive_brief'
        elif role_level == 'senior':
            customized_content['focus_areas'] = industry_intelligence.get('senior_focus', [
                'leadership', 'strategic_impact', 'mentoring', 'complex_projects'
            ])
            customized_content['summary_style'] = 'comprehensive'

        logger.info(
            "Dynamic industry customization applied",
            industry=industry,
            role_level=role_level,
            trending_skills_count=len(customized_content.get('trending_skills', [])),
            emphasis_areas_count=len(customized_content.get('emphasis_areas', []))
        )

    except Exception as e:
        logger.error(
            "Dynamic research failed, falling back to static customizations",
            industry=industry,
            error=str(e)
        )

        # Fallback to static customizations if research fails
        industry_lower = industry.lower()

        if 'technology' in industry_lower or 'software' in industry_lower:
            customized_content.update({
                'emphasis_areas': ['technical_skills', 'system_impact', 'scalability_metrics', 'innovation'],
                'terminology_style': 'technical',
                'achievement_format': 'metric_driven'
            })
        elif 'finance' in industry_lower or 'banking' in industry_lower:
            customized_content.update({
                'emphasis_areas': ['regulatory_compliance', 'risk_management', 'revenue_impact', 'analysis'],
                'terminology_style': 'business',
                'achievement_format': 'financial_impact'
            })
        elif 'healthcare' in industry_lower or 'medical' in industry_lower:
            customized_content.update({
                'emphasis_areas': ['patient_outcomes', 'compliance', 'quality_improvement', 'safety'],
                'terminology_style': 'clinical',
                'achievement_format': 'outcome_focused'
            })

        # Static role level adjustments
        if role_level == 'executive':
            customized_content['focus_areas'] = ['vision', 'transformation', 'organizational_leadership', 'strategic_results']
            customized_content['summary_style'] = 'executive_brief'
        elif role_level == 'senior':
            customized_content['focus_areas'] = ['leadership', 'strategic_impact', 'mentoring', 'complex_projects']
            customized_content['summary_style'] = 'comprehensive'

    return customized_content
