"""Output generation module for final JSON database creation."""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import re

from jsonschema import validate, ValidationError
from rich.console import Console
from rich.panel import Panel

from ..schemas.master_schema import MASTER_SCHEMA


class OutputGenerator:
    """Generates the final JSON output from consolidated data."""

    def __init__(self, output_dir: Path = None):
        """Initialize output generator.

        Args:
            output_dir: Directory for output files. Defaults to 'output'
        """
        self.console = Console()
        self._logger = logging.getLogger(__name__)
        self.output_dir = output_dir or Path("output")
        self.output_dir.mkdir(exist_ok=True)

    def generate_json(self, consolidated_data: Dict[str, Any]) -> Path:
        """Generate and save the final JSON output.

        Args:
            consolidated_data: Consolidated data from ConsolidationEngine

        Returns:
            Path to the generated JSON file

        Raises:
            ValidationError: If data doesn't match schema
            IOError: If file writing fails
        """
        self._logger.info("Starting JSON output generation")

        # Transform data to match schema
        final_data = self._transform_to_schema(consolidated_data)

        # Validate against schema
        validated_data = self._validate_data(final_data)

        # Enrich with metadata
        enriched_data = self._add_metadata(validated_data, consolidated_data)

        # Create backup
        self._create_backup(enriched_data)

        # Write to file
        output_path = self._write_json(enriched_data)

        # Display success message
        self._display_success(output_path, enriched_data)

        self._logger.info(f"JSON output generated successfully: {output_path}")
        return output_path

    def _transform_to_schema(self, raw_data: Dict) -> Dict:
        """Transform consolidated data to match schema structure.

        Args:
            raw_data: Raw consolidated data

        Returns:
            Schema-compliant data structure
        """
        self._logger.debug("Transforming data to schema format")

        transformed = {
            "work_experience": self._transform_work_experience(raw_data),
            "projects": self._transform_projects(raw_data),
            "skills_inventory": self._transform_skills(raw_data),
            "strategic_metadata": self._generate_strategic_metadata(raw_data),
            "holistic_profile": raw_data.get("holistic_profile", {}),
        }

        return transformed

    def _transform_work_experience(self, data: Dict) -> List[Dict]:
        """Transform work experience to schema format.

        Args:
            data: Raw data containing work experience

        Returns:
            List of transformed work experiences
        """
        experiences = []

        for exp in data.get("work_experience", []):
            transformed_exp = {
                "role": exp.get("role", ""),
                "company": exp.get("company", ""),
                "dates": exp.get("dates", ""),
                "description": exp.get("description", ""),
                "accomplishments": [],
            }

            # Process accomplishments
            for acc in exp.get("accomplishments", []):
                accomplishment = {
                    "original": acc,
                    "deconstructed": self._deconstruct_accomplishment(acc),
                    "metrics": self._extract_metrics(acc),
                    "associated_skills": self._extract_skills_from_text(acc),
                    "impact_score": self._calculate_impact_score(acc),
                }
                transformed_exp["accomplishments"].append(accomplishment)

            experiences.append(transformed_exp)

        return experiences

    def _transform_projects(self, data: Dict) -> List[Dict]:
        """Transform projects to schema format.

        Args:
            data: Raw data containing projects

        Returns:
            List of transformed projects
        """
        projects = []

        for project in data.get("projects", []):
            transformed_project = {
                "name": project.get("name", ""),
                "description": project.get("description", ""),
                "technologies": project.get("technologies", []),
                "outcomes": project.get("outcomes", []),
            }
            projects.append(transformed_project)

        return projects

    def _transform_skills(self, data: Dict) -> Dict[str, List[Dict]]:
        """Transform skills to schema format with evidence pointers.

        Args:
            data: Raw data containing skills

        Returns:
            Skills inventory with evidence pointers
        """
        skills_inventory = {}
        skills_data = data.get("skills", {})

        for category, skills_list in skills_data.items():
            skills_inventory[category] = []

            for skill in skills_list:
                skill_entry = {
                    "skill": skill,
                    "evidence_pointers": self._find_evidence_pointers(skill, data),
                }
                skills_inventory[category].append(skill_entry)

        return skills_inventory

    def _find_evidence_pointers(self, skill: str, data: Dict) -> List[str]:
        """Find evidence of skill usage in work experience and projects.

        Args:
            skill: Skill to find evidence for
            data: Complete data to search through

        Returns:
            List of evidence pointer strings
        """
        evidence = []
        skill_lower = skill.lower()

        # Search in work experience
        for i, exp in enumerate(data.get("work_experience", [])):
            company = exp.get("company", "")

            # Check description
            if skill_lower in exp.get("description", "").lower():
                evidence.append(f"Work experience at {company}")

            # Check accomplishments
            for j, acc in enumerate(exp.get("accomplishments", [])):
                if skill_lower in acc.lower():
                    evidence.append(f"Accomplishment at {company}")

        # Search in projects
        for project in data.get("projects", []):
            project_name = project.get("name", "")

            # Check technologies
            if skill in project.get("technologies", []):
                evidence.append(f"Project: {project_name}")

            # Check description
            if skill_lower in project.get("description", "").lower():
                evidence.append(f"Project: {project_name}")

        return evidence[:3]  # Limit to top 3 evidence points

    def _deconstruct_accomplishment(self, text: str) -> Dict[str, str]:
        """Break down accomplishment into action, challenge, outcome.

        Args:
            text: Accomplishment text

        Returns:
            Dictionary with action, challenge, outcome components
        """
        parts = {"action": "", "challenge": "", "outcome": ""}

        # Look for action verbs
        action_verbs = [
            "led",
            "developed",
            "implemented",
            "designed",
            "managed",
            "created",
            "built",
            "optimized",
            "improved",
            "delivered",
            "achieved",
            "reduced",
            "increased",
            "established",
            "coordinated",
            "supervised",
            "analyzed",
        ]

        for verb in action_verbs:
            if verb.lower() in text.lower():
                parts["action"] = verb.capitalize()
                break

        # Look for result indicators
        result_patterns = [
            r"resulting in (.+?)(?:\.|$)",
            r"achieved (.+?)(?:\.|$)",
            r"leading to (.+?)(?:\.|$)",
            r"which (.+?)(?:\.|$)",
        ]

        for pattern in result_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                parts["outcome"] = match.group(1).strip()
                break

        # The challenge is the main context (simplified approach)
        if not parts["outcome"]:
            parts["challenge"] = text[:100] + "..." if len(text) > 100 else text
        else:
            # Extract the part before the outcome
            outcome_pos = text.lower().find(parts["outcome"].lower())
            if outcome_pos > 0:
                parts["challenge"] = text[:outcome_pos].strip()

        return parts

    def _extract_metrics(self, text: str) -> Dict[str, Any]:
        """Extract quantifiable metrics from accomplishment text.

        Args:
            text: Text to extract metrics from

        Returns:
            Dictionary of extracted metrics
        """
        metrics = {}

        # Common metric patterns
        patterns = {
            "percentage": r"(\d+(?:\.\d+)?)%",
            "dollar_amount": r"\$(\d+(?:,\d{3})*(?:\.\d{2})?)[KkMmBb]?",
            "number": r"(\d+(?:,\d{3})*)",
            "time_period": r"(\d+)\s+(days?|weeks?|months?|years?)",
        }

        for metric_type, pattern in patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                metrics[metric_type] = matches

        return metrics

    def _extract_skills_from_text(self, text: str) -> List[str]:
        """Extract potential skills mentioned in accomplishment text.

        Args:
            text: Text to extract skills from

        Returns:
            List of potential skills
        """
        # Common skill indicators (simplified approach)
        tech_keywords = [
            "Python",
            "Java",
            "JavaScript",
            "React",
            "Node.js",
            "SQL",
            "AWS",
            "Docker",
            "Kubernetes",
            "Git",
            "API",
            "REST",
            "GraphQL",
            "MongoDB",
            "PostgreSQL",
            "machine learning",
            "AI",
            "data analysis",
            "leadership",
            "management",
        ]

        found_skills = []
        text_lower = text.lower()

        for skill in tech_keywords:
            if skill.lower() in text_lower:
                found_skills.append(skill)

        return found_skills[:5]  # Limit to top 5

    def _calculate_impact_score(self, text: str) -> float:
        """Calculate impact score based on accomplishment content.

        Args:
            text: Accomplishment text

        Returns:
            Impact score between 0 and 10
        """
        score = 0.0
        text_lower = text.lower()

        # Quantifiable results
        if re.search(r"\d+%", text):
            score += 2.0
        if re.search(r"\$\d+", text):
            score += 2.0
        if re.search(r"\d+(?:,\d{3})*", text):
            score += 1.0

        # Impact words
        impact_words = [
            "improved",
            "increased",
            "reduced",
            "optimized",
            "enhanced",
            "achieved",
            "delivered",
            "successful",
            "exceeded",
        ]
        for word in impact_words:
            if word in text_lower:
                score += 0.5

        # Leadership indicators
        leadership_words = ["led", "managed", "supervised", "coordinated"]
        for word in leadership_words:
            if word in text_lower:
                score += 1.0

        # Cap at 10
        return min(score, 10.0)

    def _generate_strategic_metadata(self, data: Dict) -> Dict[str, Any]:
        """Generate strategic metadata from the data.

        Args:
            data: Complete consolidated data

        Returns:
            Strategic metadata dictionary
        """
        metadata = {
            "job_title_variations": self._extract_title_variations(data),
            "top_anchor_accomplishments": self._identify_top_accomplishments(data),
            "core_competencies": self._identify_core_competencies(data),
        }

        return metadata

    def _extract_title_variations(self, data: Dict) -> List[str]:
        """Extract all unique job titles and variations.

        Args:
            data: Data containing work experience

        Returns:
            List of job title variations
        """
        titles = set()

        for exp in data.get("work_experience", []):
            role = exp.get("role", "")
            if role:
                titles.add(role)

                # Generate common variations
                base_title = role
                variations = [
                    base_title.replace("Senior", "Lead"),
                    base_title.replace("Senior", "Principal"),
                    base_title.replace("Engineer", "Developer"),
                    base_title.replace("Developer", "Engineer"),
                    base_title.replace("Manager", "Lead"),
                ]

                for variation in variations:
                    if variation != base_title:
                        titles.add(variation)

        return list(titles)

    def _identify_top_accomplishments(self, data: Dict) -> List[str]:
        """Identify the most impactful accomplishments.

        Args:
            data: Data containing work experience

        Returns:
            List of top accomplishments
        """
        all_accomplishments = []

        for exp in data.get("work_experience", []):
            for acc in exp.get("accomplishments", []):
                score = self._calculate_impact_score(acc)
                all_accomplishments.append((acc, score))

        # Sort by impact score and take top 5
        all_accomplishments.sort(key=lambda x: x[1], reverse=True)

        return [acc[0] for acc in all_accomplishments[:5]]

    def _identify_core_competencies(self, data: Dict) -> List[str]:
        """Identify core competencies from skills and experience.

        Args:
            data: Complete data

        Returns:
            List of core competencies
        """
        competencies = []

        # Get most frequent skills
        all_skills = []
        for skills_list in data.get("skills", {}).values():
            all_skills.extend(skills_list)

        # Count skill frequency
        skill_counts = {}
        for skill in all_skills:
            skill_counts[skill] = skill_counts.get(skill, 0) + 1

        # Get top skills
        top_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)
        competencies.extend([skill for skill, _ in top_skills[:10]])

        return competencies

    def _validate_data(self, data: Dict) -> Dict:
        """Validate data against schema.

        Args:
            data: Data to validate

        Returns:
            Validated data (possibly with fixes applied)

        Raises:
            ValidationError: If validation fails and can't be auto-fixed
        """
        try:
            validate(instance=data, schema=MASTER_SCHEMA)
            self.console.print("[green]✓ Data validation passed[/green]")
            return data
        except ValidationError as e:
            self._logger.warning(f"Validation error: {e.message}")
            self.console.print(f"[red]✗ Validation error: {e.message}[/red]")

            # Attempt to fix common issues
            fixed_data = self._attempt_auto_fix(data, e)
            if fixed_data:
                self.console.print("[yellow]⚠ Applied automatic fixes[/yellow]")
                validate(instance=fixed_data, schema=MASTER_SCHEMA)
                return fixed_data
            else:
                raise e

    def _attempt_auto_fix(self, data: Dict, error: ValidationError) -> Optional[Dict]:
        """Try to automatically fix validation errors.

        Args:
            data: Data with validation errors
            error: Validation error details

        Returns:
            Fixed data if possible, None otherwise
        """
        fixed_data = data.copy()

        # Common fixes for missing required properties
        if "is a required property" in str(error):
            if "work_experience" not in fixed_data:
                fixed_data["work_experience"] = []
            if "skills_inventory" not in fixed_data:
                fixed_data["skills_inventory"] = {}
            if "holistic_profile" not in fixed_data:
                fixed_data["holistic_profile"] = {}
            if "strategic_metadata" not in fixed_data:
                fixed_data["strategic_metadata"] = {
                    "job_title_variations": [],
                    "top_anchor_accomplishments": [],
                    "core_competencies": [],
                }

            return fixed_data

        # Fix type mismatches
        if "is not of type" in str(error):
            # This would require more specific handling based on the error path
            self._logger.debug("Type mismatch detected, manual fix required")
            return None

        return None

    def _add_metadata(self, data: Dict, original_data: Dict) -> Dict:
        """Add metadata to the final output.

        Args:
            data: Schema-compliant data
            original_data: Original consolidated data for reference

        Returns:
            Data with metadata added
        """
        metadata = {
            "generated_at": datetime.now().isoformat(),
            "version": "1.0",
            "source_files": original_data.get("source_files", []),
            "statistics": {
                "total_work_experiences": len(data.get("work_experience", [])),
                "total_projects": len(data.get("projects", [])),
                "total_skills": sum(
                    len(skills) for skills in data.get("skills_inventory", {}).values()
                ),
                "processing_metadata": original_data.get("processing_metadata", {}),
            },
        }

        data["_metadata"] = metadata
        return data

    def _create_backup(self, data: Dict) -> None:
        """Create backup before writing main file.

        Args:
            data: Data to backup
        """
        timestamp = datetime.now().timestamp()
        backup_path = self.output_dir / f".backup_{timestamp}.json"

        try:
            with open(backup_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            self._logger.debug(f"Backup created: {backup_path}")

            # Clean old backups (keep last 5)
            backups = sorted(self.output_dir.glob(".backup_*.json"))
            for old_backup in backups[:-5]:
                old_backup.unlink()
                self._logger.debug(f"Removed old backup: {old_backup}")

        except Exception as e:
            self._logger.warning(f"Failed to create backup: {e}")

    def _write_json(self, data: Dict) -> Path:
        """Write JSON to file with proper formatting.

        Args:
            data: Data to write

        Returns:
            Path to written file

        Raises:
            IOError: If file writing fails
        """
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"master_career_database_{timestamp}.json"
        output_path = self.output_dir / filename

        # Also create a "latest" version
        latest_path = self.output_dir / "master_career_database.json"

        try:
            # Write timestamped version
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(
                    data,
                    f,
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=False,  # Preserve logical ordering
                )

            # Write latest version
            with open(latest_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=False)

            self._logger.info(f"JSON files written: {output_path}, {latest_path}")
            return output_path

        except Exception as e:
            self._logger.error(f"Failed to write JSON file: {e}")
            raise IOError(f"Failed to write JSON file: {e}")

    def _display_success(self, output_path: Path, data: Dict) -> None:
        """Display success message with statistics.

        Args:
            output_path: Path to generated file
            data: Generated data for statistics
        """
        stats = {
            "Work Experiences": len(data.get("work_experience", [])),
            "Projects": len(data.get("projects", [])),
            "Skills": sum(
                len(skills) for skills in data.get("skills_inventory", {}).values()
            ),
            "Transversal Projects": len(
                data.get("holistic_profile", {}).get("transversal_projects", [])
            ),
            "File Size": f"{output_path.stat().st_size / 1024:.1f} KB",
        }

        # Create summary lines
        summary_lines = [f"{key}: {value}" for key, value in stats.items()]

        latest_file = output_path.parent / "master_career_database.json"
        self.console.print(
            Panel.fit(
                "\n".join(
                    [
                        "[bold green]✓ Database successfully generated![/bold green]",
                        "",
                        *summary_lines,
                        "",
                        f"[cyan]Output: {output_path}[/cyan]",
                        f"[cyan]Latest: {latest_file}[/cyan]",
                    ]
                ),
                title="Success",
                border_style="green",
            )
        )
