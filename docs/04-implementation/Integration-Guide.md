# Integration Guide
# Helios Career Operations System

## Story 1.1 Integration Points
### Profile Ingestor Service (COMPLETED)

The Profile Ingestor service is complete and ready for integration with the Helios orchestrator system.

#### Service Location
```
services/profile-ingestor/
├── src/resume_extractor/           # Core implementation
├── tests/                         # 208 tests (99% pass rate)
├── data/                          # Skill mapping configs
└── requirements.txt               # Dependencies
```

#### Integration API Contract

**Input:**
- Directory path containing resumes (PDF, DOCX, MD, TXT, YAML, JSON)
- Optional configuration parameters

**Output:**
- Master Career Database (JSON)
- Processing logs and metadata

**Entry Point:**
```python
from services.profile_ingestor.src.resume_extractor.pipeline import Pipeline
from pathlib import Path

# Initialize pipeline
pipeline = Pipeline()

# Process resume directory
result = pipeline.process(Path("/path/to/resumes"))

# Access Master Career Database
master_db = result.master_career_database
```

#### REST API Wrapper (Recommended)

Create FastAPI wrapper for microservices integration:

```python
# services/profile-ingestor/api/main.py
from fastapi import FastAPI, File, UploadFile
from typing import List
import tempfile
import shutil

app = FastAPI(title="Profile Ingestor Service", version="1.0.0")

@app.post("/ingest/directory")
async def ingest_directory(directory_path: str):
    """Ingest resumes from directory path"""
    # Implementation here
    pass

@app.post("/ingest/files")  
async def ingest_files(files: List[UploadFile] = File(...)):
    """Ingest uploaded resume files"""
    # Implementation here
    pass

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "profile-ingestor"}
```

#### Database Integration

The Master Career Database JSON should be stored in PostgreSQL for RAG access:

```sql
-- Master career profiles table
CREATE TABLE career_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    profile_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    version INTEGER DEFAULT 1
);

-- Indexes for efficient RAG queries
CREATE INDEX idx_career_profiles_user_id ON career_profiles(user_id);
CREATE INDEX idx_career_profiles_skills ON career_profiles USING GIN ((profile_data -> 'skills_inventory'));
CREATE INDEX idx_career_profiles_experience ON career_profiles USING GIN ((profile_data -> 'work_experience'));
```

#### Vector Embeddings for RAG

Create embeddings from Master Career Database for semantic search:

```python
# scripts/setup/create_embeddings.py
import json
from sentence_transformers import SentenceTransformer
import numpy as np

def create_career_embeddings(master_db_path):
    """Create vector embeddings from Master Career Database"""
    
    # Load sentence transformer model
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Load career data
    with open(master_db_path, 'r') as f:
        career_data = json.load(f)
    
    # Extract text for embedding
    text_chunks = []
    
    # Work experience
    for exp in career_data.get('work_experience', []):
        text_chunks.append(f"{exp.get('company', '')} {exp.get('title', '')} {exp.get('description', '')}")
    
    # Skills
    for category, skills in career_data.get('skills_inventory', {}).items():
        text_chunks.append(f"{category}: {', '.join(skills)}")
    
    # Projects
    for project in career_data.get('projects', []):
        text_chunks.append(f"{project.get('name', '')} {project.get('description', '')}")
    
    # Create embeddings
    embeddings = model.encode(text_chunks)
    
    return text_chunks, embeddings
```

## Agent Communication Protocol

### Message Format
```json
{
  "agent_id": "PROFILE_INGESTOR",
  "session_id": "uuid",
  "command": "/ingest",
  "payload": {
    "directory_path": "/path/to/resumes",
    "options": {
      "languages": ["en", "fr"],
      "conflict_resolution": "interactive"
    }
  },
  "timestamp": "2025-01-04T12:00:00Z"
}
```

### Response Format
```json
{
  "agent_id": "PROFILE_INGESTOR", 
  "session_id": "uuid",
  "status": "success",
  "result": {
    "master_career_database": { /* JSON object */ },
    "processing_metadata": {
      "files_processed": 5,
      "conflicts_resolved": 2,
      "skills_mapped": 45
    }
  },
  "timestamp": "2025-01-04T12:05:00Z"
}
```

