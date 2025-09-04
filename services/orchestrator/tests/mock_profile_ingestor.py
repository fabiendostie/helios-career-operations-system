"""Mock Profile Ingestor service for integration testing."""

import json
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
import uvicorn


class MockIngestionRequest(BaseModel):
    """Mock ingestion request model."""
    session_id: str
    file_paths: list[str] = Field(default_factory=list)
    text_content: Optional[str] = None
    user_context: Dict[str, Any] = Field(default_factory=dict)
    processing_options: Dict[str, Any] = Field(default_factory=dict)


class MockIngestionResponse(BaseModel):
    """Mock ingestion response model."""
    success: bool
    session_id: str
    master_career_database: Dict[str, Any]
    processing_summary: Dict[str, Any]
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class MockProgressResponse(BaseModel):
    """Mock progress response model."""
    session_id: str
    status: str
    progress_percent: float
    current_step: str
    estimated_completion: Optional[str] = None
    errors: list[str] = Field(default_factory=list)


# In-memory storage for mock data
mock_sessions: Dict[str, Dict[str, Any]] = {}
mock_processing_delays: Dict[str, float] = {}


def create_mock_profile_ingestor_app() -> FastAPI:
    """Create mock Profile Ingestor FastAPI application."""
    
    app = FastAPI(
        title="Mock Profile Ingestor Service",
        description="Mock service for testing HELIOS Orchestrator integration",
        version="1.0.0-test"
    )
    
    @app.get("/health")
    async def health_check():
        """Mock health check endpoint."""
        return {
            "status": "healthy",
            "service": "Mock Profile Ingestor",
            "version": "1.0.0-test",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    @app.post("/api/ingest", response_model=MockIngestionResponse)
    async def mock_ingest(request: MockIngestionRequest):
        """Mock ingestion endpoint with realistic behavior."""
        
        # Simulate processing delay
        processing_delay = mock_processing_delays.get(request.session_id, 0.1)
        if processing_delay > 0:
            await asyncio.sleep(processing_delay)
        
        # Generate mock Master Career Database based on input
        if request.text_content:
            mock_data = generate_mock_career_data_from_text(request.text_content)
        elif request.file_paths:
            mock_data = generate_mock_career_data_from_files(request.file_paths)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No input provided for ingestion"
            )
        
        # Simulate different success/failure scenarios based on session_id
        success = not request.session_id.endswith("-fail")
        errors = []
        warnings = []
        
        if request.session_id.endswith("-fail"):
            errors = ["Simulated processing failure for testing"]
            success = False
            mock_data = {}
        elif request.session_id.endswith("-warn"):
            warnings = ["Simulated warning: Some data could not be extracted"]
        
        # Store session data
        mock_sessions[request.session_id] = {
            "master_career_database": mock_data,
            "status": "completed" if success else "failed",
            "processing_summary": {
                "files_processed": len(request.file_paths),
                "text_length": len(request.text_content or ""),
                "skills_extracted": len(mock_data.get("skills_inventory", {}).get("technical_skills", [])),
                "experience_years": len(mock_data.get("work_experience", [])),
                "processing_time_ms": processing_delay * 1000
            }
        }
        
        return MockIngestionResponse(
            success=success,
            session_id=request.session_id,
            master_career_database=mock_data,
            processing_summary=mock_sessions[request.session_id]["processing_summary"],
            errors=errors,
            warnings=warnings
        )
    
    @app.get("/api/progress/{session_id}", response_model=MockProgressResponse)
    async def get_progress(session_id: str):
        """Mock progress tracking endpoint."""
        
        if session_id not in mock_sessions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        session_data = mock_sessions[session_id]
        
        return MockProgressResponse(
            session_id=session_id,
            status=session_data["status"],
            progress_percent=100.0 if session_data["status"] == "completed" else 50.0,
            current_step="parsing" if session_data["status"] == "processing" else "completed",
            estimated_completion=None if session_data["status"] == "completed" else "30 seconds"
        )
    
    @app.post("/api/cancel/{session_id}")
    async def cancel_ingestion(session_id: str):
        """Mock cancellation endpoint."""
        
        if session_id in mock_sessions:
            mock_sessions[session_id]["status"] = "cancelled"
            return {"message": f"Ingestion cancelled for session {session_id}"}
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    return app


