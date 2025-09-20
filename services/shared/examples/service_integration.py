#!/usr/bin/env python3
"""
Service integration examples for the ResilientLLMClient.

This script shows how to integrate the LLM client into Helios services
like Strategist and Analyst, following best practices for production use.
"""

import asyncio
import logging
import os
from dataclasses import asdict, dataclass
from typing import Any

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Add parent directory to path for imports
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.shared.llm_client import ResilientLLMClient
from services.shared.llm_client.exceptions import LLMClientError


@dataclass
class CareerProfile:
    """Example career profile data structure."""

    name: str
    current_role: str
    experience_years: int
    skills: list[str]
    interests: list[str]
    goals: list[str]
    location: str
    education: str


@dataclass
class CareerPath:
    """Generated career path recommendation."""

    target_roles: list[str]
    skill_development: list[str]
    timeline: dict[str, str]
    salary_expectations: dict[str, str]
    recommended_actions: list[str]


class CareerStrategistLLMService:
    """
    Example Strategist service using ResilientLLMClient.

    This service generates career path recommendations based on
    user profiles using AI-powered analysis.
    """

    def __init__(self, llm_client: ResilientLLMClient | None = None):
        self.llm_client = llm_client or ResilientLLMClient()
        self.logger = logging.getLogger(self.__class__.__name__)

    async def generate_career_path(self, profile: CareerProfile) -> CareerPath:
        """
        Generate a comprehensive career path for the given profile.

        Args:
            profile: User's career profile

        Returns:
            CareerPath with recommendations

        Raises:
            LLMClientError: If generation fails
        """
        self.logger.info(f"Generating career path for {profile.name}")

        # Create structured prompt
        prompt = self._build_career_prompt(profile)
        system_prompt = self._get_strategist_system_prompt()

        try:
            response = await self.llm_client.generate(
                prompt,
                system_prompt=system_prompt,
                temperature=0.7,  # Balanced creativity and consistency
                max_tokens=2000,  # Comprehensive response
                # Prefer Anthropic for nuanced career advice
                provider_preference=["anthropic", "openai"],
            )

            self.logger.info(
                f"Generated career path using {response['provider']} "
                f"(cached: {response['cached']}, attempts: {response['attempts']})"
            )

            # Parse and structure the response
            career_path = self._parse_career_response(response["content"])
            return career_path

        except LLMClientError as e:
            self.logger.error(f"Failed to generate career path: {e}")
            raise

    def _build_career_prompt(self, profile: CareerProfile) -> str:
        """Build a structured prompt for career path generation."""
        return f"""
        Please analyze this professional's career profile and provide a comprehensive career development plan:

        PROFILE:
        - Name: {profile.name}
        - Current Role: {profile.current_role}
        - Experience: {profile.experience_years} years
        - Skills: {', '.join(profile.skills)}
        - Interests: {', '.join(profile.interests)}
        - Goals: {', '.join(profile.goals)}
        - Location: {profile.location}
        - Education: {profile.education}

        Please provide a structured analysis with:

        1. TARGET ROLES (3-5 specific roles they should consider)
        2. SKILL DEVELOPMENT (prioritized list of skills to develop)
        3. TIMELINE (12-month, 2-year, and 5-year milestones)
        4. SALARY EXPECTATIONS (ranges for target roles in their location)
        5. RECOMMENDED ACTIONS (specific steps they can take this month)

        Format your response as a structured analysis with clear sections.
        """

    def _get_strategist_system_prompt(self) -> str:
        """Get the system prompt for career strategist."""
        return """
        You are a senior career strategist with 20+ years of experience helping technology
        professionals advance their careers. You have deep knowledge of:
        - Industry trends and emerging roles
        - Skill requirements across tech domains
        - Salary benchmarks and market conditions
        - Professional development best practices

        Provide practical, actionable advice based on current market realities.
        Be specific with recommendations and timelines. Consider the individual's
        unique background and goals when making suggestions.
        """

    def _parse_career_response(self, content: str) -> CareerPath:
        """Parse LLM response into structured CareerPath."""
        # In a real implementation, you might use more sophisticated parsing
        # For this example, we'll create a simple structure

        return CareerPath(
            target_roles=[
                "Senior Software Engineer",
                "Tech Lead",
                "Engineering Manager",
            ],
            skill_development=["System Design", "Leadership", "Cloud Architecture"],
            timeline={
                "12_months": "Senior role transition",
                "24_months": "Technical leadership position",
                "60_months": "Engineering management role",
            },
            salary_expectations={
                "current_range": "$80K-$120K",
                "target_range": "$120K-$180K",
            },
            recommended_actions=[
                "Complete system design course",
                "Lead a cross-team project",
                "Start mentoring junior developers",
            ],
        )

    async def close(self):
        """Clean up resources."""
        await self.llm_client.close()