### Error Handling
```json
{
  "agent_id": "PROFILE_INGESTOR",
  "session_id": "uuid", 
  "status": "error",
  "error": {
    "code": "PROCESSING_ERROR",
    "message": "Failed to parse PDF file",
    "details": { /* error context */ }
  },
  "timestamp": "2025-01-04T12:02:00Z"
}
```

## Next Agent Integrations

### Story 2.1: HELIOS Orchestrator
- **Role**: Main controller maintaining session state
- **Integration**: Receives Master Career Database from Profile Ingestor
- **Commands**: `/session`, `/status`, `/route`

### Story 2.2: STRATEGIST Agent  
- **Role**: Career path generation using skill adjacency modeling
- **Integration**: Uses Master Career Database for skill analysis
- **Commands**: `/discover`, `/pathways`, `/adjacency`

### Story 2.3: ANALYST Agent
- **Role**: Market correlation & resume optimization
- **Integration**: Analyzes career data against market trends
- **Commands**: `/analyze`, `/optimize`, `/market`

### Story 2.4: ARCHITECT Agent
- **Role**: Document generation with ATS compliance  
- **Integration**: Generates documents from Master Career Database
- **Commands**: `/build`, `/template`, `/validate`

### Story 2.5: EDITOR Agent
- **Role**: Granular text optimization
- **Integration**: Refines generated documents
- **Commands**: `/edit`, `/optimize`, `/review`

## Deployment Configuration

### Docker Configuration
```dockerfile
# services/profile-ingestor/Dockerfile
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

# Install spaCy models
RUN python -m spacy download en_core_web_sm
RUN python -m spacy download fr_core_news_sm

COPY . .

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Kubernetes Configuration
```yaml
# infrastructure/k8s/profile-ingestor-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: profile-ingestor
spec:
  replicas: 3
  selector:
    matchLabels:
      app: profile-ingestor
  template:
    metadata:
      labels:
        app: profile-ingestor
    spec:
      containers:
      - name: profile-ingestor
        image: helios/profile-ingestor:1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          value: "postgresql://user:pass@postgres:5432/helios"
        - name: REDIS_URL  
          value: "redis://redis:6379"
```

## Testing Integration

### Integration Test Framework
```python
# tests/integration/test_profile_ingestor_integration.py
import pytest
import requests
import json
from pathlib import Path

class TestProfileIngestorIntegration:
    
    @pytest.fixture
    def api_client(self):
        return "http://localhost:8000"  # Profile Ingestor API
    
    def test_directory_ingestion(self, api_client):
        """Test full directory ingestion workflow"""
        response = requests.post(
            f"{api_client}/ingest/directory",
            json={"directory_path": "tests/sample_resumes"}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "master_career_database" in result
        assert result["processing_metadata"]["files_processed"] > 0
    
    def test_agent_communication(self, api_client):
        """Test agent communication protocol"""
        message = {
            "agent_id": "ORCHESTRATOR",
            "command": "/ingest",
            "payload": {"directory_path": "tests/sample_resumes"}
        }
        
        response = requests.post(f"{api_client}/agent/message", json=message)
        assert response.status_code == 200
        
        result = response.json() 
        assert result["agent_id"] == "PROFILE_INGESTOR"
        assert result["status"] == "success"
```

## Monitoring and Observability

### Logging Configuration
```python
# services/profile-ingestor/api/logging_config.py
import logging
import sys
from datetime import datetime

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'logs/profile-ingestor-{datetime.now().strftime("%Y%m%d")}.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
```

### Metrics Collection
```python
# services/profile-ingestor/api/metrics.py
from prometheus_client import Counter, Histogram, Gauge
import time

# Metrics
FILES_PROCESSED = Counter('files_processed_total', 'Total files processed')
PROCESSING_TIME = Histogram('processing_time_seconds', 'Time spent processing')
ACTIVE_SESSIONS = Gauge('active_sessions', 'Number of active processing sessions')

@PROCESSING_TIME.time()
def process_with_metrics(directory_path):
    start_time = time.time()
    
    # Process files
    result = process_directory(directory_path)
    
    # Update metrics
    FILES_PROCESSED.inc(result.files_count)
    
    return result
```

This integration guide provides everything needed to connect the completed Profile Ingestor service with the rest of the Helios system.