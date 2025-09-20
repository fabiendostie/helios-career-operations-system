"""
Integrated Document Generation API

Provides document generation endpoints that coordinate with other Helios services
to create optimized, intelligent documents using ANALYST recommendations and
STRATEGIST insights.
"""

import asyncio
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, List

import structlog
from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ..core.research_integrations import get_sophisticated_research_engine
from ..core.template_engine import TemplateEngine
from ..integration import (
    DocumentGenerationResponse,
    ResumeArchitecture,
    get_service_clients,
)
from ..models.generation_request import DocumentType
from ..models.generation_request import OutputFormat as DocumentFormat
from ..validation import ATSVendor, ComplianceLevel, get_ats_validator

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/integrated", tags=["integrated-generation"])

# Request Models


class IntegratedGenerationRequest(BaseModel):
    """Request for integrated document generation with service coordination."""

    session_id: str = Field(description="Orchestrator session ID")

    # Document specifications
    document_type: DocumentType
    output_format: DocumentFormat = DocumentFormat.PDF
    architecture: ResumeArchitecture = ResumeArchitecture.T_SHAPED

    # Targeting parameters
    target_role: str | None = None
    target_company: str | None = None
    target_industry: str | None = None

    # Service coordination options
    use_analyst_recommendations: bool = True
    use_strategist_insights: bool = True
    request_fresh_analysis: bool = False  # Request new analysis if none exists

    # Quality requirements
    ats_compliance_level: str = "standard"
    target_ats_vendors: list[str] = Field(default_factory=lambda: ["generic"])

    # Processing options
    include_validation: bool = True
    include_research_citations: bool = False
    custom_instructions: str | None = None


class GenerationStatus(BaseModel):
    """Status response for document generation."""

    request_id: str
    status: str  # queued, processing, completed, failed
    progress_percentage: float
    current_stage: str | None = None
    estimated_completion: datetime | None = None
    error_message: str | None = None


# Document Generation Coordination