class MarketAnalyzerLLMService:
    """
    Example Analyst service using ResilientLLMClient.

    This service analyzes job markets and provides insights
    on demand, salary trends, and skill requirements.
    """

    def __init__(self, llm_client: ResilientLLMClient | None = None):
        self.llm_client = llm_client or ResilientLLMClient()
        self.logger = logging.getLogger(self.__class__.__name__)

    async def analyze_job_market(
        self, skills: list[str], location: str, experience_level: str = "mid"
    ) -> dict[str, Any]:
        """
        Analyze job market conditions for specific skills and location.

        Args:
            skills: List of relevant skills
            location: Geographic location
            experience_level: Experience level (junior, mid, senior)

        Returns:
            Market analysis dictionary
        """
        self.logger.info(f"Analyzing job market for {skills} in {location}")

        prompt = f"""
        Analyze the current job market for a {experience_level}-level professional with these skills:
        Skills: {', '.join(skills)}
        Location: {location}

        Please provide analysis on:

        1. MARKET DEMAND
        - How high is demand for these skills?
        - Which industries are hiring most?
        - Growth trends for next 2 years

        2. SALARY ANALYSIS
        - Current salary ranges for {experience_level} level
        - Salary growth potential
        - Comparison with national averages

        3. SKILL GAPS
        - What additional skills would increase marketability?
        - Which skills are becoming obsolete?
        - Emerging technologies to learn

        4. OPPORTUNITIES
        - Best companies to target
        - Alternative career paths
        - Remote work availability

        Provide specific, data-driven insights where possible.
        """

        system_prompt = """
        You are a labor market analyst with access to current job market data,
        salary surveys, and industry reports. Provide evidence-based analysis
        of employment trends, compensation, and skill demands. Be specific about
        numbers when possible and cite general market knowledge.
        """

        try:
            response = await self.llm_client.generate(
                prompt,
                system_prompt=system_prompt,
                temperature=0.3,  # Lower temperature for factual analysis
                max_tokens=1500,
                # OpenAI might be better for data-driven analysis
                provider_preference=["openai", "anthropic"],
            )

            self.logger.info(
                f"Generated market analysis using {response['provider']} "
                f"(cached: {response['cached']})"
            )

            return {
                "analysis": response["content"],
                "metadata": {
                    "model": response["model"],
                    "provider": response["provider"],
                    "cached": response["cached"],
                    "skills_analyzed": skills,
                    "location": location,
                    "experience_level": experience_level,
                },
            }

        except LLMClientError as e:
            self.logger.error(f"Failed to analyze job market: {e}")
            raise

    async def generate_resume_optimization(
        self, current_resume: str, target_job_description: str
    ) -> dict[str, Any]:
        """
        Generate resume optimization recommendations.

        Args:
            current_resume: Current resume text
            target_job_description: Target job posting

        Returns:
            Optimization recommendations
        """
        self.logger.info("Generating resume optimization recommendations")

        prompt = f"""
        Optimize this resume for the target job posting:

        CURRENT RESUME:
        {current_resume[:2000]}  # Limit length

        TARGET JOB DESCRIPTION:
        {target_job_description[:1000]}  # Limit length

        Please provide:

        1. KEYWORD OPTIMIZATION
        - Missing keywords from job description
        - Keywords to emphasize more
        - ATS-friendly formatting suggestions

        2. CONTENT IMPROVEMENTS
        - Skills to highlight
        - Experience to emphasize
        - Achievements to quantify better

        3. STRUCTURE RECOMMENDATIONS
        - Section reordering suggestions
        - Length optimization
        - Format improvements

        4. SPECIFIC EDITS
        - 3-5 specific text improvements
        - Better action verbs to use
        - Numbers/metrics to add

        Focus on maximizing ATS compatibility and human readability.
        """

        system_prompt = """
        You are an expert resume writer and ATS optimization specialist.
        You understand how Applicant Tracking Systems parse resumes and
        what hiring managers look for. Provide specific, actionable advice
        to improve resume effectiveness for the target role.
        """

        try:
            response = await self.llm_client.generate(
                prompt,
                system_prompt=system_prompt,
                temperature=0.4,
                max_tokens=1500,
                use_cache=False,  # Don't cache resume optimizations (privacy)
            )

            return {
                "recommendations": response["content"],
                "metadata": {
                    "model": response["model"],
                    "provider": response["provider"],
                    "resume_length": len(current_resume),
                    "job_desc_length": len(target_job_description),
                },
            }

        except LLMClientError as e:
            self.logger.error(f"Failed to generate resume optimization: {e}")
            raise

    async def close(self):
        """Clean up resources."""
        await self.llm_client.close()


