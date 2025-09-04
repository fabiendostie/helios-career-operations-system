"""
Data consolidation engine and skill mapping functionality.
"""

import logging
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional, Set
from dataclasses import dataclass

from fuzzywuzzy import fuzz

from resume_extractor.ui.conflict_resolver import (
    ConflictResolverUI,
    Conflict,
    Variation,
)

logger = logging.getLogger(__name__)


@dataclass
class SkillEntry:
    """Represents a skill entry from a document source."""

    name: str
    source_reference: str
    category: Optional[str] = None


@dataclass
class SkillInventoryEntry:
    """Represents a consolidated skill entry with evidence and metadata."""

    skill: str
    evidence_pointers: List[str]
    categories: Set[str]
    proficiency_indicators: List[str]

    def to_dict(self) -> dict:
        """Convert to dictionary format for JSON serialization."""
        return {
            "skill": self.skill,
            "evidence_pointers": self.evidence_pointers,
            "categories": list(self.categories),
            "proficiency": self._determine_proficiency(),
        }

    def _determine_proficiency(self) -> str:
        """Determine proficiency based on evidence and indicators."""
        evidence_count = len(self.evidence_pointers)

        if evidence_count >= 5:
            return "expert"
        elif evidence_count >= 3:
            return "intermediate"
        else:
            return "beginner"


@dataclass
class ParsedData:
    """Represents parsed data from a single document."""

    content: Dict[str, Any]
    source_file: str
    language: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ConsolidatedData:
    """Represents the consolidated data structure."""

    data: Dict[str, Any]
    conflicts_resolved: int
    source_documents: List[str]