@router.post(
    "/generate-document",
    response_model=DocumentGenerationResponse,
    summary="Generate optimized document with service coordination",
    description="""
    Generate a document using coordination between ARCHITECT, ANALYST, and STRATEGIST services.

    This endpoint:
    1. Retrieves session data from Orchestrator
    2. Gets optimization recommendations from ANALYST
    3. Incorporates strategic insights from STRATEGIST
    4. Uses sophisticated research engine for dynamic content
    5. Validates against ATS compliance standards
    6. Returns optimized document with quality metrics
    """,
)
async def generate_integrated_document(
    request: IntegratedGenerationRequest, background_tasks: BackgroundTasks
) -> DocumentGenerationResponse:
    """Generate document with full service integration."""

    request_id = f"doc_gen_{int(datetime.utcnow().timestamp())}"
    start_time = datetime.utcnow()

    logger.info(
        "Starting integrated document generation",
        request_id=request_id,
        session_id=request.session_id,
        document_type=request.document_type.value,
    )

    try:
        # Initialize service clients
        service_clients = await get_service_clients()

        # Step 1: Get session data from Orchestrator
        session_data = await service_clients.orchestrator.get_session(
            request.session_id
        )
        if not session_data:
            raise HTTPException(
                status_code=404,
                detail=f"Session {request.session_id} not found in Orchestrator",
            )

        # Update session status to indicate ARCHITECT is processing
        await service_clients.orchestrator.update_session_status(
            request.session_id,
            "processing_document",
            {"request_id": request_id, "document_type": request.document_type.value},
        )

        # Step 2: Get user profile data
        user_profile = session_data.user_profile
        if not user_profile:
            raise HTTPException(
                status_code=400, detail="No user profile data available in session"
            )

        # Step 3: Get ANALYST recommendations
        analyst_recommendations = None
        if request.use_analyst_recommendations:
            if request.request_fresh_analysis:
                # Request new analysis
                await service_clients.analyst.request_analysis(
                    request.session_id,
                    user_profile,
                    request.target_role,
                    request.target_company,
                )
                # Wait a moment for processing
                await asyncio.sleep(2)

            analyst_recommendations = await service_clients.analyst.get_recommendations(
                request.session_id, request.target_role, request.target_company
            )

        # Step 4: Get STRATEGIST insights
        strategist_insights = None
        if request.use_strategist_insights:
            if request.request_fresh_analysis:
                # Request new strategic analysis
                career_goals = session_data.session_metadata.get("career_goals")
                await service_clients.strategist.request_strategy_analysis(
                    request.session_id, user_profile, career_goals
                )
                # Wait a moment for processing
                await asyncio.sleep(2)

            strategist_insights = await service_clients.strategist.get_insights(
                request.session_id, session_data.user_id
            )

        # Step 5: Initialize research engine for dynamic intelligence
        research_engine = await get_sophisticated_research_engine()

        # Gather industry and company intelligence if targeting specific entities
        industry_intelligence = {}
        company_intelligence = {}

        if request.target_industry:
            industry_intelligence = await research_engine.get_industry_intelligence(
                request.target_industry
            )

        if request.target_company:
            company_intelligence = await research_engine.get_company_intelligence(
                request.target_company
            )

        # Step 6: Generate document with integrated intelligence
        template_engine = TemplateEngine()

        # Prepare template context with all available intelligence
        template_context = {
            "user_profile": user_profile,
            "target_role": request.target_role,
            "target_company": request.target_company,
            "target_industry": request.target_industry,
            "analyst_recommendations": (
                analyst_recommendations.model_dump() if analyst_recommendations else {}
            ),
            "strategist_insights": (
                strategist_insights.model_dump() if strategist_insights else {}
            ),
            "industry_intelligence": industry_intelligence,
            "company_intelligence": company_intelligence,
            "generation_metadata": {
                "request_id": request_id,
                "generated_at": datetime.utcnow().isoformat(),
                "architecture": request.architecture.value,
                "services_used": {
                    "analyst": analyst_recommendations is not None,
                    "strategist": strategist_insights is not None,
                    "research_engine": bool(
                        industry_intelligence or company_intelligence
                    ),
                },
            },
        }

        # Apply custom instructions if provided
        if request.custom_instructions:
            template_context["custom_instructions"] = request.custom_instructions

        # Generate document content
        document_content = await template_engine.generate_document(
            template_name=f"{request.document_type.value}_{request.architecture.value}",
            context=template_context,
            output_format=request.output_format,
        )

        # Step 7: Save document to temporary file for validation
        temp_file = None
        if request.include_validation:
            temp_file = await _save_temporary_document(
                document_content, request.output_format
            )

        # Step 8: Perform ATS validation if requested
        validation_results = None
        compliance_score = None

        if request.include_validation and temp_file:
            validator = await get_ats_validator()

            # Parse ATS vendors
            target_vendors = []
            for vendor_name in request.target_ats_vendors:
                try:
                    target_vendors.append(ATSVendor(vendor_name.lower()))
                except ValueError:
                    logger.warning("Invalid ATS vendor ignored", vendor=vendor_name)

            if not target_vendors:
                target_vendors = [ATSVendor.GENERIC]

            # Parse compliance level
            try:
                compliance_level = ComplianceLevel(request.ats_compliance_level.lower())
            except ValueError:
                compliance_level = ComplianceLevel.STANDARD

            validation_result = await validator.validate_document(
                temp_file, target_vendors, compliance_level
            )

            validation_results = {
                "is_compliant": validation_result.is_compliant,
                "compliance_score": validation_result.compliance_score,
                "parsing_confidence": validation_result.parsing_confidence,
                "violations": validation_result.violations,
                "recommendations": validation_result.recommendations,
                "vendor_scores": {
                    v.value: s for v, s in validation_result.ats_vendor_scores.items()
                },
            }
            compliance_score = validation_result.compliance_score

        # Step 9: Calculate quality metrics
        optimization_score = None
        if analyst_recommendations:
            optimization_score = analyst_recommendations.optimization_score

        content_quality_score = _calculate_content_quality_score(
            template_context, analyst_recommendations, strategist_insights
        )

        # Step 10: Register completion with Orchestrator
        processing_time = (datetime.utcnow() - start_time).total_seconds()

        quality_metrics = {
            "ats_compliance_score": compliance_score,
            "optimization_score": optimization_score,
            "content_quality_score": content_quality_score,
            "processing_time_seconds": processing_time,
        }

        # For this implementation, we'll return content directly
        # In production, you'd save to persistent storage and return URL
        document_url = None  # Would be storage URL in production

        await service_clients.orchestrator.register_document_completion(
            request.session_id,
            request.document_type.value,
            document_url or "inline",
            quality_metrics,
        )

        # Update session status to completed
        await service_clients.orchestrator.update_session_status(
            request.session_id,
            "document_completed",
            {
                "request_id": request_id,
                "completion_time": datetime.utcnow().isoformat(),
                "quality_metrics": quality_metrics,
            },
        )

        logger.info(
            "Integrated document generation completed",
            request_id=request_id,
            session_id=request.session_id,
            processing_time=processing_time,
            compliance_score=compliance_score,
        )

        # Cleanup temporary file in background
        if temp_file:
            background_tasks.add_task(_cleanup_temp_file, temp_file)

        # Build response
        response = DocumentGenerationResponse(
            request_id=request_id,
            session_id=request.session_id,
            processing_time_seconds=processing_time,
            success=True,
            document_url=document_url,
            document_content=document_content,
            ats_compliance_score=compliance_score,
            optimization_score=optimization_score,
            content_quality_score=content_quality_score,
            validation_results=validation_results,
            compliance_violations=(
                validation_results.get("violations", []) if validation_results else []
            ),
            recommendations=(
                validation_results.get("recommendations", [])
                if validation_results
                else []
            ),
            template_used=f"{request.document_type.value}_{request.architecture.value}",
            research_sources=_extract_research_sources(
                industry_intelligence, company_intelligence
            ),
            generation_metadata={
                "services_coordinated": ["orchestrator", "analyst", "strategist"],
                "intelligence_sources": len(
                    _extract_research_sources(
                        industry_intelligence, company_intelligence
                    )
                ),
                "template_context_size": len(str(template_context)),
            },
        )

        return response

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise

    except Exception as e:
        processing_time = (datetime.utcnow() - start_time).total_seconds()

        logger.error(
            "Integrated document generation failed",
            request_id=request_id,
            session_id=request.session_id,
            error=str(e),
            error_type=type(e).__name__,
            processing_time=processing_time,
        )

        # Try to update Orchestrator about the failure
        try:
            service_clients = await get_service_clients()
            await service_clients.orchestrator.update_session_status(
                request.session_id,
                "document_failed",
                {
                    "request_id": request_id,
                    "error": str(e),
                    "failed_at": datetime.utcnow().isoformat(),
                },
            )
        except Exception:
            pass  # Don't fail the error response if Orchestrator update fails

        return DocumentGenerationResponse(
            request_id=request_id,
            session_id=request.session_id,
            processing_time_seconds=processing_time,
            success=False,
            error_message=str(e),
            error_code=type(e).__name__,
            retry_suggestions=[
                "Verify session exists in Orchestrator",
                "Check service connectivity",
                "Ensure user profile data is complete",
            ],
        )