class HeliosServiceOrchestrator:
    """
    Example orchestrator that coordinates multiple LLM-powered services.

    This demonstrates how to manage multiple services sharing an LLM client
    and implement graceful error handling and monitoring.
    """

    def __init__(self):
        self.llm_client = ResilientLLMClient()
        self.strategist = CareerStrategistLLMService(self.llm_client)
        self.analyzer = MarketAnalyzerLLMService(self.llm_client)
        self.logger = logging.getLogger(self.__class__.__name__)

    async def comprehensive_career_analysis(
        self, profile: CareerProfile
    ) -> dict[str, Any]:
        """
        Perform comprehensive career analysis using multiple services.

        Args:
            profile: User's career profile

        Returns:
            Complete analysis results
        """
        self.logger.info(f"Starting comprehensive analysis for {profile.name}")

        # Run analysis tasks concurrently
        tasks = [
            self.strategist.generate_career_path(profile),
            self.analyzer.analyze_job_market(
                profile.skills,
                profile.location,
                self._determine_experience_level(profile.experience_years),
            ),
        ]

        try:
            career_path, market_analysis = await asyncio.gather(*tasks)

            # Get client status for monitoring
            client_status = self.llm_client.get_status()

            return {
                "career_path": asdict(career_path),
                "market_analysis": market_analysis,
                "analysis_metadata": {
                    "timestamp": asyncio.get_event_loop().time(),
                    "profile_name": profile.name,
                    "llm_status": client_status,
                },
            }

        except Exception as e:
            self.logger.error(f"Comprehensive analysis failed: {e}")
            raise

    def _determine_experience_level(self, years: int) -> str:
        """Determine experience level from years of experience."""
        if years < 3:
            return "junior"
        elif years < 8:
            return "mid"
        else:
            return "senior"

    async def get_health_status(self) -> dict[str, Any]:
        """Get health status of all services and the LLM client."""
        try:
            # Test LLM client with a simple prompt
            test_response = await self.llm_client.generate(
                "Say 'OK' if you can respond",
                use_cache=False,  # Don't cache health checks
            )

            client_status = self.llm_client.get_status()

            return {
                "status": "healthy",
                "llm_client": {
                    "responsive": test_response is not None,
                    "providers": list(client_status["providers"].keys()),
                    "cache_enabled": client_status["cache"]["enabled"],
                },
                "services": {"strategist": "ready", "analyzer": "ready"},
            }

        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    async def close(self):
        """Clean up all resources."""
        await self.strategist.close()
        await self.analyzer.close()
        # Note: llm_client.close() will be called by strategist.close()
        # since they share the same client instance


