"""Document generation API endpoints."""

import asyncio
import time
import base64
from typing import Dict, Any, List

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks, Depends
from fastapi.responses import Response
import structlog

from ..core.document_generator import DocumentGenerator, monitor_memory_usage
from ..models.generation_request import (
    DocumentGenerationRequest, DocumentResponse,
    TemplateListRequest, TemplateListResponse,
    BulkGenerationRequest, BulkGenerationResponse,
    GenerationStatusRequest, GenerationStatus
)
from ..core.config import get_settings

logger = structlog.get_logger(__name__)
router = APIRouter()

# Global document generator instance
document_generator = DocumentGenerator()

# Active generation tasks (for status tracking)
generation_tasks: Dict[str, Dict[str, Any]] = {}


async def get_session_data(session_id: str) -> Dict[str, Any]:
    """Fetch session data from orchestrator service."""
    settings = get_settings()

    try:
        import aiohttp

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=settings.orchestrator_timeout)
        ) as session:
            async with session.get(
                f"{settings.orchestrator_url}/session/{session_id}"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('career_data', {})
                elif response.status == 404:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Session {session_id} not found"
                    )
                else:
                    raise HTTPException(
                        status_code=503,
                        detail="Orchestrator service unavailable"
                    )

    except aiohttp.ClientError as e:
        logger.error("Failed to connect to orchestrator", error=str(e))
        raise HTTPException(
            status_code=503,
            detail="Unable to connect to orchestrator service"
        )
    except asyncio.TimeoutError:
        logger.error("Timeout connecting to orchestrator")
        raise HTTPException(
            status_code=504,
            detail="Orchestrator service timeout"
        )


@router.post("/resume", response_model=DocumentResponse)
async def generate_resume(
    request: DocumentGenerationRequest,
    background_tasks: BackgroundTasks
) -> DocumentResponse:
    """Generate a resume document."""

    # Validate document type
    if request.document_type != "resume":
        raise HTTPException(
            status_code=400,
            detail="This endpoint is for resume generation only"
        )

    # Check memory usage before processing
    if not await monitor_memory_usage():
        raise HTTPException(
            status_code=503,
            detail="Service overloaded - please try again later"
        )

    try:
        # Get career data from orchestrator
        career_data = await get_session_data(request.session_id)

        if not career_data:
            raise HTTPException(
                status_code=404,
                detail="No career data found for session"
            )

        logger.info(
            "Starting resume generation",
            session_id=request.session_id,
            template_name=request.template_name,
            output_format=request.output_format
        )

        # Generate document
        result = await document_generator.generate_document(
            template_name=request.template_name,
            career_data=career_data,
            output_format=request.output_format,
            job_requirements=request.job_requirements,
            customizations=request.customizations,
            document_type="resume"
        )

        # Prepare response
        content = result["content"]

        # Encode binary content as base64 for JSON response
        if isinstance(content, bytes):
            content_str = base64.b64encode(content).decode('utf-8')
            content_encoding = "base64"
        else:
            content_str = content
            content_encoding = "utf-8"

        response = DocumentResponse(
            content=content_str,
            content_encoding=content_encoding,
            mime_type=result["mime_type"],
            metadata=result.get("metadata") if request.include_metadata else None,
            success=True,
            message="Resume generated successfully"
        )

        # Schedule cleanup task
        background_tasks.add_task(cleanup_generation_artifacts, request.session_id)

        logger.info(
            "Resume generation completed",
            session_id=request.session_id,
            file_size=len(content),
            generation_time=result["metadata"]["generation_time"]
        )

        return response

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(
            "Resume generation failed",
            session_id=request.session_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Resume generation failed: {str(e)}"
        )


