"""Fit scoring algorithm that combines skill similarity and aspiration alignment."""

import logging
import statistics
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass

from ..models.role_taxonomy import JobRole, RIASECCode, CareerAnchor
from ..models.skill_vector import CandidateProfile
from ..core.config import StrategistConfig

logger = logging.getLogger(__name__)


@dataclass
class FitScoreDetails:
    """Detailed breakdown of fit score calculation."""
    skill_match_score: float
    aspiration_alignment_score: float
    weighted_fit_score: float
    skill_overlap_count: int
    riasec_matches: List[str]
    career_anchor_matches: List[str]
    explanation: str


@dataclass
class AspirationProfile:
    """User's aspiration profile extracted from Master Career Database."""
    riasec_codes: List[RIASECCode]
    career_anchors: List[CareerAnchor]
    interests: List[str]
    motivators: List[str]
    confidence_level: float = 1.0


class FitScorer:
    """Calculates fit scores between candidate profiles and job roles."""
    
    def __init__(self, config: Optional[StrategistConfig] = None):
        """Initialize fit scorer with configuration."""
        self.config = config or StrategistConfig()
        self.skill_weight = self.config.skill_weight
        self.aspiration_weight = self.config.aspiration_weight
        
        # Ensure weights sum to 1.0
        total_weight = self.skill_weight + self.aspiration_weight
        if total_weight != 1.0:
            self.skill_weight = self.skill_weight / total_weight
            self.aspiration_weight = self.aspiration_weight / total_weight
            logger.info(f"Normalized weights: skill={self.skill_weight:.2f}, aspiration={self.aspiration_weight:.2f}")
    
    def calculate_fit_score(self, candidate_profile: CandidateProfile, 
                           role: JobRole, role_vector: List[float],
                           aspiration_profile: AspirationProfile) -> FitScoreDetails:
        """Calculate comprehensive fit score between candidate and role."""
        
        # 1. Calculate skill similarity (cosine similarity between vectors)
        skill_score = self._calculate_skill_similarity(
            candidate_profile.aggregated_vector, 
            role_vector
        )
        
        # 2. Calculate aspiration alignment (RIASEC + career anchors)
        aspiration_score = self._calculate_aspiration_alignment(
            aspiration_profile, 
            role
        )
        
        # 3. Calculate weighted final score
        weighted_score = (
            self.skill_weight * skill_score + 
            self.aspiration_weight * aspiration_score
        )
        
        # 4. Generate detailed explanation
        explanation = self._generate_score_explanation(
            skill_score, aspiration_score, weighted_score, 
            candidate_profile, role, aspiration_profile
        )
        
        # 5. Calculate additional details
        skill_overlap = self._count_skill_overlap(candidate_profile.skills, role)
        riasec_matches = self._find_riasec_matches(aspiration_profile.riasec_codes, role)
        anchor_matches = self._find_career_anchor_matches(aspiration_profile.career_anchors, role)
        
        return FitScoreDetails(
            skill_match_score=skill_score,
            aspiration_alignment_score=aspiration_score,
            weighted_fit_score=weighted_score,
            skill_overlap_count=skill_overlap,
            riasec_matches=riasec_matches,
            career_anchor_matches=anchor_matches,
            explanation=explanation
        )
    
    def _calculate_skill_similarity(self, candidate_vector: List[float], 
                                   role_vector: List[float]) -> float:
        """Calculate cosine similarity between candidate and role vectors."""
        if len(candidate_vector) != len(role_vector):
            logger.warning(f"Vector dimension mismatch: candidate={len(candidate_vector)}, role={len(role_vector)}")
            return 0.0
        
        try:
            # Calculate cosine similarity manually
            dot_product = sum(a * b for a, b in zip(candidate_vector, role_vector))
            
            magnitude_a = sum(a * a for a in candidate_vector) ** 0.5
            magnitude_b = sum(b * b for b in role_vector) ** 0.5
            
            if magnitude_a == 0 or magnitude_b == 0:
                return 0.0
            
            similarity = dot_product / (magnitude_a * magnitude_b)
            
            # Ensure similarity is between 0 and 1
            return max(0.0, min(1.0, similarity))
        
        except Exception as e:
            logger.error(f"Error calculating skill similarity: {e}")
            return 0.0
    
    def _calculate_aspiration_alignment(self, aspiration_profile: AspirationProfile, 
                                      role: JobRole) -> float:
        """Calculate alignment between user aspirations and role characteristics."""
        alignment_scores = []
        
        # 1. RIASEC code alignment (Holland Codes)
        riasec_score = self._calculate_riasec_alignment(
            aspiration_profile.riasec_codes, 
            role.associated_riasec_codes
        )
        alignment_scores.append(riasec_score)
        
        # 2. Career anchor alignment (Schein's Career Anchors)
        anchor_score = self._calculate_career_anchor_alignment(
            aspiration_profile.career_anchors, 
            role.associated_career_anchors
        )
        alignment_scores.append(anchor_score)
        
        # 3. Interest-based alignment (keywords matching)
        interest_score = self._calculate_interest_alignment(
            aspiration_profile.interests, 
            role
        )
        alignment_scores.append(interest_score)
        
        # Return weighted average of alignment scores
        if alignment_scores:
            # Weight RIASEC and career anchors more heavily than interests
            weights = [0.4, 0.4, 0.2]
            weighted_score = sum(score * weight for score, weight in zip(alignment_scores, weights))
            return min(1.0, max(0.0, weighted_score))
        
        return 0.0
    
    def _calculate_riasec_alignment(self, user_riasec: List[RIASECCode], 
                                   role_riasec: List[RIASECCode]) -> float:
        """Calculate RIASEC personality type alignment."""
        if not user_riasec or not role_riasec:
            return 0.0
        
        # Count overlapping RIASEC codes
        user_set = set(user_riasec)
        role_set = set(role_riasec)
        overlap = user_set.intersection(role_set)
        
        # Calculate Jaccard similarity (intersection over union)
        union = user_set.union(role_set)
        if not union:
            return 0.0
        
        return len(overlap) / len(union)
    
    def _calculate_career_anchor_alignment(self, user_anchors: List[CareerAnchor], 
                                         role_anchors: List[CareerAnchor]) -> float:
        """Calculate career anchor alignment based on Schein's framework."""
        if not user_anchors or not role_anchors:
            return 0.0
        
        # Count overlapping career anchors
        user_set = set(user_anchors)
        role_set = set(role_anchors)
        overlap = user_set.intersection(role_set)
        
        # Calculate Jaccard similarity
        union = user_set.union(role_set)
        if not union:
            return 0.0
        
        return len(overlap) / len(union)
    
    def _calculate_interest_alignment(self, user_interests: List[str], 
                                    role: JobRole) -> float:
        """Calculate alignment between user interests and role characteristics."""
        if not user_interests:
            return 0.0
        
        # Create role context for matching
        role_context = (
            role.title.lower() + " " + 
            role.description.lower() + " " +
            " ".join([skill.lower() for skill in role.required_skill_keywords]) + " " +
            " ".join([skill.lower() for skill in role.preferred_skill_keywords])
        )
        
        # Count interest keyword matches
        matches = 0
        for interest in user_interests:
            interest_words = interest.lower().split()
            for word in interest_words:
                if len(word) > 2 and word in role_context:  # Skip very short words
                    matches += 1
                    break  # Only count one match per interest
        
        # Return match ratio
        return matches / len(user_interests) if user_interests else 0.0
    
    def _count_skill_overlap(self, candidate_skills: List[str], role: JobRole) -> int:
        """Count overlapping skills between candidate and role."""
        candidate_skills_lower = set([skill.lower() for skill in candidate_skills])
        role_skills_lower = set([skill.lower() for skill in role.required_skill_keywords + role.preferred_skill_keywords])
        
        overlap = candidate_skills_lower.intersection(role_skills_lower)
        return len(overlap)
    
    def _find_riasec_matches(self, user_riasec: List[RIASECCode], 
                           role: JobRole) -> List[str]:
        """Find matching RIASEC codes between user and role."""
        user_set = set(user_riasec)
        role_set = set(role.associated_riasec_codes)
        matches = user_set.intersection(role_set)
        return [code.value for code in matches]
    
    def _find_career_anchor_matches(self, user_anchors: List[CareerAnchor], 
                                   role: JobRole) -> List[str]:
        """Find matching career anchors between user and role."""
        user_set = set(user_anchors)
        role_set = set(role.associated_career_anchors)
        matches = user_set.intersection(role_set)
        return [anchor.value for anchor in matches]
    
    def _generate_score_explanation(self, skill_score: float, aspiration_score: float,
                                   weighted_score: float, candidate_profile: CandidateProfile,
                                   role: JobRole, aspiration_profile: AspirationProfile) -> str:
        """Generate human-readable explanation of the fit score."""
        
        explanation_parts = []
        
        # Overall score interpretation
        if weighted_score >= 0.8:
            overall = "excellent match"
        elif weighted_score >= 0.6:
            overall = "good match"
        elif weighted_score >= 0.4:
            overall = "moderate match"
        else:
            overall = "weak match"
        
        explanation_parts.append(f"This role is an {overall} (fit score: {weighted_score:.2f})")
        
        # Skill alignment explanation
        skill_percentage = int(skill_score * 100)
        explanation_parts.append(
            f"Your skills align {skill_percentage}% with this role's requirements"
        )
        
        # Aspiration alignment explanation
        aspiration_percentage = int(aspiration_score * 100)
        explanation_parts.append(
            f"The role matches {aspiration_percentage}% of your career aspirations and personality type"
        )
        
        # Specific strengths
        riasec_matches = self._find_riasec_matches(aspiration_profile.riasec_codes, role)
        if riasec_matches:
            explanation_parts.append(
                f"Strong personality fit: {', '.join(riasec_matches)} traits align well"
            )
        
        career_anchor_matches = self._find_career_anchor_matches(aspiration_profile.career_anchors, role)
        if career_anchor_matches:
            explanation_parts.append(
                f"Career motivations align: {', '.join(career_anchor_matches)}"
            )
        
        return ". ".join(explanation_parts) + "."
    
    def extract_aspiration_profile(self, master_career_data: Dict[str, Any]) -> AspirationProfile:
        """Extract aspiration profile from Master Career Database."""
        
        # Extract holistic profile data
        holistic_profile = master_career_data.get("holistic_profile", {})
        
        # Extract interests and motivators
        interests = []
        if isinstance(holistic_profile.get("aspirations"), list):
            interests.extend(holistic_profile["aspirations"])
        elif isinstance(holistic_profile.get("aspirations"), str):
            interests.append(holistic_profile["aspirations"])
        
        motivators = []
        if isinstance(holistic_profile.get("motivators"), list):
            motivators.extend(holistic_profile["motivators"])
        elif isinstance(holistic_profile.get("motivators"), str):
            motivators.append(holistic_profile["motivators"])
        
        # Infer RIASEC codes from interests and work experience
        riasec_codes = self._infer_riasec_codes(master_career_data)
        
        # Infer career anchors from motivators and work patterns
        career_anchors = self._infer_career_anchors(master_career_data)
        
        return AspirationProfile(
            riasec_codes=riasec_codes,
            career_anchors=career_anchors,
            interests=interests,
            motivators=motivators,
            confidence_level=0.7  # Moderate confidence for inferred data
        )
    
    def _infer_riasec_codes(self, master_career_data: Dict[str, Any]) -> List[RIASECCode]:
        """Infer RIASEC codes from user's career data and interests."""
        inferred_codes = []
        
        # Analyze skills and work experience for patterns
        all_skills = []
        
        # Collect skills from various sources
        skills_inventory = master_career_data.get("skills_inventory", {})
        for category, skills in skills_inventory.items():
            if isinstance(skills, list):
                all_skills.extend(skills)
            elif isinstance(skills, dict):
                all_skills.extend(skills.keys())
        
        # Add skills from work experience
        work_experience = master_career_data.get("work_experience", [])
        for job in work_experience:
            job_skills = job.get("skills_demonstrated", [])
            all_skills.extend(job_skills)
        
        # Convert to lowercase for matching
        all_skills_lower = [skill.lower() for skill in all_skills]
        
        # RIASEC inference rules based on skill keywords
        if any(skill in all_skills_lower for skill in ["programming", "coding", "software", "python", "java", "development"]):
            inferred_codes.append(RIASECCode.INVESTIGATIVE)
        
        if any(skill in all_skills_lower for skill in ["management", "leadership", "strategy", "business", "sales", "marketing"]):
            inferred_codes.append(RIASECCode.ENTERPRISING)
        
        if any(skill in all_skills_lower for skill in ["teaching", "training", "counseling", "healthcare", "social work", "communication"]):
            inferred_codes.append(RIASECCode.SOCIAL)
        
        if any(skill in all_skills_lower for skill in ["design", "creative", "writing", "art", "ux", "ui", "graphic"]):
            inferred_codes.append(RIASECCode.ARTISTIC)
        
        if any(skill in all_skills_lower for skill in ["engineering", "construction", "manufacturing", "operations", "technical"]):
            inferred_codes.append(RIASECCode.REALISTIC)
        
        if any(skill in all_skills_lower for skill in ["accounting", "finance", "data entry", "administration", "organization"]):
            inferred_codes.append(RIASECCode.CONVENTIONAL)
        
        # Default to Investigative if no clear pattern (common in tech)
        if not inferred_codes:
            inferred_codes.append(RIASECCode.INVESTIGATIVE)
        
        return inferred_codes
    
    def _infer_career_anchors(self, master_career_data: Dict[str, Any]) -> List[CareerAnchor]:
        """Infer career anchors from user's motivators and work patterns."""
        inferred_anchors = []
        
        # Extract motivators and interests
        holistic_profile = master_career_data.get("holistic_profile", {})
        motivators = holistic_profile.get("motivators", [])
        aspirations = holistic_profile.get("aspirations", [])
        
        # Combine motivators and aspirations for analysis
        motivation_text = " ".join([
            str(motivators) if isinstance(motivators, str) else " ".join(motivators) if isinstance(motivators, list) else "",
            str(aspirations) if isinstance(aspirations, str) else " ".join(aspirations) if isinstance(aspirations, list) else ""
        ]).lower()
        
        # Career anchor inference rules
        if any(keyword in motivation_text for keyword in ["technical", "expertise", "skills", "specialization"]):
            inferred_anchors.append(CareerAnchor.TECHNICAL_COMPETENCE)
        
        if any(keyword in motivation_text for keyword in ["management", "leadership", "team", "organization"]):
            inferred_anchors.append(CareerAnchor.GENERAL_MANAGERIAL)
        
        if any(keyword in motivation_text for keyword in ["independence", "autonomy", "freedom", "own pace"]):
            inferred_anchors.append(CareerAnchor.AUTONOMY_INDEPENDENCE)
        
        if any(keyword in motivation_text for keyword in ["security", "stability", "benefits", "safe"]):
            inferred_anchors.append(CareerAnchor.SECURITY_STABILITY)
        
        if any(keyword in motivation_text for keyword in ["innovation", "creativity", "entrepreneurial", "startup"]):
            inferred_anchors.append(CareerAnchor.ENTREPRENEURIAL_CREATIVITY)
        
        if any(keyword in motivation_text for keyword in ["service", "help", "social impact", "community"]):
            inferred_anchors.append(CareerAnchor.SERVICE_DEDICATION)
        
        if any(keyword in motivation_text for keyword in ["challenge", "problem solving", "difficult", "complex"]):
            inferred_anchors.append(CareerAnchor.PURE_CHALLENGE)
        
        if any(keyword in motivation_text for keyword in ["balance", "lifestyle", "flexible", "family"]):
            inferred_anchors.append(CareerAnchor.LIFESTYLE)
        
        # Default to Technical Competence if no clear pattern
        if not inferred_anchors:
            inferred_anchors.append(CareerAnchor.TECHNICAL_COMPETENCE)
        
        return inferred_anchors