async def demo_strategist_service():
    """Demonstrate the career strategist service."""
    print("\n=== Career Strategist Service Demo ===")

    # Create sample profile
    profile = CareerProfile(
        name="Alice Johnson",
        current_role="Software Developer",
        experience_years=4,
        skills=["Python", "JavaScript", "React", "PostgreSQL", "Docker"],
        interests=["Machine Learning", "Team Leadership", "Product Development"],
        goals=["Become a Tech Lead", "Learn System Design", "Increase Salary"],
        location="San Francisco, CA",
        education="BS Computer Science",
    )

    strategist = CareerStrategistLLMService()

    try:
        career_path = await strategist.generate_career_path(profile)

        print(f"Generated career path for {profile.name}:")
        print(f"Target Roles: {career_path.target_roles}")
        print(f"Skills to Develop: {career_path.skill_development}")
        print(f"Timeline: {career_path.timeline}")
        print(f"Salary Expectations: {career_path.salary_expectations}")
        print(f"Recommended Actions: {career_path.recommended_actions}")

    except Exception as e:
        print(f"Strategist demo failed: {e}")
    finally:
        await strategist.close()


async def demo_analyzer_service():
    """Demonstrate the market analyzer service."""
    print("\n=== Market Analyzer Service Demo ===")

    analyzer = MarketAnalyzerLLMService()

    try:
        # Job market analysis
        market_analysis = await analyzer.analyze_job_market(
            skills=["Python", "Machine Learning", "AWS"],
            location="Seattle, WA",
            experience_level="mid",
        )

        print("Market Analysis Results:")
        print(f"Analysis: {market_analysis['analysis'][:300]}...")
        print(f"Provider: {market_analysis['metadata']['provider']}")
        print(f"Cached: {market_analysis['metadata']['cached']}")

    except Exception as e:
        print(f"Analyzer demo failed: {e}")
    finally:
        await analyzer.close()


async def demo_orchestrator():
    """Demonstrate the service orchestrator."""
    print("\n=== Service Orchestrator Demo ===")

    profile = CareerProfile(
        name="Bob Smith",
        current_role="Frontend Developer",
        experience_years=6,
        skills=["React", "TypeScript", "Node.js", "GraphQL"],
        interests=["Full Stack", "Architecture", "Mentoring"],
        goals=["Become Full Stack", "Lead a Team", "Remote Work"],
        location="Austin, TX",
        education="Bootcamp Graduate",
    )

    orchestrator = HeliosServiceOrchestrator()

    try:
        # Health check
        health = await orchestrator.get_health_status()
        print(f"System Health: {health['status']}")

        if health["status"] == "healthy":
            # Comprehensive analysis
            analysis = await orchestrator.comprehensive_career_analysis(profile)

            print("\nComprehensive Analysis Complete:")
            print(
                f"Career Path Target Roles: {analysis['career_path']['target_roles']}"
            )
            print(
                f"Market Analysis Provider: {analysis['market_analysis']['metadata']['provider']}"
            )

            # Show LLM usage stats
            llm_status = analysis["analysis_metadata"]["llm_status"]
            print("\nLLM Usage:")
            for provider, stats in llm_status["providers"].items():
                cb_stats = stats["circuit_breaker"]
                print(
                    f"  {provider}: {cb_stats['state']} ({cb_stats['success_count']} successes)"
                )

    except Exception as e:
        print(f"Orchestrator demo failed: {e}")
    finally:
        await orchestrator.close()


async def main():
    """Run all service integration examples."""
    print("=== ResilientLLMClient Service Integration Examples ===")
    print("These examples show how to integrate the LLM client into Helios services.")
    print()

    # Run individual service demos
    await demo_strategist_service()
    await demo_analyzer_service()
    await demo_orchestrator()

    print("\n=== Integration Complete ===")
    print("Check the logs above for detailed information about LLM usage,")
    print("caching behavior, provider selection, and error handling.")


if __name__ == "__main__":
    asyncio.run(main())
