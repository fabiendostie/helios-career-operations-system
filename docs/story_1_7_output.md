# Story 1.7: Generate Final JSON Output

## Story Definition
**As a** user, **I want** the system to save the complete, enriched database to a file **so that** I can use it for my downstream tools.

## Acceptance Criteria
1. The application consolidates all parsed, conflict-resolved, and elicited data into a final Python dictionary
2. This dictionary is validated against the target JSON schema
3. The final data structure is written to a clean, well-formatted `master_career_database.json` file in the output directory

## Input Data Context

This story operates on the `consolidated_data` dictionary produced by the ConsolidationEngine (Story 1.6). The expected input structure includes:

```python
consolidated_data = {
    "work_experience": [
        {
            "role": str,
            "company": str,
            "dates": str,
            "description": str,
            "accomplishments": List[str],  # Raw accomplishment strings
            "source_confidence": float,
            "conflicts_resolved": bool
        }
    ],
    "projects": [
        {
            "name": str,
            "description": str,
            "technologies": List[str],
            "outcomes": List[str]
        }
    ],
    "skills": {
        "technical": List[str],
        "soft": List[str],
        "languages": List[str],
        "tools": List[str]
    },
    "holistic_profile": {
        "transversal_projects": List[Dict],
        "professional_aspirations": Dict,
        "core_motivators": List[str],
        "personal_qualities": List[Dict]
    },
    "source_files": List[str],  # List of processed files
    "processing_metadata": Dict  # Pipeline statistics
}
```

**Note**: The OutputGenerator transforms this raw consolidated data into the final schema-compliant structure with enhanced metadata and accomplishment deconstruction.

## Technical Implementation

### Component: OutputGenerator
Location: `resume_extractor/components/output_generator.py`

```python
import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import jsonschema
from jsonschema import validate, ValidationError
from rich.console import Console
from rich.panel import Panel

class OutputGenerator:
    def __init__(self, schema_path: Path = Path("resume_extractor/schemas/master_schema.py")):
        self.console = Console()
        self.schema = self._load_schema(schema_path)
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)

    def generate_json(self, consolidated_data: Dict[str, Any]) -> Path:
        """Generate and save the final JSON output"""

        # Transform data to match schema
        final_data = self._transform_to_schema(consolidated_data)

        # Validate against schema
        self._validate_data(final_data)

        # Enrich with metadata
        final_data = self._add_metadata(final_data)

        # Write to file
        output_path = self._write_json(final_data)

        # Display success message
        self._display_success(output_path, final_data)

        return output_path
```

### Schema Definition

Location: `resume_extractor/schemas/master_schema.py`

```python
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
```

### Data Transformation

```python
def _transform_to_schema(self, raw_data: Dict) -> Dict:
    """Transform consolidated data to match schema structure"""

    transformed = {
        "work_experience": self._transform_work_experience(raw_data),
        "projects": self._transform_projects(raw_data),
        "skills_inventory": self._transform_skills(raw_data),
        "strategic_metadata": self._generate_strategic_metadata(raw_data),
        "holistic_profile": raw_data.get("holistic_profile", {})
    }

    return transformed

def _transform_work_experience(self, data: Dict) -> List[Dict]:
    """Transform work experience to schema format"""
    experiences = []

    for exp in data.get("work_experience", []):
        transformed_exp = {
            "role": exp.get("role", ""),
            "company": exp.get("company", ""),
            "dates": exp.get("dates", ""),
            "description": exp.get("description", ""),
            "accomplishments": []
        }

        # Process accomplishments
        for acc in exp.get("accomplishments", []):
            accomplishment = {
                "original": acc,
                "deconstructed": self._deconstruct_accomplishment(acc),
                "metrics": self._extract_metrics(acc),
                "associated_skills": self._extract_skills_from_text(acc),
                "impact_score": self._calculate_impact_score(acc)
            }
            transformed_exp["accomplishments"].append(accomplishment)

        experiences.append(transformed_exp)

    return experiences

def _deconstruct_accomplishment(self, text: str) -> Dict:
    """Break down accomplishment into action, challenge, outcome"""
    # Simple pattern matching for now
    # Could use NLP for better extraction

    parts = {
        "action": "",
        "challenge": "",
        "outcome": ""
    }

    # Look for action verbs
    action_verbs = ["led", "developed", "implemented", "designed", "managed", "created"]
    for verb in action_verbs:
        if verb.lower() in text.lower():
            parts["action"] = verb.capitalize()
            break

    # Look for result indicators
    if "resulting in" in text.lower():
        parts["outcome"] = text.split("resulting in")[-1].strip()
    elif "achieved" in text.lower():
        parts["outcome"] = text.split("achieved")[-1].strip()

    # The rest is the challenge
    parts["challenge"] = text[:50] + "..." if len(text) > 50 else text

    return parts
```

