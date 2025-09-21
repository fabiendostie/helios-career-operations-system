# Source Tree Structure
# Helios Career Operations System

## Project Root Layout

```
helios-career-operations-system/
├── bmad-core/                          # BMAD methodology core
│   ├── core-config.yaml               # Main BMAD configuration
│   ├── agents/                         # Agent configurations
│   │   └── profile-ingestor.yaml      # Story 1.1 agent config
│   ├── templates/                      # Code/document templates
│   │   └── helios-agent-tmpl.yaml     # Agent template
│   └── workflows/                      # BMAD workflows
│       └── helios-development-workflow.md
├── docs/                               # BMAD Documentation Structure
│   ├── PRD.md                         # Main Product Requirements Document
│   ├── architecture.md                # Main Architecture Document
│   ├── 01-requirements/               # PRD shards and user stories
│   │   ├── PRD-Helios-Career-Operations-System.md
│   │   └── Epic-Breakdown-User-Stories.md
│   ├── 02-architecture/               # Architecture shards and specs
│   │   ├── Architecture-Document.md
│   │   ├── Tech-Stack-Specification.md
│   │   ├── coding-standards.md        # Dev agent required file
│   │   └── source-tree.md             # Dev agent required file
│   ├── 03-design/                     # BMAD analysis and design docs
│   │   └── BMAD-Analysis.md
│   ├── 04-implementation/             # Implementation guides
│   │   └── Integration-Guide.md
│   ├── 05-testing/                    # Testing strategies
│   ├── 06-deployment/                 # Deployment guides
│   └── 07-operations/                 # Operations monitoring
├── knowledge-base/                     # AI Knowledge Management
│   ├── agent-knowledge/               # Individual agent knowledge docs
│   │   ├── Knowledge_Document_1_PROFILE_INGESTOR.md
│   │   ├── Knowledge_Document_2_STRATEGIST.md
│   │   ├── Knowledge_Document_3_ANALYST.md
│   │   ├── Knowledge_Document_4_ARCHITECT.md
│   │   └── Knowledge_Document_5_EDITOR.md
│   └── domain-knowledge/              # Career domain expertise
├── services/                          # Microservices Architecture
│   ├── profile-ingestor/              # Story 1.1 - Data Acquisition (COMPLETED)
│   │   ├── src/                       # Original resume_extractor implementation
│   │   │   ├── __init__.py
│   │   │   ├── main.py                # CLI entry point
│   │   │   ├── pipeline.py            # Processing pipeline orchestration
│   │   │   ├── components/            # Core processing modules
│   │   │   │   ├── __init__.py
│   │   │   │   ├── ingestion.py       # File discovery and reading
│   │   │   │   ├── parsing.py         # NLP processing
│   │   │   │   ├── consolidation.py   # Data merging and conflict resolution
│   │   │   │   └── output_generator.py # JSON generation
│   │   │   ├── schemas/               # Data structure definitions
│   │   │   │   ├── __init__.py
│   │   │   │   └── master_schema.py   # Master Career Database schema
│   │   │   ├── ui/                    # User interface components
│   │   │   │   ├── __init__.py
│   │   │   │   ├── conflict_resolver.py # Interactive conflict resolution
│   │   │   │   └── elicitation.py     # Data gathering interviews
│   │   │   └── utils/                 # Shared utilities
│   │   │       └── logging_config.py  # Centralized logging
│   │   ├── tests/                     # Comprehensive test suite (208 tests, 99% pass)
│   │   ├── data/                      # Static data files
│   │   │   └── skill_map.json        # Bilingual skill mapping
│   │   └── requirements.txt           # Service dependencies
│   ├── orchestrator/                  # HELIOS main orchestrator (Story 2.1 - PENDING)
│   ├── strategist/                    # Career strategy generation (Story 2.2 - PENDING)
│   ├── analyst/                       # Market analysis & optimization (Story 2.3 - PENDING)
│   ├── architect/                     # Document generation (Story 2.4 - PENDING)
│   └── editor/                        # Text optimization (Story 2.5 - PENDING)
├── infrastructure/                    # Infrastructure as Code
│   ├── docker/                        # Container configurations
│   ├── k8s/                          # Kubernetes manifests
│   └── terraform/                     # Cloud infrastructure
├── scripts/                          # Automation Scripts
│   ├── deployment/                    # Deployment automation
│   ├── migration/                     # Data migration scripts
│   └── setup/                         # Environment setup
│       ├── bmad_init.py              # BMAD initialization script
│       ├── bmad_status.py            # Status reporting script
│       └── simple_status.py          # ASCII status script
├── .ai/                              # AI development artifacts
│   └── debug-log.md                  # Development debugging log
├── .gitignore                        # Git ignore patterns
├── package.json                      # NPM scripts for BMAD methodology
├── requirements.txt                  # Root Python dependencies
├── CLAUDE.md                         # Development instructions for Claude Code
└── README.md                         # Project overview and setup
```