@router.get(
    "/health/integration",
    summary="Check integration health with all services",
    description="Health check endpoint that verifies connectivity to all integrated services",
)
async def check_integration_health():
    """Check health of all service integrations."""

    try:
        service_clients = await get_service_clients()
        health_report = await service_clients.health_check_all()

        status_code = 200 if health_report.overall_health else 503

        return JSONResponse(status_code=status_code, content=health_report.model_dump())

    except Exception as e:
        logger.error("Integration health check failed", error=str(e))

        return JSONResponse(
            status_code=500,
            content={
                "overall_health": False,
                "error": "Health check system failure",
                "error_message": str(e),
            },
        )


# Helper Functions


async def _save_temporary_document(content: str, format: DocumentFormat) -> Path:
    """Save document content to temporary file for validation."""

    suffix_map = {
        DocumentFormat.PDF: ".pdf",
        DocumentFormat.DOCX: ".docx",
        DocumentFormat.HTML: ".html",
        DocumentFormat.MARKDOWN: ".md",
        DocumentFormat.TXT: ".txt",
    }

    suffix = suffix_map.get(format, ".txt")

    with tempfile.NamedTemporaryFile(
        suffix=suffix,
        mode="w" if format != DocumentFormat.PDF else "wb",
        delete=False,
        encoding="utf-8" if format != DocumentFormat.PDF else None,
    ) as temp_file:

        if format == DocumentFormat.PDF:
            # For PDF, content would be bytes in a real implementation
            temp_file.write(content.encode("utf-8"))
        else:
            temp_file.write(content)

        return Path(temp_file.name)


async def _cleanup_temp_file(file_path: Path):
    """Clean up temporary file."""
    try:
        file_path.unlink(missing_ok=True)
    except Exception as e:
        logger.warning(
            "Failed to cleanup temp file", file_path=str(file_path), error=str(e)
        )


def _calculate_content_quality_score(
    context: dict[str, Any], analyst_recs: Any, strategist_insights: Any
) -> float:
    """Calculate content quality score based on available intelligence."""

    base_score = 60.0  # Base score for basic profile

    # Add points for analyst recommendations
    if analyst_recs:
        base_score += 20.0

        # Bonus for specific optimizations
        if analyst_recs.priority_keywords:
            base_score += 5.0
        if analyst_recs.critical_skills:
            base_score += 5.0

    # Add points for strategist insights
    if strategist_insights:
        base_score += 15.0

        # Bonus for strategic positioning
        if strategist_insights.positioning_strategy:
            base_score += 5.0

    # Bonus for targeting specificity
    if context.get("target_role"):
        base_score += 5.0
    if context.get("target_company"):
        base_score += 3.0
    if context.get("target_industry"):
        base_score += 2.0

    return min(100.0, base_score)


def _extract_research_sources(
    industry_intel: dict[str, Any], company_intel: dict[str, Any]
) -> List[str]:
    """Extract research sources from intelligence data."""

    sources = []

    # Extract sources from industry intelligence
    if industry_intel.get("sources"):
        sources.extend(industry_intel["sources"])

    # Extract sources from company intelligence
    if company_intel.get("sources"):
        sources.extend(company_intel["sources"])

    # Add dynamic research engine as source
    if industry_intel or company_intel:
        sources.append("Helios Dynamic Research Engine")

    return list(set(sources))  # Remove duplicates