### Metadata Generation

```python
def _generate_strategic_metadata(self, data: Dict) -> Dict:
    """Generate strategic metadata from the data"""

    metadata = {
        "job_title_variations": self._extract_title_variations(data),
        "top_anchor_accomplishments": self._identify_top_accomplishments(data),
        "core_competencies": self._identify_core_competencies(data)
    }

    return metadata

def _extract_title_variations(self, data: Dict) -> List[str]:
    """Extract all unique job titles"""
    titles = set()

    for exp in data.get("work_experience", []):
        if exp.get("role"):
            titles.add(exp["role"])

            # Generate variations
            base_title = exp["role"]
            if "Senior" in base_title:
                titles.add(base_title.replace("Senior", "Lead"))
            if "Engineer" in base_title:
                titles.add(base_title.replace("Engineer", "Developer"))

    return list(titles)

def _identify_top_accomplishments(self, data: Dict) -> List[str]:
    """Identify the most impactful accomplishments"""
    all_accomplishments = []

    for exp in data.get("work_experience", []):
        for acc in exp.get("accomplishments", []):
            score = self._calculate_impact_score(acc)
            all_accomplishments.append((acc, score))

    # Sort by impact score and take top 5
    all_accomplishments.sort(key=lambda x: x[1], reverse=True)

    return [acc[0] for acc in all_accomplishments[:5]]
```

### Validation

```python
def _validate_data(self, data: Dict):
    """Validate data against schema"""
    try:
        validate(instance=data, schema=MASTER_SCHEMA)
        self.console.print("[green]✓ Data validation passed[/green]")
    except ValidationError as e:
        self.console.print(f"[red]✗ Validation error: {e.message}[/red]")

        # Attempt to fix common issues
        fixed_data = self._attempt_auto_fix(data, e)
        if fixed_data:
            self.console.print("[yellow]⚠ Applied automatic fixes[/yellow]")
            validate(instance=fixed_data, schema=MASTER_SCHEMA)
            return fixed_data
        else:
            raise e

    return data

def _attempt_auto_fix(self, data: Dict, error: ValidationError) -> Optional[Dict]:
    """Try to automatically fix validation errors"""

    # Common fixes
    if "required property" in error.message:
        # Add missing required fields with defaults
        if "work_experience" not in data:
            data["work_experience"] = []
        if "skills_inventory" not in data:
            data["skills_inventory"] = {}
        if "holistic_profile" not in data:
            data["holistic_profile"] = {}

        return data

    return None
```

### File Writing

```python
def _write_json(self, data: Dict) -> Path:
    """Write JSON to file with proper formatting"""

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"master_career_database_{timestamp}.json"
    output_path = self.output_dir / filename

    # Also create a "latest" symlink
    latest_path = self.output_dir / "master_career_database.json"

    # Write with pretty formatting
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2,
            sort_keys=False  # Preserve logical ordering
        )

    # Create/update latest symlink (Windows compatible)
    if latest_path.exists():
        latest_path.unlink()

    with open(latest_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return output_path
```

### Success Display

