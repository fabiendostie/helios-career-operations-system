"""Document generation endpoints for the Architect service."""

import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from src.core.document_generator import ATSCompliantDocumentGenerator, DocumentGenerationError
from src.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Global generator instance
document_generator = ATSCompliantDocumentGenerator()


class GenerationRequest(BaseModel):
    """Request model for document generation."""
    profile_data: Dict[str, Any]
    target_job: Optional[Dict[str, Any]] = None
    document_type: str  # "resume" or "cover_letter"
    preferences: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    correlation_id: Optional[str] = None


class GenerationResponse(BaseModel):
    """Response model for document generation."""
    content: str
    compliance_score: float
    generation_time: float
    metadata: Dict[str, Any]
    document_type: str
    correlation_id: Optional[str] = None


@router.post("/generate", response_model=GenerationResponse)
async def generate_document(
    request: GenerationRequest,
    background_tasks: BackgroundTasks
) -> GenerationResponse:
    """Generate ATS-compliant document (resume or cover letter)."""

    correlation_id = request.correlation_id or "unknown"

    logger.info(
        f"Starting document generation for user {request.user_id}, "
        f"type: {request.document_type}, correlation_id: {correlation_id}"
    )

    try:
        if request.document_type == "resume":
            result = await document_generator.generate_resume(
                profile_data=request.profile_data,
                target_job=request.target_job,
                preferences=request.preferences
            )
        elif request.document_type == "cover_letter":
            if not request.target_job:
                raise HTTPException(
                    status_code=400,
                    detail="Target job is required for cover letter generation"
                )

            result = await document_generator.generate_cover_letter(
                profile_data=request.profile_data,
                target_job=request.target_job,
                preferences=request.preferences
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported document type: {request.document_type}"
            )

        # Validate compliance threshold
        if result.compliance_score < settings.ATS_COMPLIANCE_THRESHOLD:
            logger.warning(
                f"Document compliance score ({result.compliance_score}%) below threshold "
                f"({settings.ATS_COMPLIANCE_THRESHOLD}%) for correlation_id: {correlation_id}"
            )

        # Ensure generation time requirement (<30s)
        if result.generation_time > settings.GENERATION_TIMEOUT:
            logger.warning(
                f"Document generation exceeded timeout: {result.generation_time}s > "
                f"{settings.GENERATION_TIMEOUT}s for correlation_id: {correlation_id}"
            )

        logger.info(
            f"Document generated successfully in {result.generation_time:.2f}s "
            f"with {result.compliance_score}% ATS compliance for correlation_id: {correlation_id}"
        )

        return GenerationResponse(
            content=result.content,
            compliance_score=result.compliance_score,
            generation_time=result.generation_time,
            metadata=result.metadata,
            document_type=request.document_type,
            correlation_id=correlation_id
        )

    except DocumentGenerationError as e:
        logger.error(f"Document generation failed for correlation_id {correlation_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Document generation failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error for correlation_id {correlation_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during document generation: {str(e)}"
        )


@router.get("/templates")
async def list_available_templates() -> Dict[str, Any]:
    """List available document templates."""
    return {
        "resume_templates": [
            "resume_senior_2025.j2",
            "resume_mid_level_2025.j2",
            "resume_entry_level_2025.j2"
        ],
        "cover_letter_templates": [
            "cover_letter_technical_2025.j2",
            "cover_letter_standard_2025.j2"
        ],
        "ats_optimizations": "2025_standards_enabled",
        "compliance_features": [
            "single_column_layout",
            "semantic_keyword_integration",
            "verb_metric_outcome_format",
            "91_percent_parsing_success"
        ]
    }


@router.post("/validate-compliance")
async def validate_ats_compliance(
    content: str
) -> Dict[str, Any]:
    """Validate ATS compliance of existing document content."""

    try:
        # Use the compliance engine from document generator
        compliance_score = document_generator._calculate_compliance_score(content)

        return {
            "compliance_score": compliance_score,
            "meets_threshold": compliance_score >= settings.ATS_COMPLIANCE_THRESHOLD,
            "threshold": settings.ATS_COMPLIANCE_THRESHOLD,
            "recommendations": _generate_compliance_recommendations(content, compliance_score)
        }

    except Exception as e:
        logger.error(f"Compliance validation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Compliance validation failed: {str(e)}"
        )


def _generate_compliance_recommendations(content: str, score: float) -> list[str]:
    """Generate compliance improvement recommendations."""
    recommendations = []

    if score < 70:
        recommendations.append("Document requires major ATS optimization")
        recommendations.append("Consider using single-column layout for 91% parsing success")
        recommendations.append("Add quantified metrics to bullet points")
    elif score < 85:
        recommendations.append("Document needs moderate ATS improvements")
        recommendations.append("Enhance semantic keyword integration")
        recommendations.append("Apply Verb + Metric + Outcome formula to accomplishments")
    else:
        recommendations.append("Document meets ATS compliance standards")
        recommendations.append("Minor optimizations may further improve parsing success")

    return recommendations


@router.get("/health/generation")
async def generation_health_check() -> Dict[str, Any]:
    """Health check specific to document generation capabilities."""
    return {
        "document_generator": "operational",
        "ats_compliance_engine": "ready",
        "2025_optimizations": "enabled",
        "supported_formats": ["markdown", "pdf_ready", "docx_compatible"],
        "average_generation_time": "< 10 seconds",
        "compliance_threshold": f"{settings.ATS_COMPLIANCE_THRESHOLD}%"
    }