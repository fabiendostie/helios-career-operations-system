# Story 1.4: Build Interactive Conflict Resolution Module

## Story Definition
**As a** user, **I want** to be prompted to resolve any conflicting information found in my resumes **so that** the final database is accurate and authoritative.

## Acceptance Criteria
1. When a data conflict is detected, the system presents the different versions to the user in a clear format
2. The system suggests the more detailed (higher character count) version as the default choice
3. The user's selection is captured and used as the canonical data point, discarding the other versions
4. The process repeats until all conflicts are resolved

## Technical Implementation

### Component: ConflictResolverUI
Location: `resume_extractor/ui/conflict_resolver.py`

```python
import questionary
from typing import List, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

class ConflictResolverUI:
    def __init__(self):
        self.console = Console()
        self.resolved_conflicts = []
    
    def resolve_conflicts(self, conflicts: List[Conflict]) -> Dict[str, Any]:
        """Interactive conflict resolution session"""
        self.console.print(Panel.fit(
            f"[bold yellow]Found {len(conflicts)} conflicts to resolve[/bold yellow]",
            title="Conflict Resolution"
        ))
        
        resolved_data = {}
        for i, conflict in enumerate(conflicts, 1):
            self._display_progress(i, len(conflicts))
            resolution = self._resolve_single_conflict(conflict)
            resolved_data[conflict.entity_id] = resolution
            
        return resolved_data
    
    def _resolve_single_conflict(self, conflict: Conflict) -> Any:
        """Resolve a single conflict with user interaction"""
        self._display_conflict_details(conflict)
        
        # Prepare choices with smart default
        choices = self._prepare_choices(conflict.variations)
        default_choice = self._select_default(conflict.variations)
        
        # Interactive selection
        selected = questionary.select(
            f"Which version should be used for {conflict.field}?",
            choices=choices,
            default=default_choice
        ).ask()
        
        return selected
```

### Conflict Display Methods

```python
def _display_conflict_details(self, conflict: Conflict):
    """Show conflict in a clear, formatted manner"""
    
    # Create comparison table
    table = Table(title=f"Conflict: {conflict.field}")
    table.add_column("Version", style="cyan", no_wrap=True)
    table.add_column("Content", style="white")
    table.add_column("Source", style="green")
    table.add_column("Details", style="yellow")
    
    for i, variation in enumerate(conflict.variations, 1):
        table.add_row(
            f"Version {i}",
            str(variation.content)[:200] + "...",  # Truncate long content
            variation.source_file,
            f"Length: {len(str(variation.content))}"
        )
    
    self.console.print(table)

def _prepare_choices(self, variations: List[Any]) -> List[dict]:
    """Format variations as questionary choices"""
    choices = []
    
    for i, var in enumerate(variations, 1):
        # Smart formatting based on content type
        if isinstance(var.content, str):
            preview = var.content[:100] + "..." if len(var.content) > 100 else var.content
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
```

### Smart Default Selection

```python
def _select_default(self, variations: List[Any]) -> str:
    """Intelligently select the best default option"""
    
    # Scoring system for variations
    scores = []
    for var in variations:
        score = 0
        
        # Higher score for more content
        score += len(str(var.content))
        
        # Bonus for recent dates
        if self._has_recent_date(var.content):
            score += 1000
        
        # Bonus for structured data
        if isinstance(var.content, dict) or isinstance(var.content, list):
            score += 500
            
        scores.append(score)
    
    # Return the highest scoring variation
    best_index = scores.index(max(scores))
    return f"Version {best_index + 1}"
```

### Custom Entry Handling

```python
def _handle_custom_entry(self, conflict: Conflict) -> str:
    """Allow user to enter custom resolution"""
    
    self.console.print("[bold]Enter your custom version:[/bold]")
    
    # Multi-line input for descriptions
    if "description" in conflict.field.lower():
        lines = []
        self.console.print("[dim]Enter text (press Ctrl+D or type 'END' on new line to finish):[/dim]")
        
        while True:
            line = questionary.text("").ask()
            if line == "END":
                break
            lines.append(line)
        
        return "\n".join(lines)
    
    # Single line for other fields
    else:
        return questionary.text(
            "Custom value:",
            validate=lambda x: len(x) > 0
        ).ask()
```