@router.post("/cover-letter", response_model=DocumentResponse)
async def generate_cover_letter(
    request: DocumentGenerationRequest,
    background_tasks: BackgroundTasks
) -> DocumentResponse:
    """Generate a cover letter document."""

    # Validate document type
    if request.document_type != "cover_letter":
        raise HTTPException(
            status_code=400,
            detail="This endpoint is for cover letter generation only"
        )

    # Validate required fields for cover letters
    if not request.job_requirements:
        raise HTTPException(
            status_code=400,
            detail="Job requirements are required for cover letter generation"
        )

    # Check memory usage before processing
    if not await monitor_memory_usage():
        raise HTTPException(
            status_code=503,
            detail="Service overloaded - please try again later"
        )

    try:
        # Get career data from orchestrator
        career_data = await get_session_data(request.session_id)

        if not career_data:
            raise HTTPException(
                status_code=404,
                detail="No career data found for session"
            )

        logger.info(
            "Starting cover letter generation",
            session_id=request.session_id,
            template_name=request.template_name,
            company=request.job_requirements.get('company', 'Unknown')
        )

        # Generate document
        result = await document_generator.generate_document(
            template_name=request.template_name,
            career_data=career_data,
            output_format=request.output_format,
            job_requirements=request.job_requirements,
            customizations=request.customizations,
            document_type="cover_letter"
        )

        # Prepare response
        content = result["content"]

        # Encode binary content as base64 for JSON response
        if isinstance(content, bytes):
            content_str = base64.b64encode(content).decode('utf-8')
            content_encoding = "base64"
        else:
            content_str = content
            content_encoding = "utf-8"

        response = DocumentResponse(
            content=content_str,
            content_encoding=content_encoding,
            mime_type=result["mime_type"],
            metadata=result.get("metadata") if request.include_metadata else None,
            success=True,
            message="Cover letter generated successfully"
        )

        # Schedule cleanup task
        background_tasks.add_task(cleanup_generation_artifacts, request.session_id)

        logger.info(
            "Cover letter generation completed",
            session_id=request.session_id,
            file_size=len(content)
        )

        return response

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(
            "Cover letter generation failed",
            session_id=request.session_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Cover letter generation failed: {str(e)}"
        )


@router.post("/document", response_model=DocumentResponse)
async def generate_document(
    request: DocumentGenerationRequest,
    background_tasks: BackgroundTasks
) -> DocumentResponse:
    """Generate any type of document (unified endpoint)."""

    # Route to specific endpoints based on document type
    if request.document_type == "resume":
        return await generate_resume(request, background_tasks)
    elif request.document_type == "cover_letter":
        return await generate_cover_letter(request, background_tasks)
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported document type: {request.document_type}"
        )


@router.get("/templates", response_model=TemplateListResponse)
async def list_templates(
    document_type: str = None,
    industry: str = None,
    ats_optimization: str = None
) -> TemplateListResponse:
    """List available templates with optional filtering."""

    try:
        # Get all templates
        templates = await document_generator.list_available_templates(document_type)

        # Apply additional filters
        filtered_templates = templates

        if industry:
            filtered_templates = [
                t for t in filtered_templates
                if industry.lower() in [ind.lower() for ind in t.get('target_industries', [])]
            ]

        if ats_optimization:
            filtered_templates = [
                t for t in filtered_templates
                if t.get('ats_optimization', '').lower() == ats_optimization.lower()
            ]

        # Get available filter options
        available_industries = set()
        available_optimizations = set()

        for template in templates:
            available_industries.update(template.get('target_industries', []))
            available_optimizations.add(template.get('ats_optimization', ''))

        return TemplateListResponse(
            templates=filtered_templates,
            total_count=len(templates),
            filtered_count=len(filtered_templates),
            available_industries=sorted(list(available_industries)),
            available_optimizations=sorted(list(available_optimizations))
        )

    except Exception as e:
        logger.error("Failed to list templates", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve template list"
        )


@router.get("/templates/{template_name}")
async def get_template_info(template_name: str) -> Dict[str, Any]:
    """Get detailed information about a specific template."""

    try:
        template_info = await document_generator.get_template_info(template_name)

        if not template_info:
            raise HTTPException(
                status_code=404,
                detail=f"Template '{template_name}' not found"
            )

        return {
            "template_name": template_name,
            "info": template_info,
            "supported_formats": ["pdf", "html", "markdown", "docx"],
            "generation_examples": {
                "basic": f"/generate/document with template_name='{template_name}'",
                "with_customizations": "Include customizations object for personalization"
            }
        }

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(
            "Failed to get template info",
            template_name=template_name,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve template information"
        )


