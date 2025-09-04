# validate-next-story Task
**BMAD Core Task - Scrum Master Agent**

## Purpose
Validate the next development story is ready for implementation, ensuring all prerequisites are met and requirements are clear before engaging development agents.

## Prerequisites Check
- [ ] Story definition exists in `docs/stories/` or requirements documentation  
- [ ] Story acceptance criteria are clearly defined
- [ ] Dependencies from previous stories are satisfied
- [ ] Technical specifications are complete
- [ ] Agent knowledge base is updated for target agent
- [ ] Test strategy is documented

## Story Validation Criteria

### Story 2.1 - HELIOS Orchestrator (Next Story)
**Validate the following:**

#### Requirements Clarity
- [ ] Session management requirements clearly specified
- [ ] Command routing interface defined (`/start`, `/ingest`, `/discover`, `/analyze`, `/build`)
- [ ] Integration points with Profile Ingestor (Story 1.1) documented
- [ ] API contract specifications complete
- [ ] Error handling and edge cases identified

#### Technical Readiness
- [ ] Service architecture design approved (FastAPI, SQLite/PostgreSQL)
- [ ] Database schema for session management designed
- [ ] Agent communication protocols defined
- [ ] Performance requirements specified (<2s response time)
- [ ] Security considerations documented

#### Dependencies Satisfied
- [ ] Story 1.1 (Profile Ingestor) - ✅ COMPLETED (208 tests, 99% pass)
- [ ] Master Career Database schema available - ✅ Available  
- [ ] Development environment ready - ✅ Ready
- [ ] Agent knowledge base accessible - ✅ Available

#### Development Environment
- [ ] `services/orchestrator/` directory ready for creation
- [ ] Docker/FastAPI development setup validated
- [ ] Database connection and migration tools ready
- [ ] Testing framework available (pytest)
- [ ] CI/CD pipeline considerations addressed

#### Quality Gates Defined
- [ ] Unit test coverage target: >95%
- [ ] Integration test scenarios defined
- [ ] Performance benchmarks established
- [ ] Code quality standards (Black, Ruff) ready
- [ ] Review process defined

## Validation Process

### Step 1: Story Prerequisites
Review `docs/stories/MVP-Sequential-4Week-Plan.md` Day 1-5 tasks for Story 2.1:
- Session management design
- Command routing implementation  
- Profile Ingestor integration
- Database setup and persistence
- API documentation and testing

### Step 2: Technical Validation  
- Verify all technical specifications are implementable
- Confirm development tools and frameworks are available
- Validate integration points with existing services
- Check resource availability and constraints

### Step 3: Quality Assurance Readiness
- Ensure test scenarios are defined
- Confirm QA criteria and acceptance tests
- Validate deployment and monitoring strategy
- Check rollback and error recovery procedures

## Decision Matrix

### ✅ READY FOR DEVELOPMENT
**Criteria**: All validation checks pass, no critical blockers
**Next Action**: Transform to development agent for Story 2.1 implementation
**Command**: `*agent dev` or specific development agent

### ⚠️ NEEDS CLARIFICATION  
**Criteria**: Minor issues or clarifications needed
**Next Action**: Address questions, update requirements, re-validate
**Command**: Continue with SM agent to resolve issues

### ❌ BLOCKED
**Criteria**: Critical dependencies missing or requirements unclear
**Next Action**: Escalate blockers, update story definition
**Command**: Address blockers before proceeding

## Post-Validation Actions

### If READY:
1. Update story status to "In Development" in `bmad-core/core-config.yaml`
2. Create development branch (if using git)
3. Transform to appropriate development agent
4. Begin Day 1 tasks from MVP-Sequential plan

### If NOT READY:
1. Document specific blockers and issues
2. Create action items to resolve blockers  
3. Update story requirements as needed
4. Schedule re-validation when blockers resolved

## Scrum Master Agent Cycle
```
SM (validate-next-story) → Dev Agent (implement) → QA Agent (test) → SM (validate-completion) → Next Story
```

## Story 2.1 Specific Validation

**Story**: HELIOS Orchestrator Service  
**Epic**: Intelligence & Analysis Layer  
**Priority**: HIGH (foundation for other agents)  
**Estimated Effort**: 5 days (Week 1 of MVP plan)  
**Dependencies**: Story 1.1 (COMPLETED)  

**Key Implementation Components**:
1. FastAPI service setup with health checks
2. Session state management (SQLite → PostgreSQL transition)
3. Command parsing and routing system
4. Integration with Profile Ingestor service
5. API documentation and client SDK preparation

**Success Criteria**:
- [ ] All basic commands (`/start`, `/ingest`, `/status`) working
- [ ] Session persistence across service restarts  
- [ ] Integration with Profile Ingestor successful
- [ ] API documentation complete
- [ ] >95% test coverage achieved
- [ ] Response time <2 seconds for all operations

## Next Steps After Validation
1. If validated: `*agent dev` → Begin Story 2.1 implementation
2. During development: Daily check-ins with SM agent  
3. After implementation: `*agent qa` → Comprehensive testing
4. After QA: `*agent sm` → Story completion validation
5. Repeat cycle for Story 2.2 (STRATEGIST)

---

**VALIDATION STATUS**: ⏳ PENDING - Run this task to validate Story 2.1 readiness