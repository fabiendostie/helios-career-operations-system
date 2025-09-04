"""
Master schema definition for the career database JSON structure.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class Document:
    """Represents a document processed by the ingestion engine."""

    file_path: Path
    content: str
    language: str  # 'en' or 'fr'
    file_type: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class WorkExperience:
    """Represents a work experience entry."""

    company: str
    role: str
    duration: str
    description: Optional[str] = None
    accomplishments: Optional[List[str]] = None
    technologies: Optional[List[str]] = None


@dataclass
class Education:
    """Represents an education entry."""

    institution: str
    degree: str
    field: Optional[str] = None
    year: Optional[str] = None
    gpa: Optional[str] = None


@dataclass
class Project:
    """Represents a project entry."""

    name: str
    description: str
    technologies: Optional[List[str]] = None
    url: Optional[str] = None
    impact: Optional[str] = None


@dataclass
class SkillsInventory:
    """Represents categorized skills inventory."""

    technical: List[str]
    languages: List[str]
    frameworks: List[str]
    tools: List[str]
    soft_skills: List[str]


@dataclass
class StrategicMetadata:
    """Represents strategic career metadata."""

    job_title_variations: List[str]
    core_competencies: List[str]
    industry_experience: List[str]


@dataclass
class HolisticProfile:
    """Represents holistic career profile."""

    aspirations: Dict[str, Any]
    motivators: Dict[str, Any]
    personal_qualities: Dict[str, Any]
    transversal_projects: List[Dict[str, Any]]


@dataclass
class PersonalInfo:
    """Represents personal information."""

    name: str
    contact: Dict[str, str]
    location: Optional[str] = None


@dataclass
class MasterCareerDatabase:
    """Main structure for the master career database."""

    personal_info: PersonalInfo
    work_experience: List[WorkExperience]
    education: List[Education]
    projects: List[Project]
    skills_inventory: SkillsInventory
    strategic_metadata: StrategicMetadata
    holistic_profile: HolisticProfile
    source_documents: List[str]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MasterCareerDatabase":
        """Create MasterCareerDatabase from dictionary."""
        # Convert work experience
        work_exp = []
        for exp in data.get("work_experience", []):
            if isinstance(exp, dict):
                work_exp.append(WorkExperience(**exp))

        # Convert education
        education = []
        for edu in data.get("education", []):
            if isinstance(edu, dict):
                education.append(Education(**edu))

        # Convert projects
        projects = []
        for proj in data.get("projects", []):
            if isinstance(proj, dict):
                projects.append(Project(**proj))

        # Skills inventory
        skills_data = data.get("skills_inventory", {})
        if not isinstance(skills_data, dict):
            skills_data = {
                "technical": data.get("skills", []),
                "languages": [],
                "frameworks": [],
                "tools": [],
                "soft_skills": [],
            }

        skills_inventory = SkillsInventory(
            technical=skills_data.get("technical", []),
            languages=skills_data.get("languages", []),
            frameworks=skills_data.get("frameworks", []),
            tools=skills_data.get("tools", []),
            soft_skills=skills_data.get("soft_skills", []),
        )

        # Strategic metadata
        strategic_data = data.get("strategic_metadata", {})
        strategic_metadata = StrategicMetadata(
            job_title_variations=strategic_data.get("job_title_variations", []),
            core_competencies=strategic_data.get("core_competencies", []),
            industry_experience=strategic_data.get("industry_experience", []),
        )

        # Holistic profile
        holistic_data = data.get("holistic_profile", {})
        holistic_profile = HolisticProfile(
            aspirations=holistic_data.get("aspirations", {}),
            motivators=holistic_data.get("motivators", {}),
            personal_qualities=holistic_data.get("personal_qualities", {}),
            transversal_projects=holistic_data.get("transversal_projects", []),
        )

        # Personal info
        personal_data = data.get("personal_info", {})
        personal_info = PersonalInfo(
            name=personal_data.get("name", "Unknown"),
            contact=personal_data.get("contact", {}),
            location=personal_data.get("location"),
        )

        return cls(
            personal_info=personal_info,
            work_experience=work_exp,
            education=education,
            projects=projects,
            skills_inventory=skills_inventory,
            strategic_metadata=strategic_metadata,
            holistic_profile=holistic_profile,
            source_documents=data.get("source_documents", []),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


# JSON Schema definition for validation
MASTER_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["work_experience", "skills_inventory", "holistic_profile"],
    "properties": {
        "work_experience": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["role", "company", "dates", "description"],
                "properties": {
                    "role": {"type": "string"},
                    "company": {"type": "string"},
                    "dates": {"type": "string"},
                    "description": {"type": "string"},
                    "accomplishments": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["original"],
                            "properties": {
                                "original": {"type": "string"},
                                "deconstructed": {
                                    "type": "object",
                                    "properties": {
                                        "action": {"type": "string"},
                                        "challenge": {"type": "string"},
                                        "outcome": {"type": "string"}
                                    }
                                },
                                "metrics": {"type": "object"},
                                "associated_skills": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                },
                                "impact_score": {"type": "number"}
                            }
                        }
                    }
                }
            }
        },
        "projects": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name", "description"],
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "technologies": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "outcomes": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                }
            }
        },
        "skills_inventory": {
            "type": "object",
            "additionalProperties": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["skill"],
                    "properties": {
                        "skill": {"type": "string"},
                        "evidence_pointers": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    }
                }
            }
        },
        "strategic_metadata": {
            "type": "object",
            "properties": {
                "job_title_variations": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "top_anchor_accomplishments": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "core_competencies": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        },
        "holistic_profile": {
            "type": "object",
            "properties": {
                "transversal_projects": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "description": {"type": "string"},
                            "skills_demonstrated": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "link": {"type": ["string", "null"]}
                        }
                    }
                },
                "professional_aspirations": {
                    "type": "object",
                    "properties": {
                        "target_roles": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "industries_of_interest": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "technologies_to_learn": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    }
                },
                "core_motivators": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "personal_qualities": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "trait": {"type": "string"},
                            "evidence": {"type": "string"}
                        }
                    }
                }
            }
        },
        "_metadata": {
            "type": "object",
            "properties": {
                "generated_at": {"type": "string"},
                "version": {"type": "string"},
                "source_files": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "statistics": {"type": "object"}
            }
        }
    }
}
