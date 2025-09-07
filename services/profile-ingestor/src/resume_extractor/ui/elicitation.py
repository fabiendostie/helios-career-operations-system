"""
Interactive elicitation UI for gathering additional qualitative data.
"""

import logging
import pickle
from typing import Dict, Any, List, Optional
from pathlib import Path

import questionary
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn


logger = logging.getLogger(__name__)


class ElicitationUI:
    """Interactive UI for gathering additional career information."""

    def __init__(self):
        """Initialize elicitation UI."""
        self.console = Console()
        self.elicited_data = {
            "transversal_projects": [],
            "professional_aspirations": {},
            "core_motivators": [],
            "personal_qualities": [],
        }
        logger.info("ElicitationUI initialized")

    def conduct_interview(self, existing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Conduct the full elicitation interview."""
        logger.info("Starting interactive elicitation interview")

        # Check for previous progress
        previous_data = self._load_progress()
        if previous_data:
            self.elicited_data.update(previous_data)

        self._show_welcome_message()

        # Interview sections
        sections = [
            ("Transversal Projects", self._elicit_transversal_projects),
            ("Professional Aspirations", self._elicit_aspirations),
            ("Core Motivators", self._elicit_motivators),
            ("Personal Qualities", self._elicit_qualities),
        ]

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:

            main_task = progress.add_task(
                "[cyan]Interview Progress", total=len(sections)
            )

            for section_name, elicitation_func in sections:
                progress.update(main_task, description=f"Section: {section_name}")

                elicitation_func(existing_data)
                self._save_progress()
                progress.advance(main_task)

        self._show_completion_summary()
        self._cleanup_progress()

        return self.elicited_data

    def _show_welcome_message(self):
        """Display welcome message and instructions."""
        welcome_text = (
            "[bold cyan]Welcome to the Career Profile Interview![/bold cyan]\n\n"
            "This interview will help us gather qualitative information that "
            "complements your formal resume data. We'll explore:\n\n"
            "• Side projects and initiatives\n"
            "• Career aspirations and goals\n"
            "• What motivates you professionally\n"
            "• Your key personal qualities\n\n"
            "[dim]The interview is saved automatically, so you can resume if interrupted.[/dim]"
        )

        self.console.print(
            Panel.fit(
                welcome_text, title="🎯 Career Profile Enhancement", border_style="cyan"
            )
        )
        self.console.print()

    def _elicit_transversal_projects(self, existing_data: Dict[str, Any]):
        """Gather information about side projects and initiatives."""

        self.console.print(
            Panel.fit(
                "[bold]Let's talk about projects outside your main work[/bold]\n"
                "These could be open source, personal projects, volunteering, etc.",
                title="🚀 Transversal Projects",
            )
        )

        add_more = True
        while add_more:
            project = self._get_project_details()

            if project:
                self.elicited_data["transversal_projects"].append(project)
                self._display_captured_project(project)

            add_more = questionary.confirm(
                "Would you like to add another project?", default=False
            ).ask()

    def _get_project_details(self) -> Optional[Dict[str, Any]]:
        """Get details for a single project."""

        # Project name
        name = questionary.text(
            "Project name:",
            validate=lambda x: len(x) > 0 if x else "Project name is required",
        ).ask()

        if not name:
            return None

        # Project description
        description = self._get_multiline_input(
            "Describe the project (what it does, your role, impact):"
        )

        # Technologies/Skills
        skills_raw = questionary.text(
            "Key skills/technologies used (comma-separated):", default=""
        ).ask()

        skills = [s.strip() for s in skills_raw.split(",") if s.strip()]

        # Link (optional)
        link = questionary.text(
            "Project link (GitHub, website, etc.) - optional:", default=""
        ).ask()

        return {
            "name": name,
            "description": description,
            "skills_demonstrated": skills,
            "link": link if link else None,
        }

    def _display_captured_project(self, project: Dict[str, Any]):
        """Display what was captured for a project."""
        self.console.print(f"[green]✓ Added project: {project['name']}[/green]")
        if project.get("skills_demonstrated"):
            skills_text = ", ".join(project["skills_demonstrated"])
            self.console.print(f"[dim]  Skills: {skills_text}[/dim]")

    def _elicit_aspirations(self, existing_data: Dict[str, Any]):
        """Gather career goals and aspirations."""

        self.console.print(
            Panel.fit(
                "[bold]Let's explore your professional aspirations[/bold]\n"
                "Understanding where you want to go helps shape your narrative",
                title="🎯 Professional Aspirations",
            )
        )

        # Target roles
        target_roles = self._get_list_input(
            "What roles are you targeting?",
            "Enter role (or press Enter to finish):",
            min_items=1,
            suggestions=self._suggest_roles_from_data(existing_data),
        )

        # Industries of interest
        industries = self._get_list_input(
            "Which industries interest you?",
            "Enter industry (or press Enter to finish):",
            min_items=1,
            suggestions=[
                "Technology",
                "Finance",
                "Healthcare",
                "Education",
                "Consulting",
            ],
        )

        # Technologies to learn
        tech_to_learn = self._get_list_input(
            "What technologies/skills do you want to learn?",
            "Enter technology/skill (or press Enter to finish):",
            min_items=0,
        )

        self.elicited_data["professional_aspirations"] = {
            "target_roles": target_roles,
            "industries_of_interest": industries,
            "technologies_to_learn": tech_to_learn,
        }

    def _suggest_roles_from_data(self, existing_data: Dict[str, Any]) -> List[str]:
        """Generate role suggestions based on parsed work experience."""
        suggestions = []

        if "work_experience" in existing_data:
            for exp in existing_data["work_experience"]:
                if "role" in exp:
                    # Suggest next level roles
                    role = exp["role"]
                    if "Senior" in role:
                        suggestions.append(role.replace("Senior", "Lead"))
                        suggestions.append(role.replace("Senior", "Principal"))
                    elif "Junior" in role:
                        suggestions.append(role.replace("Junior", ""))
                        suggestions.append(role.replace("Junior", "Senior"))

        return list(set(suggestions))  # Remove duplicates

    def _elicit_motivators(self, existing_data: Dict[str, Any]):
        """Identify what drives the user professionally."""

        self.console.print(
            Panel.fit(
                "[bold]What motivates you in your work?[/bold]\n"
                "Understanding your drivers helps align opportunities",
                title="💡 Core Motivators",
            )
        )

        # Predefined motivator categories with examples
        motivator_prompts = [
            {
                "category": "Impact",
                "prompt": "How important is making a direct impact? (e.g., 'Building products that help millions')",
                "examples": ["Social impact", "User satisfaction", "Business growth"],
            },
            {
                "category": "Learning",
                "prompt": "What about continuous learning and growth?",
                "examples": [
                    "New technologies",
                    "Domain expertise",
                    "Leadership skills",
                ],
            },
            {
                "category": "Challenge",
                "prompt": "Do you thrive on solving complex problems?",
                "examples": ["Technical challenges", "Scale problems", "Innovation"],
            },
            {
                "category": "Team",
                "prompt": "How important is team dynamics and culture?",
                "examples": ["Mentoring", "Collaboration", "Diverse teams"],
            },
            {
                "category": "Recognition",
                "prompt": "Is professional recognition important?",
                "examples": ["Industry leadership", "Thought leadership", "Awards"],
            },
        ]

        for motivator_info in motivator_prompts:
            response = questionary.text(
                f"{motivator_info['prompt']}\n"
                f"Examples: {', '.join(motivator_info['examples'])}\n"
                "Your response (or skip):",
                default="",
            ).ask()

            if response:
                self.elicited_data["core_motivators"].append(
                    {"category": motivator_info["category"], "description": response}
                )

    def _elicit_qualities(self, existing_data: Dict[str, Any]):
        """Capture personal qualities and soft skills."""

        self.console.print(
            Panel.fit(
                "[bold]Let's identify your key personal qualities[/bold]\n"
                "These differentiate you beyond technical skills",
                title="⭐ Personal Qualities",
            )
        )

        # Guide user with examples
        quality_categories = [
            "Leadership",
            "Communication",
            "Problem-solving",
            "Creativity",
            "Adaptability",
            "Attention to detail",
            "Empathy",
            "Strategic thinking",
            "Resilience",
        ]

        selected_qualities = questionary.checkbox(
            "Select qualities that best describe you:", choices=quality_categories
        ).ask()

        # Get evidence for each selected quality
        for quality in selected_qualities:
            evidence = questionary.text(
                f"Brief example demonstrating your {quality}:",
                validate=lambda x: (
                    len(x) > 10 if x else "Please provide a brief example"
                ),
            ).ask()

            self.elicited_data["personal_qualities"].append(
                {"trait": quality, "evidence": evidence}
            )

        # Allow custom qualities
        add_custom = questionary.confirm(
            "Would you like to add other qualities?", default=False
        ).ask()

        if add_custom:
            self._add_custom_qualities()

    def _add_custom_qualities(self):
        """Add custom personal qualities."""
        while True:
            custom_trait = questionary.text(
                "Enter a personal quality (or press Enter to finish):", default=""
            ).ask()

            if not custom_trait:
                break

            evidence = questionary.text(
                f"Brief example demonstrating your {custom_trait}:",
                validate=lambda x: (
                    len(x) > 10 if x else "Please provide a brief example"
                ),
            ).ask()

            self.elicited_data["personal_qualities"].append(
                {"trait": custom_trait, "evidence": evidence}
            )

            self.console.print(f"[green]✓ Added quality: {custom_trait}[/green]")

    def _get_multiline_input(self, prompt: str) -> str:
        """Get multi-line text input from user."""
        self.console.print(f"[bold]{prompt}[/bold]")
        self.console.print(
            "[dim]Type your response. Press Enter twice to finish.[/dim]"
        )

        lines = []
        consecutive_empty = 0

        while consecutive_empty < 2:
            line = input()
            if line:
                lines.append(line)
                consecutive_empty = 0
            else:
                consecutive_empty += 1
                if consecutive_empty == 1:
                    lines.append("")  # Preserve single line breaks

        # Remove trailing empty lines
        while lines and not lines[-1]:
            lines.pop()

        return "\n".join(lines)

    def _get_list_input(
        self, intro: str, prompt: str, min_items: int = 0, suggestions: List[str] = None
    ) -> List[str]:
        """Get a list of items from user."""

        self.console.print(f"[bold]{intro}[/bold]")

        if suggestions:
            self.console.print(
                "[dim]Suggestions:", ", ".join(suggestions[:5]), "[/dim]"
            )

        items = []
        while True:
            item = questionary.text(prompt, default="").ask()

            if not item:
                if len(items) >= min_items:
                    break
                else:
                    self.console.print(
                        f"[yellow]Please add at least {min_items} item(s)[/yellow]"
                    )
            else:
                items.append(item)
                self.console.print(f"[green]✓ Added: {item}[/green]")

        return items

    def _show_completion_summary(self):
        """Display a summary of what was captured."""
        summary_lines = ["[bold green]Interview Complete![/bold green]\n"]

        if self.elicited_data["transversal_projects"]:
            summary_lines.append(
                f"• {len(self.elicited_data['transversal_projects'])} transversal projects"
            )

        if self.elicited_data["professional_aspirations"]:
            summary_lines.append("• Professional aspirations captured")

        if self.elicited_data["core_motivators"]:
            summary_lines.append(
                f"• {len(self.elicited_data['core_motivators'])} motivators identified"
            )

        if self.elicited_data["personal_qualities"]:
            summary_lines.append(
                f"• {len(self.elicited_data['personal_qualities'])} personal qualities documented"
            )

        summary_text = "\n".join(summary_lines)

        self.console.print(
            Panel.fit(summary_text, title="📋 Summary", border_style="green")
        )

    def _save_progress(self):
        """Save interview progress for recovery."""
        progress_file = Path(".interview_progress.pkl")
        try:
            with open(progress_file, "wb") as f:
                pickle.dump(self.elicited_data, f)
            logger.debug("Progress saved successfully")
        except Exception as e:
            logger.warning(f"Failed to save progress: {e}")

    def _load_progress(self) -> Optional[Dict[str, Any]]:
        """Load previous interview progress if available."""
        progress_file = Path(".interview_progress.pkl")

        if progress_file.exists():
            resume = questionary.confirm(
                "Previous interview session found. Resume from where you left off?",
                default=True,
            ).ask()

            if resume:
                try:
                    with open(progress_file, "rb") as f:
                        data = pickle.load(f)
                    logger.info("Previous progress loaded successfully")
                    return data
                except Exception as e:
                    logger.warning(f"Failed to load progress: {e}")
                    # Clean up corrupted progress file
                    progress_file.unlink(missing_ok=True)

        return None

    def _cleanup_progress(self):
        """Remove progress file after successful completion."""
        progress_file = Path(".interview_progress.pkl")
        progress_file.unlink(missing_ok=True)
        logger.debug("Progress file cleaned up")

    # Legacy method for backward compatibility
    def gather_additional_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Legacy method - redirect to new interview system."""
        logger.info("Legacy method called - redirecting to new interview system")
        elicited = self.conduct_interview(data)

        # Format for legacy system
        enhanced_data = data.copy()
        enhanced_data["holistic_profile"] = elicited

        return enhanced_data
