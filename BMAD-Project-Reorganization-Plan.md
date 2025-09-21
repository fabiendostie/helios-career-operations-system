# BMAD Project Reorganization Plan
# From resume_extractor to Helios Career Operations System

## Current Situation Analysis

### Problems with Current Structure:
1. **Project-in-Project**: Helios docs are nested inside resume_extractor
2. **No BMAD Standards**: Folder structure doesn't follow BMAD methodology
3. **Agent Access Issues**: BMAD agents won't find expected folder structure
4. **Unclear Hierarchy**: Unclear what's foundational vs. what's new development

## Proposed New Structure

### Root Level: `Helios/`
```
Helios/
├── README.md                           # Main project overview
├── CLAUDE.md                          # Main project CLAUDE.md
├── .gitignore
├── requirements.txt                    # Root project requirements
├── docker-compose.yml                 # Development environment
├──
├── docs/                              # BMAD Standard Documentation
│   ├── 00-project-overview/
│   │   ├── project-charter.md
│   │   ├── stakeholder-analysis.md
│   │   └── success-criteria.md
│   │
│   ├── 01-requirements/
│   │   ├── PRD-Helios-Career-Operations-System.md
│   │   ├── user-personas.md
│   │   ├── functional-requirements.md
│   │   └── non-functional-requirements.md
│   │
│   ├── 02-architecture/
│   │   ├── Architecture-Document.md
│   │   ├── system-context-diagram.md
│   │   ├── component-diagrams.md
│   │   ├── sequence-diagrams.md
│   │   └── deployment-architecture.md
│   │
│   ├── 03-design/
│   │   ├── BMAD-Analysis.md
│   │   ├── data-models.md
│   │   ├── api-specifications.md
│   │   ├── ui-wireframes/
│   │   └── agent-interaction-flows.md
│   │
│   ├── 04-implementation/
│   │   ├── Epic-Breakdown-User-Stories.md
│   │   ├── sprint-planning.md
│   │   ├── implementation-roadmap.md
│   │   ├── coding-standards.md
│   │   └── Tech-Stack-Specification.md
│   │
│   ├── 05-testing/
│   │   ├── test-strategy.md
│   │   ├── test-cases/
│   │   ├── performance-testing.md
│   │   └── security-testing.md
│   │
│   ├── 06-deployment/
│   │   ├── deployment-guide.md
│   │   ├── infrastructure-setup.md
│   │   ├── monitoring-setup.md
│   │   └── disaster-recovery.md
│   │
│   ├── 07-operations/
│   │   ├── runbook.md
│   │   ├── monitoring-guide.md
│   │   ├── troubleshooting.md
│   │   └── maintenance-procedures.md
│   │
│   └── 99-archive/
│       ├── meeting-notes/
│       ├── research/
│       └── deprecated/
│
├── knowledge-base/                     # Agent Knowledge Base
│   ├── agent-knowledge/
│   │   ├── Knowledge_Document_1_PROFILE_INGESTOR.md
│   │   ├── Knowledge_Document_2_STRATEGIST.md
│   │   ├── Knowledge_Document_3_ANALYST.md
│   │   ├── Knowledge_Document_4_ARCHITECT.md
│   │   └── Knowledge_Document_5_EDITOR.md
│   │
│   ├── domain-knowledge/
│   │   ├── Career_Operations_System.md
│   │   ├── Strategic Intelligence Framework.md
│   │   └── Ultimate Strategic Resume Intelligence System.md
│   │
│   ├── templates/
│   │   ├── resume-templates/
│   │   ├── cover-letter-templates/
│   │   └── linkedin-templates/
│   │
│   └── reference-data/
│       ├── skill-taxonomies/
│       ├── industry-data/
│       └── job-market-data/
│
├── services/                          # Microservices
│   ├── orchestrator/
│   │   ├── src/
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── profile-ingestor/              # Story 1.1 - Resume Extractor (COMPLETED)
│   │   ├── src/
│   │   │   ├── resume_extractor/      # Current resume_extractor code
│   │   │   │   ├── components/
│   │   │   │   ├── schemas/
│   │   │   │   ├── ui/
│   │   │   │   └── utils/
│   │   │   └── api/                   # New API wrapper
│   │   │       ├── main.py
│   │   │       ├── endpoints/
│   │   │       └── models/
│   │   ├── tests/                     # Current tests moved here
│   │   ├── data/
│   │   │   └── skill_map.json
│   │   ├── docs/
│   │   │   ├── story-1.1-completion-report.md
│   │   │   └── integration-guide.md
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── strategist/
│   │   ├── src/
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── analyst/
│   │   ├── src/
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── architect/
│   │   ├── src/
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   └── editor/
│       ├── src/
│       ├── tests/
│       ├── Dockerfile
│       └── requirements.txt
│
├── infrastructure/                    # Infrastructure as Code
│   ├── terraform/
│   │   ├── environments/
│   │   ├── modules/
│   │   └── variables.tf
│   │
│   ├── kubernetes/
│   │   ├── base/
│   │   ├── overlays/
│   │   └── helm-charts/
│   │
│   └── docker/
│       ├── docker-compose.dev.yml
│       ├── docker-compose.prod.yml
│       └── Dockerfiles/
│
├── data/                              # Data Storage
│   ├── sample-data/
│   │   ├── test-resumes/              # Current sample_resumes moved here
│   │   ├── mock-job-data/
│   │   └── reference-profiles/
│   │
│   ├── schemas/
│   │   ├── database-schemas/
│   │   ├── api-schemas/
│   │   └── message-schemas/
│   │
│   └── migrations/
│       ├── postgresql/
│       └── vector-db/
│
├── tools/                             # Development Tools
│   ├── scripts/
│   │   ├── setup-dev-env.sh
│   │   ├── run-tests.sh
│   │   └── deploy.sh
│   │
│   ├── generators/
│   │   ├── service-generator/
│   │   └── documentation-generator/
│   │
│   └── utilities/
│       ├── data-migration/
│       └── performance-testing/
│
├── output/                           # Generated Artifacts
│   ├── documents/
│   ├── reports/
│   └── analytics/
│
└── legacy/                           # Legacy Components (Current resume_extractor docs)
    ├── original-resume-extractor/
    │   ├── docs/                     # Current docs/ folder contents
    │   └── source-docs/              # Current source docs/ folder
    │
    └── migration-notes/
        ├── what-was-moved.md
        └── integration-points.md
```