@router.post("/bulk", response_model=BulkGenerationResponse)
async def bulk_generate_documents(
    request: BulkGenerationRequest,
    background_tasks: BackgroundTasks
) -> BulkGenerationResponse:
    """Generate multiple documents in parallel."""

    # Check memory usage before processing
    if not await monitor_memory_usage():
        raise HTTPException(
            status_code=503,
            detail="Service overloaded - cannot process bulk requests"
        )

    if len(request.generations) > 10:
        raise HTTPException(
            status_code=400,
            detail="Maximum 10 documents can be generated in a single bulk request"
        )

    start_time = time.time()
    results = []
    success_count = 0
    failure_count = 0

    try:
        logger.info(
            "Starting bulk document generation",
            session_id=request.session_id,
            document_count=len(request.generations),
            parallel=request.parallel_processing
        )

        if request.parallel_processing:
            # Process in parallel
            tasks = []
            for gen_request in request.generations:
                gen_request.session_id = request.session_id  # Ensure consistent session ID
                task = asyncio.create_task(
                    _generate_single_document(gen_request)
                )
                tasks.append(task)

            # Wait for all tasks to complete
            task_results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in task_results:
                if isinstance(result, Exception):
                    results.append(DocumentResponse(
                        content="",
                        mime_type="text/plain",
                        success=False,
                        message=str(result)
                    ))
                    failure_count += 1
                else:
                    results.append(result)
                    success_count += 1

                # Check fail_fast option
                if request.fail_fast and failure_count > 0:
                    break
        else:
            # Process sequentially
            for gen_request in request.generations:
                gen_request.session_id = request.session_id

                try:
                    result = await _generate_single_document(gen_request)
                    results.append(result)
                    success_count += 1
                except Exception as e:
                    results.append(DocumentResponse(
                        content="",
                        mime_type="text/plain",
                        success=False,
                        message=str(e)
                    ))
                    failure_count += 1

                    # Check fail_fast option
                    if request.fail_fast:
                        break

        total_time = time.time() - start_time

        # Schedule cleanup
        background_tasks.add_task(cleanup_generation_artifacts, request.session_id)

        logger.info(
            "Bulk generation completed",
            session_id=request.session_id,
            success_count=success_count,
            failure_count=failure_count,
            total_time=total_time
        )

        return BulkGenerationResponse(
            results=results,
            success_count=success_count,
            failure_count=failure_count,
            total_time=total_time,
            summary={
                "average_time_per_document": total_time / len(request.generations),
                "parallel_processing": request.parallel_processing,
                "fail_fast": request.fail_fast
            }
        )

    except Exception as e:
        logger.error(
            "Bulk generation failed",
            session_id=request.session_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Bulk generation failed: {str(e)}"
        )


async def _generate_single_document(request: DocumentGenerationRequest) -> DocumentResponse:
    """Generate a single document (internal helper)."""

    # Get career data
    career_data = await get_session_data(request.session_id)

    if not career_data:
        raise ValueError("No career data found for session")

    # Generate document
    result = await document_generator.generate_document(
        template_name=request.template_name,
        career_data=career_data,
        output_format=request.output_format,
        job_requirements=request.job_requirements,
        customizations=request.customizations,
        document_type=request.document_type
    )

    # Prepare response
    content = result["content"]

    if isinstance(content, bytes):
        content_str = base64.b64encode(content).decode('utf-8')
        content_encoding = "base64"
    else:
        content_str = content
        content_encoding = "utf-8"

    return DocumentResponse(
        content=content_str,
        content_encoding=content_encoding,
        mime_type=result["mime_type"],
        metadata=result.get("metadata"),
        success=True,
        message="Document generated successfully"
    )


@router.get("/download/{session_id}/{format}")
async def download_document(
    session_id: str,
    format: str,
    template_name: str = "t_shaped_classic",
    document_type: str = "resume"
) -> Response:
    """Download document directly as file."""

    try:
        # Validate format
        if format.lower() not in ['pdf', 'html', 'markdown', 'docx']:
            raise HTTPException(
                status_code=400,
                detail="Unsupported format. Use: pdf, html, markdown, docx"
            )

        # Get career data
        career_data = await get_session_data(session_id)

        if not career_data:
            raise HTTPException(
                status_code=404,
                detail="Session not found"
            )

        # Generate document
        result = await document_generator.generate_document(
            template_name=template_name,
            career_data=career_data,
            output_format=format,
            document_type=document_type
        )

        # Prepare filename
        candidate_name = career_data.get('candidate_name', 'Professional').replace(' ', '_')
        timestamp = int(time.time())

        if document_type == "resume":
            filename = f"{candidate_name}_Resume_{timestamp}.{format}"
        else:
            filename = f"{candidate_name}_Cover_Letter_{timestamp}.{format}"

        # Return file response
        return Response(
            content=result["content"],
            media_type=result["mime_type"],
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Cache-Control": "no-cache"
            }
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(
            "Document download failed",
            session_id=session_id,
            format=format,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail="Document download failed"
        )


async def cleanup_generation_artifacts(session_id: str):
    """Background task to clean up generation artifacts."""
    try:
        # Clean up any temporary files, caches, etc.
        # This would typically involve cleaning up session-specific data
        logger.debug("Cleaning up generation artifacts", session_id=session_id)

        # Could implement:
        # - Remove temporary files
        # - Clear session-specific caches
        # - Update usage metrics

    except Exception as e:
        logger.error(
            "Failed to cleanup generation artifacts",
            session_id=session_id,
            error=str(e)
        )