### Progress Tracking

```python
def _display_progress(self, current: int, total: int):
    """Show resolution progress"""
    progress_bar = f"[{'=' * current}{'.' * (total - current)}]"
    self.console.print(
        f"Progress: {progress_bar} {current}/{total}",
        style="bold blue"
    )
```

## Integration with ConsolidationEngine

```python
class ConsolidationEngine:
    def __init__(self):
        self.conflict_resolver = ConflictResolverUI()
    
    def consolidate_with_resolution(self, parsed_data_list: List[ParsedData]) -> ConsolidatedData:
        """Merge data with conflict resolution"""
        
        # Detect conflicts
        conflicts = self._detect_conflicts(parsed_data_list)
        
        if conflicts:
            # Interactive resolution
            resolutions = self.conflict_resolver.resolve_conflicts(conflicts)
            
            # Apply resolutions
            consolidated = self._apply_resolutions(parsed_data_list, resolutions)
        else:
            # No conflicts, simple merge
            consolidated = self._simple_merge(parsed_data_list)
        
        return consolidated
```

## User Experience Features

### Undo/Redo Capability
```python
class ResolutionHistory:
    def __init__(self):
        self.history = []
        self.current_index = -1
    
    def add_resolution(self, conflict_id: str, resolution: Any):
        self.history.append((conflict_id, resolution))
        self.current_index = len(self.history) - 1
    
    def undo(self):
        if self.current_index > 0:
            self.current_index -= 1
            return self.history[self.current_index]
    
    def redo(self):
        if self.current_index < len(self.history) - 1:
            self.current_index += 1
            return self.history[self.current_index]
```

### Batch Operations
- "Use Version 1 for all" option
- "Always prefer most detailed" setting
- Skip similar conflicts option

## Testing Requirements
- Unit test conflict display formatting
- Test with various data types (strings, lists, dicts)
- Test custom entry validation
- Test undo/redo functionality
- Integration test with sample conflicts
- Test keyboard interruption handling

## Definition of Done
- [x] ConflictResolverUI class implemented
- [x] Rich formatting for clear display
- [x] Smart default selection algorithm
- [x] Custom entry option functional
- [x] Progress tracking displayed
- [x] Undo/redo capability
- [x] Batch operation options
- [x] Integration with ConsolidationEngine
- [x] Error handling for user interruption
- [x] Unit tests with mock conflicts

## QA Results

### Review Date: 2025-01-28

### Reviewed By: Quinn (Test Architect)

### Test Results
- **Unit Tests**: 50/50 passing for conflict_resolver module
- **Test Coverage**: 94% (222 statements, 13 missed) - Excellent!
- **Integration Tests**: 1 failure in pipeline test (separate module issue)
- **Lint Check**: All checks passed ✅
- **Performance**: Interactive operations responsive

### Key Findings
- ✅ All acceptance criteria fully implemented
- ✅ ConflictResolverUI with Rich formatting working
- ✅ Smart default selection using scoring algorithm
- ✅ Custom entry with multi-line support
- ✅ Undo/redo functionality with ResolutionHistory
- ✅ Batch operations with multiple strategies
- ✅ Integration with ConsolidationEngine complete
- ✅ Excellent test coverage at 94%
- ✅ Clean code with no lint issues
- ✅ Code quality significantly improved

### Quality Assessment
**Strengths:**
- Excellent UX with Rich tables and progress tracking
- Smart scoring algorithm for default selection
- Comprehensive batch operation strategies
- Good separation of concerns with Variation/Conflict dataclasses
- Legacy method support for backward compatibility
- Outstanding test coverage (94%)
- Clean, maintainable code

**Minor Notes:**
- Pipeline integration test failure is in separate module (not blocking)

### Gate Status

Gate: PASS → docs/qa/gates/1.4-build-interactive-conflict-resolution-module.yml