## Migration Steps

### Step 1: Create New Root Structure
1. Create new root directory: `Helios/`
2. Set up BMAD standard folder structure
3. Move/copy Helios documentation to proper locations

### Step 2: Reposition resume_extractor as Story 1.1
1. Move resume_extractor code to `services/profile-ingestor/src/resume_extractor/`
2. Create API wrapper in `services/profile-ingestor/src/api/`
3. Move tests to `services/profile-ingestor/tests/`
4. Create Story 1.1 completion documentation

### Step 3: Reorganize Knowledge Base
1. Move agent knowledge documents to `knowledge-base/agent-knowledge/`
2. Move domain knowledge to `knowledge-base/domain-knowledge/`
3. Organize reference data and templates

### Step 4: Set Up Development Environment
1. Create root-level docker-compose.yml
2. Set up infrastructure as code
3. Create development scripts and tools

### Step 5: Update Documentation
1. Create new main README.md
2. Update all documentation paths and references
3. Create integration guides
4. Document the migration process

## Benefits of New Structure

### For BMAD Agents:
- **Standard Folder Layout**: Agents can find expected folders (`docs/`, `services/`, `knowledge-base/`)
- **Clear Documentation**: Proper BMAD documentation structure
- **Easy Navigation**: Logical organization by project phase
- **Agent Knowledge Access**: Centralized knowledge base

### For Development Team:
- **Clear Responsibilities**: Each service has its own folder
- **Standard Structure**: Consistent structure across all services
- **Proper Testing**: Tests co-located with services
- **Infrastructure as Code**: All deployment configs centralized

### For Project Management:
- **Story Tracking**: Each story maps to specific folders
- **Progress Visibility**: Clear completion status
- **Documentation Standards**: BMAD-compliant documentation
- **Knowledge Management**: Centralized knowledge base

## Implementation Priority

### Phase 1: Structure Creation (1 day)
- [ ] Create new root directory structure
- [ ] Set up BMAD documentation folders
- [ ] Create basic README and project files

### Phase 2: Code Migration (2 days)
- [ ] Move resume_extractor to profile-ingestor service
- [ ] Create API wrapper
- [ ] Update all import paths
- [ ] Verify tests still pass

### Phase 3: Documentation Migration (1 day)
- [ ] Move and organize all documentation
- [ ] Update cross-references
- [ ] Create migration documentation
- [ ] Update CLAUDE.md files

### Phase 4: Infrastructure Setup (1 day)
- [ ] Create docker-compose files
- [ ] Set up development environment
- [ ] Create utility scripts
- [ ] Test full development workflow

## Next Actions Required

1. **Approval**: Confirm this reorganization approach
2. **Backup**: Ensure current project is backed up
3. **Execute Migration**: Follow the 4-phase migration plan
4. **Verify**: Test that everything works in new structure
5. **Team Alignment**: Update team on new project structure

Would you like me to proceed with creating this new structure?
