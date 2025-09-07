"""Market analysis engine with job matching and compensation analysis."""

import logging
import json
import time
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


logger = logging.getLogger(__name__)


class MarketAnalyzer:
    """Market analysis engine for job matching and compensation analysis."""

    def __init__(self):
        """Initialize market analyzer with data and models."""
        self.market_jobs: List[MarketJob] = []
        self.compensation_data: List[CompensationData] = []
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

        # Calculate similarity score
        if not job_skills_norm:
            similarity = 0.0
        else:
            similarity = len(matched_skills) / len(job_skills_norm)

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

        # Calculate statistics
        salaries = [comp.base_salary_usd for comp in relevant_comp]
        total_comps = [
            comp.total_comp_usd or comp.base_salary_usd for comp in relevant_comp
        ]

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

    def analyze_market(
        self, resume_deconstruction: ResumeDeconstruction
    ) -> MarketAnalysisResult:
        """Perform complete market analysis."""
        start_time = time.time()

        # Find job matches
        job_matches = self.find_job_matches(resume_deconstruction)

        # Perform analysis components
        compensation_analysis = self.analyze_compensation(job_matches)
        skill_demand_analysis = self.analyze_skill_demand(job_matches)
        location_analysis = self.analyze_locations(job_matches)

        # Generate market insights
        market_insights = {
            "total_job_matches": len(job_matches),
            "average_similarity_score": np.mean(
                [m.similarity_score for m in job_matches]
            )
            if job_matches
            else 0.0,
            "top_match_score": job_matches[0].similarity_score if job_matches else 0.0,
            "analysis_timestamp": time.time(),
        }

        # Generate recommendations
        analysis_components = {
            "skill_demand": skill_demand_analysis,
            "compensation": compensation_analysis,
            "location": location_analysis,
        }
        recommendations = self.generate_recommendations(analysis_components)

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
                "jobs_database_size": len(self.market_jobs),
                "compensation_records": len(self.compensation_data),
            },
        )
