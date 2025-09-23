"""Market analysis engine with job matching and compensation analysis - 2025 Enhanced."""

import logging
import json
import time
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Tuple
from collections import Counter, defaultdict

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from src.models.market_data import (
    MarketJob,
    CompensationData,
    JobMatch,
    MarketAnalysisResult,
    RemotePolicy,
)
from src.models.ner_entities import ResumeDeconstruction, EntityType
from src.core.realtime_market_data import (
    get_realtime_market_analysis,
    RealTimeJob,
    RealTimeCompensation
)


logger = logging.getLogger(__name__)


class MarketAnalyzer:
    """Market analysis engine for job matching and compensation analysis - 2025 Enhanced."""

    def __init__(self, use_realtime_data: bool = True):
        """Initialize market analyzer with data and models."""
        self.market_jobs: List[MarketJob] = []
        self.compensation_data: List[CompensationData] = []
        self.realtime_jobs: List[RealTimeJob] = []
        self.realtime_compensation: List[RealTimeCompensation] = []

        self.use_realtime_data = use_realtime_data
        self.tfidf_vectorizer = TfidfVectorizer(
            stop_words="english", max_features=5000, ngram_range=(1, 2)
        )
        self.job_vectors = None
        self._load_market_data()

    def _load_market_data(self) -> None:
        """Load market jobs and compensation data."""
        try:
            # Load market jobs
            data_dir = Path(__file__).parent.parent / "data"

            with open(data_dir / "market_jobs_sample.json", "r") as f:
                jobs_data = json.load(f)
                self.market_jobs = [MarketJob(**job) for job in jobs_data]

            with open(data_dir / "compensation_sample.json", "r") as f:
                comp_data = json.load(f)
                self.compensation_data = [
                    CompensationData(**comp) for comp in comp_data
                ]

            # Prepare TF-IDF vectors for job descriptions
            job_texts = [job.full_description_text for job in self.market_jobs]
            if job_texts:
                self.job_vectors = self.tfidf_vectorizer.fit_transform(job_texts)

            logger.info(
                f"Loaded {len(self.market_jobs)} market jobs and {len(self.compensation_data)} compensation records"
            )

        except Exception as e:
            logger.error(f"Failed to load market data: {str(e)}")
            raise

    async def _fetch_realtime_market_data(
        self, candidate_skills: List[str], target_roles: List[str] = None, location: str = None
    ) -> None:
        """
        Fetch real-time market data from 2025 sources.
        Integrates LinkedIn Economic Graph, JobsPikr, and Levels.fyi data.
        """
        if not self.use_realtime_data:
            logger.info("Real-time data fetching disabled, using static data only")
            return

        try:
            logger.info("Fetching real-time market data from 2025 sources...")

            # Determine target roles if not provided
            if not target_roles:
                # Infer target roles from candidate skills
                target_roles = self._infer_target_roles_from_skills(candidate_skills)

            # Fetch comprehensive real-time data
            realtime_data = await get_realtime_market_analysis(
                candidate_skills=candidate_skills,
                target_roles=target_roles,
                location=location
            )

            # Convert real-time data to internal format
            self.realtime_jobs = [
                self._convert_realtime_job_to_market_job(job_data)
                for job_data in realtime_data.get("jobs", [])
            ]

            self.realtime_compensation = [
                self._convert_realtime_compensation(comp_data)
                for comp_data in realtime_data.get("compensation", [])
            ]

            # Store market trends for enhanced analysis
            self.market_trends_2025 = realtime_data.get("market_trends", {})

            logger.info(
                f"Fetched {len(self.realtime_jobs)} real-time jobs and "
                f"{len(self.realtime_compensation)} compensation records"
            )

        except Exception as e:
            logger.error(f"Failed to fetch real-time market data: {str(e)}")
            # Fallback to static data
            logger.warning("Falling back to static market data")

    def _infer_target_roles_from_skills(self, skills: List[str]) -> List[str]:
        """Infer likely target roles based on candidate skills."""
        skill_to_roles = {
            "python": ["Software Engineer", "Data Scientist", "ML Engineer"],
            "machine learning": ["ML Engineer", "Data Scientist", "AI Engineer"],
            "data science": ["Data Scientist", "Data Analyst", "AI Researcher"],
            "ai": ["AI Engineer", "ML Engineer", "AI Researcher"],
            "nlp": ["NLP Engineer", "AI Engineer", "Data Scientist"],
            "deep learning": ["Deep Learning Engineer", "AI Researcher", "ML Engineer"],
            "cloud": ["Cloud Engineer", "DevOps Engineer", "Software Engineer"],
            "aws": ["Cloud Engineer", "DevOps Engineer", "Software Engineer"],
            "docker": ["DevOps Engineer", "Software Engineer", "Platform Engineer"],
            "kubernetes": ["DevOps Engineer", "Platform Engineer", "Site Reliability Engineer"]
        }

        target_roles = set()
        for skill in skills:
            skill_lower = skill.lower()
            for keyword, roles in skill_to_roles.items():
                if keyword in skill_lower:
                    target_roles.update(roles)

        return list(target_roles)[:5]  # Limit to top 5 inferred roles

    def _convert_realtime_job_to_market_job(self, job_data: Dict[str, Any]) -> MarketJob:
        """Convert real-time job data to MarketJob format."""
        return MarketJob(
            job_id=job_data.get("job_id", ""),
            role_title=job_data.get("title", ""),
            company=job_data.get("company", ""),
            location=job_data.get("location", ""),
            full_description_text=job_data.get("description", ""),
            required_skills=job_data.get("required_skills", []),
            preferred_skills=job_data.get("preferred_skills", []),
            remote_policy=RemotePolicy(job_data.get("remote_policy", "unknown")),
            salary_range_min=job_data.get("salary_min"),
            salary_range_max=job_data.get("salary_max"),
            source_url=job_data.get("url", ""),
            posting_date=job_data.get("posted_date", ""),
            seniority_level=job_data.get("seniority_level", "mid")
        )

    def _convert_realtime_compensation(self, comp_data: Dict[str, Any]) -> CompensationData:
        """Convert real-time compensation data to CompensationData format."""
        return CompensationData(
            role_title=comp_data.get("role_title", ""),
            level=comp_data.get("level", ""),
            location=comp_data.get("location", ""),
            base_salary_usd=comp_data.get("base_salary", 0),
            total_comp_usd=comp_data.get("total_compensation", 0),
            years_experience=comp_data.get("years_experience", 0),
            company=comp_data.get("company", ""),
            data_source=comp_data.get("source", "realtime")
        )

    def extract_candidate_skills(
        self, resume_deconstruction: ResumeDeconstruction
    ) -> List[str]:
        """Extract candidate skills from resume deconstruction."""
        skills = []

        for section in resume_deconstruction.sections:
            for entity in section.entities:
                if entity.label in [EntityType.SKILL, EntityType.TOOL]:
                    skills.append(entity.text)

        # Deduplicate and normalize
        skills = list(set([skill.lower().strip() for skill in skills]))
        return skills

    def calculate_job_similarity(
        self, candidate_skills: List[str], job: MarketJob
    ) -> Tuple[float, List[str], List[str]]:
        """Calculate similarity between candidate skills and job requirements."""
        if not candidate_skills:
            return 0.0, [], job.required_skills

        # Normalize skills for comparison
        candidate_skills_norm = [skill.lower().strip() for skill in candidate_skills]
        job_skills_norm = [
            skill.lower().strip()
            for skill in job.required_skills + job.preferred_skills
        ]

        # Find matches
        matched_skills = []
        for candidate_skill in candidate_skills_norm:
            for job_skill in job_skills_norm:
                if candidate_skill in job_skill or job_skill in candidate_skill:
                    matched_skills.append(job_skill)

        matched_skills = list(set(matched_skills))
        missing_skills = [
            skill
            for skill in job.required_skills
            if skill.lower() not in [m.lower() for m in matched_skills]
        ]

        # Calculate similarity score with NaN protection
        if not job_skills_norm or len(job_skills_norm) == 0:
            similarity = 0.0
        else:
            similarity = len(matched_skills) / len(job_skills_norm)

        # Handle potential NaN
        if not (similarity == similarity):  # NaN check
            similarity = 0.0

        # Ensure similarity is between 0 and 1
        similarity = max(0.0, min(1.0, similarity))

        return similarity, matched_skills, missing_skills

    def find_job_matches(
        self, resume_deconstruction: ResumeDeconstruction, top_k: int = 10
    ) -> List[JobMatch]:
        """Find top job matches for candidate."""
        candidate_skills = self.extract_candidate_skills(resume_deconstruction)

        job_matches = []
        for job in self.market_jobs:
            similarity_score, matched_skills, missing_skills = (
                self.calculate_job_similarity(candidate_skills, job)
            )

            match_details = {
                "skill_match_ratio": similarity_score,
                "total_candidate_skills": len(candidate_skills),
                "total_job_skills": len(job.required_skills + job.preferred_skills),
                "matched_count": len(matched_skills),
                "missing_count": len(missing_skills),
            }

            job_matches.append(
                JobMatch(
                    job=job,
                    similarity_score=similarity_score,
                    matched_skills=matched_skills,
                    missing_skills=missing_skills,
                    match_details=match_details,
                )
            )

        # Sort by similarity score and return top matches
        job_matches = sorted(
            job_matches, key=lambda x: x.similarity_score, reverse=True
        )
        return job_matches[:top_k]

    def analyze_compensation(self, matched_jobs: List[JobMatch]) -> Dict[str, Any]:
        """Analyze compensation data for matched roles."""
        if not matched_jobs:
            return {"error": "No job matches for compensation analysis"}

        # Extract role titles from matches
        matched_roles = [match.job.role_title.lower() for match in matched_jobs]

        # Find relevant compensation data
        relevant_comp = []
        for comp in self.compensation_data:
            if any(role in comp.role_title.lower() for role in matched_roles):
                relevant_comp.append(comp)

        if not relevant_comp:
            return {"message": "No compensation data found for matched roles"}

        # Calculate statistics with error handling
        salaries = [comp.base_salary_usd for comp in relevant_comp if comp.base_salary_usd and comp.base_salary_usd > 0]
        total_comps = [
            (comp.total_comp_usd or comp.base_salary_usd) for comp in relevant_comp
            if (comp.total_comp_usd or comp.base_salary_usd) and (comp.total_comp_usd or comp.base_salary_usd) > 0
        ]

        # Ensure we have valid data
        if not salaries:
            return {"error": "No valid salary data found for matched roles"}
        if not total_comps:
            total_comps = salaries

        # Group by level
        level_analysis = defaultdict(list)
        for comp in relevant_comp:
            level_analysis[comp.level].append(
                comp.total_comp_usd or comp.base_salary_usd
            )

        level_stats = {}
        for level, comps in level_analysis.items():
            level_stats[level] = {
                "count": len(comps),
                "min": min(comps),
                "max": max(comps),
                "median": np.median(comps),
                "mean": np.mean(comps),
            }

        return {
            "total_records": len(relevant_comp),
            "base_salary_stats": {
                "min": min(salaries),
                "max": max(salaries),
                "median": int(np.median(salaries)),
                "mean": int(np.mean(salaries)),
            },
            "total_compensation_stats": {
                "min": min(total_comps),
                "max": max(total_comps),
                "median": int(np.median(total_comps)),
                "mean": int(np.mean(total_comps)),
            },
            "by_level": level_stats,
            "sample_data": [
                {
                    "role": comp.role_title,
                    "level": comp.level,
                    "location": comp.location,
                    "total_comp": comp.total_comp_usd or comp.base_salary_usd,
                }
                for comp in relevant_comp[:5]
            ],
        }

    def analyze_skill_demand(self, matched_jobs: List[JobMatch]) -> Dict[str, Any]:
        """Analyze skill demand from matched jobs."""
        if not matched_jobs:
            return {"error": "No job matches for skill analysis"}

        # Count skill occurrences
        skill_counts = Counter()
        total_jobs = len(matched_jobs)

        for match in matched_jobs:
            job = match.job
            all_skills = job.required_skills + job.preferred_skills
            for skill in all_skills:
                skill_counts[skill.lower()] += 1

        # Calculate demand percentages
        skill_demand = [
            {
                "skill": skill,
                "count": count,
                "demand_percentage": (count / total_jobs) * 100,
            }
            for skill, count in skill_counts.most_common(20)
        ]

        return {
            "total_jobs_analyzed": total_jobs,
            "unique_skills": len(skill_counts),
            "top_skills": skill_demand,
            "high_demand_skills": [
                s["skill"] for s in skill_demand if s["demand_percentage"] > 50
            ],
        }

    def analyze_locations(self, matched_jobs: List[JobMatch]) -> Dict[str, Any]:
        """Analyze geographic distribution of opportunities."""
        if not matched_jobs:
            return {"error": "No job matches for location analysis"}

        # Count locations and remote policies
        location_counts = Counter()
        remote_counts = Counter()

        for match in matched_jobs:
            job = match.job
            location_counts[job.location] += 1
            remote_counts[job.remote_policy] += 1

        return {
            "top_locations": [
                {
                    "location": loc,
                    "count": count,
                    "percentage": (count / len(matched_jobs)) * 100,
                }
                for loc, count in location_counts.most_common(10)
            ],
            "remote_policies": [
                {
                    "policy": policy,
                    "count": count,
                    "percentage": (count / len(matched_jobs)) * 100,
                }
                for policy, count in remote_counts.most_common()
            ],
            "remote_opportunities": location_counts.get("Remote", 0)
            + sum(
                1
                for match in matched_jobs
                if match.job.remote_policy == RemotePolicy.REMOTE
            ),
        }

    def generate_recommendations(
        self, analysis_components: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable recommendations based on analysis."""
        recommendations = []

        # Skill-based recommendations
        if "skill_demand" in analysis_components:
            skill_data = analysis_components["skill_demand"]
            if "high_demand_skills" in skill_data and skill_data["high_demand_skills"]:
                top_skills = skill_data["high_demand_skills"][:3]
                recommendations.append(
                    f"Focus on developing these high-demand skills: {', '.join(top_skills)}"
                )

        # Compensation recommendations
        if "compensation" in analysis_components:
            comp_data = analysis_components["compensation"]
            if "total_compensation_stats" in comp_data:
                median_comp = comp_data["total_compensation_stats"]["median"]
                recommendations.append(
                    f"Market median compensation for similar roles is ${median_comp:,}"
                )

        # Location recommendations
        if "location" in analysis_components:
            loc_data = analysis_components["location"]
            if (
                "remote_opportunities" in loc_data
                and loc_data["remote_opportunities"] > 0
            ):
                recommendations.append(
                    f"Consider remote opportunities - {loc_data['remote_opportunities']} remote positions found"
                )

        return recommendations

    async def analyze_market(
        self, resume_deconstruction: ResumeDeconstruction, location: str = None
    ) -> MarketAnalysisResult:
        """Perform complete market analysis with 2025 real-time data."""
        start_time = time.time()

        # Extract candidate skills
        candidate_skills = self.extract_candidate_skills(resume_deconstruction)

        # Fetch real-time market data first
        if self.use_realtime_data:
            await self._fetch_realtime_market_data(
                candidate_skills=candidate_skills, location=location
            )

        # Combine static and real-time jobs for analysis
        all_jobs = self.market_jobs + self.realtime_jobs
        all_compensation = self.compensation_data + self.realtime_compensation

        # Update internal data for analysis methods
        original_market_jobs = self.market_jobs
        original_compensation_data = self.compensation_data

        try:
            # Temporarily update data for analysis
            self.market_jobs = all_jobs
            self.compensation_data = all_compensation

            # Find job matches
            job_matches = self.find_job_matches(resume_deconstruction)

            # Perform analysis components
            compensation_analysis = self.analyze_compensation(job_matches)
            skill_demand_analysis = self.analyze_skill_demand(job_matches)
            location_analysis = self.analyze_locations(job_matches)

            # Enhanced market insights with 2025 data
            market_insights = {
                "total_job_matches": len(job_matches),
                "average_similarity_score": np.mean(
                    [m.similarity_score for m in job_matches]
                )
                if job_matches
                else 0.0,
                "top_match_score": job_matches[0].similarity_score if job_matches else 0.0,
                "analysis_timestamp": time.time(),
                "realtime_data_included": self.use_realtime_data,
                "static_jobs": len(original_market_jobs),
                "realtime_jobs": len(self.realtime_jobs),
                "static_compensation": len(original_compensation_data),
                "realtime_compensation": len(self.realtime_compensation),
            }

            # Add 2025 market trends if available
            if hasattr(self, "market_trends_2025"):
                market_insights["market_trends_2025"] = self.market_trends_2025

            # Generate enhanced recommendations
            analysis_components = {
                "skill_demand": skill_demand_analysis,
                "compensation": compensation_analysis,
                "location": location_analysis,
            }
            recommendations = self.generate_recommendations(analysis_components)

            # Add 2025-specific recommendations
            recommendations.extend(self._generate_2025_recommendations(candidate_skills))

            processing_time = time.time() - start_time

            return MarketAnalysisResult(
                job_matches=job_matches,
                market_insights=market_insights,
                compensation_analysis=compensation_analysis,
                skill_demand_analysis=skill_demand_analysis,
                location_analysis=location_analysis,
                recommendations=recommendations,
                processing_metadata={
                    "processing_time_seconds": processing_time,
                    "jobs_database_size": len(all_jobs),
                    "compensation_records": len(all_compensation),
                    "data_sources": ["static", "realtime"] if self.use_realtime_data else ["static"],
                    "analysis_enhanced_2025": True,
                },
            )

        finally:
            # Restore original data
            self.market_jobs = original_market_jobs
            self.compensation_data = original_compensation_data

    def _generate_2025_recommendations(self, candidate_skills: List[str]) -> List[str]:
        """Generate 2025-specific market recommendations."""
        recommendations = []

        # Check for trending skills from 2025 market data
        if hasattr(self, "market_trends_2025"):
            trending_skills = self.market_trends_2025.get("trending_skills", [])
            candidate_skills_lower = [skill.lower() for skill in candidate_skills]

            # Identify missing trending skills
            missing_trending = []
            for trend in trending_skills[:5]:  # Top 5 trending skills
                skill_name = trend.get("skill", "").lower()
                if not any(skill_name in cs for cs in candidate_skills_lower):
                    missing_trending.append(trend)

            if missing_trending:
                top_missing = missing_trending[0]
                recommendations.append(
                    f"Consider developing {top_missing.get('skill')} skills - "
                    f"trending with {top_missing.get('growth')} growth in 2025"
                )

            # Salary trend recommendations
            salary_trends = self.market_trends_2025.get("salary_trends", {})
            ai_premium = salary_trends.get("ai_premium", 0)
            if ai_premium > 10:  # Significant AI premium
                recommendations.append(
                    f"AI/ML skills command a {ai_premium}% salary premium in 2025 - "
                    "consider highlighting AI-related experience"
                )

            # Remote work recommendations
            remote_growth = salary_trends.get("remote_availability", 0)
            if remote_growth > 50:
                recommendations.append(
                    f"Remote opportunities available in {remote_growth}% of roles - "
                    "consider expanding geographic search"
                )

        return recommendations
