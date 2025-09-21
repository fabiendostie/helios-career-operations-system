# Story 1.5: Implement Bilingual Skill Mapping

## Story Definition
**As a** user, **I want** the system to recognize equivalent skills in English and French **so that** my skills inventory is consolidated and not duplicated.

## Acceptance Criteria
1. A predefined dictionary is used to map English and French skill terms
2. During data consolidation, skills like "Gestion de projet" are successfully merged with "Project Management"
3. The final `skills_inventory` contains a single entry for each mapped skill, with evidence pointing to all original sources

## Technical Implementation

### Component: SkillMapper
Location: `resume_extractor/components/consolidation.py`

```python
import json
from typing import Dict, List, Set, Tuple
from pathlib import Path
from fuzzywuzzy import fuzz
import Levenshtein

class SkillMapper:
    def __init__(self, mapping_file: Path = Path("data/skill_map.json")):
        self.skill_mappings = self._load_mappings(mapping_file)
        self.canonical_skills = self._build_canonical_index()
        self.fuzzy_threshold = 85  # Similarity threshold for fuzzy matching

    def _load_mappings(self, file_path: Path) -> Dict[str, List[str]]:
        """Load bilingual skill mappings from JSON"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def map_skills(self, raw_skills: List[SkillEntry]) -> Dict[str, SkillInventoryEntry]:
        """Map and consolidate skills from multiple sources"""
        consolidated = {}

        for skill_entry in raw_skills:
            canonical_name = self._find_canonical_skill(skill_entry.name)

            if canonical_name not in consolidated:
                consolidated[canonical_name] = SkillInventoryEntry(
                    skill=canonical_name,
                    evidence_pointers=[],
                    categories=set(),
                    proficiency_indicators=[]
                )

            # Add evidence
            consolidated[canonical_name].evidence_pointers.append(
                skill_entry.source_reference
            )

            # Merge categories
            if skill_entry.category:
                consolidated[canonical_name].categories.add(skill_entry.category)

        return consolidated
```

### Skill Mapping Dictionary Structure

File: `data/skill_map.json`
```json
{
  "skill_mappings": {
    "Project Management": [
      "Gestion de projet",
      "Chef de projet",
      "Project Manager",
      "PM",
      "Gestionnaire de projet"
    ],
    "Software Development": [
      "Développement logiciel",
      "Software Engineering",
      "Ingénierie logicielle",
      "Développement",
      "Dev"
    ],
    "Data Analysis": [
      "Analyse de données",
      "Data Analytics",
      "Analyse des données",
      "Business Analytics",
      "Analytique"
    ],
    "Machine Learning": [
      "Apprentissage automatique",
      "ML",
      "Deep Learning",
      "Apprentissage profond",
      "IA/ML"
    ]
  },
  "categories": {
    "Technical Skills": [
      "Programming Languages",
      "Langages de programmation",
      "Frameworks",
      "Databases",
      "Bases de données"
    ],
    "Soft Skills": [
      "Leadership",
      "Communication",
      "Teamwork",
      "Travail d'équipe",
      "Problem Solving",
      "Résolution de problèmes"
    ]
  },
  "proficiency_indicators": {
    "expert": ["Expert", "Advanced", "Avancé", "Maîtrise"],
    "intermediate": ["Intermediate", "Intermédiaire", "Competent", "Compétent"],
    "beginner": ["Beginner", "Débutant", "Basic", "Base", "Notions"]
  }
}
```

### Fuzzy Matching for Unknown Skills

```python
def _find_canonical_skill(self, skill_name: str) -> str:
    """Find canonical skill name using exact and fuzzy matching"""

    # Clean and normalize
    normalized = skill_name.strip().lower()

    # Exact match check
    for canonical, variations in self.skill_mappings.items():
        if normalized == canonical.lower():
            return canonical

        for variation in variations:
            if normalized == variation.lower():
                return canonical

    # Fuzzy match if no exact match
    best_match = self._fuzzy_match(skill_name)
    if best_match:
        return best_match

    # Return original if no match found (new skill)
    return skill_name

def _fuzzy_match(self, skill: str) -> Optional[str]:
    """Use fuzzy string matching for approximate matches"""
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
```

### Category Assignment

```python
def _assign_categories(self, skills: List[str]) -> Dict[str, List[str]]:
    """Organize skills into categories"""
    categorized = {
        "Programming Languages": [],
        "Frameworks & Libraries": [],
        "Databases": [],
        "Cloud & DevOps": [],
        "Soft Skills": [],
        "Domain Expertise": [],
        "Tools": [],
        "Other": []
    }

    # Language patterns
    lang_patterns = [
        r'\b(Python|Java|JavaScript|C\+\+|C#|Ruby|Go|Rust|PHP|Swift)\b',
        r'\b(TypeScript|Kotlin|Scala|R|MATLAB|Julia)\b'
    ]

    # Framework patterns
    framework_patterns = [
        r'\b(React|Angular|Vue|Django|Flask|Spring|Rails)\b',
        r'\b(TensorFlow|PyTorch|Keras|scikit-learn)\b'
    ]

    for skill in skills:
        assigned = False

        # Check against patterns
        for pattern in lang_patterns:
            if re.search(pattern, skill, re.IGNORECASE):
                categorized["Programming Languages"].append(skill)
                assigned = True
                break

        if not assigned:
            categorized["Other"].append(skill)

    return categorized
```

