# AGENT HANDOFF PROMPT: HELIOS MVP IMPLEMENTATION
## CRITICAL: READ THIS ENTIRE DOCUMENT BEFORE TAKING ANY ACTION

### CONTEXT AND OBJECTIVE
You are tasked with implementing the approved MVP completion plan for the Helios Career Operations System. This is a production-critical implementation following BMAD methodology. The system is an AI-powered career intelligence platform with 1 fully operational service and 4 partially implemented services that require completion.

### PRIMARY DIRECTIVE
Complete all tasks marked as [TODO] and [IN-PROGRESS] in the approved MVP Backlog Report located at `C:\Users\fabie\Documents\Prompt_Engineering\job seeking\helios-career-operations-system\docs\mvp-backlog-report.md`

---

## ESSENTIAL DOCUMENTS - READ IN THIS ORDER

### 1. PROJECT CONFIGURATION AND STATUS
```yaml
primary_config: C:\Users\fabie\Documents\Prompt_Engineering\job seeking\helios-career-operations-system\bmad-core\core-config.yaml
approved_backlog: C:\Users\fabie\Documents\Prompt_Engineering\job seeking\helios-career-operations-system\docs\mvp-backlog-report.md
project_instructions: C:\Users\fabie\Documents\Prompt_Engineering\job seeking\helios-career-operations-system\CLAUDE.md
technical_handoff: C:\Users\fabie\Documents\Prompt_Engineering\job seeking\helios-career-operations-system\BMAD_PHASE_4_TECHNICAL_HANDOFF.md
```

### 2. REQUIREMENTS AND SPECIFICATIONS
```yaml
product_requirements: C:\Users\fabie\Documents\Prompt_Engineering\job seeking\helios-career-operations-system\docs\PRD.md
epic_breakdown: C:\Users\fabie\Documents\Prompt_Engineering\job seeking\helios-career-operations-system\docs\01-requirements\Epic-Breakdown-User-Stories.md
strategic_framework: C:\Users\fabie\Documents\Prompt_Engineering\job seeking\helios-career-operations-system\source docs\Knowledge\The_Strategic_Career_Co-Pilot_A_Complete_Playbook.md
```

### 3. SERVICE LOCATIONS
```yaml
services:
  profile_ingestor:
    path: C:\Users\fabie\Documents\Prompt_Engineering\job seeking\helios-career-operations-system\services\profile-ingestor\
    status: COMPLETE
    action: NO_ACTION_REQUIRED

  orchestrator:
    path: C:\Users\fabie\Documents\Prompt_Engineering\job seeking\helios-career-operations-system\services\orchestrator\
    status: IN_PROGRESS
    main: src\main.py
    tests: tests\
    requirements: requirements.txt

  strategist:
    path: C:\Users\fabie\Documents\Prompt_Engineering\job seeking\helios-career-operations-system\services\strategist\
    status: IN_PROGRESS
    main: src\main.py
    tests: tests\
    requirements: requirements.txt

  analyst:
    path: C:\Users\fabie\Documents\Prompt_Engineering\job seeking\helios-career-operations-system\services\analyst\
    status: IN_PROGRESS
    main: src\main.py
    tests: tests\
    requirements: requirements.txt

  architect:
    path: C:\Users\fabie\Documents\Prompt_Engineering\job seeking\helios-career-operations-system\services\architect\
    status: TODO
    main: src\main.py
    tests: tests\
    requirements: requirements.txt

  editor:
    path: C:\Users\fabie\Documents\Prompt_Engineering\job seeking\helios-career-operations-system\services\editor\
    status: TODO
    main: src\main.py
    tests: tests\
    requirements: requirements.txt
```

---

## IMPLEMENTATION PHASES - EXECUTE IN STRICT ORDER

### PHASE 1: COMPLETE IN-FLIGHT SERVICES [PRIORITY: P0]
**Timeline**: 1-2 weeks
**Branch Strategy**: Create feature branches for each service

