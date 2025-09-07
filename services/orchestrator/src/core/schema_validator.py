"""Master Career Database schema validation and data flow verification."""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field, ValidationError
from datetime import datetime

logger = logging.getLogger(__name__)


class WorkExperienceEntry(BaseModel):
    """Schema for work experience entry."""
    
    job_title: str = Field(..., description="Job title/position")
    company: str = Field(..., description="Company name")
    duration: Optional[str] = Field(None, description="Duration of employment")
    start_date: Optional[str] = Field(None, description="Start date")
    end_date: Optional[str] = Field(None, description="End date")
    location: Optional[str] = Field(None, description="Job location")
    accomplishments: List[str] = Field(default_factory=list, description="List of accomplishments")
    responsibilities: List[str] = Field(default_factory=list, description="List of responsibilities")
    skills_used: List[str] = Field(default_factory=list, description="Skills used in this role")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Quantifiable metrics")


class ProjectEntry(BaseModel):
    """Schema for project entry."""
    
    name: str = Field(..., description="Project name")
    description: str = Field(..., description="Project description")
    duration: Optional[str] = Field(None, description="Project duration")
    technologies: List[str] = Field(default_factory=list, description="Technologies used")
    outcomes: List[str] = Field(default_factory=list, description="Project outcomes")
    role: Optional[str] = Field(None, description="Role in the project")
    team_size: Optional[int] = Field(None, description="Team size")
    url: Optional[str] = Field(None, description="Project URL")


class SkillInventory(BaseModel):
    """Schema for skills inventory."""
    
    technical: List[str] = Field(default_factory=list, description="Technical skills")
    soft_skills: List[str] = Field(default_factory=list, description="Soft skills")
    languages: List[str] = Field(default_factory=list, description="Programming languages")
    frameworks: List[str] = Field(default_factory=list, description="Frameworks")
    databases: List[str] = Field(default_factory=list, description="Database technologies")
    cloud: List[str] = Field(default_factory=list, description="Cloud platforms")
    tools: List[str] = Field(default_factory=list, description="Tools and software")
    certifications: List[str] = Field(default_factory=list, description="Professional certifications")


class StrategicMetadata(BaseModel):
    """Schema for strategic metadata."""
    
    job_title_variations: List[str] = Field(default_factory=list, description="Job title variations")
    core_competencies: List[str] = Field(default_factory=list, description="Core competencies")
    career_level: Optional[str] = Field(None, description="Career level (junior, mid, senior)")
    industry_experience: List[str] = Field(default_factory=list, description="Industry experience")
    top_accomplishments: List[str] = Field(default_factory=list, description="Top accomplishments")
    leadership_experience: Optional[bool] = Field(None, description="Has leadership experience")


class HolisticProfile(BaseModel):
    """Schema for holistic profile."""
    
    transversal_projects: List[Dict[str, Any]] = Field(default_factory=list, description="Cross-functional projects")
    career_aspirations: List[str] = Field(default_factory=list, description="Career aspirations")
    motivators: List[str] = Field(default_factory=list, description="Career motivators")
    preferred_work_environment: Optional[str] = Field(None, description="Preferred work environment")
    geographic_preferences: List[str] = Field(default_factory=list, description="Geographic preferences")
    salary_expectations: Optional[Dict[str, Any]] = Field(None, description="Salary expectations")


class MasterCareerDatabase(BaseModel):
    """Complete Master Career Database schema."""
    
    work_experience: List[WorkExperienceEntry] = Field(default_factory=list, description="Work experience entries")
    projects: List[ProjectEntry] = Field(default_factory=list, description="Project entries")
    skills_inventory: SkillInventory = Field(default_factory=SkillInventory, description="Skills inventory")
    strategic_metadata: StrategicMetadata = Field(default_factory=StrategicMetadata, description="Strategic metadata")
    holistic_profile: HolisticProfile = Field(default_factory=HolisticProfile, description="Holistic profile")
    
    # Metadata
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")
    version: str = Field("1.0", description="Schema version")
    source: Optional[str] = Field(None, description="Data source")


