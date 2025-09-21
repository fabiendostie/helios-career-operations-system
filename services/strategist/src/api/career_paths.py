"""Career path generation API endpoints."""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse

from ..models.career_path import CareerPathRequest, CareerPathResponse
from ..core.career_generator import CareerGenerator
from ..core.config import get_config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/career-paths", tags=["career-paths"])

# Global career generator instance (will be initialized on startup)
career_generator: CareerGenerator = None


async def get_career_generator() -> CareerGenerator:
    """Dependency to get initialized career generator."""
    if career_generator is None:
        raise HTTPException(
            status_code=503,
            detail="STRATEGIST service not fully initialized. Please try again later."
        )
    return career_generator


async def initialize_career_generator():
    """Initialize the career generator (called during app startup)."""
    global career_generator
    try:
        config = get_config()
        career_generator = CareerGenerator(config)
        await career_generator.initialize()
        logger.info("CareerGenerator initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize CareerGenerator: {e}")
        raise


@router.post("/generate", response_model=CareerPathResponse)
async def generate_career_paths(
    request: CareerPathRequest,
    generator: CareerGenerator = Depends(get_career_generator)
) -> CareerPathResponse:
    """Generate career path recommendations for a user.

    This is the main endpoint that the Orchestrator calls for the /discover command.
    """
    try:
        logger.info(f"Generating career paths for user {request.user_id}")

        # Validate request
        if not request.master_career_database:
            raise HTTPException(
                status_code=400,
                detail="master_career_database is required"
            )

        # Generate career paths
        response = await generator.generate_career_paths(request)

        logger.info(f"Successfully generated {len(response.career_target_profiles)} recommendations for user {request.user_id}")

        return response

    except ValueError as e:
        logger.warning(f"Invalid request for user {request.user_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Error generating career paths for user {request.user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal error during career path generation"
        )


@router.post("/discover")
async def discover_command_handler(
    payload: Dict[str, Any],
    generator: CareerGenerator = Depends(get_career_generator)
) -> JSONResponse:
    """Handle /discover command from HELIOS Orchestrator.

    This endpoint matches the expected interface from the Orchestrator service.
    """
    try:
        # Extract required fields from orchestrator payload
        user_id = payload.get("user_id")
        session_data = payload.get("session_data", {})
        master_career_database = session_data.get("master_career_database")

        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")

        if not master_career_database:
            raise HTTPException(
                status_code=400,
                detail="master_career_database not found in session data"
            )

        # Create career path request
        request = CareerPathRequest(
            user_id=user_id,
            master_career_database=master_career_database,
            max_recommendations=payload.get("max_recommendations", 3),
            include_challenging_transitions=payload.get("include_challenging_transitions", True),
            preferred_industries=payload.get("preferred_industries"),
            salary_requirements=payload.get("salary_requirements")
        )

        # Generate career paths
        response = await generator.generate_career_paths(request)

        # Format response for Orchestrator
        orchestrator_response = {
            "status": "success",
            "user_id": user_id,
            "service": "STRATEGIST",
            "data": {
                "career_recommendations": [
                    {
                        "role_title": ctp.role.title,
                        "role_description": ctp.role.description,
                        "fit_score": round(ctp.fit_score, 3),
                        "skill_match_score": round(ctp.skill_match_score, 3),
                        "aspiration_score": round(ctp.aspiration_score, 3),
                        "transition_difficulty": ctp.transition_difficulty.value,
                        "estimated_transition_time": ctp.estimated_transition_time,
                        "explanation": ctp.explanation,
                        "key_selling_points": ctp.key_selling_points,
                        "next_steps": ctp.next_steps[:3],  # Top 3 next steps
                        "skill_gaps_count": len(ctp.skill_gaps),
                        "critical_skills_needed": [
                            sg.skill_name for sg in ctp.skill_gaps
                            if sg.priority.value == "critical"
                        ][:5],  # Top 5 critical skills
                        "salary_range": ctp.role.median_salary_range,
                        "remote_work_compatibility": ctp.role.remote_work_compatibility,
                        "industry": ctp.role.industry_categories[0].value if ctp.role.industry_categories else "Unknown"
                    }
                    for ctp in response.career_target_profiles
                ],
                "summary": response.generation_summary
            },
            "metadata": {
                "processing_time_ms": response.processing_time_ms,
                "model_version": response.model_version,
                "timestamp": response.career_target_profiles[0].generation_timestamp if response.career_target_profiles else None
            }
        }

        return JSONResponse(content=orchestrator_response)

    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is

    except Exception as e:
        logger.error(f"Error in discover command handler: {e}")

        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "user_id": payload.get("user_id"),
                "service": "STRATEGIST",
                "error": "Internal error during career discovery",
                "metadata": {
                    "timestamp": payload.get("timestamp")
                }
            }
        )


@router.get("/status")
async def service_status() -> Dict[str, Any]:
    """Get STRATEGIST service status and statistics."""
    try:
        config = get_config()

        # Check if career generator is initialized
        is_ready = career_generator is not None and career_generator._initialized

        status_info = {
            "service": "STRATEGIST",
            "version": "1.0.0",
            "status": "ready" if is_ready else "initializing",
            "configuration": {
                "max_career_paths": config.max_career_paths,
                "skill_weight": config.skill_weight,
                "aspiration_weight": config.aspiration_weight,
                "embedding_model": config.embedding_model
            }
        }

        if is_ready and career_generator.taxonomy_manager.is_loaded():
            # Add taxonomy statistics
            stats = career_generator.taxonomy_manager.get_statistics()
            status_info["taxonomy_stats"] = {
                "total_roles": stats.total_roles,
                "industries": len(stats.roles_by_industry),
                "unique_skills": stats.unique_skills
            }

            # Add vectorizer statistics
            vectorizer_stats = career_generator.vectorizer.get_cache_stats()
            status_info["vectorizer_stats"] = vectorizer_stats

        return status_info

    except Exception as e:
        logger.error(f"Error getting service status: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving service status")