#### TASK 1.1: FIX HELIOS ORCHESTRATOR
```yaml
service: orchestrator
branch: feature/fix-orchestrator-session-management
location: services\orchestrator\
critical_files:
  - src\core\session_manager.py
  - src\core\command_router.py
  - src\api\sessions.py
  - tests\test_session_manager.py

issues_to_fix:
  - session_persistence: "Redis connection not maintaining state between requests"
  - command_routing: "Routes not properly forwarding to all agent services"
  - error_recovery: "No graceful degradation on service failures"

verification_command: |
  cd services/orchestrator
  pytest tests/ -v
  python -m src.main  # Should start on port 8001
  curl http://localhost:8001/health  # Should return {"status": "healthy"}

success_criteria:
  - test_coverage: ">= 85%"
  - all_endpoints_functional: true
  - session_state_persists: true
  - inter_service_communication: "working with all deployed services"
```

#### TASK 1.2: STABILIZE STRATEGIST SERVICE
```yaml
service: strategist
branch: feature/fix-strategist-career-paths
location: services\strategist\
critical_files:
  - src\core\career_generator.py
  - src\core\skill_vectorizer.py
  - src\core\fit_scorer.py
  - tests\test_career_generator.py

issues_to_fix:
  - career_path_generation: "ML model predictions not generating valid CTPs"
  - constraint_filtering: "Filter logic not respecting user constraints"
  - fit_scoring: "Algorithm returning NaN values for certain inputs"

dependencies_check: |
  # Verify sentence-transformers is loaded
  python -c "from sentence_transformers import SentenceTransformer; model = SentenceTransformer('all-MiniLM-L6-v2'); print('Model loaded successfully')"

verification_command: |
  cd services/strategist
  pytest tests/test_career_generator.py -v
  python -m src.main  # Should start on port 8002
  # Test career path generation endpoint
  curl -X POST http://localhost:8002/api/v1/career-paths \
    -H "Content-Type: application/json" \
    -d '{"skills": ["Python", "FastAPI", "Docker"], "experience_years": 5}'

success_criteria:
  - generates_3_to_5_paths: true
  - fit_scores_valid: "all between 0.0 and 1.0"
  - ml_model_functional: true
  - response_time: "< 5 seconds"
```

#### TASK 1.3: DEBUG ANALYST SERVICE
```yaml
service: analyst
branch: feature/fix-analyst-pipeline
location: services\analyst\
critical_files:
  - src\core\resume_deconstructor.py
  - src\core\market_analyzer.py
  - src\core\skill_recalibrator.py
  - tests\test_analysis_pipeline.py

critical_issue: |
  # spaCy models failing to load - MUST FIX FIRST
  # Current code in resume_deconstructor.py:
  nlp = spacy.load("en_core_web_sm")  # Fails if model missing

  # Required fix:
  try:
      nlp = spacy.load("en_core_web_sm")
  except OSError:
      import subprocess
      subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
      nlp = spacy.load("en_core_web_sm")

pipeline_steps_to_implement:
  1_resume_deconstruction: "Parse and extract structured data"
  2_market_correlation: "Match skills to market demands"
  3_ats_optimization: "Score and optimize for ATS"
  4_skill_gap_analysis: "Identify missing skills"
  5_career_pathway_mapping: "Generate progression paths"
  6_compensation_benchmarking: "Analyze salary data"

verification_command: |
  cd services/analyst
  # First ensure spaCy models are installed
  python -m spacy download en_core_web_sm
  python -m spacy download fr_core_news_sm

  # Run tests
  pytest tests/ -v

  # Start service
  python -m src.main  # Should start on port 8003

success_criteria:
  - spacy_models_loaded: true
  - six_step_pipeline_functional: true
  - test_pass_rate: ">= 89%"
  - all_nlp_operations_working: true
```

### PHASE 2: IMPLEMENT MISSING CORE SERVICES [PRIORITY: P0]
**Timeline**: 2-3 weeks

