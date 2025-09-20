"""
LLM-enhanced career path generation that extends the base CareerGenerator
with AI-powered insights and explanations.
"""

import asyncio
import logging
from typing import Any

from ..models.career_path import CareerPathRequest, CareerTargetProfile
from ..models.role_taxonomy import JobRole
from ..models.skill_vector import CandidateProfile
from .career_generator import CareerGenerator
from .config import StrategistConfig

# Import the shared LLM client
try:
    from services.shared.llm_client import ResilientLLMClient
    from services.shared.llm_client.exceptions import LLMClientError
except ImportError:
    # Fallback if shared client not available
    ResilientLLMClient = None
    LLMClientError = Exception

logger = logging.getLogger(__name__)


class LLMEnhancedCareerGenerator(CareerGenerator):
    """
    Enhanced career generator that uses LLM for generating detailed explanations,
    market insights, and personalized recommendations.
    """

    def __init__(self, config: StrategistConfig | None = None):
        super().__init__(config)
        self.llm_client: ResilientLLMClient | None = None
        self.llm_enabled = False

        # Initialize LLM client if available
        if ResilientLLMClient:
            try:
                self.llm_client = ResilientLLMClient()
                self.llm_enabled = True
                logger.info("LLM-enhanced generation enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize LLM client: {e}")
                self.llm_enabled = False
        else:
            logger.warning(
                "Shared LLM client not available, using base generation only"
            )

    async def close(self):
        """Clean up LLM client resources."""
        if self.llm_client:
            await self.llm_client.close()

    async def _generate_career_target_profile(
        self,
        request: CareerPathRequest,
        candidate_profile: CandidateProfile,
        role: JobRole,
        fit_details,
        aspiration_profile,
    ) -> CareerTargetProfile:
        """Generate enhanced Career Target Profile with LLM insights."""

        # Get base CTP from parent class
        base_ctp = await super()._generate_career_target_profile(
            request, candidate_profile, role, fit_details, aspiration_profile
        )

        # Enhance with LLM if available
        if self.llm_enabled and self.llm_client:
            try:
                enhanced_ctp = await self._enhance_with_llm(
                    base_ctp, request, candidate_profile, role
                )
                return enhanced_ctp
            except Exception as e:
                logger.warning(f"LLM enhancement failed, using base CTP: {e}")

        return base_ctp

    async def _enhance_with_llm(
        self,
        base_ctp: CareerTargetProfile,
        request: CareerPathRequest,
        candidate_profile: CandidateProfile,
        role: JobRole,
    ) -> CareerTargetProfile:
        """Enhance career target profile with LLM-generated insights."""

        logger.info(f"Enhancing CTP for role {role.title} with LLM insights")

        # Generate enhanced explanations concurrently
        enhancement_tasks = [
            self._generate_detailed_explanation(base_ctp, candidate_profile, role),
            self._generate_market_insights(role),
            self._generate_personalized_advice(base_ctp, candidate_profile, role),
        ]

        try:
            detailed_explanation, market_insights, personalized_advice = (
                await asyncio.gather(*enhancement_tasks, return_exceptions=True)
            )

            # Handle any failed tasks
            if isinstance(detailed_explanation, Exception):
                logger.warning(
                    f"Failed to generate detailed explanation: {detailed_explanation}"
                )
                detailed_explanation = base_ctp.explanation

            if isinstance(market_insights, Exception):
                logger.warning(f"Failed to generate market insights: {market_insights}")
                market_insights = ""

            if isinstance(personalized_advice, Exception):
                logger.warning(
                    f"Failed to generate personalized advice: {personalized_advice}"
                )
                personalized_advice = []

            # Create enhanced CTP
            enhanced_ctp = CareerTargetProfile(
                **base_ctp.__dict__,  # Copy all base attributes
                explanation=detailed_explanation,
                market_insights=market_insights,
                personalized_recommendations=personalized_advice,
            )

            return enhanced_ctp

        except Exception as e:
            logger.error(f"LLM enhancement failed: {e}")
            return base_ctp

    async def _generate_detailed_explanation(
        self,
        ctp: CareerTargetProfile,
        candidate_profile: CandidateProfile,
        role: JobRole,
    ) -> str:
        """Generate detailed explanation of why this role is a good fit."""

        prompt = f"""
        Analyze why this career transition makes sense for this professional:

        CANDIDATE PROFILE:
        - Current skills: {', '.join(candidate_profile.skills[:10])}
        - Key accomplishments: {'; '.join(candidate_profile.accomplishments[:3]) if candidate_profile.accomplishments else 'Not specified'}
        - Career interests: {', '.join(candidate_profile.interests) if candidate_profile.interests else 'Not specified'}

        TARGET ROLE:
        - Position: {role.title}
        - Industry: {', '.join([ind.value for ind in role.industry_categories[:2]])}
        - Required skills: {', '.join(role.required_skill_keywords[:8])}
        - Salary range: {role.median_salary_range or 'Market competitive'}

        FIT ANALYSIS:
        - Overall fit score: {ctp.fit_score:.2f}/1.0
        - Skill match: {ctp.skill_match_score:.2f}/1.0
        - Transition difficulty: {ctp.transition_difficulty.value}
        - Key strengths: {', '.join(ctp.existing_strengths[:5])}

        Provide a compelling, personalized explanation (150-200 words) of why this career transition
        makes strategic sense. Focus on:
        1. How their existing skills transfer
        2. Growth opportunities in this role
        3. Market demand and potential
        4. Personal fit with their interests

        Write in a professional but encouraging tone, as if advising the candidate directly.
        """

        system_prompt = """
        You are a senior career strategist providing personalized career transition analysis.
        Write clear, actionable insights that help professionals understand their career opportunities.
        Be specific about skill transferability and growth potential.
        """

        try:
            response = await self.llm_client.generate(
                prompt,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=300,
                provider_preference=[
                    "anthropic",
                    "openai",
                ],  # Prefer Anthropic for nuanced explanations
            )

            return response["content"]

        except LLMClientError as e:
            logger.error(f"Failed to generate detailed explanation: {e}")
            return ctp.explanation  # Fallback to original

    async def _generate_market_insights(self, role: JobRole) -> str:
        """Generate market insights for the target role."""

        prompt = f"""
        Provide current market insights for this role:

        ROLE: {role.title}
        INDUSTRIES: {', '.join([ind.value for ind in role.industry_categories])}
        REQUIRED SKILLS: {', '.join(role.required_skill_keywords[:10])}

        Provide market analysis (100-150 words) covering:
        1. Current demand trends for this role
        2. Key industries that are hiring
        3. Salary growth potential
        4. Emerging skills becoming important
        5. Remote work availability

        Focus on 2024-2025 market conditions and provide actionable insights.
        Be factual and data-driven where possible.
        """

        system_prompt = """
        You are a labor market analyst with expertise in tech and professional services.
        Provide current, realistic market insights based on general industry knowledge.
        Avoid speculation and focus on observable trends.
        """

        try:
            response = await self.llm_client.generate(
                prompt,
                system_prompt=system_prompt,
                temperature=0.3,  # Lower temperature for factual content
                max_tokens=250,
                provider_preference=[
                    "openai",
                    "anthropic",
                ],  # OpenAI might be better for market data
            )

            return response["content"]

        except LLMClientError as e:
            logger.error(f"Failed to generate market insights: {e}")
            return ""

    async def _generate_personalized_advice(
        self,
        ctp: CareerTargetProfile,
        candidate_profile: CandidateProfile,
        role: JobRole,
    ) -> list[str]:
        """Generate personalized recommendations for this career transition."""

        # Extract key skill gaps for context
        critical_gaps = [
            sg.skill_name for sg in ctp.skill_gaps if sg.priority.value == "CRITICAL"
        ]
        transition_time = ctp.estimated_transition_time

        prompt = f"""
        Provide personalized career transition advice for this professional:

        CURRENT SITUATION:
        - Skills: {', '.join(candidate_profile.skills[:8])}
        - Target role: {role.title}
        - Critical skill gaps: {', '.join(critical_gaps[:5]) if critical_gaps else 'None'}
        - Estimated transition time: {transition_time}
        - Transition difficulty: {ctp.transition_difficulty.value}

        Generate 4-6 specific, actionable recommendations that this person should prioritize.
        Focus on:
        1. Immediate skill development priorities
        2. Networking and industry connection strategies
        3. Portfolio/experience building opportunities
        4. Application and positioning strategies
        5. Timeline optimization tips

        Format as a simple list of actionable recommendations (each 10-15 words).
        Be specific and practical, not generic.
        """

        system_prompt = """
        You are a career coach providing specific, actionable advice for career transitions.
        Focus on practical steps the person can take in the next 1-3 months.
        Avoid generic advice and be specific to their situation.
        """

        try:
            response = await self.llm_client.generate(
                prompt,
                system_prompt=system_prompt,
                temperature=0.6,
                max_tokens=300,
                provider_preference=["anthropic", "openai"],
            )

            # Parse response into list format
            advice_text = response["content"]
            recommendations = []

            # Split by lines and clean up
            for line in advice_text.split("\n"):
                line = line.strip()
                # Remove list markers and clean up
                line = line.lstrip("123456789.-• ").strip()
                if line and len(line) > 10:  # Filter out empty or very short lines
                    recommendations.append(line)

            return recommendations[:6]  # Limit to 6 recommendations

        except LLMClientError as e:
            logger.error(f"Failed to generate personalized advice: {e}")
            return []

    async def generate_career_summary(
        self, request: CareerPathRequest, career_paths: list[CareerTargetProfile]
    ) -> str | None:
        """Generate an executive summary of all career recommendations."""

        if not self.llm_enabled or not career_paths:
            return None

        # Extract key information from top 3 paths
        top_paths = career_paths[:3]
        path_summaries = []

        for i, ctp in enumerate(top_paths, 1):
            path_summaries.append(
                f"{i}. {ctp.role.title} (fit: {ctp.fit_score:.2f}, "
                f"difficulty: {ctp.transition_difficulty.value})"
            )

        prompt = f"""
        Provide an executive summary for these career recommendations:

        CANDIDATE CONTEXT:
        - User requesting career guidance
        - {len(career_paths)} total recommendations generated
        - Looking for strategic career advancement

        TOP RECOMMENDATIONS:
        {chr(10).join(path_summaries)}

        Generate a brief executive summary (80-120 words) that:
        1. Highlights the strongest opportunities
        2. Notes the overall career trajectory theme
        3. Mentions key development areas across recommendations
        4. Provides encouraging, strategic perspective

        Write as if briefing the candidate on their career potential.
        Be professional but encouraging.
        """

        system_prompt = """
        You are an executive career advisor providing strategic career guidance.
        Synthesize multiple career options into clear, strategic insights.
        Focus on the big picture and career momentum.
        """

        try:
            response = await self.llm_client.generate(
                prompt, system_prompt=system_prompt, temperature=0.5, max_tokens=200
            )

            return response["content"]

        except LLMClientError as e:
            logger.error(f"Failed to generate career summary: {e}")
            return None

    def get_llm_status(self) -> dict[str, Any]:
        """Get status of LLM enhancement capabilities."""
        if not self.llm_enabled:
            return {"enabled": False, "reason": "LLM client not available"}

        if self.llm_client:
            status = self.llm_client.get_status()
            return {
                "enabled": True,
                "providers": list(status["providers"].keys()),
                "cache_enabled": status["cache"]["enabled"],
            }

        return {"enabled": False, "reason": "LLM client not initialized"}