class SkillMapper:
    """Handles bilingual skill mapping and consolidation with fuzzy matching."""

    def __init__(self, mapping_file: Path = Path("data/skill_map.json")):
        """Initialize with skill mapping file."""
        self.mapping_file = mapping_file
        self.skill_mappings = self._load_mappings(mapping_file)
        self.canonical_skills = self._build_canonical_index()
        self.fuzzy_threshold = 85  # Similarity threshold for fuzzy matching
        self.user_corrections: Dict[str, str] = {}

    def _load_mappings(self, file_path: Path) -> Dict[str, List[str]]:
        """Load bilingual skill mappings from JSON."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("skill_mappings", {})
        except FileNotFoundError:
            logger.warning(f"Skill map not found at {file_path}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in skill map file: {e}")
            return {}

    def _build_canonical_index(self) -> Dict[str, str]:
        """Build reverse index for faster lookups."""
        index = {}
        for canonical, variations in self.skill_mappings.items():
            # Add canonical form
            index[canonical.lower()] = canonical
            # Add all variations
            for variation in variations:
                index[variation.lower()] = canonical
        return index

    def map_skills(
        self, raw_skills: List[SkillEntry]
    ) -> Dict[str, SkillInventoryEntry]:
        """Map and consolidate skills from multiple sources."""
        consolidated = {}

        for skill_entry in raw_skills:
            canonical_name = self._find_canonical_skill(skill_entry.name)

            if canonical_name not in consolidated:
                consolidated[canonical_name] = SkillInventoryEntry(
                    skill=canonical_name,
                    evidence_pointers=[],
                    categories=set(),
                    proficiency_indicators=[],
                )

            # Add evidence
            consolidated[canonical_name].evidence_pointers.append(
                skill_entry.source_reference
            )

            # Merge categories
            if skill_entry.category:
                consolidated[canonical_name].categories.add(skill_entry.category)

        return consolidated

    def _find_canonical_skill(self, skill_name: str) -> str:
        """Find canonical skill name using exact and fuzzy matching."""

        # Clean and normalize
        normalized = skill_name.strip().lower()

        # Check user corrections first
        if normalized in self.user_corrections:
            return self.user_corrections[normalized]

        # Exact match check using index
        if normalized in self.canonical_skills:
            return self.canonical_skills[normalized]

        # Fuzzy match if no exact match
        best_match = self._fuzzy_match(skill_name)
        if best_match:
            return best_match

        # Return original if no match found (new skill)
        return skill_name

    def _fuzzy_match(self, skill: str) -> Optional[str]:
        """Use fuzzy string matching for approximate matches."""
        best_score = 0
        best_match = None

        for canonical, variations in self.skill_mappings.items():
            # Check canonical name
            score = fuzz.ratio(skill.lower(), canonical.lower())
            if score > best_score:
                best_score = score
                best_match = canonical

            # Check variations
            for variation in variations:
                score = fuzz.ratio(skill.lower(), variation.lower())
                if score > best_score:
                    best_score = score
                    best_match = canonical

        # Return match if above threshold
        return best_match if best_score >= self.fuzzy_threshold else None

    def _assign_categories(self, skills: List[str]) -> Dict[str, List[str]]:
        """Organize skills into categories."""
        categorized = {
            "Programming Languages": [],
            "Frameworks & Libraries": [],
            "Databases": [],
            "Cloud & DevOps": [],
            "Soft Skills": [],
            "Domain Expertise": [],
            "Tools": [],
            "Other": [],
        }

        # Language patterns
        lang_patterns = [
            r"\b(Python|Java|JavaScript|C\+\+|C#|Ruby|Go|Rust|PHP|Swift)\b",
            r"\b(TypeScript|Kotlin|Scala|R|MATLAB|Julia)\b",
        ]

        # Framework patterns
        framework_patterns = [
            r"\b(React|Angular|Vue|Django|Flask|Spring|Rails)\b",
            r"\b(TensorFlow|PyTorch|Keras|scikit-learn)\b",
        ]

        # Database patterns
        database_patterns = [
            r"\b(MySQL|PostgreSQL|SQLite|MongoDB|Redis|Oracle)\b",
            r"\b(SQL|NoSQL|Database)\b",
        ]

        # Cloud patterns
        cloud_patterns = [
            r"\b(AWS|Azure|GCP|Docker|Kubernetes|Terraform)\b",
            r"\b(Cloud|DevOps|CI/CD)\b",
        ]

        # Soft skills patterns
        soft_patterns = [
            r"\b(Leadership|Communication|Management|Team)\b",
            r"\b(Problem Solving|Critical Thinking)\b",
        ]

        for skill in skills:
            assigned = False

            # Check against patterns
            if not assigned:
                for pattern in lang_patterns:
                    if re.search(pattern, skill, re.IGNORECASE):
                        categorized["Programming Languages"].append(skill)
                        assigned = True
                        break

            if not assigned:
                for pattern in framework_patterns:
                    if re.search(pattern, skill, re.IGNORECASE):
                        categorized["Frameworks & Libraries"].append(skill)
                        assigned = True
                        break

            if not assigned:
                for pattern in database_patterns:
                    if re.search(pattern, skill, re.IGNORECASE):
                        categorized["Databases"].append(skill)
                        assigned = True
                        break

            if not assigned:
                for pattern in cloud_patterns:
                    if re.search(pattern, skill, re.IGNORECASE):
                        categorized["Cloud & DevOps"].append(skill)
                        assigned = True
                        break

            if not assigned:
                for pattern in soft_patterns:
                    if re.search(pattern, skill, re.IGNORECASE):
                        categorized["Soft Skills"].append(skill)
                        assigned = True
                        break

            if not assigned:
                categorized["Other"].append(skill)

        return categorized

    def add_skill_mapping(self, canonical: str, variations: List[str]):
        """Add new skill mapping at runtime."""
        if canonical not in self.skill_mappings:
            self.skill_mappings[canonical] = []

        self.skill_mappings[canonical].extend(variations)
        self._rebuild_index()

    def learn_from_user_input(self, original: str, corrected: str):
        """Learn new mappings from user corrections."""
        # Store user corrections for future use
        self.user_corrections[original.lower()] = corrected

    def _rebuild_index(self):
        """Rebuild the canonical skills index after updates."""
        self.canonical_skills = self._build_canonical_index()


class ConsolidationEngine:
    """Consolidates data from multiple parsed documents."""

    def __init__(self):
        """Initialize consolidation engine."""
        self.skill_mapper = SkillMapper()
        self.conflict_resolver = ConflictResolverUI()
        logger.info("ConsolidationEngine initialized with conflict resolver")

    def consolidate(
        self, parsed_data: List[Any]
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Consolidate parsed data and identify conflicts.
        Legacy method for backward compatibility.
        """
        if not parsed_data:
            return {}, []

        # Convert ParsedData objects to dicts if needed
        data_dicts = []
        for item in parsed_data:
            if hasattr(item, "content"):  # ParsedData object
                data_dict = item.content.copy()
                data_dict["source_file"] = item.source_file
                data_dicts.append(data_dict)
            else:  # Already a dict
                data_dicts.append(item)

        # Start with first document as base
        consolidated = self._initialize_base_structure(data_dicts[0])
        conflicts = []

        # Merge additional documents
        for i, document_data in enumerate(data_dicts[1:], 1):
            document_conflicts = self._merge_document(consolidated, document_data, i)
            conflicts.extend(document_conflicts)

        # Consolidate skills using bilingual mapping
        consolidated["skills"] = self._consolidate_skills(
            consolidated.get("skills", [])
        )

        logger.info(
            f"Consolidated data from {len(parsed_data)} documents with {len(conflicts)} conflicts"
        )
        return consolidated, conflicts

    def consolidate_with_resolution(
        self, parsed_data_list: List[ParsedData], auto_resolve: bool = False
    ) -> ConsolidatedData:
        """
        Merge data with interactive conflict resolution.

        Args:
            parsed_data_list: List of ParsedData objects
            auto_resolve: If True, automatically resolve conflicts using smart defaults

        Returns:
            ConsolidatedData object with resolved conflicts
        """
        if not parsed_data_list:
            return ConsolidatedData(data={}, conflicts_resolved=0, source_documents=[])

        # Detect all conflicts
        conflicts = self._detect_conflicts(parsed_data_list)

        # Resolve conflicts interactively or automatically
        if conflicts:
            if auto_resolve:
                resolutions = self._auto_resolve_conflicts(conflicts)
            else:
                resolutions = self.conflict_resolver.resolve_conflicts(conflicts)

            # Apply resolutions and merge
            consolidated = self._apply_resolutions(parsed_data_list, resolutions)
            conflicts_resolved = len(conflicts)
        else:
            # No conflicts, simple merge
            consolidated = self._simple_merge(parsed_data_list)
            conflicts_resolved = 0

        # Extract source documents
        source_documents = [pd.source_file for pd in parsed_data_list]

        return ConsolidatedData(
            data=consolidated,
            conflicts_resolved=conflicts_resolved,
            source_documents=source_documents,
        )

    def _detect_conflicts(self, parsed_data_list: List[ParsedData]) -> List[Conflict]:
        """Detect conflicts across all parsed data."""
        conflicts = []

        # Check for name conflicts
        names = []
        for pd in parsed_data_list:
            personal_info = self._extract_personal_info(pd.content)
            if personal_info["name"] != "Unknown":
                names.append((personal_info["name"], pd.source_file))

        if len(set(name for name, _ in names)) > 1:
            variations = [
                Variation(content=name, source_file=source) for name, source in names
            ]
            conflicts.append(
                Conflict(
                    entity_id="personal_info.name",
                    field="Name",
                    variations=variations,
                    conflict_type="name_conflict",
                )
            )

        # Check for job title conflicts
        job_titles = []
        for pd in parsed_data_list:
            if "work_experience" in pd.content and pd.content["work_experience"]:
                for job in pd.content["work_experience"]:
                    if "title" in job:
                        job_titles.append((job["title"], pd.source_file))

        # Group similar job titles and detect conflicts
        if job_titles:
            unique_titles = {}
            for title, source in job_titles:
                # Simple grouping by first word
                key = title.split()[0] if title else "unknown"
                if key not in unique_titles:
                    unique_titles[key] = []
                unique_titles[key].append((title, source))

            # Create conflicts for groups with different titles
            for key, title_list in unique_titles.items():
                if len(set(title for title, _ in title_list)) > 1:
                    variations = [
                        Variation(content=title, source_file=source)
                        for title, source in title_list
                    ]
                    conflicts.append(
                        Conflict(
                            entity_id=f"job_title.{key}",
                            field=f"Job Title ({key})",
                            variations=variations,
                            conflict_type="job_title_conflict",
                        )
                    )

        # Check for date conflicts in work experience
        checked_companies = set()
        for pd in parsed_data_list:
            if "work_experience" in pd.content:
                for i, job in enumerate(pd.content["work_experience"]):
                    company = job.get("company", "")
                    if not company or company in checked_companies:
                        continue

                    # Check for different date formats or values
                    if "dates" in job:
                        date_variations = []
                        for check_pd in parsed_data_list:
                            if "work_experience" in check_pd.content:
                                for check_job in check_pd.content["work_experience"]:
                                    # Simple comparison by company name
                                    if check_job.get("company") == company:
                                        date_entry = (
                                            check_job.get("dates", ""),
                                            check_pd.source_file,
                                        )
                                        if date_entry not in date_variations:
                                            date_variations.append(date_entry)

                        # Only create conflict if there are different dates
                        unique_dates = set(date for date, _ in date_variations)
                        if len(unique_dates) > 1:
                            variations = [
                                Variation(content=date, source_file=source)
                                for date, source in date_variations
                            ]
                            conflicts.append(
                                Conflict(
                                    entity_id=f"work_experience.{company}.dates",
                                    field=f"Employment Dates at {company}",
                                    variations=variations,
                                    conflict_type="date_conflict",
                                )
                            )
                            checked_companies.add(company)

        return conflicts

    def _auto_resolve_conflicts(self, conflicts: List[Conflict]) -> Dict[str, Any]:
        """Automatically resolve conflicts using smart defaults."""
        resolutions = {}

        for conflict in conflicts:
            # Use the most detailed variation
            best_variation = None
            max_score = -1

            for var in conflict.variations:
                score = len(str(var.content))

                # Bonus for structured data
                if isinstance(var.content, (dict, list)):
                    score += 500

                if score > max_score:
                    max_score = score
                    best_variation = var

            if best_variation:
                resolutions[conflict.entity_id] = best_variation.content

        return resolutions

    def _apply_resolutions(
        self, parsed_data_list: List[ParsedData], resolutions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply conflict resolutions and merge data."""
        # Start with base structure
        if not parsed_data_list:
            return {}

        consolidated = self._initialize_base_structure(parsed_data_list[0].content)

        # Apply resolutions
        for entity_id, resolved_value in resolutions.items():
            keys = entity_id.split(".")
            current = consolidated

            # Navigate to parent
            for i, key in enumerate(keys[:-1]):
                # Handle list indices
                if isinstance(current, list):
                    continue

                if key not in current:
                    # Check if next key is numeric (list index)
                    if i + 1 < len(keys) - 1 and keys[i + 1].isdigit():
                        current[key] = []
                    else:
                        current[key] = {}
                current = current[key]

            # Set resolved value
            final_key = keys[-1]
            if isinstance(current, dict):
                current[final_key] = resolved_value

        # Merge remaining non-conflicting data
        for pd in parsed_data_list[1:]:
            # Merge work experience
            if "work_experience" in pd.content:
                if "work_experience" not in consolidated:
                    consolidated["work_experience"] = []
                consolidated["work_experience"].extend(pd.content["work_experience"])

            # Merge education
            if "education" in pd.content:
                if "education" not in consolidated:
                    consolidated["education"] = []
                consolidated["education"].extend(pd.content["education"])

            # Merge skills
            if "skills" in pd.content:
                if "skills" not in consolidated:
                    consolidated["skills"] = []
                consolidated["skills"].extend(pd.content["skills"])

            # Merge projects
            if "projects" in pd.content:
                if "projects" not in consolidated:
                    consolidated["projects"] = []
                consolidated["projects"].extend(pd.content["projects"])

        # Consolidate and deduplicate
        if "skills" in consolidated:
            consolidated["skills"] = self._consolidate_skills(consolidated["skills"])

        return consolidated

    def _simple_merge(self, parsed_data_list: List[ParsedData]) -> Dict[str, Any]:
        """Simple merge when no conflicts exist."""
        if not parsed_data_list:
            return {}

        consolidated = self._initialize_base_structure(parsed_data_list[0].content)

        for pd in parsed_data_list[1:]:
            # Merge all sections
            for key in ["work_experience", "education", "skills", "projects"]:
                if key in pd.content:
                    if key not in consolidated:
                        consolidated[key] = []
                    consolidated[key].extend(pd.content[key])

        # Consolidate skills
        if "skills" in consolidated:
            consolidated["skills"] = self._consolidate_skills(consolidated["skills"])

        return consolidated

    def _initialize_base_structure(self, base_doc: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize consolidated structure with base document."""
        return {
            "personal_info": self._extract_personal_info(base_doc),
            "work_experience": base_doc.get("work_experience", []),
            "education": base_doc.get("education", []),
            "skills": base_doc.get("skills", []),
            "projects": base_doc.get("projects", []),
            "source_documents": [base_doc.get("source_file", "unknown")],
        }

    def _extract_personal_info(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract personal information from document."""
        # Basic extraction - would be enhanced with NER
        entities = document_data.get("entities", [])
        persons = [e for e in entities if e.get("label") == "PERSON"]

        return {"name": persons[0]["text"] if persons else "Unknown", "contact": {}}

    def _merge_document(
        self, consolidated: Dict[str, Any], new_doc: Dict[str, Any], doc_index: int
    ) -> List[Dict[str, Any]]:
        """Merge new document into consolidated data and track conflicts."""
        conflicts = []

        # Add to source documents
        consolidated["source_documents"].append(
            new_doc.get("source_file", f"document_{doc_index}")
        )

        # Merge work experience
        consolidated["work_experience"].extend(new_doc.get("work_experience", []))

        # Merge education
        consolidated["education"].extend(new_doc.get("education", []))

        # Merge skills
        consolidated["skills"].extend(new_doc.get("skills", []))

        # Merge projects
        consolidated["projects"].extend(new_doc.get("projects", []))

        # Check for name conflicts (placeholder)
        current_name = consolidated["personal_info"]["name"]
        new_name = self._extract_personal_info(new_doc)["name"]
        if (
            current_name != "Unknown"
            and new_name != "Unknown"
            and current_name != new_name
        ):
            conflicts.append(
                {
                    "type": "name_conflict",
                    "field": "personal_info.name",
                    "values": [current_name, new_name],
                    "sources": [
                        consolidated["source_documents"][0],
                        new_doc.get("source_file"),
                    ],
                }
            )

        return conflicts

    def _consolidate_skills(self, skills: List[str]) -> List[str]:
        """Consolidate skills using bilingual mapping."""
        if not skills:
            return []

        # Convert to SkillEntry objects with dummy sources
        skill_entries = []
        for i, skill in enumerate(skills):
            skill_entries.append(
                SkillEntry(
                    name=skill,
                    source_reference=f"consolidated_source_{i}",
                    category=None,
                )
            )

        # Map and consolidate
        skill_inventory = self.skill_mapper.map_skills(skill_entries)

        # Return just the skill names for backward compatibility
        return sorted(list(skill_inventory.keys()))

    def consolidate_skills(self, parsed_data_list: List[ParsedData]) -> Dict[str, Any]:
        """Extract and map all skills from parsed data."""

        # Collect all skills from all sources
        all_skills = []
        for i, data in enumerate(parsed_data_list):
            skills_list = data.content.get("skills", [])
            for skill in skills_list:
                all_skills.append(
                    SkillEntry(
                        name=skill,
                        source_reference=f"document_{i}_{data.source_file}",
                        category=self._infer_category(skill),
                    )
                )

        # Map and consolidate
        skill_inventory = self.skill_mapper.map_skills(all_skills)

        # Organize by category
        categorized = self._categorize_inventory(skill_inventory)

        return categorized

    def _infer_category(self, skill: str) -> Optional[str]:
        """Infer category for a skill based on patterns."""
        skill_lower = skill.lower()

        # Technical skills
        if any(
            tech in skill_lower
            for tech in ["python", "java", "javascript", "c++", "c#"]
        ):
            return "Programming Languages"
        elif any(fw in skill_lower for fw in ["react", "angular", "django", "flask"]):
            return "Frameworks & Libraries"
        elif any(db in skill_lower for db in ["sql", "mysql", "postgresql", "mongodb"]):
            return "Databases"
        elif any(
            cloud in skill_lower for cloud in ["aws", "azure", "docker", "kubernetes"]
        ):
            return "Cloud & DevOps"
        elif any(
            soft in skill_lower
            for soft in ["leadership", "communication", "management"]
        ):
            return "Soft Skills"
        else:
            return "Other"

    def _categorize_inventory(
        self, skill_inventory: Dict[str, SkillInventoryEntry]
    ) -> Dict[str, Any]:
        """Organize skill inventory by categories."""
        categorized = {
            "Programming Languages": {},
            "Frameworks & Libraries": {},
            "Databases": {},
            "Cloud & DevOps": {},
            "Soft Skills": {},
            "Domain Expertise": {},
            "Tools": {},
            "Other": {},
        }

        for skill_name, skill_entry in skill_inventory.items():
            # Use existing categories if available, otherwise infer
            if skill_entry.categories:
                for category in skill_entry.categories:
                    if category in categorized:
                        categorized[category][skill_name] = skill_entry.to_dict()
                    else:
                        categorized["Other"][skill_name] = skill_entry.to_dict()
            else:
                # Infer category
                inferred_category = self._infer_category(skill_name)
                if inferred_category in categorized:
                    categorized[inferred_category][skill_name] = skill_entry.to_dict()
                else:
                    categorized["Other"][skill_name] = skill_entry.to_dict()

        # Remove empty categories
        return {k: v for k, v in categorized.items() if v}
