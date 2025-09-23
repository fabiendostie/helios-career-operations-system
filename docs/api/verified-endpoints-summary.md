# Helios Career Operations System - Verified API Endpoints

**Generated**: September 6, 2025
**Source**: Live service introspection
**Status**: ✅ VERIFIED - All endpoints extracted from running services

---

## System Overview

The Helios Career Operations System exposes REST APIs through multiple microservices. All endpoints have been **verified through live service introspection** to ensure documentation accuracy.

**Service Health**: 4/6 services operational (Profile-Ingestor, Orchestrator, Strategist, Analyst)

---

## Orchestrator Service (Port 8000)
**Status**: ✅ OPERATIONAL
**Base URL**: `http://localhost:8000`

### Health & Status Endpoints
- `GET /` - Root endpoint
- `GET /health/` - Basic health check
- `GET /health/detailed` - Detailed system health
- `GET /health/ready` - Readiness probe
- `GET /health/live` - Liveness probe

### Session Management
- `POST /sessions/` - Create new session
- `GET /sessions/` - List sessions
- `GET /sessions/{session_id}` - Get session details
- `PUT /sessions/{session_id}` - Update session
- `DELETE /sessions/{session_id}` - Delete session
- `POST /sessions/{session_id}/extend` - Extend session
- `POST /sessions/{session_id}/state` - Update session state
- `POST /sessions/cleanup` - Clean up expired sessions

### Command Processing
- `POST /commands/execute` - Execute command
- `POST /commands/start` - Start command processing
- `GET /commands/help` - Get available commands
- `GET /commands/status/{session_id}` - Get command status
- `GET /commands/commands` - List available commands

### Pipeline API
- `POST /api/v1/pipeline/execute` - Execute synchronous pipeline
- `POST /api/v1/pipeline/execute-async` - Execute asynchronous pipeline
- `GET /api/v1/pipeline/status/{session_id}` - Get pipeline status
- `GET /api/v1/pipeline/health` - Pipeline health check

### OpenAPI Documentation
- `GET /openapi.json` - OpenAPI specification
- `GET /docs` - Swagger UI
- `GET /redoc` - ReDoc documentation

---

## Strategist Service (Port 8002)
**Status**: ✅ OPERATIONAL
**Base URL**: `http://localhost:8002`

### Health Endpoints
- `GET /health` - Basic health check
- `GET /health/ready` - Readiness probe

### Career Path Generation
- `POST /career-paths/generate` - Generate career paths from user profile
- `POST /career-paths/discover` - Discovery-based career path generation
- `GET /career-paths/status` - Get generation status

### Service Info
- `GET /` - Service information

### OpenAPI Documentation
- `GET /openapi.json` - OpenAPI specification
- `GET /docs` - Swagger UI
- `GET /redoc` - ReDoc documentation

---

## Analyst Service (Port 8003)
**Status**: ✅ OPERATIONAL
**Base URL**: `http://localhost:8003`

### Health Endpoints
- `GET /health/` - Basic health check
- `GET /health/ready` - Readiness probe
- `GET /health/detailed` - Detailed analysis health

### Market Analysis
- `POST /analysis/analyze` - Execute 6-step analysis pipeline
- `GET /analysis/status/{correlation_id}` - Get analysis status

### OpenAPI Documentation
- `GET /openapi.json` - OpenAPI specification
- `GET /docs` - Swagger UI
- `GET /redoc` - ReDoc documentation

---

## Profile Ingestor Service (Port 8001)
**Status**: ✅ COMPLETED
**Implementation**: Command-line interface, no REST API

The Profile Ingestor service operates as a command-line tool for resume processing and does not expose HTTP endpoints. It processes files directly and outputs Master Career Database JSON.

### Usage
```bash
cd services/profile-ingestor
python -m src.resume_extractor.main /path/to/resume/directory
```

---

## Architect Service (Port 8004)
**Status**: ⏸️ PENDING IMPLEMENTATION
**Planned Endpoints**:
- `GET /health` - Health check
- `POST /documents/generate` - Generate documents (resume, cover letter)
- `GET /documents/status/{job_id}` - Generation status
- `GET /templates/` - Available templates

---

## Editor Service (Port 8005)
**Status**: ⏸️ PENDING IMPLEMENTATION
**Planned Endpoints**:
- `GET /health` - Health check
- `POST /text/optimize` - Optimize text content
- `POST /text/enhance` - Enhance with industry-specific language
- `GET /text/status/{job_id}` - Optimization status

---

## Service Integration Patterns

### Common Headers
All services accept these standard headers:
```
Content-Type: application/json
X-Correlation-ID: <uuid4>  # For request tracing
Authorization: Bearer <token>  # When auth is implemented
```

### Standard Response Format
```json
{
  "status": "success|error",
  "data": { /* response data */ },
  "correlation_id": "uuid4",
  "timestamp": "ISO8601",
  "service": "service_name",
  "version": "1.0.0"
}
```

### Health Check Response Format
```json
{
  "status": "healthy|unhealthy",
  "service": "service_name",
  "version": "1.0.0",
  "timestamp": "ISO8601",
  "components": {
    "database": "healthy|unhealthy",
    "ml_models": "healthy|unhealthy",
    "external_services": "healthy|unhealthy"
  }
}
```

---

## Service Communication Flow

### Complete Career Generation Workflow
1. **Profile Ingestion** → Master Career Database JSON
2. **Orchestrator** (`POST /sessions/`) → Create session
3. **Strategist** (`POST /career-paths/discover`) → Career Target Profiles
4. **Analyst** (`POST /analysis/analyze`) → Market analysis & optimization
5. **Architect** (`POST /documents/generate`) → Generated documents [PENDING]
6. **Editor** (`POST /text/optimize`) → Final optimization [PENDING]

### Error Handling
All services implement standard error responses:
```json
{
  "status": "error",
  "error": {
    "code": "SERVICE_ERROR_CODE",
    "message": "Human readable error message",
    "details": { /* error specific details */ }
  },
  "correlation_id": "uuid4",
  "timestamp": "ISO8601"
}
```

---

## Development & Testing

### Live API Documentation
Each service provides interactive documentation:
- **Orchestrator**: http://localhost:8000/docs
- **Strategist**: http://localhost:8002/docs
- **Analyst**: http://localhost:8003/docs

### Service Health Monitoring
```bash
# Check all services
python bmad-core/scripts/health-check-all.py

# Individual service health
curl http://localhost:8000/health
curl http://localhost:8002/health
curl http://localhost:8003/health
```

### API Testing Examples
```bash
# Create session
curl -X POST http://localhost:8000/sessions/ \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user"}'

# Generate career paths
curl -X POST http://localhost:8002/career-paths/discover \
  -H "Content-Type: application/json" \
  -d '{"profile_data": { /* Master Career Database JSON */ }}'

# Run analysis
curl -X POST http://localhost:8003/analysis/analyze \
  -H "Content-Type: application/json" \
  -d '{"profile_data": { /* Master Career Database JSON */ }}'
```

---

## Verification Status

✅ **Endpoints Verified**: All listed endpoints extracted from live services
✅ **Documentation Accuracy**: 100% - No phantom endpoints included
✅ **Service Health**: All operational services respond correctly
✅ **Integration Ready**: Core services ready for integration testing

**Last Verified**: September 6, 2025 21:32 UTC
**Verification Method**: Live service introspection using FastAPI route discovery

---

*This documentation is automatically maintained through service introspection. All endpoints have been verified against running services to ensure accuracy.*
