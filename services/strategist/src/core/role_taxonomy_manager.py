"""Role taxonomy database manager for loading and querying job roles."""

import logging
import yaml
import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path

from ..models.role_taxonomy import (
    JobRole, RoleTaxonomyStats, RoleSearchFilter, RoleMatchResult,
    RIASECCode, CareerAnchor, IndustryCategory, ExperienceLevel
)
from ..models.skill_vector import SkillVector

logger = logging.getLogger(__name__)


class RoleTaxonomyManager:
    """Manages the role taxonomy database and provides search/query capabilities."""
    
    def __init__(self, taxonomy_file_path: Optional[str] = None, use_production: bool = True):
        """Initialize the role taxonomy manager.
        
        Args:
            taxonomy_file_path: Optional custom path to taxonomy file
            use_production: Whether to use production (2000+ roles) or MVP (17 roles) database
        """
        self.roles: Dict[str, JobRole] = {}
        self.stats: Optional[RoleTaxonomyStats] = None
        
        # Default path relative to this file
        if taxonomy_file_path is None:
            current_dir = Path(__file__).parent.parent
            # Use production database if available and requested
            if use_production:
                production_path = current_dir / "data" / "role_taxonomy_production.yaml"
                if production_path.exists():
                    taxonomy_file_path = production_path
                    logger.info("Using production role taxonomy (2000+ roles)")
                else:
                    taxonomy_file_path = current_dir / "data" / "role_taxonomy.yaml"
                    logger.warning("Production taxonomy not found, falling back to MVP database")
            else:
                taxonomy_file_path = current_dir / "data" / "role_taxonomy.yaml"
        
        self.taxonomy_file_path = Path(taxonomy_file_path)
        
    async def load_taxonomy(self) -> None:
        """Load the role taxonomy from YAML file."""
        try:
            logger.info(f"Loading role taxonomy from {self.taxonomy_file_path}")
            
            if not self.taxonomy_file_path.exists():
                raise FileNotFoundError(f"Role taxonomy file not found: {self.taxonomy_file_path}")
            
            with open(self.taxonomy_file_path, 'r', encoding='utf-8') as file:
                taxonomy_data = yaml.safe_load(file)
            
            # Parse roles
            roles_data = taxonomy_data.get('roles', [])
            self.roles = {}
            
            for role_data in roles_data:
                try:
                    job_role = JobRole(**role_data)
                    self.roles[job_role.role_id] = job_role
                except Exception as e:
                    logger.warning(f"Failed to parse role {role_data.get('role_id', 'unknown')}: {e}")
                    continue
            
            # Generate statistics
            self.stats = self._generate_stats()
            
            logger.info(f"Successfully loaded {len(self.roles)} roles from taxonomy")
            logger.info(f"Industries: {list(self.stats.roles_by_industry.keys())}")
            
        except Exception as e:
            logger.error(f"Failed to load role taxonomy: {e}")
            raise
    
    def _generate_stats(self) -> RoleTaxonomyStats:
        """Generate statistics about the loaded taxonomy."""
        if not self.roles:
            return RoleTaxonomyStats(
                total_roles=0, 
                roles_by_industry={}, 
                roles_by_experience={},
                roles_by_riasec={}, 
                unique_skills=0
            )
        
        roles_by_industry = {}
        roles_by_experience = {}
        roles_by_riasec = {}
        all_skills = set()
        
        for role in self.roles.values():
            # Count by industry
            for industry in role.industry_categories:
                roles_by_industry[industry.value] = roles_by_industry.get(industry.value, 0) + 1
            
            # Count by experience level
            exp_level = role.experience_level.value
            roles_by_experience[exp_level] = roles_by_experience.get(exp_level, 0) + 1
            
            # Count by RIASEC codes
            for riasec in role.associated_riasec_codes:
                roles_by_riasec[riasec.value] = roles_by_riasec.get(riasec.value, 0) + 1
            
            # Collect all skills
            all_skills.update(role.required_skill_keywords)
            all_skills.update(role.preferred_skill_keywords)
        
        return RoleTaxonomyStats(
            total_roles=len(self.roles),
            roles_by_industry=roles_by_industry,
            roles_by_experience=roles_by_experience,
            roles_by_riasec=roles_by_riasec,
            unique_skills=len(all_skills)
        )
    
    def get_role_by_id(self, role_id: str) -> Optional[JobRole]:
        """Get a specific role by its ID."""
        return self.roles.get(role_id)
    
    def get_all_roles(self) -> List[JobRole]:
        """Get all roles in the taxonomy."""
        return list(self.roles.values())
    
    def search_roles(self, search_filter: RoleSearchFilter) -> List[JobRole]:
        """Search roles using provided filters."""
        matching_roles = []
        
        for role in self.roles.values():
            if self._role_matches_filter(role, search_filter):
                matching_roles.append(role)
        
        return matching_roles
    
    def _role_matches_filter(self, role: JobRole, search_filter: RoleSearchFilter) -> bool:
        """Check if a role matches the search filter criteria."""
        # Industry filter
        if search_filter.industries:
            if not any(industry in role.industry_categories for industry in search_filter.industries):
                return False
        
        # Experience level filter
        if search_filter.experience_levels:
            if role.experience_level not in search_filter.experience_levels:
                return False
        
        # RIASEC codes filter
        if search_filter.riasec_codes:
            if not any(riasec in role.associated_riasec_codes for riasec in search_filter.riasec_codes):
                return False
        
        # Career anchors filter
        if search_filter.career_anchors:
            if not any(anchor in role.associated_career_anchors for anchor in search_filter.career_anchors):
                return False
        
        # Required skills filter
        if search_filter.required_skills:
            role_skills = set([skill.lower() for skill in role.required_skill_keywords + role.preferred_skill_keywords])
            search_skills = set([skill.lower() for skill in search_filter.required_skills])
            
            # Check if any search skills match role skills
            if not search_skills.intersection(role_skills):
                return False
        
        # Salary filters
        if search_filter.salary_min and role.median_salary_range:
            if role.median_salary_range.get("max", 0) < search_filter.salary_min:
                return False
        
        if search_filter.salary_max and role.median_salary_range:
            if role.median_salary_range.get("min", float('inf')) > search_filter.salary_max:
                return False
        
        # Remote work filter
        if search_filter.remote_work_min is not None:
            if role.remote_work_compatibility < search_filter.remote_work_min:
                return False
        
        return True
    
    def get_roles_by_skill_keywords(self, skill_keywords: List[str], limit: int = 10) -> List[JobRole]:
        """Find roles that match given skill keywords."""
        skill_set = set([skill.lower() for skill in skill_keywords])
        
        role_matches = []
        
        for role in self.roles.values():
            role_skills = set([skill.lower() for skill in role.required_skill_keywords + role.preferred_skill_keywords])
            
            # Calculate skill overlap
            matching_skills = skill_set.intersection(role_skills)
            match_ratio = len(matching_skills) / len(skill_set) if skill_set else 0
            
            if matching_skills:  # At least some skill overlap
                role_matches.append((role, match_ratio, len(matching_skills)))
        
        # Sort by match ratio (descending), then by number of matches
        role_matches.sort(key=lambda x: (x[1], x[2]), reverse=True)
        
        return [role for role, _, _ in role_matches[:limit]]
    
    def get_roles_by_riasec(self, riasec_codes: List[RIASECCode]) -> List[JobRole]:
        """Find roles that match RIASEC personality types."""
        matching_roles = []
        
        for role in self.roles.values():
            # Check if any of the user's RIASEC codes match the role's codes
            if any(code in role.associated_riasec_codes for code in riasec_codes):
                matching_roles.append(role)
        
        return matching_roles
    
    def get_roles_by_career_anchors(self, career_anchors: List[CareerAnchor]) -> List[JobRole]:
        """Find roles that match career anchor preferences."""
        matching_roles = []
        
        for role in self.roles.values():
            # Check if any of the user's career anchors match the role's anchors
            if any(anchor in role.associated_career_anchors for anchor in career_anchors):
                matching_roles.append(role)
        
        return matching_roles
    
    async def generate_role_vectors(self, vectorizer) -> Dict[str, List[float]]:
        """Generate skill vectors for all roles using the skill vectorizer."""
        role_vectors = {}
        
        for role_id, role in self.roles.items():
            # Combine required and preferred skills
            all_skills = role.required_skill_keywords + role.preferred_skill_keywords
            combined_skills_text = ", ".join(all_skills)
            
            # Add role title and description for better context
            role_context = f"{role.title}. {role.description}. Skills: {combined_skills_text}"
            
            try:
                # Generate embedding for the role
                skill_embeddings = await vectorizer.generate_skill_embeddings([role_context])
                if skill_embeddings:
                    role_vectors[role_id] = skill_embeddings[0].embedding.tolist()
            except Exception as e:
                logger.warning(f"Failed to generate vector for role {role_id}: {e}")
                continue
        
        logger.info(f"Generated vectors for {len(role_vectors)} roles")
        return role_vectors
    
    def get_statistics(self) -> Optional[RoleTaxonomyStats]:
        """Get taxonomy statistics."""
        return self.stats
    
    def is_loaded(self) -> bool:
        """Check if taxonomy is loaded."""
        return len(self.roles) > 0