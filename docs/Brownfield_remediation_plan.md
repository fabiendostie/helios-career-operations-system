Of course. Here is a detailed brownfield workflow plan for the Helios Career Operations System, designed to address the findings in your validation reports and meet your specific requirements for testing, code quality, and version control.

This plan systematically stabilizes the existing components before proceeding to new development, ensuring a robust and reliable final product.

---
##  Helios Brownfield Remediation & Completion Plan

This workflow is divided into four phases:
1.  **Foundation & Remediation:** Establish project-wide standards and quality gates.
2.  **Service Stabilization:** Make existing but incomplete services fully operational and tested.
3.  **Core Integration & Resilience:** Implement critical cross-service patterns and integration tests.
4.  **New Feature Implementation:** Develop the remaining services based on the now-stable foundation.
5.  **Release Preparation:** Finalize documentation and prepare for deployment.

### Phase 0: Project Foundation & Remediation

**Goal:** Address foundational gaps in coding standards, quality checks, and documentation before modifying services.

1.  **Setup Code Quality & Pre-commit Hooks**
    * **Action:** Install `pre-commit`, `black` (formatter), and `flake8` (linter).
    * **Action:** Create a `.pre-commit-config.yaml` at the project root to automatically run `black` and `flake8` on every commit attempt. This enforces style and linting rules universally.
    * **Verification:** Make a test commit with style violations; the commit should fail. Make a clean commit; it should succeed.
    * **Git:** `git add .pre-commit-config.yaml pyproject.toml && git commit -m "chore: setup pre-commit hooks for linting and style" && git push`

2.  **Standardize Test & Coverage Requirements**
    * **Action:** Update the project's root `README.md` and `CONTRIBUTING.md` to formally state that **all services must meet or exceed 85% test coverage** and **all test suites must pass with at least an 85% success rate** (ideally 100%).
    * **Action:** Configure the CI/CD pipeline (e.g., in `.github/workflows/ci.yaml`) to fail if these coverage and pass-rate thresholds are not met on a pull request.
    * **Git:** `git add README.md CONTRIBUTING.md .github/workflows/ci.yaml && git commit -m "docs(quality): standardize test coverage and pass rate at 85%" && git push`

3.  **Document Missing Standards & Patterns**
    * **Agent:** `*agent architect`
    * **Action:** Create `docs/coding-standards.md`. Document the project's **naming conventions**, **error message formats**, and detailed **resilience patterns** (circuit breakers, retry logic with exponential backoff).
    * **Action:** Formally document that the project is **CLI/API-first** and a web UI is out of scope for the current MVP, resolving that ambiguity.
    * **Git:** `git add docs/coding-standards.md && git commit -m "docs(architect): define coding standards and resilience patterns" && git push`

---
### Phase 1: Service Stabilization

**Goal:** Bring the three architecturally-complete services (Orchestrator, Strategist, Analyst) to a fully operational and validated state.

1.  **Stabilize Orchestrator Service (Story 2.1)**
    * **Action:** Install the 6 missing dependencies (`fastapi`, `sqlalchemy`, etc.) using `pip install -r services/orchestrator/requirements.txt`.
    * **Action:** Run the existing test suite (`pytest`). Remediate any failing tests until the pass rate is >85%.
    * **Action:** Measure test coverage (`pytest --cov`). Write additional unit and integration tests to achieve >85% coverage.
    * **Verification:** The service starts correctly, and all tests pass with required coverage.
    * **Git:** `git add services/orchestrator/ && git commit -m "fix(orchestrator): install dependencies and stabilize test suite" && git push`

2.  **Set up Strategist Service (Story 2.2)**
    * **Action:** Create a script (`scripts/download_models.sh`) to download the required `all-MiniLM-L6-v2` model (2.8GB). Add the model directory to `.gitignore`.
    * **Action:** Run the script to download the model.
    * **Action:** Run the existing test suite. Remediate any failures.
    * **Action:** Measure and improve test coverage to meet the 85% target.
    * **Verification:** The service loads the model, and all tests pass with required coverage.
    * **Git:** `git add services/strategist/ scripts/download_models.sh .gitignore && git commit -m "feat(strategist): add model download script and stabilize service" && git push`

