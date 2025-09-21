"""Career path generation engine that combines all components to generate CTPs."""

import logging
import time
import uuid
from typing import List, Dict, Any, Optional, Tuple

from ..models.career_path import (
    CareerTargetProfile, CareerPathRequest, CareerPathResponse,
    SkillGap, SkillGapPriority, TransitionStep, TransitionDifficulty,
    GenerationStats
)
from ..models.skill_vector import CandidateProfile
from ..models.role_taxonomy import JobRole
from ..core.skill_vectorizer import SkillVectorizer
from ..core.role_taxonomy_manager import RoleTaxonomyManager
from ..core.fit_scorer import FitScorer, AspirationProfile, FitScoreDetails
from ..core.config import StrategistConfig

logger = logging.getLogger(__name__)


class CareerGenerator:
    """Main career path generation engine."""

    def __init__(self, config: Optional[StrategistConfig] = None):
        """Initialize career generator with all required components."""
        self.config = config or StrategistConfig()

        # Initialize components with Redis support
        self.vectorizer = SkillVectorizer(
            model_name=self.config.embedding_model,
            enable_redis=self.config.redis_enabled
        )
        self.taxonomy_manager = RoleTaxonomyManager()
        self.fit_scorer = FitScorer(self.config)

        # Cache for role vectors to avoid recomputation
        self._role_vectors_cache: Dict[str, List[float]] = {}
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize all components asynchronously."""
        start_time = time.time()
        logger.info("Initializing CareerGenerator components...")

        try:
            # Initialize skill vectorizer (loads embedding model)
            await self.vectorizer.initialize()

            # Load role taxonomy database
            await self.taxonomy_manager.load_taxonomy()

            # Pre-generate role vectors for better performance
            logger.info("Pre-generating role vectors...")

            # Check if we have Redis cache available
            if self.vectorizer.cache_manager and self.vectorizer.cache_manager.redis_cache:
                # Try to load from Redis first
                all_role_ids = list(self.taxonomy_manager.roles.keys())
                cached_vectors = await self.vectorizer.cache_manager.redis_cache.get_role_vectors(all_role_ids)

                if cached_vectors:
                    logger.info(f"Loaded {len(cached_vectors)} role vectors from Redis cache")
                    self._role_vectors_cache = {k: v.tolist() for k, v in cached_vectors.items()}

                # Generate missing vectors
                missing_roles = set(all_role_ids) - set(cached_vectors.keys())
                if missing_roles:
                    logger.info(f"Generating {len(missing_roles)} missing role vectors...")
                    new_vectors = await self.taxonomy_manager.generate_role_vectors(self.vectorizer)

                    # Update cache with all vectors
                    self._role_vectors_cache.update(new_vectors)

                    # Store in Redis for next time
                    vectors_to_cache = {k: np.array(v) for k, v in new_vectors.items()}
                    await self.vectorizer.cache_manager.redis_cache.set_role_vectors(vectors_to_cache)
            else:
                # No Redis, generate all vectors
                self._role_vectors_cache = await self.taxonomy_manager.generate_role_vectors(
                    self.vectorizer
                )

            self._initialized = True

            init_time = (time.time() - start_time) * 1000
            logger.info(f"CareerGenerator initialization complete in {init_time:.2f}ms")

        except Exception as e:
            logger.error(f"Failed to initialize CareerGenerator: {e}")
            raise

    async def generate_career_paths(self, request: CareerPathRequest) -> CareerPathResponse:
        """Generate career target profiles for a user."""
        if not self._initialized:
            raise RuntimeError("CareerGenerator not initialized. Call initialize() first.")

        start_time = time.time()
        logger.info(f"Generating career paths for user {request.user_id}")

        try:
            # 1. Generate candidate profile vector
            candidate_profile = await self.vectorizer.generate_candidate_vector(
                request.master_career_database
            )

            # 2. Extract aspiration profile
            aspiration_profile = self.fit_scorer.extract_aspiration_profile(
                request.master_career_database
            )

            # 3. Get all available roles
            all_roles = self.taxonomy_manager.get_all_roles()

            # 4. Calculate fit scores for all roles
            role_scores = []
            for role in all_roles:
                if role.role_id in self._role_vectors_cache:
                    role_vector = self._role_vectors_cache[role.role_id]
                    fit_details = self.fit_scorer.calculate_fit_score(
                        candidate_profile, role, role_vector, aspiration_profile
                    )
                    role_scores.append((role, fit_details))

            # 5. Filter and rank roles
            filtered_scores = self._filter_roles(role_scores, request)
            top_roles = self._rank_roles(filtered_scores, request.max_recommendations)

            # 6. Generate detailed CTPs for top roles
            career_target_profiles = []
            for role, fit_details in top_roles:
                ctp = await self._generate_career_target_profile(
                    request, candidate_profile, role, fit_details, aspiration_profile
                )
                career_target_profiles.append(ctp)

            # 7. Generate response with statistics
            processing_time = (time.time() - start_time) * 1000

            generation_summary = {
                "total_roles_analyzed": len(all_roles),
                "roles_above_threshold": len(filtered_scores),
                "recommendations_generated": len(career_target_profiles),
                "avg_fit_score": sum(ctp.fit_score for ctp in career_target_profiles) / len(career_target_profiles) if career_target_profiles else 0,
                "processing_time_ms": processing_time
            }

            logger.info(f"Generated {len(career_target_profiles)} career recommendations in {processing_time:.2f}ms")

            return CareerPathResponse(
                user_id=request.user_id,
                career_target_profiles=career_target_profiles,
                generation_summary=generation_summary,
                processing_time_ms=processing_time
            )

        except Exception as e:
            logger.error(f"Error generating career paths for user {request.user_id}: {e}")
            raise

    def _filter_roles(self, role_scores: List[Tuple[JobRole, FitScoreDetails]],
                     request: CareerPathRequest) -> List[Tuple[JobRole, FitScoreDetails]]:
        """Filter roles based on fit score threshold and request criteria."""
        filtered = []

        # Minimum fit score threshold for recommendations
        min_fit_score = 0.3  # Don't recommend very poor fits

        for role, fit_details in role_scores:
            # Basic fit score filter
            if fit_details.weighted_fit_score < min_fit_score:
                continue

            # Industry preferences filter
            if request.preferred_industries:
                role_industries = [ind.value for ind in role.industry_categories]
                if not any(pref in role_industries for pref in request.preferred_industries):
                    continue

            # Salary requirements filter
            if request.salary_requirements and role.median_salary_range:
                role_min = role.median_salary_range.get("min", 0)
                role_max = role.median_salary_range.get("max", float('inf'))
                req_min = request.salary_requirements.get("min", 0)
                req_max = request.salary_requirements.get("max", float('inf'))

                # Check for salary range overlap
                if role_max < req_min or role_min > req_max:
                    continue

            # Transition difficulty filter (if user doesn't want challenging transitions)
            if not request.include_challenging_transitions:
                # Calculate basic transition difficulty
                skill_match = fit_details.skill_match_score
                if skill_match < 0.4:  # Very challenging transition
                    continue

            filtered.append((role, fit_details))

        logger.debug(f"Filtered {len(filtered)} roles from {len(role_scores)} total")
        return filtered

    def _rank_roles(self, role_scores: List[Tuple[JobRole, FitScoreDetails]],
                   max_recommendations: int) -> List[Tuple[JobRole, FitScoreDetails]]:
        """Rank and select top N roles for detailed CTP generation."""

        # Sort by weighted fit score (descending)
        sorted_roles = sorted(
            role_scores,
            key=lambda x: x[1].weighted_fit_score,
            reverse=True
        )

        # Apply diversity to avoid too many similar roles
        diverse_roles = self._apply_diversity_filter(sorted_roles, max_recommendations)

        return diverse_roles[:max_recommendations]

    def _apply_diversity_filter(self, sorted_roles: List[Tuple[JobRole, FitScoreDetails]],
                              max_recommendations: int) -> List[Tuple[JobRole, FitScoreDetails]]:
        """Apply diversity filter to avoid too many similar roles."""
        if len(sorted_roles) <= max_recommendations:
            return sorted_roles

        diverse_roles = []
        seen_titles = set()
        seen_industries = {}

        for role, fit_details in sorted_roles:
            # Skip if we already have a very similar role title
            normalized_title = role.title.lower().replace(" ", "")
            if normalized_title in seen_titles:
                continue

            # Limit roles per industry to ensure diversity
            primary_industry = role.industry_categories[0] if role.industry_categories else "Other"
            industry_count = seen_industries.get(primary_industry, 0)

            # Allow max 2 roles per industry for small recommendation sets
            max_per_industry = max(1, max_recommendations // 2)
            if industry_count >= max_per_industry:
                continue

            diverse_roles.append((role, fit_details))
            seen_titles.add(normalized_title)
            seen_industries[primary_industry] = industry_count + 1

            if len(diverse_roles) >= max_recommendations:
                break

        # If we don't have enough diverse roles, fill with remaining high-scoring roles
        if len(diverse_roles) < max_recommendations:
            for role, fit_details in sorted_roles:
                if (role, fit_details) not in diverse_roles:
                    diverse_roles.append((role, fit_details))
                    if len(diverse_roles) >= max_recommendations:
                        break

        return diverse_roles

    async def _generate_career_target_profile(self, request: CareerPathRequest,
                                            candidate_profile: CandidateProfile,
                                            role: JobRole, fit_details: FitScoreDetails,
                                            aspiration_profile: AspirationProfile) -> CareerTargetProfile:
        """Generate detailed Career Target Profile for a specific role."""

        # Generate skill gap analysis
        skill_gaps = self._analyze_skill_gaps(candidate_profile, role)

        # Determine transition difficulty
        transition_difficulty = self._assess_transition_difficulty(fit_details, skill_gaps)

        # Generate transition roadmap
        transition_roadmap = self._generate_transition_roadmap(
            candidate_profile, role, skill_gaps, transition_difficulty
        )

        # Calculate existing strengths
        existing_strengths = self._identify_existing_strengths(candidate_profile, role)

        # Generate insights and recommendations
        key_selling_points = self._generate_selling_points(candidate_profile, role, fit_details)
        potential_challenges = self._identify_challenges(skill_gaps, transition_difficulty)
        next_steps = self._generate_next_steps(skill_gaps, transition_roadmap)

        return CareerTargetProfile(
            ctp_id=f"ctp_{uuid.uuid4().hex[:8]}",
            user_id=request.user_id,
            role=role,

            # Fit scores
            fit_score=fit_details.weighted_fit_score,
            skill_match_score=fit_details.skill_match_score,
            aspiration_score=fit_details.aspiration_alignment_score,
            confidence_level=self._calculate_confidence_level(fit_details, skill_gaps),

            # Skill analysis
            skill_gaps=skill_gaps,
            existing_strengths=existing_strengths,
            skill_overlap_percentage=fit_details.skill_overlap_count / max(1, len(candidate_profile.skills)),

            # Transition analysis
            transition_difficulty=transition_difficulty,
            transition_roadmap=transition_roadmap,
            estimated_transition_time=self._estimate_transition_time(skill_gaps, transition_difficulty),

            # Insights
            explanation=fit_details.explanation,
            key_selling_points=key_selling_points,
            potential_challenges=potential_challenges,
            next_steps=next_steps,

            # Metadata
            generation_timestamp=time.time()
        )

    def _analyze_skill_gaps(self, candidate_profile: CandidateProfile,
                           role: JobRole) -> List[SkillGap]:
        """Analyze skill gaps between candidate and role requirements."""
        skill_gaps = []

        candidate_skills_lower = set([skill.lower() for skill in candidate_profile.skills])

        # Analyze required skills
        for required_skill in role.required_skill_keywords:
            if required_skill.lower() not in candidate_skills_lower:
                skill_gap = SkillGap(
                    skill_name=required_skill,
                    gap_description=f"Required skill not present in candidate profile",
                    priority=SkillGapPriority.CRITICAL,
                    estimated_learning_time=self._estimate_learning_time(required_skill),
                    target_level="Proficient",
                    learning_resources=self._suggest_learning_resources(required_skill)
                )
                skill_gaps.append(skill_gap)

        # Analyze preferred skills (lower priority)
        for preferred_skill in role.preferred_skill_keywords:
            if preferred_skill.lower() not in candidate_skills_lower:
                # Only add if not already a required skill gap
                if not any(sg.skill_name.lower() == preferred_skill.lower() for sg in skill_gaps):
                    skill_gap = SkillGap(
                        skill_name=preferred_skill,
                        gap_description=f"Preferred skill that would strengthen candidacy",
                        priority=SkillGapPriority.MEDIUM,
                        estimated_learning_time=self._estimate_learning_time(preferred_skill),
                        target_level="Familiar",
                        learning_resources=self._suggest_learning_resources(preferred_skill)
                    )
                    skill_gaps.append(skill_gap)

        return skill_gaps

    def _estimate_learning_time(self, skill: str) -> str:
        """Estimate learning time for a skill based on complexity."""
        skill_lower = skill.lower()

        # Programming languages and frameworks
        if any(tech in skill_lower for tech in ["python", "java", "javascript", "react", "node"]):
            return "2-4 months"

        # Data science and ML
        if any(ds in skill_lower for ds in ["machine learning", "data science", "tensorflow", "pytorch"]):
            return "3-6 months"

        # Tools and software
        if any(tool in skill_lower for tool in ["excel", "sql", "git", "docker"]):
            return "2-6 weeks"

        # Management and soft skills
        if any(soft in skill_lower for soft in ["leadership", "management", "communication"]):
            return "6-12 months (ongoing development)"

        # Default estimate
        return "1-3 months"

    def _suggest_learning_resources(self, skill: str) -> List[str]:
        """Suggest learning resources for a skill."""
        skill_lower = skill.lower()

        resources = ["Online courses (Coursera, Udemy)", "Official documentation"]

        # Add specific resources based on skill type
        if "python" in skill_lower:
            resources.extend(["Python.org tutorials", "Real Python", "Automate the Boring Stuff"])
        elif any(ds in skill_lower for ds in ["machine learning", "data science"]):
            resources.extend(["Kaggle Learn", "Fast.ai courses", "Andrew Ng's ML Course"])
        elif "sql" in skill_lower:
            resources.extend(["SQLBolt", "W3Schools SQL", "Mode Analytics SQL Tutorial"])
        elif any(mgmt in skill_lower for mgmt in ["management", "leadership"]):
            resources.extend(["Harvard Business Review", "Management books", "Leadership workshops"])

        return resources

    def _assess_transition_difficulty(self, fit_details: FitScoreDetails,
                                    skill_gaps: List[SkillGap]) -> TransitionDifficulty:
        """Assess overall transition difficulty."""

        # Count critical skill gaps
        critical_gaps = len([sg for sg in skill_gaps if sg.priority == SkillGapPriority.CRITICAL])

        # Consider skill match score
        skill_match = fit_details.skill_match_score

        if skill_match >= 0.7 and critical_gaps <= 2:
            return TransitionDifficulty.EASY
        elif skill_match >= 0.5 and critical_gaps <= 4:
            return TransitionDifficulty.MODERATE
        elif skill_match >= 0.3 and critical_gaps <= 6:
            return TransitionDifficulty.CHALLENGING
        else:
            return TransitionDifficulty.VERY_CHALLENGING

    def _generate_transition_roadmap(self, candidate_profile: CandidateProfile,
                                   role: JobRole, skill_gaps: List[SkillGap],
                                   difficulty: TransitionDifficulty) -> List[TransitionStep]:
        """Generate step-by-step transition roadmap."""
        steps = []

        # Step 1: Assess and plan
        steps.append(TransitionStep(
            step_number=1,
            title="Skills Assessment & Career Planning",
            description="Complete detailed skills assessment and create learning plan",
            estimated_duration="1-2 weeks",
            success_metrics=["Completed skills inventory", "Created learning timeline"],
            resources=["Career assessment tools", "Industry career guides"]
        ))

        # Step 2: Address critical skill gaps
        critical_gaps = [sg for sg in skill_gaps if sg.priority == SkillGapPriority.CRITICAL]
        if critical_gaps:
            critical_skills = [sg.skill_name for sg in critical_gaps[:3]]  # Top 3
            steps.append(TransitionStep(
                step_number=2,
                title="Develop Critical Skills",
                description=f"Focus on developing: {', '.join(critical_skills)}",
                estimated_duration="3-6 months",
                prerequisites=["Learning plan from Step 1"],
                success_metrics=[f"Proficiency in {skill}" for skill in critical_skills],
                resources=["Online courses", "Practice projects", "Mentorship"]
            ))

        # Step 3: Build portfolio/experience
        steps.append(TransitionStep(
            step_number=len(steps) + 1,
            title="Build Relevant Experience",
            description="Create portfolio projects and gain practical experience",
            estimated_duration="2-4 months",
            prerequisites=["Core skills from previous steps"],
            success_metrics=["2-3 relevant projects", "Updated portfolio/resume"],
            resources=["Personal projects", "Open source contributions", "Freelance work"]
        ))

        # Step 4: Network and apply
        steps.append(TransitionStep(
            step_number=len(steps) + 1,
            title="Network & Job Search",
            description="Build professional network and start targeted job search",
            estimated_duration="1-3 months",
            prerequisites=["Strong portfolio and skills foundation"],
            success_metrics=["Active professional network", "Targeted applications"],
            resources=["LinkedIn", "Industry events", "Professional associations"]
        ))

        return steps

    def _identify_existing_strengths(self, candidate_profile: CandidateProfile,
                                   role: JobRole) -> List[str]:
        """Identify candidate's existing strengths relevant to the role."""
        strengths = []

        candidate_skills_lower = set([skill.lower() for skill in candidate_profile.skills])
        role_skills_lower = set([skill.lower() for skill in role.required_skill_keywords + role.preferred_skill_keywords])

        # Find overlapping skills
        overlapping_skills = candidate_skills_lower.intersection(role_skills_lower)

        # Convert back to original case
        for candidate_skill in candidate_profile.skills:
            if candidate_skill.lower() in overlapping_skills:
                strengths.append(candidate_skill)

        return strengths

    def _generate_selling_points(self, candidate_profile: CandidateProfile,
                               role: JobRole, fit_details: FitScoreDetails) -> List[str]:
        """Generate key selling points for this career transition."""
        selling_points = []

        # Skill alignment points
        if fit_details.skill_match_score >= 0.7:
            selling_points.append("Strong technical skills alignment with role requirements")

        # RIASEC alignment points
        if fit_details.riasec_matches:
            selling_points.append(f"Personality fit: {', '.join(fit_details.riasec_matches)} traits match well")

        # Career anchor alignment
        if fit_details.career_anchor_matches:
            selling_points.append(f"Career motivations align: {', '.join(fit_details.career_anchor_matches)}")

        # Experience relevance
        if candidate_profile.accomplishments:
            selling_points.append("Proven track record of achievements and impact")

        # Skill overlap
        if fit_details.skill_overlap_count >= 3:
            selling_points.append(f"Already possess {fit_details.skill_overlap_count} key skills for this role")

        return selling_points

    def _identify_challenges(self, skill_gaps: List[SkillGap],
                           difficulty: TransitionDifficulty) -> List[str]:
        """Identify potential challenges in the career transition."""
        challenges = []

        critical_gaps_count = len([sg for sg in skill_gaps if sg.priority == SkillGapPriority.CRITICAL])

        if critical_gaps_count > 3:
            challenges.append("Significant skill development required before transition")

        if difficulty in [TransitionDifficulty.CHALLENGING, TransitionDifficulty.VERY_CHALLENGING]:
            challenges.append("May require substantial time investment for skill development")

        if critical_gaps_count > 0:
            challenges.append("Competition with candidates who already have required skills")

        # Add specific skill-related challenges
        technical_gaps = [sg for sg in skill_gaps if any(tech in sg.skill_name.lower() for tech in ["programming", "coding", "technical"])]
        if technical_gaps:
            challenges.append("Need to develop technical expertise in new domain")

        return challenges

    def _generate_next_steps(self, skill_gaps: List[SkillGap],
                           roadmap: List[TransitionStep]) -> List[str]:
        """Generate immediate next steps."""
        next_steps = []

        # Always start with assessment
        next_steps.append("Complete detailed skills assessment and career planning")

        # Focus on most critical skills first
        critical_gaps = [sg for sg in skill_gaps if sg.priority == SkillGapPriority.CRITICAL]
        if critical_gaps:
            top_skill = critical_gaps[0].skill_name
            next_steps.append(f"Start learning {top_skill} through recommended resources")

        # Add networking
        next_steps.append("Connect with professionals in target industry/role")

        # Add portfolio development
        next_steps.append("Begin building relevant portfolio projects")

        return next_steps

    def _calculate_confidence_level(self, fit_details: FitScoreDetails,
                                   skill_gaps: List[SkillGap]) -> float:
        """Calculate confidence level in the recommendation."""

        # Base confidence on fit score
        base_confidence = fit_details.weighted_fit_score

        # Adjust for skill gaps
        critical_gaps = len([sg for sg in skill_gaps if sg.priority == SkillGapPriority.CRITICAL])
        gap_penalty = min(0.3, critical_gaps * 0.05)  # Max 30% penalty

        # Adjust for aspiration alignment
        aspiration_boost = fit_details.aspiration_alignment_score * 0.1  # Max 10% boost

        confidence = base_confidence - gap_penalty + aspiration_boost

        return max(0.1, min(1.0, confidence))  # Keep between 0.1 and 1.0

    def _estimate_transition_time(self, skill_gaps: List[SkillGap],
                                difficulty: TransitionDifficulty) -> str:
        """Estimate total time for career transition."""

        critical_gaps = len([sg for sg in skill_gaps if sg.priority == SkillGapPriority.CRITICAL])

        if difficulty == TransitionDifficulty.EASY:
            return "3-6 months"
        elif difficulty == TransitionDifficulty.MODERATE:
            return "6-12 months"
        elif difficulty == TransitionDifficulty.CHALLENGING:
            return "12-18 months"
        else:
            return "18+ months"
