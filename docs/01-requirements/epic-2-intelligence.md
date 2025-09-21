# Epic 2: Intelligence & Analysis Layer
**Status**: ⏳ PENDING
**Stories**: 2.1 (Orchestrator), 2.2 (Strategist), 2.3 (Analyst)
**Timeline**: Week 1-2 of MVP-Sequential Plan

## Overview
Build the core intelligence layer that transforms raw career data into actionable insights, career path recommendations, and optimization strategies.

## Planned Stories

### Story 2.1 - HELIOS Orchestrator Service ⏳
- **Status**: APPROVED (Story ready for development in docs/stories/2.1.helios-orchestrator.md)
- **Priority**: HIGH (foundation for other agents)
- **Acceptance Criteria**:
  1. The orchestrator must maintain session state across multiple interactions and service restarts
  2. The system must route commands (`/start`, `/ingest`, `/discover`, `/analyze`, `/build`) to appropriate services
  3. The orchestrator must handle 100+ concurrent user sessions with <2s response time
  4. The system must integrate seamlessly with Story 1.1 Profile Ingestor service
  5. The orchestrator must provide comprehensive API documentation and health monitoring
  6. The service must maintain >95% test coverage and follow all coding standards
  7. The orchestrator must implement proper error handling and graceful degradation
  8. The system must provide session persistence and recovery mechanisms

### Story 2.2 - STRATEGIST Agent ⏳
- **Status**: PENDING
- **Priority**: HIGH
- **Functionality**:
  - Skill adjacency modeling and vectorization
  - Career path generation (2-3 CTPs in MVP)
  - Fit scoring algorithm (skill + aspiration alignment)
  - Market-aligned role recommendations

### Story 2.3 - ANALYST Agent ⏳
- **Status**: PENDING
- **Priority**: HIGH
- **Functionality**:
  - Resume-to-market correlation analysis (3-step MVP pipeline)
  - ATS readiness scoring and optimization recommendations
  - Skill gap identification and strategic framing
  - Market positioning and competitive analysis

## Key Deliverables (Planned)
- [ ] Session management and orchestration system
- [ ] Career path generation with fit scoring
- [ ] Market analysis and optimization recommendations
- [ ] Agent communication protocols
- [ ] Performance benchmarks (<2s response time)

## Success Criteria
- [ ] End-to-end intelligence pipeline working
- [ ] Generate 2-3 relevant career paths with fit scores >75%
- [ ] ATS optimization recommendations with measurable impact
- [ ] Handle 100+ concurrent sessions
- [ ] Maintain >90% test coverage

## Dependencies
- ✅ Story 1.1 (Profile Ingestor) - COMPLETED
- [ ] Master Career Database API integration
- [ ] Agent knowledge base implementation
- [ ] Inter-agent communication framework

## Integration Points
- **Input**: Master Career Database from Profile Ingestor
- **Output**: Career insights, analysis reports, optimization recommendations
- **Consumers**: Document Generation agents (Architect, Editor)
- **Services**: `services/orchestrator/`, `services/strategist/`, `services/analyst/`

This epic establishes the core AI-powered intelligence that transforms career data into strategic insights and actionable recommendations.
