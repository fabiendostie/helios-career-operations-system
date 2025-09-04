# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with the Helios Career Operations System.

## Project Overview

**Helios Career Operations System** is an AI-powered career intelligence platform built using [BMAD (Behavioral Model Analysis and Design)](https://github.com/bmad-code-org/BMAD-METHOD) methodology. The system transforms job searching through multiple specialized AI agents working in concert to provide intelligent career guidance, document optimization, and market analysis.

## Architecture

The system follows a **microservices architecture with AI agent orchestration**:
1. **HELIOS Orchestrator** - Main controller maintaining session state
2. **PROFILE_INGESTOR** - Deep conversational profiling (Story 1.1 - COMPLETED)
3. **STRATEGIST** - Career path generation using skill adjacency modeling
4. **ANALYST** - Market correlation & resume optimization 
5. **ARCHITECT** - Document generation with ATS compliance
6. **EDITOR** - Granular text optimization

## Project Structure ([BMAD Standard](https://github.com/bmad-code-org/BMAD-METHOD))

```
helios-career-operations-system/
├── CLAUDE.md                           # This file
├── bmad-core/                          # BMAD methodology core
│   ├── core-config.yaml               # Main BMAD configuration
│   ├── agents/                         # Agent configurations
│   ├── config/                         # System configurations
│   ├── templates/                      # Code/document templates
│   └── workflows/                      # BMAD workflows
├── docs/                               # BMAD Documentation Structure
│   ├── 00-project-overview/           # Project overview documents
│   ├── 01-requirements/               # PRDs, user stories, requirements
│   ├── 02-architecture/               # Architecture, tech stack
│   ├── 03-design/                     # BMAD analysis, design docs
│   ├── 04-implementation/             # Implementation guides
│   ├── 05-testing/                    # Testing strategies, plans
│   ├── 06-deployment/                 # Deployment guides
│   └── 07-operations/                 # Operations, monitoring
├── knowledge-base/                     # AI Knowledge Management
│   ├── agent-knowledge/               # Individual agent knowledge docs
│   └── domain-knowledge/              # Career domain expertise
├── services/                          # Microservices Architecture
│   ├── profile-ingestor/              # Story 1.1 - Data Acquisition (COMPLETED)
│   │   ├── src/resume_extractor/      # Original implementation
│   │   ├── tests/                     # Comprehensive test suite
│   │   ├── data/                      # Skill mapping, configs
│   │   └── requirements.txt           # Dependencies
│   ├── orchestrator/                  # HELIOS main orchestrator
│   ├── strategist/                    # Career strategy generation
│   ├── analyst/                       # Market analysis & optimization
│   ├── architect/                     # Document generation
│   └── editor/                        # Text optimization
├── infrastructure/                    # Infrastructure as Code
│   ├── docker/                        # Container configurations
│   ├── k8s/                          # Kubernetes manifests
│   └── terraform/                     # Cloud infrastructure
└── scripts/                          # Automation Scripts
    ├── deployment/                    # Deployment automation
    ├── migration/                     # Data migration scripts
    └── setup/                         # Environment setup
```

## Development Commands

### Story 1.1 (COMPLETED) - Profile Ingestor Service
```bash
# Navigate to completed service
cd services/profile-ingestor/

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Unix/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy models (using smaller models for compatibility)
python -m spacy download en_core_web_sm
python -m spacy download fr_core_news_sm

# Run tests (208 tests, 99% pass rate)
pytest

# Run the data acquisition service
python -m src.resume_extractor.main /path/to/resume/directory
```

### [BMAD](https://github.com/bmad-code-org/BMAD-METHOD) Agent Development
```bash
# Check BMAD configuration
cat bmad-core/core-config.yaml

# Access agent knowledge base
ls knowledge-base/agent-knowledge/

# Review project documentation
ls docs/01-requirements/
ls docs/02-architecture/
```

## Tech Stack

- **Python 3.13.1** - Core language
- **spaCy 4.0.2** - NLP processing (en_core_web_sm, fr_core_news_sm)
- **FastAPI** - Microservices API framework
- **PostgreSQL** - Primary database
- **Redis** - Session state & caching
- **Docker/Kubernetes** - Containerization & orchestration
- **Questionary 2.1.0** - Interactive CLI prompts
- **pytest 9.0.1** - Testing framework

## Key Design Patterns

- **[BMAD Methodology](https://github.com/bmad-code-org/BMAD-METHOD)** - Behavioral Model Analysis and Design
- **Microservices Architecture** - Independent, scalable services
- **Agent Orchestration** - HELIOS coordinates specialized agents
- **Pipeline Architecture** - Sequential data processing stages
- **Strategy Pattern** - Modular parsing and processing

## Current Status

✅ **Story 1.1 - COMPLETED**: Profile Ingestor Service (Data Acquisition)
- Multi-format resume processing (PDF, DOCX, MD, TXT, YAML, JSON)
- Bilingual NLP processing (English/French)
- Interactive conflict resolution
- Skill mapping with fuzzy matching
- Schema-validated JSON output
- 208 tests with 99% pass rate

🔄 **Next Stories**: Orchestrator, Strategist, Analyst, Architect, Editor services

## Output Schema

The Profile Ingestor produces a Master Career Database JSON with:
- `work_experience[]` - Job roles with accomplishments and metrics
- `projects[]` - Project descriptions and outcomes  
- `skills_inventory{}` - Categorized skills with evidence pointers
- `strategic_metadata{}` - Job title variations, core competencies
- `holistic_profile{}` - Transversal projects, aspirations, motivators

## Important Notes

- Story 1.1 is fully implemented and tested - serves as foundation for other services
- All agent knowledge documents available in `knowledge-base/agent-knowledge/`
- [BMAD methodology](https://github.com/bmad-code-org/BMAD-METHOD) followed throughout - proper documentation structure
- System designed for 10,000+ users with microservices scalability
- Logging outputs to service-specific logs with centralized monitoring

## [BMAD](https://github.com/bmad-code-org/BMAD-METHOD) Agent Instructions

When working on this project:
1. Check `bmad-core/core-config.yaml` for current agent status
2. Reference agent knowledge documents in `knowledge-base/agent-knowledge/`
3. Follow [BMAD](https://github.com/bmad-code-org/BMAD-METHOD) documentation structure in `docs/`
4. Implement new services in `services/` following Story 1.1 pattern
5. Maintain test coverage >95% for all services