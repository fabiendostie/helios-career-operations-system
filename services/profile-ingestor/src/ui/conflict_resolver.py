"""
Interactive conflict resolution UI using questionary and Rich.
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import re
import questionary
from rich.console import Console
from rich.table import Table
from rich.panel import Panel


logger = logging.getLogger(__name__)


@dataclass
class Variation:
    """Represents a variation of conflicting data."""
    content: Any
    source_file: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class Conflict:
    """Represents a data conflict to be resolved."""
    entity_id: str
    field: str
    variations: List[Variation]
    conflict_type: str = "generic"


class ResolutionHistory:
    """Manages undo/redo functionality for conflict resolutions."""

    def __init__(self):
        """Initialize resolution history."""
        self.history: List[tuple] = []
        self.current_index: int = -1

    def add_resolution(self, conflict_id: str, resolution: Any) -> None:
        """Add a resolution to history."""
        # Remove any future history if we're not at the end
        if self.current_index < len(self.history) - 1:
            self.history = self.history[:self.current_index + 1]

        self.history.append((conflict_id, resolution))
        self.current_index = len(self.history) - 1

    def undo(self) -> Optional[tuple]:
        """Undo last resolution."""
        if self.current_index > 0:
            self.current_index -= 1
            return self.history[self.current_index]
        return None

    def redo(self) -> Optional[tuple]:
        """Redo previously undone resolution."""
        if self.current_index < len(self.history) - 1:
            self.current_index += 1
            return self.history[self.current_index]
        return None

    def can_undo(self) -> bool:
        """Check if undo is possible."""
        return self.current_index > 0

    def can_redo(self) -> bool:
        """Check if redo is possible."""
        return self.current_index < len(self.history) - 1


class ConflictResolverUI:
    """Interactive UI for resolving data conflicts with Rich formatting."""

    def __init__(self):
        """Initialize conflict resolver."""
        self.console = Console()
        self.resolved_conflicts = []
        self.resolution_history = ResolutionHistory()
        self.batch_mode = False
        self.default_strategy = None
        logger.info("ConflictResolverUI initialized with Rich support")

    def resolve_conflicts(
        self, conflicts: List[Conflict], batch_options: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Resolve conflicts through interactive prompts.

        Args:
            conflicts: List of Conflict objects to resolve
            batch_options: Optional batch resolution settings

        Returns:
            Dictionary mapping conflict entity_ids to resolved values
        """
        if not conflicts:
            return {}

        # Show initial panel
        self.console.print(Panel.fit(
            f"[bold yellow]Found {len(conflicts)} conflicts to resolve[/bold yellow]",
            title="Conflict Resolution"
        ))

        # Check for batch options
        if batch_options:
            self.batch_mode = batch_options.get("batch_mode", False)
            self.default_strategy = batch_options.get("strategy", None)

        resolved_data = {}

        # Process conflicts with progress tracking
        for i, conflict in enumerate(conflicts, 1):
            self._display_progress(i, len(conflicts))

            # Allow undo/redo options
            if self.resolution_history.can_undo():
                if self._offer_undo():
                    conflict_id, resolution = self.resolution_history.undo()
                    resolved_data[conflict_id] = resolution
                    continue

            resolution = self._resolve_single_conflict(conflict)
            resolved_data[conflict.entity_id] = resolution
            self.resolution_history.add_resolution(conflict.entity_id, resolution)

        self.console.print(Panel.fit(
            "[bold green]✅ All conflicts resolved![/bold green]",
            title="Resolution Complete"
        ))
        return resolved_data

    def _resolve_single_conflict(self, conflict: Conflict) -> Any:
        """Resolve a single conflict with user interaction."""
        self._display_conflict_details(conflict)

        # Check for batch mode
        if self.batch_mode and self.default_strategy:
            if self.default_strategy == "most_detailed":
                return self._get_most_detailed_variation(conflict.variations)
            elif self.default_strategy == "most_recent":
                return self._get_most_recent_variation(conflict.variations)

        # Prepare choices with smart default
        choices = self._prepare_choices(conflict.variations)
        default_choice = self._select_default(conflict.variations)

        # Add batch options if not already in batch mode
        if not self.batch_mode:
            choices.extend([
                {"name": "📋 Use this choice for all similar conflicts", "value": "BATCH_SIMILAR"},
                {"name": "🔄 Always prefer most detailed", "value": "BATCH_DETAILED"}
            ])

        # Interactive selection
        selected = questionary.select(
            f"Which version should be used for {conflict.field}?",
            choices=choices,
            default=default_choice
        ).ask()

        # Handle special options
        if selected == "CUSTOM":
            return self._handle_custom_entry(conflict)
        elif selected == "BATCH_SIMILAR":
            self.batch_mode = True
            self.default_strategy = "current"
            return conflict.variations[0].content
        elif selected == "BATCH_DETAILED":
            self.batch_mode = True
            self.default_strategy = "most_detailed"
            return self._get_most_detailed_variation(conflict.variations)

        return selected

    def _display_conflict_details(self, conflict: Conflict) -> None:
        """Show conflict in a clear, formatted manner using Rich."""
        # Create comparison table
        table = Table(title=f"Conflict: {conflict.field}", show_lines=True)
        table.add_column("Version", style="cyan", no_wrap=True, width=10)
        table.add_column("Content", style="white", width=50)
        table.add_column("Source", style="green", width=20)
        table.add_column("Details", style="yellow", width=20)

        for i, variation in enumerate(conflict.variations, 1):
            content_str = str(variation.content)
            # Truncate long content for display
            display_content = (
                content_str[:200] + "..."
                if len(content_str) > 200
                else content_str
            )

            # Calculate details
            details = []
            details.append(f"Length: {len(content_str)}")

            # Check for dates
            if self._has_recent_date(variation.content):
                details.append("📅 Has dates")

            # Check for structure
            if isinstance(variation.content, (dict, list)):
                details.append("📊 Structured")

            table.add_row(
                f"Version {i}",
                display_content,
                variation.source_file,
                "\n".join(details)
            )

        self.console.print(table)

    def _prepare_choices(self, variations: List[Variation]) -> List[dict]:
        """Format variations as questionary choices."""
        choices = []

        for i, var in enumerate(variations, 1):
            # Smart formatting based on content type
            if isinstance(var.content, str):
                preview = var.content[:100] + "..." if len(var.content) > 100 else var.content
            elif isinstance(var.content, list):
                preview = f"[List with {len(var.content)} items]"
            elif isinstance(var.content, dict):
                preview = f"[Dict with {len(var.content)} keys]"
            else:
                preview = str(var.content)[:100]

            choices.append({
                "name": f"Version {i}: {preview}",
                "value": var.content
            })

        # Add custom entry option
        choices.append({
            "name": "⚡ Enter custom version",
            "value": "CUSTOM"
        })

        return choices

    def _select_default(self, variations: List[Variation]) -> str:
        """Intelligently select the best default option."""
        scores = []

        for i, var in enumerate(variations):
            score = 0

            # Score based on content length (more detail is better)
            content_str = str(var.content)
            score += len(content_str)

            # Bonus for recent dates
            if self._has_recent_date(var.content):
                score += 1000

            # Bonus for structured data
            if isinstance(var.content, dict):
                score += 500
                # Extra bonus for nested structures
                if any(isinstance(v, (dict, list)) for v in var.content.values()):
                    score += 300
            elif isinstance(var.content, list):
                score += 400
                # Extra bonus for non-empty lists
                if var.content:
                    score += 200

            # Bonus for specific keywords indicating completeness
            keywords = ["senior", "lead", "manager", "director", "expert", "specialist"]
            content_lower = content_str.lower()
            for keyword in keywords:
                if keyword in content_lower:
                    score += 100

            scores.append(score)

        # Return the highest scoring variation
        best_index = scores.index(max(scores))
        return f"Version {best_index + 1}"

    def _has_recent_date(self, content: Any) -> bool:
        """Check if content contains recent dates."""
        content_str = str(content)

        # Look for year patterns (2020-2025)
        year_pattern = r"20[2][0-5]"
        if re.search(year_pattern, content_str):
            return True

        # Look for month/year patterns
        month_year_pattern = r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* 20[12][0-9]"
        if re.search(month_year_pattern, content_str, re.IGNORECASE):
            return True

        return False

    def _handle_custom_entry(self, conflict: Conflict) -> str:
        """Allow user to enter custom resolution."""
        self.console.print("[bold]Enter your custom version:[/bold]")

        # Multi-line input for descriptions and long text
        if any(keyword in conflict.field.lower() for keyword in ["description", "summary", "bio"]):
            lines = []
            self.console.print(
                "[dim]Enter text (press Enter twice or type 'END' on new line to finish):[/dim]"
            )

            empty_count = 0
            while True:
                line = questionary.text("", multiline=False).ask()
                if line == "END":
                    break
                if line == "":
                    empty_count += 1
                    if empty_count >= 2:
                        break
                else:
                    empty_count = 0
                    lines.append(line)

            return "\n".join(lines)

        # Single line for other fields
        else:
            return questionary.text(
                f"Custom value for {conflict.field}:",
                validate=lambda x: len(x) > 0 or "Value cannot be empty"
            ).ask()

    def _display_progress(self, current: int, total: int) -> None:
        """Show resolution progress."""
        # Create progress bar
        filled = "=" * int((current / total) * 30)
        empty = "." * (30 - len(filled))
        progress_bar = f"[{filled}{empty}]"

        self.console.print(
            f"[bold blue]Progress: {progress_bar} {current}/{total}[/bold blue]"
        )

    def _offer_undo(self) -> bool:
        """Offer undo option to user."""
        return questionary.confirm(
            "Would you like to undo the last resolution?",
            default=False
        ).ask()

    def _get_most_detailed_variation(self, variations: List[Variation]) -> Any:
        """Get the variation with most detail."""
        max_length = 0
        best_variation = variations[0].content

        for var in variations:
            content_length = len(str(var.content))
            if isinstance(var.content, dict):
                content_length += len(var.content) * 100  # Favor structured data
            elif isinstance(var.content, list):
                content_length += len(var.content) * 50

            if content_length > max_length:
                max_length = content_length
                best_variation = var.content

        return best_variation

    def _get_most_recent_variation(self, variations: List[Variation]) -> Any:
        """Get the variation with most recent information."""
        for var in variations:
            if self._has_recent_date(var.content):
                return var.content
        # Fallback to most detailed if no recent dates found
        return self._get_most_detailed_variation(variations)

    def resolve_conflicts_legacy(
        self, data: Dict[str, Any], conflicts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Legacy method for backward compatibility.
        Converts old conflict format to new Conflict objects.
        """
        if not conflicts:
            return data

        # Convert legacy conflicts to new format
        new_conflicts = []
        for conflict in conflicts:
            variations = []
            for value, source in zip(conflict["values"], conflict.get("sources", [])):
                variations.append(Variation(
                    content=value,
                    source_file=source
                ))

            new_conflicts.append(Conflict(
                entity_id=conflict["field"],
                field=conflict["field"],
                variations=variations,
                conflict_type=conflict["type"]
            ))

        # Resolve using new method
        resolutions = self.resolve_conflicts(new_conflicts)

        # Apply resolutions to data
        resolved_data = data.copy()
        for field_path, value in resolutions.items():
            self._apply_resolution(resolved_data, field_path, value)

        return resolved_data

    def _apply_resolution(
        self, data: Dict[str, Any], field_path: str, value: Any
    ) -> None:
        """Apply resolved value to the data structure."""
        keys = field_path.split(".")
        current = data

        # Navigate to the parent of the target field
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        # Set the resolved value
        current[keys[-1]] = value
