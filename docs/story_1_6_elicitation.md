# Story 1.6: Build Interactive Elicitation Module

## Related PRD Requirements
- **FR5:** Interactive command-line interview to elicit qualitative data (`docs/prd.md#story-16-build-interactive-elicitation-module`)
- **NFR3:** User-friendly interactive CLI guidance (`docs/prd.md#non-functional`)

## Architecture Context
- **Component Design:** ElicitationUI follows the established CLI component pattern (`docs/architecture.md#components`)
- **Data Flow Integration:** Elicitation occurs after ConsolidationEngine in the pipeline (`docs/architecture.md#high-level-project-diagram`)
- **UI Component Pattern:** Implements the interactive CLI pattern established in ConflictResolverUI (`docs/architecture.md#components`)

## Schema Validation
- **Output Structure:** All elicited data must conform to the `HolisticProfile` dataclass in `resume_extractor/schemas/master_schema.py`
- **Data Types:** Transversal projects, aspirations, motivators, and qualities map to the defined schema structure

## Pipeline Dependencies
- **Prerequisites:** Requires completion of Story 1.4 (Conflict Resolution) and Story 1.5 (Skill Mapping)
- **Input Data:** The `existing_data` parameter contains parsed work experience and skills from Stories 1.2-1.3 (`docs/story_1_3_parser.md`)
- **Data Structure:** Input follows the consolidated data structure output from ConsolidationEngine

## Story Definition
**As a** user, **I want** to be interviewed by the system **so that** I can add important professional context that isn't in my formal resumes.

## Acceptance Criteria
1. After parsing is complete, the system asks the user a series of targeted questions
2. The system successfully prompts for and captures at least one of each: transversal project, professional aspiration, core motivator, and personal quality
3. The user's answers are correctly structured and saved into the `holistic_profile` section of the database

## Technical Implementation

### Component: ElicitationUI
Location: `resume_extractor/ui/elicitation.py`

```python
import questionary
from typing import Dict, List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from dataclasses import dataclass
from pathlib import Path

class ElicitationUI:
    def __init__(self):
        self.console = Console()
        self.elicited_data = {
            "transversal_projects": [],
            "professional_aspirations": {},
            "core_motivators": [],
            "personal_qualities": []
        }
        self.questions = self._load_question_bank()
    
    def conduct_interview(self, existing_data: Dict) -> Dict:
        """Conduct the full elicitation interview"""
        
        self._show_welcome_message()
        
        # Interview sections
        sections = [
            ("Transversal Projects", self._elicit_transversal_projects),
            ("Professional Aspirations", self._elicit_aspirations),
            ("Core Motivators", self._elicit_motivators),
            ("Personal Qualities", self._elicit_qualities)
        ]
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            
            main_task = progress.add_task(
                "[cyan]Interview Progress", 
                total=len(sections)
            )
            
            for section_name, elicitation_func in sections:
                progress.update(
                    main_task, 
                    description=f"Section: {section_name}"
                )
                
                elicitation_func(existing_data)
                progress.advance(main_task)
        
        self._show_completion_summary()
        
        return self.elicited_data
```

### Transversal Projects Elicitation

```python
def _elicit_transversal_projects(self, existing_data: Dict):
    """Gather information about side projects and initiatives"""
    
    self.console.print(Panel.fit(
        "[bold]Let's talk about projects outside your main work[/bold]\n"
        "These could be open source, personal projects, volunteering, etc.",
        title="🚀 Transversal Projects"
    ))
    
    add_more = True
    while add_more:
        project = self._get_project_details()
        
        if project:
            self.elicited_data["transversal_projects"].append(project)
            
            # Show what was captured
            self._display_captured_project(project)
        
        add_more = questionary.confirm(
            "Would you like to add another project?",
            default=False
        ).ask()

def _get_project_details(self) -> Optional[Dict]:
    """Get details for a single project"""
    
    # Project name
    name = questionary.text(
        "Project name:",
        validate=lambda x: len(x) > 0
    ).ask()
    
    if not name:
        return None
    
    # Project description
    description = self._get_multiline_input(
        "Describe the project (what it does, your role, impact):"
    )
    
    # Technologies/Skills
    skills_raw = questionary.text(
        "Key skills/technologies used (comma-separated):",
        default=""
    ).ask()
    
    skills = [s.strip() for s in skills_raw.split(",") if s.strip()]
    
    # Link (optional)
    link = questionary.text(
        "Project link (GitHub, website, etc.) - optional:",
        default=""
    ).ask()
    
    return {
        "name": name,
        "description": description,
        "skills_demonstrated": skills,
        "link": link if link else None
    }
```