#### TASK 2.1: BUILD ARCHITECT SERVICE
```yaml
service: architect
branch: feature/implement-architect-service
location: services\architect\
template_reference: services\profile-ingestor\  # Use as implementation pattern

implementation_requirements:
  document_generation:
    - resume_generator: "Create ATS-optimized resumes from master database"
    - cover_letter_generator: "Generate tailored cover letters"
    - template_engine: "Jinja2-based template rendering"
    - pdf_generation: "ReportLab for PDF output"

  ats_compliance:
    validation_rules:
      - single_column_layout: true
      - standard_fonts: ["Arial", "Calibri", "Times New Roman"]
      - no_headers_footers: true
      - no_tables_or_columns: true
      - keyword_density: "optimal between 2-3%"

  integration_points:
    - orchestrator: "Receive generation commands"
    - profile_ingestor: "Access master career database"
    - analyst: "Get optimization recommendations"
    - strategist: "Align with career paths"

files_to_create:
  - src\api\generation.py: "FastAPI endpoints for document generation"
  - src\core\document_generator.py: "Main generation logic"
  - src\core\template_engine.py: "Template management and rendering"
  - src\validation\ats_compliance.py: "ATS validation rules"
  - tests\test_document_generation.py: "Comprehensive test suite"
  - tests\test_ats_compliance.py: "ATS validation tests"

templates_location: src\templates\
template_structure: |
  templates/
  ├── resume/
  │   ├── classic.j2
  │   ├── modern.j2
  │   └── technical.j2
  └── cover_letter/
      ├── standard.j2
      └── technical.j2

verification_command: |
  cd services/architect
  pytest tests/ -v --cov=src --cov-report=term-missing
  python -m src.main  # Should start on port 8004

  # Test document generation
  curl -X POST http://localhost:8004/api/v1/generate/resume \
    -H "Content-Type: application/json" \
    -d @test_data/sample_profile.json

success_criteria:
  - generates_valid_pdf: true
  - ats_compliance_score: ">= 95%"
  - template_rendering_works: true
  - all_output_formats_supported: ["PDF", "DOCX", "MD"]
  - test_coverage: ">= 95%"
```

#### TASK 2.2: BUILD EDITOR SERVICE
```yaml
service: editor
branch: feature/implement-editor-service
location: services\editor\
reference_pattern: services\profile-ingestor\

implementation_requirements:
  text_optimization:
    - xyz_transformation: "Convert bullets to Verb+Metric+Outcome format"
    - weak_word_detection: "Identify and flag weak verbs"
    - action_verb_substitution: "Replace with high-impact verbs"
    - metric_extraction: "Extract and highlight quantifiable results"
    - keyword_optimization: "Ensure optimal keyword density"

  transformation_rules:
    xyz_model: |
      # Input: "Managed team"
      # Output: "Managed 12-person engineering team, increasing productivity by 25% through agile implementation"

    weak_words_to_replace:
      - responsible_for: "led|directed|orchestrated"
      - helped: "facilitated|enabled|accelerated"
      - worked_on: "engineered|developed|architected"
      - handled: "managed|orchestrated|optimized"

files_to_create:
  - src\api\editing.py: "FastAPI endpoints for text optimization"
  - src\core\text_optimizer.py: "Main optimization engine"
  - src\core\weak_word_detector.py: "Weak word detection logic"
  - src\core\metric_extractor.py: "Extract metrics from text"
  - src\data\action_verbs.yaml: "High-impact verb database"
  - tests\test_text_optimization.py: "Optimization tests"
  - tests\test_metric_extraction.py: "Metric extraction tests"

verification_command: |
  cd services/editor
  pytest tests/ -v --cov=src
  python -m src.main  # Should start on port 8005

  # Test text optimization
  curl -X POST http://localhost:8005/api/v1/optimize \
    -H "Content-Type: application/json" \
    -d '{"text": "Responsible for managing team", "mode": "xyz"}'

success_criteria:
  - xyz_transformation_accurate: true
  - weak_word_detection_rate: ">= 90%"
  - metric_extraction_precision: ">= 85%"
  - response_time: "< 500ms"
  - test_coverage: ">= 95%"
```

### PHASE 3: USER INTERFACE & INTEGRATION [PRIORITY: P0]
**Timeline**: 1 week

#### TASK 3.1: IMPLEMENT CLI INTERFACE
```yaml
component: cli
branch: feature/implement-cli
location: C:\Users\fabie\Documents\Prompt_Engineering\job seeking\helios-career-operations-system\cli\

implementation_requirements:
  command_structure:
    - /start: "Initialize new session"
    - /ingest: "Begin profile interview"
    - /discover: "Generate career paths"
    - /analyze {id}: "Deep market analysis"
    - /build resume: "Generate resume"
    - /build letter: "Generate cover letter"
    - /optimize "{text}": "Optimize text snippet"
    - /status: "Show session state"
    - /help: "Display available commands"

  technical_stack:
    - framework: "Click or Typer for CLI"
    - session_management: "Via orchestrator API"
    - output_formatting: "Rich library for terminal UI"
    - progress_indicators: "tqdm for progress bars"

files_to_create:
  - cli\__init__.py: "CLI package initialization"
  - cli\main.py: "Main CLI entry point"
  - cli\commands.py: "Command implementations"
  - cli\session.py: "Session management"
  - cli\formatters.py: "Output formatting utilities"
  - tests\test_cli.py: "CLI tests"

verification_command: |
  cd cli
  pytest tests/ -v
  python -m cli.main --help  # Should display all commands

  # Test full workflow
  python -m cli.main /start
  python -m cli.main /ingest --file ../test_data/sample_resume.pdf
  python -m cli.main /discover
  python -m cli.main /status

success_criteria:
  - all_commands_functional: true
  - session_persistence_works: true
  - error_handling_graceful: true
  - help_documentation_complete: true
```