## Key Directories Explained

### `/services/` - Microservices Architecture
Each agent gets its own service directory:
- **profile-ingestor/** - Story 1.1 (COMPLETED) - Resume data extraction and consolidation
- **orchestrator/** - HELIOS main controller (PENDING)
- **strategist/** - Career path generation (PENDING)
- **analyst/** - Market analysis pipeline (PENDING)
- **architect/** - Document generation (PENDING)
- **editor/** - Text optimization (PENDING)

### `/bmad-core/` - BMAD Methodology Core
- **core-config.yaml** - Main BMAD configuration following official format
- **agents/** - Individual agent configurations
- **templates/** - Code and document templates
- **workflows/** - Development process documentation

### `/knowledge-base/` - AI Agent Knowledge Management
- **agent-knowledge/** - Specialized knowledge documents for each agent
- **domain-knowledge/** - Career domain expertise and frameworks

### `/docs/` - BMAD Documentation Structure
Following official BMAD methodology:
- **01-requirements/** - PRD shards and user stories
- **02-architecture/** - Architecture shards and technical specifications
- **03-design/** - BMAD analysis and design documents
- **04-implementation/** - Integration and implementation guides
- **05-testing/** through **07-operations/** - Complete project lifecycle docs

### `/infrastructure/` - Infrastructure as Code
- **docker/** - Service containerization
- **k8s/** - Kubernetes deployment manifests
- **terraform/** - Cloud infrastructure provisioning

## Service Dependencies

```
HELIOS Orchestrator (Story 2.1)
├── Profile Ingestor Service (Story 1.1) ✅ COMPLETED
├── Strategist Service (Story 2.2)
├── Analyst Service (Story 2.3)
├── Architect Service (Story 2.4)
└── Editor Service (Story 2.5)
```

## Module Dependencies (Profile Ingestor - COMPLETED)

```
services/profile-ingestor/src/main.py
├── pipeline.py
│   ├── components/
│   │   ├── ingestion.py (→ pypdf, python-docx, PyYAML, mistune)
│   │   ├── parsing.py (→ spacy, langdetect)
│   │   ├── consolidation.py (→ fuzzywuzzy, data/skill_map.json)
│   │   └── output_generator.py (→ jsonschema)
│   ├── ui/
│   │   ├── conflict_resolver.py (→ questionary)
│   │   └── elicitation.py (→ questionary)
│   ├── schemas/master_schema.py
│   └── utils/logging_config.py
```

## File Naming Conventions

### Python Services
- **snake_case** for all Python files and directories
- **Descriptive names** reflecting primary function
- **Service organization** by agent responsibility

### BMAD Documentation
- **kebab-case** for markdown files
- **Numbered prefixes** for BMAD structure (01-requirements, 02-architecture)
- **Descriptive names** following BMAD conventions

### Agent Configuration
- **kebab-case** for YAML configuration files
- **agent-name.yaml** format for individual agent configs
- **Hierarchical organization** by agent type

## Entry Points & Execution

### Story 1.1 - Profile Ingestor (COMPLETED)
```bash
cd services/profile-ingestor/
python -m src.main /path/to/resume/directory
```

### BMAD Management
```bash
npm run install:bmad                 # Install all dependencies
npm run bmad:status                 # Check project status
python scripts/setup/bmad_init.py   # Initialize BMAD environment
```

### Development Testing
```bash
cd services/profile-ingestor/
pytest                              # Run all tests (208 tests, 99% pass)
pytest tests/test_parsing.py        # Run specific module tests
```

### Code Quality
```bash
npm run lint:python                 # Lint all Python code
npm run format:python               # Format all Python code
```

## Agent Communication Architecture

### Session Flow
```
User Command → HELIOS Orchestrator → Specific Agent → Response → User
```

### Inter-Agent Data Flow
```
Profile Ingestor → Master Career Database → RAG Storage
                                        ↓
Strategic → Analyst → Architect → Editor → Final Documents
```

## Development Workflow

### Story Implementation
1. Create service directory in `/services/`
2. Implement agent following `/bmad-core/templates/helios-agent-tmpl.yaml`
3. Add agent configuration to `/bmad-core/agents/`
4. Update knowledge base in `/knowledge-base/agent-knowledge/`
5. Create integration tests
6. Update story status in `bmad-core/core-config.yaml`

### Quality Gates
- Unit test coverage >95%
- Integration tests passing
- BMAD configuration compliance
- Documentation complete
- Agent knowledge base updated