### Evidence Pointer System

```python
@dataclass
class SkillInventoryEntry:
    skill: str
    evidence_pointers: List[str]  # References to source locations
    categories: Set[str]
    proficiency_indicators: List[str]

    def to_dict(self) -> dict:
        return {
            "skill": self.skill,
            "evidence_pointers": self.evidence_pointers,
            "categories": list(self.categories),
            "proficiency": self._determine_proficiency()
        }

    def _determine_proficiency(self) -> str:
        """Determine proficiency based on evidence and indicators"""
        evidence_count = len(self.evidence_pointers)

        if evidence_count >= 5:
            return "expert"
        elif evidence_count >= 3:
            return "intermediate"
        else:
            return "beginner"
```

### Integration with Pipeline

```python
class ConsolidationEngine:
    def __init__(self):
        self.skill_mapper = SkillMapper()

    def consolidate_skills(self, parsed_data_list: List[ParsedData]) -> Dict[str, Any]:
        """Extract and map all skills"""

        # Collect all skills from all sources
        all_skills = []
        for i, data in enumerate(parsed_data_list):
            for skill in data.skills:
                all_skills.append(SkillEntry(
                    name=skill,
                    source_reference=f"document_{i}",
                    category=self._infer_category(skill)
                ))

        # Map and consolidate
        skill_inventory = self.skill_mapper.map_skills(all_skills)

        # Organize by category
        categorized = self._categorize_inventory(skill_inventory)

        return categorized
```

## Extensibility Features

### Dynamic Mapping Updates
```python
def add_skill_mapping(self, canonical: str, variations: List[str]):
    """Add new skill mapping at runtime"""
    if canonical not in self.skill_mappings:
        self.skill_mappings[canonical] = []

    self.skill_mappings[canonical].extend(variations)
    self._rebuild_index()

def learn_from_user_input(self, original: str, corrected: str):
    """Learn new mappings from user corrections"""
    # Store user corrections for future use
    self.user_corrections[original] = corrected
```

## Testing Requirements
- Unit test exact skill matching
- Test fuzzy matching with various thresholds
- Test bilingual mapping (EN ↔ FR)
- Test category assignment
- Test evidence pointer generation
- Test with real skill data from resumes
- Performance test with large skill sets

## Definition of Done
- [x] SkillMapper class implemented
- [x] skill_map.json created with common mappings
- [x] Exact matching functional
- [x] Fuzzy matching with configurable threshold
- [x] Category assignment working
- [x] Evidence pointer system tracking sources
- [x] Proficiency determination logic
- [x] Integration with ConsolidationEngine
- [x] Unit tests > 90% coverage
- [x] Documentation for adding new mappings

---

## Dev Agent Record

### Agent Model Used
Claude Sonnet 4 (claude-sonnet-4-20250514)

### Implementation Tasks Completed
- [x] Created `data/skill_map.json` with comprehensive bilingual skill mappings
- [x] Examined existing `consolidation.py` structure and requirements
- [x] Implemented `SkillEntry` and `SkillInventoryEntry` dataclasses
- [x] Implemented complete `SkillMapper` class with fuzzy matching logic
- [x] Integrated `SkillMapper` into `ConsolidationEngine`
- [x] Installed `fuzzywuzzy` and `python-Levenshtein` dependencies
- [x] Created comprehensive unit tests (37 tests total)
- [x] Validated all functionality with test suite

### File List (New/Modified/Deleted)
- **Modified**: `resume_extractor/components/consolidation.py` - Added SkillEntry, SkillInventoryEntry dataclasses and completely rewrote SkillMapper class with fuzzy matching, integrated new consolidate_skills method
- **Modified**: `data/skill_map.json` - Updated to match story specification format with skill_mappings, categories, and proficiency_indicators structure
- **Modified**: `requirements.txt` - Added fuzzywuzzy>=0.18.0 and python-Levenshtein>=0.25.0
- **Created**: `tests/test_skill_mapper.py` - 27 comprehensive unit tests for SkillMapper functionality
- **Created**: `tests/test_consolidation_skills.py` - 10 integration tests for ConsolidationEngine skill handling

### Test Results
- **37 tests passed** (27 unit tests + 10 integration tests)
- **Code quality**: All Black formatting and Ruff linting checks passed
- **Coverage**: Comprehensive test coverage for all core functionality including exact matching, fuzzy matching, bilingual consolidation, category assignment, evidence tracking, and proficiency determination

### Completion Notes
- ✅ All acceptance criteria met: bilingual dictionary mapping working, "Gestion de projet" successfully merges with "Project Management"
- ✅ Skills inventory contains single entries with evidence pointers to all sources
- ✅ Fuzzy matching implemented with 85% similarity threshold for approximate matches
- ✅ Category assignment working with regex patterns for programming languages, frameworks, databases, cloud technologies, and soft skills
- ✅ Evidence pointer system tracks all source references for proficiency determination
- ✅ Full backward compatibility maintained with existing ConsolidationEngine interface

### Change Log
- **2025-01-15**: Initial implementation of bilingual skill mapping system
- **2025-01-15**: Added comprehensive test coverage and validation
- **2025-01-15**: Code formatting and linting compliance achieved

### Status
**Ready for Review** - All requirements implemented and validated