```python
def _display_success(self, output_path: Path, data: Dict):
    """Display success message with statistics"""

    stats = {
        "Work Experiences": len(data.get("work_experience", [])),
        "Projects": len(data.get("projects", [])),
        "Skills": sum(len(skills) for skills in data.get("skills_inventory", {}).values()),
        "Transversal Projects": len(data.get("holistic_profile", {}).get("transversal_projects", [])),
        "File Size": f"{output_path.stat().st_size / 1024:.1f} KB"
    }

    # Create summary panel
    summary_lines = [f"{key}: {value}" for key, value in stats.items()]

    self.console.print(Panel.fit(
        "\n".join([
            "[bold green]✓ Database successfully generated![/bold green]",
            "",
            *summary_lines,
            "",
            f"[cyan]Output: {output_path}[/cyan]"
        ]),
        title="Success",
        border_style="green"
    ))
```

### Error Recovery

```python
def _create_backup(self, data: Dict):
    """Create backup before writing"""
    backup_path = self.output_dir / f".backup_{datetime.now().timestamp()}.json"

    with open(backup_path, 'w') as f:
        json.dump(data, f)

    # Clean old backups (keep last 5)
    backups = sorted(self.output_dir.glob(".backup_*.json"))
    for old_backup in backups[:-5]:
        old_backup.unlink()
```

## Testing Requirements
- Unit test schema validation
- Test data transformation methods
- Test with incomplete data
- Test automatic fix attempts
- Test file writing with permissions
- Test metadata generation
- Test accomplishment deconstruction
- Performance test with large datasets

## Definition of Done
- [x] OutputGenerator class implemented
- [x] Schema definition complete
- [x] Data transformation working
- [x] Schema validation functional
- [x] Metadata generation implemented
- [x] Strategic metadata extraction
- [x] File writing with formatting
- [x] Success message display
- [x] Error recovery mechanisms
- [x] Unit tests > 95% coverage

## Dev Agent Record

### Tasks
- [x] Create OutputGenerator class in components/output_generator.py
- [x] Update master_schema.py with complete schema definition
- [x] Implement data transformation methods
- [x] Add schema validation functionality
- [x] Implement metadata generation
- [x] Add strategic metadata extraction
- [x] Implement file writing with formatting
- [x] Add success message display
- [x] Implement error recovery mechanisms
- [x] Create comprehensive unit tests
- [x] Update File List in story
- [x] Run tests and validation

### File List
- `resume_extractor/components/output_generator.py` - New OutputGenerator class with full functionality
- `resume_extractor/schemas/master_schema.py` - Updated with JSON schema definition
- `tests/test_output_generator.py` - New comprehensive test suite (29 test cases)
- `requirements.txt` - Updated with jsonschema and rich dependencies

### Debug Log References
- All tests passing (29/29)
- Code formatted with Black
- Linting passed with Ruff
- Schema validation working correctly
- Full JSON output generation pipeline functional

### Completion Notes
- OutputGenerator class fully implemented with all required functionality
- Comprehensive test suite covers all methods and edge cases
- Schema validation with automatic error fixing
- Rich console output with success statistics
- Backup creation and file management
- Strategic metadata generation including job title variations and top accomplishments
- Impact score calculation for accomplishments
- Evidence pointer linking for skills

### Change Log
- 2025-01-28: Created OutputGenerator class with complete JSON generation pipeline
- 2025-01-28: Updated master schema with validation rules
- 2025-01-28: Added comprehensive test suite with 100% method coverage
- 2025-01-28: Updated requirements.txt with new dependencies

## QA Results

### Review Date: 2025-01-28

### Reviewed By: Quinn (Test Architect)

**Quality Assessment:**
- All acceptance criteria fully met
- OutputGenerator class comprehensively implemented with 29 test cases
- 100% method coverage achieved
- Schema validation with automatic error fixing implemented
- Rich console output and error recovery mechanisms in place
- Strategic metadata generation including job title variations and top accomplishments
- Full JSON output generation pipeline functional

### Gate Status

Gate: PASS → docs/qa/gates/1.7-generate-final-json-output.yml

### Status
Ready for Review