#### TASK 3.2: END-TO-END INTEGRATION
```yaml
task: e2e_integration
branch: feature/e2e-integration
scope: entire_system

integration_requirements:
  service_communication:
    - orchestrator_routes_to_all_services: true
    - data_flows_correctly_between_services: true
    - error_propagation_handled: true
    - timeout_handling_implemented: true

  data_flow_verification: |
    1. CLI -> Orchestrator: Command received
    2. Orchestrator -> Profile Ingestor: Process resume
    3. Profile Ingestor -> Orchestrator: Return master database
    4. Orchestrator -> Strategist: Generate career paths
    5. Strategist -> Orchestrator: Return CTPs
    6. Orchestrator -> Analyst: Analyze career fit
    7. Analyst -> Orchestrator: Return analysis
    8. Orchestrator -> Architect: Generate documents
    9. Architect -> Orchestrator: Return documents
    10. Orchestrator -> Editor: Optimize content
    11. Editor -> Orchestrator: Return optimized text
    12. Orchestrator -> CLI: Display results

test_scenarios:
  - full_journey_test: "Complete user flow from resume upload to document generation"
  - service_failure_recovery: "Test graceful degradation when service unavailable"
  - concurrent_user_test: "Test with 10 simultaneous users"
  - data_consistency_test: "Verify data integrity across services"

verification_command: |
  # Start all services
  docker-compose up -d

  # Run integration tests
  pytest tests/integration/ -v

  # Run end-to-end test
  python tests/e2e/test_full_journey.py

success_criteria:
  - all_services_communicating: true
  - full_journey_completes: "< 60 seconds"
  - no_data_loss: true
  - error_recovery_works: true
```

### PHASE 4: PRODUCTION READINESS [PRIORITY: P1]
**Timeline**: 1 week

#### TASK 4.1: TESTING & VALIDATION
```yaml
task: comprehensive_testing
scope: all_services

testing_requirements:
  coverage_targets:
    - unit_test_coverage: ">= 95%"
    - integration_test_coverage: ">= 85%"
    - e2e_test_coverage: ">= 75%"

  performance_testing:
    - load_test: "100 concurrent users"
    - stress_test: "Find breaking point"
    - endurance_test: "24-hour continuous operation"

  security_testing:
    - vulnerability_scan: "Using OWASP ZAP"
    - dependency_audit: "pip-audit for all services"
    - secrets_scan: "Ensure no hardcoded credentials"

verification_command: |
  # Run all tests with coverage
  pytest --cov=. --cov-report=html --cov-report=term

  # Run load tests
  locust -f tests/load/locustfile.py --host=http://localhost:8001

  # Security scan
  pip-audit
  bandit -r services/
```

#### TASK 4.2: DEPLOYMENT PIPELINE
```yaml
task: deployment_setup
location: .github\workflows\

requirements:
  ci_cd_pipeline:
    - automated_testing: "On every PR"
    - build_validation: "Docker builds succeed"
    - deployment_staging: "Auto-deploy to staging"
    - deployment_production: "Manual approval required"

  infrastructure:
    - kubernetes_manifests: "infrastructure/k8s/"
    - docker_compose: "docker-compose.yml"
    - environment_configs: ".env.example"
    - secrets_management: "Via GitHub Secrets"

verification_command: |
  # Validate K8s manifests
  kubectl apply --dry-run=client -f infrastructure/k8s/

  # Test Docker builds
  docker-compose build

  # Validate CI/CD
  act -j test  # Run GitHub Actions locally
```

---

## CRITICAL SUCCESS FACTORS