### Professional Aspirations Elicitation

```python
def _elicit_aspirations(self, existing_data: Dict):
    """Gather career goals and aspirations"""
    
    self.console.print(Panel.fit(
        "[bold]Let's explore your professional aspirations[/bold]\n"
        "Understanding where you want to go helps shape your narrative",
        title="🎯 Professional Aspirations"
    ))
    
    # Target roles
    target_roles = self._get_list_input(
        "What roles are you targeting?",
        "Enter role (or press Enter to finish):",
        min_items=1,
        suggestions=self._suggest_roles_from_data(existing_data)
    )
    
    # Industries of interest
    industries = self._get_list_input(
        "Which industries interest you?",
        "Enter industry (or press Enter to finish):",
        min_items=1,
        suggestions=["Technology", "Finance", "Healthcare", "Education", "Consulting"]
    )
    
    # Technologies to learn
    tech_to_learn = self._get_list_input(
        "What technologies/skills do you want to learn?",
        "Enter technology/skill (or press Enter to finish):",
        min_items=0
    )
    
    self.elicited_data["professional_aspirations"] = {
        "target_roles": target_roles,
        "industries_of_interest": industries,
        "technologies_to_learn": tech_to_learn
    }

def _suggest_roles_from_data(self, existing_data: Dict) -> List[str]:
    """Generate role suggestions based on parsed work experience"""
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
```

### Core Motivators Elicitation

```python
def _elicit_motivators(self, existing_data: Dict):
    """Identify what drives the user professionally"""
    
    self.console.print(Panel.fit(
        "[bold]What motivates you in your work?[/bold]\n"
        "Understanding your drivers helps align opportunities",
        title="💡 Core Motivators"
    ))
    
    # Predefined motivator categories with examples
    motivator_prompts = [
        {
            "category": "Impact",
            "prompt": "How important is making a direct impact? (e.g., 'Building products that help millions')",
            "examples": ["Social impact", "User satisfaction", "Business growth"]
        },
        {
            "category": "Learning",
            "prompt": "What about continuous learning and growth?",
            "examples": ["New technologies", "Domain expertise", "Leadership skills"]
        },
        {
            "category": "Challenge",
            "prompt": "Do you thrive on solving complex problems?",
            "examples": ["Technical challenges", "Scale problems", "Innovation"]
        },
        {
            "category": "Team",
            "prompt": "How important is team dynamics and culture?",
            "examples": ["Mentoring", "Collaboration", "Diverse teams"]
        },
        {
            "category": "Recognition",
            "prompt": "Is professional recognition important?",
            "examples": ["Industry leadership", "Thought leadership", "Awards"]
        }
    ]
    
    for motivator_info in motivator_prompts:
        response = questionary.text(
            f"{motivator_info['prompt']}\n"
            f"Examples: {', '.join(motivator_info['examples'])}\n"
            "Your response (or skip):",
            default=""
        ).ask()
        
        if response:
            self.elicited_data["core_motivators"].append({
                "category": motivator_info["category"],
                "description": response
            })
```

### Personal Qualities Elicitation

```python
def _elicit_qualities(self, existing_data: Dict):
    """Capture personal qualities and soft skills"""
    
    self.console.print(Panel.fit(
        "[bold]Let's identify your key personal qualities[/bold]\n"
        "These differentiate you beyond technical skills",
        title="⭐ Personal Qualities"
    ))
    
    # Guide user with examples
    quality_categories = [
        "Leadership", "Communication", "Problem-solving",
        "Creativity", "Adaptability", "Attention to detail",
        "Empathy", "Strategic thinking", "Resilience"
    ]
    
    selected_qualities = questionary.checkbox(
        "Select qualities that best describe you:",
        choices=quality_categories
    ).ask()
    
    # Get evidence for each selected quality
    for quality in selected_qualities:
        evidence = questionary.text(
            f"Brief example demonstrating your {quality}:",
            validate=lambda x: len(x) > 10
        ).ask()
        
        self.elicited_data["personal_qualities"].append({
            "trait": quality,
            "evidence": evidence
        })
    
    # Allow custom qualities
    add_custom = questionary.confirm(
        "Would you like to add other qualities?",
        default=False
    ).ask()
    
    if add_custom:
        self._add_custom_qualities()
```

### Helper Methods