def generate_mock_career_data_from_text(text_content: str) -> Dict[str, Any]:
    """Generate realistic mock career data from text input."""
    
    # Extract mock skills based on common keywords
    all_skills = ["Python", "FastAPI", "JavaScript", "React", "SQL", "Docker", "AWS", "Git"]
    detected_skills = [skill for skill in all_skills if skill.lower() in text_content.lower()]
    
    return {
        "work_experience": [
            {
                "company": "Mock Tech Company",
                "role": "Software Engineer",
                "duration": "2022-2024",
                "key_accomplishments": [
                    "Developed scalable web applications",
                    "Improved system performance by 40%"
                ],
                "technologies_used": detected_skills[:3] if detected_skills else ["Python", "FastAPI"]
            }
        ],
        "projects": [
            {
                "name": "Career Operations System",
                "description": "AI-powered career management platform",
                "outcomes": ["Successful MVP delivery", "User engagement increased"],
                "technologies": detected_skills[:5] if detected_skills else ["Python", "FastAPI", "React"]
            }
        ],
        "skills_inventory": {
            "technical_skills": detected_skills if detected_skills else ["Python", "FastAPI", "SQL"],
            "soft_skills": ["Problem Solving", "Team Collaboration", "Communication"],
            "certifications": ["Mock Certification"],
            "languages": ["English", "Python"]
        },
        "strategic_metadata": {
            "job_title_variations": ["Software Engineer", "Developer", "Backend Engineer"],
            "core_competencies": detected_skills[:3] if detected_skills else ["Python", "API Development"],
            "experience_level": "Mid-Level",
            "industries": ["Technology", "Software Development"]
        },
        "holistic_profile": {
            "career_aspirations": ["Senior Engineer Role", "Technical Leadership"],
            "motivators": ["Innovation", "Problem Solving", "Growth"],
            "transversal_projects": ["Open Source Contributions", "Mentoring"]
        }
    }


def generate_mock_career_data_from_files(file_paths: list[str]) -> Dict[str, Any]:
    """Generate mock career data based on file paths."""
    
    # Determine skills based on file extensions and names
    detected_skills = []
    
    for path in file_paths:
        if ".py" in path.lower():
            detected_skills.extend(["Python", "FastAPI", "Django"])
        elif ".js" in path.lower():
            detected_skills.extend(["JavaScript", "React", "Node.js"])
        elif ".sql" in path.lower():
            detected_skills.extend(["SQL", "Database Design"])
        elif "resume" in path.lower() or "cv" in path.lower():
            detected_skills.extend(["Professional Writing", "Communication"])
    
    # Remove duplicates
    detected_skills = list(set(detected_skills))
    
    return {
        "work_experience": [
            {
                "company": f"Company from {file_paths[0].split('/')[-1] if file_paths else 'Unknown'}",
                "role": "Software Engineer",
                "duration": "2022-2024",
                "key_accomplishments": [
                    f"Processed {len(file_paths)} project files",
                    "Demonstrated technical expertise"
                ],
                "technologies_used": detected_skills[:4]
            }
        ],
        "projects": [
            {
                "name": "File Processing System",
                "description": f"System handling {len(file_paths)} different file types",
                "outcomes": ["Successful file parsing", "Data extraction completed"],
                "technologies": detected_skills
            }
        ],
        "skills_inventory": {
            "technical_skills": detected_skills,
            "soft_skills": ["Attention to Detail", "Documentation"],
            "tools": ["File Processing", "Data Analysis"],
            "domains": ["Software Development", "Data Processing"]
        },
        "strategic_metadata": {
            "job_title_variations": ["Software Developer", "Data Engineer", "Backend Developer"],
            "core_competencies": detected_skills[:3],
            "experience_level": "Intermediate",
            "industries": ["Technology", "Data Processing"]
        },
        "holistic_profile": {
            "career_aspirations": ["Senior Developer", "Technical Architect"],
            "motivators": ["Technical Excellence", "Innovation"],
            "transversal_projects": ["File Processing Automation", "Data Pipeline Development"]
        }
    }


def set_processing_delay(session_id: str, delay_seconds: float):
    """Set processing delay for testing async behavior."""
    mock_processing_delays[session_id] = delay_seconds


def clear_mock_data():
    """Clear all mock session data."""
    global mock_sessions, mock_processing_delays
    mock_sessions.clear()
    mock_processing_delays.clear()


# For standalone testing
if __name__ == "__main__":
    app = create_mock_profile_ingestor_app()
    uvicorn.run(app, host="0.0.0.0", port=8001)