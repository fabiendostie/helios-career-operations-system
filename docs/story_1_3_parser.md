# Story 1.3: Develop Bilingual Resume Parser

## Story Definition
**As a** system, **I want** to parse key information from both English and French text **so that** a structured representation of the user's formal career can be built.

## Acceptance Criteria
1. A parsing function correctly uses the spaCy English model on English text to extract entities like work experience, projects, and skills
2. A parsing function correctly uses the spaCy French model on French text to extract the same entities
3. The extracted data from all files is consolidated into a single preliminary data structure
4. The system identifies potential conflicts (e.g., same company and role, but different descriptions or dates)

## Technical Implementation

### Component: ParsingService
Location: `resume_extractor/components/parsing.py`

```python
import spacy
from typing import Dict, List, Any

class ParsingService:
    """Singleton service for NLP parsing using spaCy models"""
    
    _instance = None
    _models = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_models()
        return cls._instance
    
    def _load_models(self):
        """Load spaCy models once at startup"""
        self._models['en'] = spacy.load("en_core_web_trf")
        self._models['fr'] = spacy.load("fr_dep_news_trf")
    
    def parse_document(self, document: Document) -> ParsedData:
        """Parse document using appropriate language model"""
        model = self._models[document.language]
        doc = model(document.content)
        
        return ParsedData(
            work_experiences=self._extract_work_experience(doc),
            projects=self._extract_projects(doc),
            skills=self._extract_skills(doc),
            education=self._extract_education(doc),
            contact_info=self._extract_contact(doc)
        )
```

## Entity Extraction Methods

### Work Experience Extraction
```python
def _extract_work_experience(self, doc) -> List[WorkExperience]:
    """Extract job roles, companies, dates, and descriptions"""
    experiences = []
    
    # Pattern matching for job titles
    job_patterns = [
        {"LOWER": {"IN": ["senior", "junior", "lead", "principal"]}},
        {"POS": "NOUN", "OP": "+"}
    ]
    
    # Entity recognition for ORG (companies)
    # Date pattern matching for employment periods
    # Chunk parsing for job descriptions
    
    return experiences
```

### Skills Extraction
```python
def _extract_skills(self, doc) -> List[str]:
    """Extract technical and soft skills"""
    skills = []
    
    # Named Entity Recognition for PRODUCT, TECHNOLOGY
    # Custom patterns for programming languages
    # Phrase matching for multi-word skills
    
    return skills
```

### Project Extraction
```python
def _extract_projects(self, doc) -> List[Project]:
    """Extract project names, descriptions, and outcomes"""
    projects = []
    
    # Header detection for project sections
    # Dependency parsing for project descriptions
    # Pattern matching for outcomes/results
    
    return projects
```

## Data Structures

```python
@dataclass
class WorkExperience:
    role: str
    company: str
    dates: str
    description: str
    accomplishments: List[str]
    location: Optional[str]

@dataclass
class Project:
    name: str
    description: str
    technologies: List[str]
    outcomes: List[str]
    duration: Optional[str]

@dataclass
class ParsedData:
    work_experiences: List[WorkExperience]
    projects: List[Project]
    skills: List[str]
    education: List[Education]
    contact_info: ContactInfo
    raw_entities: Dict[str, Any]  # Store spaCy entities for debugging
```

## Conflict Detection

```python
class ConflictDetector:
    def find_conflicts(self, parsed_data_list: List[ParsedData]) -> List[Conflict]:
        """Identify conflicting information across documents"""
        conflicts = []
        
        # Compare work experiences by company + role
        # Flag different dates for same position
        # Flag different descriptions for same role
        # Identify duplicate projects with variations
        
        return conflicts

@dataclass
class Conflict:
    field: str  # e.g., "work_experience.dates"
    entity_id: str  # e.g., "Google-Senior Engineer"
    variations: List[Any]  # Different versions found
    sources: List[str]  # File paths where found
```

## Language-Specific Patterns

### English Patterns
- Job titles: "Senior Software Engineer", "Product Manager"
- Companies: Capitalized ORG entities
- Dates: "Jan 2020 - Present", "2019 to 2021"
- Skills: Technical terms, certifications

### French Patterns
- Job titles: "Ingénieur logiciel senior", "Chef de projet"
- Companies: ORG entities with French articles
- Dates: "janvier 2020 - présent", "2019 à 2021"
- Skills: French technical terms, diplômes

## Performance Optimization
- Load models once (Singleton pattern)
- Process documents in batches
- Cache parsed results
- Use spaCy's pipe() for batch processing

## Testing Requirements
- Unit test each extraction method
- Test with real resume samples in both languages
- Test conflict detection with known duplicates
- Verify entity extraction accuracy
- Test with poorly formatted text
- Benchmark parsing performance

## Definition of Done
- [x] ParsingService singleton implemented
- [x] Both spaCy models loading correctly
- [x] Work experience extraction functional
- [x] Skills extraction with deduplication
- [x] Project extraction working
- [x] Conflict detection identifying duplicates
- [x] Language-specific patterns tested
- [x] Unit tests > 85% coverage
- [x] Performance < 2 seconds per document
- [x] Logging for debugging entity extraction

## Dev Agent Record

### Agent Model Used
- Claude Sonnet 4 (claude-sonnet-4-20250514)

### Completion Notes
- Successfully implemented complete bilingual resume parser with singleton pattern
- All spaCy models loading with proper fallback to smaller models if transformers unavailable
- Comprehensive entity extraction for work experience, skills, projects, education, and contact info
- Advanced conflict detection system identifying variations across documents
- Full test coverage (89%) exceeding requirements with 15 test cases
- Performance optimization achieving <0.2s per document (well under 2s requirement)
- Enhanced logging system providing detailed debugging information for entity extraction
- Language-specific patterns implemented for both English and French parsing
- Deduplication logic working correctly for skills extraction
- All acceptance criteria met and validated through comprehensive testing

### File List
- `resume_extractor/components/parsing.py` - Complete implementation of ParsingService and ConflictDetector
- `tests/test_parsing.py` - Comprehensive unit tests (89% coverage)
- `test_parsing_implementation.py` - Integration test script
- `performance_test.py` - Performance validation script
- `test_logging.py` - Logging functionality demonstration
- `parsing_debug.log` - Generated debug log file

### Change Log
- Refactored ParsingService to implement proper singleton pattern
- Updated spaCy model loading to use transformer models with fallback
- Enhanced entity extraction methods with language-specific patterns
- Implemented comprehensive conflict detection across all data types
- Added detailed logging throughout the parsing pipeline
- Created extensive test suite with 89% code coverage
- Optimized performance to process documents in <0.2 seconds
- Added bilingual support with French language patterns

### Status
Ready for Review

## QA Results

### Review Date: 2025-01-28

### Reviewed By: Quinn (Test Architect)

### Test Results
- **Unit Tests**: 15/15 passing
- **Test Coverage**: 90% (272 statements, 28 missed)
- **Performance**: All documents processed in <0.1s (requirement: <2s)
- **Lint Check**: Passing (Ruff)
- **Code Formatting**: Minor issues with Black formatting

### Key Findings
- ✅ All acceptance criteria met
- ✅ Singleton pattern correctly implemented
- ✅ Both spaCy models (English/French) loading with fallbacks
- ✅ Entity extraction working for all data types
- ✅ Conflict detection system functional
- ✅ Deduplication logic working correctly
- ✅ Performance significantly exceeds requirements (10x faster)
- ⚠️ Minor code formatting issue (non-blocking)

### Gate Status

Gate: PASS → docs/qa/gates/1.3-develop-bilingual-resume-parser.yml