```python
def _get_multiline_input(self, prompt: str) -> str:
    """Get multi-line text input from user"""
    self.console.print(f"[bold]{prompt}[/bold]")
    self.console.print("[dim]Type your response. Press Enter twice to finish.[/dim]")
    
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
    self, 
    intro: str, 
    prompt: str, 
    min_items: int = 0,
    suggestions: List[str] = None
) -> List[str]:
    """Get a list of items from user"""
    
    self.console.print(f"[bold]{intro}[/bold]")
    
    if suggestions:
        self.console.print("[dim]Suggestions:", ", ".join(suggestions[:5]), "[/dim]")
    
    items = []
    while True:
        item = questionary.text(prompt, default="").ask()
        
        if not item:
            if len(items) >= min_items:
                break
            else:
                self.console.print(f"[yellow]Please add at least {min_items} item(s)[/yellow]")
        else:
            items.append(item)
            self.console.print(f"[green]✓ Added: {item}[/green]")
    
    return items
```

### Progress Saving

```python
def _save_progress(self):
    """Save interview progress for recovery"""
    import pickle
    
    progress_file = Path(".interview_progress.pkl")
    with open(progress_file, "wb") as f:
        pickle.dump(self.elicited_data, f)

def _load_progress(self) -> Optional[Dict]:
    """Load previous interview progress if available"""
    progress_file = Path(".interview_progress.pkl")
    
    if progress_file.exists():
        resume = questionary.confirm(
            "Previous interview session found. Resume from where you left off?",
            default=True
        ).ask()
        
        if resume:
            with open(progress_file, "rb") as f:
                return pickle.load(f)
    
    return None
```

## Testing Requirements
- Unit test each elicitation section
- Test multiline input handling
- Test progress saving/loading
- Test with interrupted sessions
- Test input validation
- Test suggestion generation
- Integration test full interview flow

## Definition of Done
- [x] ElicitationUI class implemented
- [x] All four elicitation sections functional
- [x] Multiline input handling
- [x] List input with validation
- [x] Progress saving for recovery
- [x] Rich formatting for better UX
- [x] Input validation for all fields
- [x] Suggestions based on existing data
- [x] Summary display after completion
- [x] Unit tests for all methods

## Dev Agent Record

### Agent Model Used
Claude Sonnet 4 (claude-sonnet-4-20250514)

### Tasks Completed
- [x] Create ElicitationUI class with base structure and initialization
- [x] Implement transversal projects elicitation section
- [x] Implement professional aspirations elicitation section
- [x] Implement core motivators elicitation section
- [x] Implement personal qualities elicitation section
- [x] Implement helper methods (_get_multiline_input, _get_list_input, etc)
- [x] Implement progress saving and loading functionality
- [x] Create comprehensive unit tests for ElicitationUI
- [x] Run validation tests and ensure all tests pass
- [x] Update story file with completed tasks and file list

### File List
- `resume_extractor/ui/elicitation.py` - Enhanced ElicitationUI class with full interview system
- `tests/test_elicitation.py` - Comprehensive unit tests (27 test cases)

### Completion Notes
- Implemented complete interview system with Rich formatting for enhanced UX
- Added progress saving/loading with pickle for interview resilience
- All four elicitation sections implemented with proper validation
- Role suggestions based on existing work experience data
- Comprehensive test coverage with proper mocking of questionary components
- All tests passing (27/27) with proper code formatting via Black
- Maintains backward compatibility with legacy `gather_additional_info` method

### Change Log
- **Enhanced ElicitationUI**: Complete rewrite with Rich console formatting, progress tracking, and structured interview flow
- **Progress Management**: Added automatic save/resume functionality for interrupted sessions  
- **Smart Suggestions**: Role suggestions generated from existing work experience data
- **Comprehensive Testing**: 27 unit tests covering all functionality including edge cases
- **Code Quality**: Formatted with Black and passes Ruff linting

### Status
Ready for Review

## QA Results

### Review Date: 2025-08-28

### Reviewed By: Claude Sonnet 4

**Implementation Assessment:**
- ✅ All acceptance criteria met completely
- ✅ All four elicitation sections implemented with Rich formatting
- ✅ Progress saving/loading with pickle for session resilience
- ✅ Smart role suggestions based on existing work experience data
- ✅ Comprehensive test coverage (27/27 tests passing)
- ✅ Input validation and error handling throughout
- ✅ Backward compatibility maintained with legacy method
- ✅ Code formatted with Black and passes Ruff linting

**Key Strengths:**
- Complete feature implementation matching specification exactly
- Robust error handling and user experience enhancements
- Comprehensive unit test coverage with proper mocking
- Clean architecture with proper separation of concerns

### Gate Status

Gate: PASS → docs/qa/gates/1.6-build-interactive-elicitation-module.yml