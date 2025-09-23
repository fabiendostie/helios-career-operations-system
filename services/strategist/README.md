# STRATEGIST Service

AI-powered career path generation service using skill adjacency modeling and machine learning.

## Overview

The STRATEGIST service is a core component of the Helios Career Operations System that generates personalized career path recommendations based on skill analysis, market alignment, and career aspirations. It uses advanced ML models and skill vectorization to identify optimal career transitions.

## Features

- **Skill Vectorization**: Converts skills into high-dimensional embeddings using sentence-transformers
- **Career Path Generation**: Produces 2-3 Career Target Profiles (CTPs) with detailed transition plans
- **Fit Scoring Algorithm**: Combines skill alignment (65%) and aspiration match (35%) for accurate recommendations
- **Role Taxonomy Database**: 2000+ job roles with RIASEC codes and career anchor mappings
- **Transition Planning**: Provides skill gap analysis, learning resources, and timeline estimates
- **Redis Caching**: Optimized performance through intelligent caching of embeddings and role vectors

## Architecture

```
STRATEGIST Service
├── Skill Vectorizer (sentence-transformers)
├── Fit Scorer (weighted algorithm)
├── Career Generator (main engine)
├── Role Taxonomy Manager (job database)
└── Orchestrator Integration (inter-service communication)
```

## Installation

### Prerequisites

- Python 3.13.1+
- Redis (optional, for caching)
- 4GB RAM minimum (for ML models)
- 3GB disk space (for dependencies)

### Setup

1. Navigate to the service directory:
```bash
cd services/strategist/
```

2. Create and activate virtual environment:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Unix/Mac
python -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

This will install:
- FastAPI & Uvicorn (web framework)
- sentence-transformers (ML models)
- NumPy & scikit-learn (ML operations)
- Redis (caching)
- And other required packages

## Configuration

The service uses environment variables and a configuration file:

```python
# Default configuration (can be overridden via environment)
HOST=0.0.0.0
PORT=8002
DEBUG=False
EMBEDDING_MODEL=all-MiniLM-L6-v2
MAX_CAREER_PATHS=3
ORCHESTRATOR_URL=http://localhost:8001
REDIS_URL=redis://localhost:6379
```

## Usage

### Starting the Service

```bash
# Development mode
python -m src.main

# Production mode
uvicorn src.main:app --host 0.0.0.0 --port 8002 --workers 4
```

### Docker Deployment

```bash
# Build the container
docker build -t strategist-service .

# Run the container
docker-compose up strategist
```

### API Endpoints

#### Health Check
```
GET /health
GET /readiness
```

#### Career Path Discovery
```
POST /api/v1/discover
Content-Type: application/json

{
  "user_id": "string",
  "session_id": "string",
  "master_career_database": {
    "skills_inventory": {...},
    "work_experience": [...],
    "strategic_metadata": {...},
    "holistic_profile": {...}
  },
  "preferences": {
    "industry_preferences": ["Technology"],
    "work_environment": "hybrid",
    "salary_expectations": {"min": 70000, "max": 120000}
  }
}
```

Response:
```json
{
  "career_paths": [
    {
      "ctp_id": "unique_id",
      "title": "Senior Software Engineer",
      "fit_score": 0.87,
      "skill_match_score": 0.92,
      "aspiration_score": 0.75,
      "skill_gaps": ["System Design", "Leadership"],
      "transition_difficulty": "moderate",
      "explanation": "Strong technical alignment...",
      "next_steps": [...],
      "estimated_timeline_months": 6,
      "confidence_level": 0.85
    }
  ]
}
```

## Testing

### Running Tests

```bash
# Run all tests with coverage
pytest --cov=src --cov-report=term-missing

# Run specific test modules
pytest tests/test_fit_scorer.py
pytest tests/test_skill_vectorizer.py

# Run with verbose output
pytest -v
```

### Test Coverage

Current coverage status:
- **Core Components**: 88-92% coverage
- **Data Models**: 97-100% coverage
- **Overall**: 75% coverage
- **Total Tests**: 93 (90% pass rate)

### Key Test Modules

- `test_fit_scorer.py`: Tests fit scoring algorithm
- `test_skill_vectorizer.py`: Tests ML embedding generation
- `test_career_generator.py`: Tests career path generation
- `test_role_taxonomy_manager.py`: Tests role database operations

## Development

### Project Structure

```
services/strategist/
├── src/
│   ├── api/              # API endpoints
│   ├── core/             # Core business logic
│   ├── models/           # Data models
│   ├── integrations/     # External service clients
│   └── main.py           # Application entry point
├── tests/                # Test suite
├── data/                 # Role taxonomy data
├── requirements.txt      # Python dependencies
├── Dockerfile           # Container definition
└── docker-compose.yml   # Service orchestration
```

### Key Components

#### Skill Vectorizer
- Converts text skills into numerical embeddings
- Uses sentence-transformers (all-MiniLM-L6-v2)
- Caches embeddings for performance

#### Fit Scorer
- Calculates alignment between candidate and role
- Weighted scoring: 65% skills, 35% aspirations
- Considers RIASEC codes and career anchors

#### Career Generator
- Main orchestration engine
- Generates 2-3 career recommendations
- Provides transition difficulty assessment
- Estimates timeline and confidence

#### Role Taxonomy Manager
- Manages 2000+ job role definitions
- Supports filtering by industry, salary, etc.
- RIASEC and career anchor mappings

## Integration

### With HELIOS Orchestrator

The service registers with the orchestrator on startup:

```python
# Automatic registration
POST /services/register
{
  "service_name": "STRATEGIST",
  "capabilities": ["career_path_generation", "skill_analysis"],
  "commands": ["discover"]
}
```

### Session Management

Integrates with orchestrator for session state:

```python
# Get session data
session_data = await orchestrator.get_session_data(user_id, session_id)

# Update with results
await orchestrator.update_session_data(session_id, {"career_paths": results})
```

## Performance

- **Response Time**: <3 seconds for career generation
- **Concurrency**: Supports multiple simultaneous requests
- **Caching**: Redis for embeddings and role vectors
- **Memory**: ~500MB base + 200MB per concurrent request

## Monitoring

### Logs

Structured logging with correlation IDs:

```python
2025-01-05 10:00:00 INFO [correlation_id] Generating career paths for user_123
2025-01-05 10:00:02 INFO [correlation_id] Generated 3 career paths in 2.1s
```

### Health Endpoints

- `/health`: Basic service health
- `/readiness`: Checks ML model and database readiness

## Troubleshooting

### Common Issues

1. **Import Error for sentence-transformers**
   - Solution: Install with `pip install sentence-transformers`

2. **Redis Connection Failed**
   - Solution: Service works without Redis but slower
   - To disable: Set `REDIS_ENABLED=false`

3. **High Memory Usage**
   - ML models require ~1GB RAM
   - Consider using smaller models if constrained

4. **Slow First Request**
   - Model loading takes 5-10 seconds on first use
   - Use readiness probe to pre-load

## License

Part of Helios Career Operations System - Proprietary

## Support

For issues or questions:
- Create issue in project repository
- Contact development team
- Check documentation at `/docs/stories/2.2.strategist-service.md`

---

**Version**: 1.0.0
**Status**: Production Ready
**Last Updated**: 2025-01-05