class SchemaValidator:
    """Validates Master Career Database schema and data flow."""
    
    def __init__(self):
        """Initialize schema validator."""
        self.validation_errors: List[str] = []
        self.validation_warnings: List[str] = []
    
    def validate_master_career_database(
        self,
        data: Dict[str, Any],
        strict: bool = True
    ) -> Tuple[bool, List[str], List[str]]:
        """Validate Master Career Database against schema.
        
        Args:
            data: Data to validate
            strict: Whether to enforce strict validation
            
        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.validation_errors.clear()
        self.validation_warnings.clear()
        
        logger.info("Validating Master Career Database schema")
        
        try:
            # Attempt to parse with Pydantic model
            career_db = MasterCareerDatabase(**data)
            
            # Additional custom validation
            self._validate_work_experience(career_db.work_experience)
            self._validate_projects(career_db.projects)
            self._validate_skills_inventory(career_db.skills_inventory)
            self._validate_strategic_metadata(career_db.strategic_metadata)
            self._validate_holistic_profile(career_db.holistic_profile)
            
            # Check for completeness
            if strict:
                self._check_data_completeness(career_db)
            
            is_valid = len(self.validation_errors) == 0
            
            logger.info(f"Schema validation completed. Valid: {is_valid}, "
                       f"Errors: {len(self.validation_errors)}, "
                       f"Warnings: {len(self.validation_warnings)}")
            
            return is_valid, self.validation_errors, self.validation_warnings
            
        except ValidationError as e:
            logger.error(f"Pydantic validation error: {str(e)}")
            for error in e.errors():
                self.validation_errors.append(f"Field '{'.'.join(str(x) for x in error['loc'])}': {error['msg']}")
            
            return False, self.validation_errors, self.validation_warnings
            
        except Exception as e:
            logger.error(f"Unexpected validation error: {str(e)}")
            self.validation_errors.append(f"Unexpected validation error: {str(e)}")
            return False, self.validation_errors, self.validation_warnings
    
    def _validate_work_experience(self, work_experience: List[WorkExperienceEntry]) -> None:
        """Validate work experience entries."""
        if not work_experience:
            self.validation_warnings.append("No work experience entries found")
            return
        
        for i, entry in enumerate(work_experience):
            if not entry.accomplishments and not entry.responsibilities:
                self.validation_warnings.append(
                    f"Work experience entry {i+1} has no accomplishments or responsibilities"
                )
            
            # Check for quantifiable metrics
            has_metrics = any(
                any(keyword in accomplishment.lower() for keyword in 
                    ['%', 'increased', 'decreased', 'improved', 'reduced', 'saved', '$', 'million', 'thousand'])
                for accomplishment in entry.accomplishments
            )
            
            if not has_metrics:
                self.validation_warnings.append(
                    f"Work experience entry {i+1} lacks quantifiable metrics"
                )
    
    def _validate_projects(self, projects: List[ProjectEntry]) -> None:
        """Validate project entries."""
        if not projects:
            self.validation_warnings.append("No project entries found")
            return
        
        for i, project in enumerate(projects):
            if not project.technologies:
                self.validation_warnings.append(
                    f"Project {i+1} '{project.name}' has no technologies listed"
                )
            
            if not project.outcomes:
                self.validation_warnings.append(
                    f"Project {i+1} '{project.name}' has no outcomes specified"
                )
    
    def _validate_skills_inventory(self, skills_inventory: SkillInventory) -> None:
        """Validate skills inventory."""
        total_skills = (
            len(skills_inventory.technical) +
            len(skills_inventory.soft_skills) +
            len(skills_inventory.languages) +
            len(skills_inventory.frameworks) +
            len(skills_inventory.databases) +
            len(skills_inventory.cloud) +
            len(skills_inventory.tools)
        )
        
        if total_skills == 0:
            self.validation_errors.append("Skills inventory is completely empty")
        elif total_skills < 5:
            self.validation_warnings.append("Skills inventory appears sparse (< 5 total skills)")
        
        # Check for balance
        if len(skills_inventory.technical) == 0:
            self.validation_warnings.append("No technical skills listed")
        
        if len(skills_inventory.soft_skills) == 0:
            self.validation_warnings.append("No soft skills listed")
    
    def _validate_strategic_metadata(self, strategic_metadata: StrategicMetadata) -> None:
        """Validate strategic metadata."""
        if not strategic_metadata.core_competencies:
            self.validation_warnings.append("No core competencies identified")
        
        if not strategic_metadata.job_title_variations:
            self.validation_warnings.append("No job title variations provided")
        
        if strategic_metadata.career_level not in [None, "junior", "mid", "senior", "executive"]:
            self.validation_warnings.append(
                f"Career level '{strategic_metadata.career_level}' may not be recognized"
            )
    
    def _validate_holistic_profile(self, holistic_profile: HolisticProfile) -> None:
        """Validate holistic profile."""
        if not holistic_profile.career_aspirations:
            self.validation_warnings.append("No career aspirations specified")
        
        if not holistic_profile.motivators:
            self.validation_warnings.append("No career motivators identified")
    
    def _check_data_completeness(self, career_db: MasterCareerDatabase) -> None:
        """Check overall data completeness."""
        completeness_score = 0
        total_sections = 5
        
        # Work experience
        if career_db.work_experience:
            completeness_score += 1
        
        # Projects
        if career_db.projects:
            completeness_score += 1
        
        # Skills inventory
        if (career_db.skills_inventory.technical or 
            career_db.skills_inventory.soft_skills or
            career_db.skills_inventory.languages):
            completeness_score += 1
        
        # Strategic metadata
        if (career_db.strategic_metadata.core_competencies or 
            career_db.strategic_metadata.job_title_variations):
            completeness_score += 1
        
        # Holistic profile
        if (career_db.holistic_profile.career_aspirations or 
            career_db.holistic_profile.motivators):
            completeness_score += 1
        
        completeness_percentage = (completeness_score / total_sections) * 100
        
        if completeness_percentage < 60:
            self.validation_warnings.append(
                f"Data completeness is low ({completeness_percentage:.1f}%)"
            )
    
    def validate_pipeline_data_flow(
        self,
        profile_data: Dict[str, Any],
        strategy_results: Dict[str, Any],
        analysis_results: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """Validate complete pipeline data flow.
        
        Args:
            profile_data: Data from Profile Ingestor
            strategy_results: Data from Strategist
            analysis_results: Data from Analyst
            
        Returns:
            Tuple of (is_valid, errors)
        """
        errors = []
        
        logger.info("Validating pipeline data flow")
        
        # Validate Profile Ingestor output
        is_valid, profile_errors, _ = self.validate_master_career_database(profile_data, strict=False)
        if not is_valid:
            errors.extend([f"Profile data: {error}" for error in profile_errors])
        
        # Validate Strategist output structure
        if not isinstance(strategy_results, dict):
            errors.append("Strategy results must be a dictionary")
        elif "recommended_paths" not in strategy_results:
            errors.append("Strategy results missing 'recommended_paths' field")
        
        # Validate Analyst output structure  
        if not isinstance(analysis_results, dict):
            errors.append("Analysis results must be a dictionary")
        else:
            required_analysis_fields = ["market_demand", "skill_gaps", "resume_optimization"]
            for field in required_analysis_fields:
                if field not in analysis_results:
                    errors.append(f"Analysis results missing '{field}' field")
        
        # Check data consistency
        if is_valid and isinstance(strategy_results, dict) and isinstance(analysis_results, dict):
            # Ensure skills from profile are referenced in analysis
            profile_skills = set()
            skills_inv = profile_data.get("skills_inventory", {})
            if isinstance(skills_inv, dict):
                for skill_category in skills_inv.values():
                    if isinstance(skill_category, list):
                        profile_skills.update(skill_category)
            
            # Check if analysis addresses profile skills
            if profile_skills and "skill_gaps" in analysis_results:
                skill_gaps = analysis_results["skill_gaps"]
                if not isinstance(skill_gaps, list) or not skill_gaps:
                    errors.append("Analysis should identify skill gaps based on profile")
        
        is_flow_valid = len(errors) == 0
        
        logger.info(f"Pipeline data flow validation completed. Valid: {is_flow_valid}, "
                   f"Errors: {len(errors)}")
        
        return is_flow_valid, errors
    
    def generate_schema_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive schema compliance report.
        
        Args:
            data: Data to analyze
            
        Returns:
            Schema compliance report
        """
        is_valid, errors, warnings = self.validate_master_career_database(data, strict=False)
        
        # Calculate metrics
        work_exp_count = len(data.get("work_experience", []))
        projects_count = len(data.get("projects", []))
        
        skills_inv = data.get("skills_inventory", {})
        total_skills = sum(
            len(skills_inv.get(category, []))
            for category in ["technical", "soft_skills", "languages", "frameworks", 
                           "databases", "cloud", "tools"]
        )
        
        report = {
            "validation_summary": {
                "is_valid": is_valid,
                "errors_count": len(errors),
                "warnings_count": len(warnings),
                "validation_timestamp": datetime.utcnow().isoformat()
            },
            "data_metrics": {
                "work_experience_entries": work_exp_count,
                "project_entries": projects_count,
                "total_skills": total_skills,
                "has_strategic_metadata": bool(data.get("strategic_metadata")),
                "has_holistic_profile": bool(data.get("holistic_profile"))
            },
            "errors": errors,
            "warnings": warnings,
            "recommendations": self._generate_recommendations(data, errors, warnings)
        }
        
        return report
    
    def _generate_recommendations(
        self,
        data: Dict[str, Any],
        errors: List[str],
        warnings: List[str]
    ) -> List[str]:
        """Generate recommendations for improving data quality."""
        recommendations = []
        
        if not data.get("work_experience"):
            recommendations.append("Add work experience entries to strengthen profile")
        
        if not data.get("projects"):
            recommendations.append("Include project information to showcase practical experience")
        
        skills_inv = data.get("skills_inventory", {})
        if not skills_inv or sum(len(skills_inv.get(cat, [])) for cat in skills_inv) < 10:
            recommendations.append("Expand skills inventory with more technical and soft skills")
        
        if "quantifiable metrics" in " ".join(warnings):
            recommendations.append("Add quantifiable achievements and metrics to work experience")
        
        strategic_metadata = data.get("strategic_metadata", {})
        if not strategic_metadata.get("core_competencies"):
            recommendations.append("Identify and list core competencies")
        
        return recommendations