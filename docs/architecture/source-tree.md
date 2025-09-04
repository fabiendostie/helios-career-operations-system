# Source Tree Structure

## Project Root Layout

```
intelligent-resume-extractor/
├── .bmad-core/                  # BMAD agent configuration (development tooling)
├── docs/                        # Project documentation
│   ├── architecture/            # Technical architecture docs
│   ├── prd/                     # Product requirements (sharded)
│   └── stories/                 # Development stories and tasks
├── data/                        # Static data files
│   └── skill_map.json          # Bilingual skill equivalency mapping
├── resume_extractor/            # Main application package
│   ├── __init__.py             # Package initialization
│   ├── main.py                 # CLI entry point and argument parsing
│   ├── pipeline.py             # Orchestration of processing pipeline
│   ├── components/             # Core processing modules
│   │   ├── __init__.py
│   │   ├── ingestion.py        # File discovery and reading (IngestionEngine)
│   │   ├── parsing.py          # NLP processing (ParsingService)
│   │   └── consolidation.py    # Data merging (ConsolidationEngine, SkillMapper)
│   ├── schemas/                # Data structure definitions
│   │   ├── __init__.py
│   │   └── master_schema.py    # JSON output schema and validation
│   ├── ui/                     # User interface components
│   │   ├── __init__.py
│   │   ├── conflict_resolver.py # Interactive conflict resolution (ConflictResolverUI)
│   │   └── elicitation.py      # Data gathering interviews (ElicitationUI)
│   └── utils/                  # Shared utilities
│       ├── __init__.py
│       └── logging_config.py   # Centralized logging setup
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── test_parsing.py         # NLP parsing tests
│   ├── test_pipeline.py        # End-to-end pipeline tests
│   ├── test_consolidation.py   # Data merging tests
│   ├── test_ingestion.py       # File processing tests
│   └── sample_resumes/         # Test data files
│       ├── english/            # English test resumes
│       │   ├── resume_1.pdf
│       │   ├── resume_2.docx
│       │   └── resume_3.md
│       ├── french/             # French test resumes
│       │   ├── cv_1.pdf
│       │   ├── cv_2.yml
│       │   └── cv_3.txt
│       └── mixed/              # Multi-language test cases
├── .ai/                        # AI development artifacts
│   └── debug-log.md           # Development debugging log
├── .gitignore                  # Git ignore patterns
├── requirements.txt            # Python dependencies
├── CLAUDE.md                   # Development instructions for Claude
└── README.md                   # User documentation
```

## Key Directories Explained

### `/resume_extractor/` - Main Application Package
Core business logic organized by functional responsibility:
- **components/** - Processing engines (ingestion → parsing → consolidation)
- **schemas/** - Data structure definitions and validation
- **ui/** - Interactive user interface components
- **utils/** - Shared utilities and configuration

### `/tests/` - Comprehensive Test Suite
- **Unit tests** for each component module
- **Integration tests** for pipeline orchestration
- **Sample data** for testing various resume formats and languages
- **Test fixtures** for consistent test data setup

### `/data/` - Static Configuration
- **skill_map.json** - Bilingual skill equivalency definitions
- Future: Additional mapping files for education, certifications, etc.

### `/docs/` - Technical Documentation
- **architecture/** - System design and coding standards
- **prd/** - Product requirements (sharded by feature)
- **stories/** - Development tasks and acceptance criteria

## Module Dependencies

```
main.py
├── pipeline.py
│   ├── components/
│   │   ├── ingestion.py
│   │   ├── parsing.py (→ spacy, langdetect)
│   │   └── consolidation.py (→ data/skill_map.json)
│   ├── ui/
│   │   ├── conflict_resolver.py (→ questionary)
│   │   └── elicitation.py (→ questionary)
│   ├── schemas/master_schema.py
│   └── utils/logging_config.py
```

## File Naming Conventions

### Python Modules
- **snake_case** for all Python files
- **Descriptive names** reflecting primary class or function
- **Component organization** by functional area

### Test Files
- **test_** prefix for all test modules
- **Mirror source structure** in test directory organization
- **sample_** prefix for test data files

### Documentation
- **kebab-case** for markdown files
- **Descriptive names** for architecture docs
- **Hierarchical organization** matching system components

## Entry Points & Execution

### Primary Execution
```bash
python -m resume_extractor.main /path/to/resume/directory
```

### Development Testing
```bash
pytest tests/                    # Run all tests
pytest tests/test_parsing.py    # Run specific module tests
```

### Code Quality
```bash
black resume_extractor/ tests/  # Format code
ruff check resume_extractor/    # Lint code
```