3.  **Set up Analyst Service (Story 2.3)**
    * **Action:** Update the `scripts/download_models.sh` script to also download the `spaCy en_core_web_sm` model.
    * **Action:** Run the script to download the model.
    * **Action:** Run the existing test suite. Remediate any failures.
    * **Action:** Measure and improve test coverage to meet the 85% target.
    * **Verification:** The 6-step pipeline executes successfully in tests, and all tests pass with required coverage.
    * **Git:** `git add services/analyst/ scripts/download_models.sh && git commit -m "feat(analyst): add model download and stabilize service" && git push`

---
### Phase 2: Core Integration & Resilience

**Goal:** Address the critical cross-service risks identified in the validation reports.

1.  **Implement LLM Fallback & Caching Strategy**
    * **Agent:** `*agent architect`
    * **Action:** Implement a resilient HTTP client wrapper to be used by the **Strategist** and **Analyst** services. This wrapper must include:
        * **Caching:** Redis caching for identical LLM prompts to reduce cost and latency.
        * **Retries:** Automatic retries with exponential backoff.
        * **Fallbacks:** Logic to fall back to a secondary LLM provider (e.g., from OpenAI to Anthropic) if the primary fails.
    * **Action:** Refactor the services to use this new client. Write tests for the fallback and caching logic.
    * **Verification:** Tests confirm that the system gracefully handles LLM API failures and uses the cache effectively.
    * **Git:** `git add . && git commit -m "feat(resilience): implement LLM client with caching and fallbacks" && git push`

2.  **Develop the Integration Test Suite**
    * **Agent:** `*agent qa`
    * **Action:** Create a new top-level `tests/integration` directory.
    * **Action:** Write integration tests that cover the primary workflow: **Orchestrator** receiving a command, calling the **Profile Ingestor**, then invoking the **Strategist** and **Analyst** services.
    * **Action:** Use Docker Compose (`docker-compose.yml`) to orchestrate the services and their dependencies (PostgreSQL, Redis) for a realistic testing environment.
    * **Verification:** The integration test suite runs successfully in the CI pipeline, with all services communicating as expected.
    * **Git:** `git add tests/integration/ docker-compose.yml && git commit -m "test(integration): create end-to-end agent workflow test suite" && git push`

---
### Phase 3: New Feature Implementation

**Goal:** Develop the remaining `Architect` and `Editor` services using the newly established standards.

1.  **Implement Architect Service (Story 2.4)**
    * **Agent:** `*agent dev`
    * **Action:** Follow a Test-Driven Development (TDD) approach. Start by writing failing tests for the core logic (ATS-compliant document generation).
    * **Action:** Implement the service logic, ensuring all new code meets the 85% test coverage and passes the pre-commit hooks.
    * **Action:** Add integration tests for this service to the main integration suite.
    * **Verification:** All unit and integration tests for the Architect service pass.
    * **Git:** `git add services/architect/ && git commit -m "feat(architect): implement architect service and tests" && git push`

2.  **Implement Editor Service (Story 2.5 - Assumed)**
    * **Agent:** `*agent dev`
    * **Action:** Repeat the TDD process for the Editor service.
    * **Action:** Implement the service logic, ensuring it meets all quality gates.
    * **Action:** Add its integration tests to the main suite.
    * **Verification:** All unit and integration tests for the Editor service pass.
    * **Git:** `git add services/editor/ && git commit -m "feat(editor): implement editor service and tests" && git push`

---
### Phase 4: Release Preparation

**Goal:** Finalize documentation and validate the entire system's operational readiness.

1.  **Finalize Runbooks**
    * **Agent:** `*agent po`
    * **Action:** Create detailed, step-by-step runbooks for:
        * **Database Migrations:** Include validation checks and a tested rollback script.
        * **System-wide Rollbacks:** Document the procedure for reverting a full deployment using feature flags and versioning.
    * **Verification:** Another team member can successfully follow the runbooks in a staging environment.
    * **Git:** `git add docs/runbooks/ && git commit -m "docs(ops): create detailed migration and rollback runbooks" && git push`

2.  **Final System Validation**
    * **Agent:** `*agent qa`
    * **Action:** Run the complete integration test suite.
    * **Action:** Perform manual exploratory testing on the primary workflows.
    * **Action:** (Optional) Run a load test to validate performance against the "1000 concurrent users" target.
    * **Verification:** The entire system is stable, performant, and meets all requirements. All QA gates in `docs/qa/gates` are updated to `PASS`.
    * **Git:** `git add docs/qa/gates/ && git commit -m "chore(qa): final validation complete, all gates pass" && git push`