### 1. DEPENDENCY MANAGEMENT
```bash
# Always verify dependencies before starting work on a service
cd services/{service_name}
pip install -r requirements.txt
python -c "import fastapi, pydantic, sqlalchemy; print('Core dependencies OK')"
```

### 2. TEST-DRIVEN DEVELOPMENT
```python
# Write tests FIRST for every new feature
# Example test structure:
def test_feature_x():
    # Arrange
    input_data = {...}
    expected_output = {...}

    # Act
    result = feature_x(input_data)

    # Assert
    assert result == expected_output
```

### 3. DOCUMENTATION UPDATES
```yaml
update_after_each_task:
  - bmad-core/core-config.yaml: "Update service status"
  - docs/stories/{story}.md: "Mark as complete"
  - README.md: "Update if API changes"
```

### 4. GIT WORKFLOW
```bash
# For EVERY task:
git checkout development
git pull origin development
git checkout -b feature/{task-description}
# ... implement feature ...
git add .
git commit -m "feat(service): implement {specific feature}"
git push -u origin feature/{task-description}
# Create PR to development branch
```

---

## ERROR RECOVERY PROCEDURES

### IF SPACY MODELS FAIL:
```python
# Add to Dockerfile:
RUN python -m spacy download en_core_web_sm
RUN python -m spacy download fr_core_news_sm

# Add to code:
import spacy
import subprocess

def load_spacy_model(model_name):
    try:
        return spacy.load(model_name)
    except OSError:
        subprocess.run(["python", "-m", "spacy", "download", model_name])
        return spacy.load(model_name)
```

### IF ML MODELS ARE SLOW:
```python
# Implement lazy loading:
class ModelLoader:
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer('all-MiniLM-L6-v2')
        return self._model
```

### IF SERVICES DON'T COMMUNICATE:
```yaml
verify_networking:
  - check_docker_network: "docker network ls"
  - inspect_service_logs: "docker-compose logs {service_name}"
  - test_direct_connection: "curl http://{service_name}:{port}/health"
  - verify_environment_vars: "docker-compose config"
```

---

## VALIDATION CHECKPOINTS

### After Each Service Completion:
1. ✅ All tests passing (>= 85% coverage)
2. ✅ Service starts without errors
3. ✅ Health endpoint returns 200
4. ✅ Can communicate with orchestrator
5. ✅ Documentation updated
6. ✅ PR created and reviewed

### Before Moving to Next Phase:
1. ✅ All services in phase are functional
2. ✅ Integration tests passing
3. ✅ Performance benchmarks met
4. ✅ No critical security issues
5. ✅ Rollback plan documented

---

## CONTACT FOR BLOCKERS

If you encounter blocking issues:
1. First consult: `knowledge-base/troubleshooting/phase-3-lessons-learned.md`
2. Check error patterns in: `bmad-core/verification-results/`
3. Review similar fixes in git history: `git log --grep="fix"`

---

## FINAL CHECKLIST BEFORE DECLARING MVP COMPLETE

```yaml
mvp_completion_criteria:
  functional_requirements:
    - [ ] User can upload resume and receive parsed profile
    - [ ] System generates 3-5 career path recommendations
    - [ ] User can request market analysis for chosen path
    - [ ] System generates ATS-optimized resume
    - [ ] System generates tailored cover letter
    - [ ] User can optimize individual text snippets
    - [ ] CLI provides access to all features

  non_functional_requirements:
    - [ ] Response time < 5 seconds for standard operations
    - [ ] Document generation < 30 seconds
    - [ ] 95% test coverage across all services
    - [ ] All services containerized and deployable
    - [ ] Monitoring and alerting operational
    - [ ] Error recovery mechanisms in place

  documentation:
    - [ ] All APIs documented
    - [ ] User guide complete
    - [ ] Deployment guide written
    - [ ] Troubleshooting guide updated
```

---

## COMPLETION CONFIRMATION

Upon completing all tasks:
1. Run full system validation: `pytest tests/ -v --cov=.`
2. Generate completion report: `python scripts/generate_completion_report.py`
3. Update status: Set `bmad-core/core-config.yaml` MVP status to "COMPLETE"
4. Create PR: With title "feat: MVP implementation complete"

---

END OF HANDOFF PROMPT

IMPORTANT: This prompt contains all necessary information to complete the MVP. Follow the phases in order, verify success criteria after each task, and maintain BMAD compliance throughout. The system's success depends on methodical execution of these tasks.