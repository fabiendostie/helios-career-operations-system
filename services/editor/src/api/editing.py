"""Editing endpoints for the Editor service."""

import logging
import time

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..core.text_optimizer import TextOptimizer
from ..core.version_control import VersionController
from ..models.edit_request import (
    EditBatch,
    EditBatchResponse,
    EditRequest,
    EditResponse,
    EditSuggestion,
    EditType,
)
from ..models.text_analysis import TextAnalysis
from ..models.version_control import VersionComparison, VersionHistory

logger = logging.getLogger(__name__)

router = APIRouter()

# Service instances (in production, these would be dependency injected)
text_optimizer = TextOptimizer()
version_controller = VersionController()


class AnalyzeRequest(BaseModel):
    """Request for text analysis."""

    text: str
    language: str = "en"


class SuggestionRequest(BaseModel):
    """Request for edit suggestions without applying them."""

    session_id: str
    text: str
    edit_type: EditType = EditType.COMPREHENSIVE
    industry: str | None = None
    role: str | None = None
    language: str = "en"
    tone: str | None = None


class SuggestionResponse(BaseModel):
    """Response with suggestions and analysis."""

    suggestions: list[EditSuggestion]
    analysis: TextAnalysis


class ApplySuggestionsRequest(BaseModel):
    """Request to apply specific suggestions."""

    session_id: str
    text: str
    suggestion_ids: list[int]


class RevertRequest(BaseModel):
    """Request to revert to a previous version."""

    target_version_id: str
    comment: str | None = None


class MetricsResponse(BaseModel):
    """Service metrics response."""

    total_edits: int
    average_processing_time: float
    success_rate: float
    active_sessions: int


# Global metrics (in production, use proper metrics collection)
_metrics = {
    "total_edits": 0,
    "total_processing_time": 0.0,
    "successful_edits": 0,
    "failed_edits": 0,
}


@router.post("/edit", response_model=EditResponse)
async def edit_text(request: EditRequest) -> EditResponse:
    """Edit text with comprehensive optimization."""
    try:
        start_time = time.time()

        # Validate request
        if not request.text or request.text.strip() == "":
            raise HTTPException(status_code=400, detail="Text cannot be empty")

        # Optimize text
        result = text_optimizer.optimize_text(request)

        # Update metrics
        processing_time = time.time() - start_time
        _metrics["total_edits"] += 1
        _metrics["total_processing_time"] += processing_time
        _metrics["successful_edits"] += 1

        logger.info(f"Successfully edited text for session {request.session_id}")
        return result

    except ValueError as e:
        _metrics["failed_edits"] += 1
        logger.error(f"Validation error in edit_text: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        _metrics["failed_edits"] += 1
        logger.error(f"Error in edit_text: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/edit/batch", response_model=EditBatchResponse)
async def edit_batch(request: EditBatch) -> EditBatchResponse:
    """Edit multiple texts in batch."""
    try:
        start_time = time.time()
        results = []
        success_count = 0
        error_count = 0

        for i, text in enumerate(request.texts):
            try:
                edit_request = EditRequest(
                    session_id=f"{request.session_id}-{i}",
                    text=text,
                    edit_type=request.edit_type,
                    industry=request.industry,
                    role=request.role,
                )

                result = text_optimizer.optimize_text(edit_request)
                results.append(result)
                success_count += 1

            except Exception as e:
                logger.error(f"Error editing text {i}: {e}")
                error_count += 1
                # Add error result
                results.append(
                    EditResponse(
                        session_id=f"{request.session_id}-{i}",
                        original_text=text,
                        edited_text=text,  # Return original on error
                        suggestions=[],
                        processing_time=0.0,
                    )
                )

        total_processing_time = time.time() - start_time

        return EditBatchResponse(
            session_id=request.session_id,
            results=results,
            total_processing_time=total_processing_time,
            success_count=success_count,
            error_count=error_count,
        )

    except Exception as e:
        logger.error(f"Error in edit_batch: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/analyze", response_model=TextAnalysis)
async def analyze_text(request: AnalyzeRequest) -> TextAnalysis:
    """Analyze text for grammar, style, and content issues."""
    try:
        if not request.text or request.text.strip() == "":
            raise HTTPException(status_code=400, detail="Text cannot be empty")

        analysis = text_optimizer.analyze_text(request.text, request.language)
        logger.info(f"Successfully analyzed text of {len(request.text)} characters")
        return analysis

    except ValueError as e:
        logger.error(f"Validation error in analyze_text: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Error in analyze_text: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/edit/suggestions", response_model=SuggestionResponse)
async def get_suggestions(request: SuggestionRequest) -> SuggestionResponse:
    """Get edit suggestions without applying them."""
    try:
        if not request.text or request.text.strip() == "":
            raise HTTPException(status_code=400, detail="Text cannot be empty")

        # Create edit request
        edit_request = EditRequest(
            session_id=request.session_id,
            text=request.text,
            edit_type=request.edit_type,
            industry=request.industry,
            role=request.role,
            language=request.language,
            tone=request.tone,
            track_changes=False,  # Don't track changes for suggestions
        )

        # Get optimization result (but don't apply changes)
        result = text_optimizer.optimize_text(edit_request)

        # Get analysis
        analysis = text_optimizer.analyze_text(request.text, request.language)

        return SuggestionResponse(suggestions=result.suggestions, analysis=analysis)

    except ValueError as e:
        logger.error(f"Validation error in get_suggestions: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Error in get_suggestions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/edit/apply", response_model=EditResponse)
async def apply_suggestions(request: ApplySuggestionsRequest) -> EditResponse:
    """Apply specific suggestions to text."""
    try:
        if not request.text or request.text.strip() == "":
            raise HTTPException(status_code=400, detail="Text cannot be empty")

        # This is a simplified implementation
        # In a full implementation, you'd store suggestions and apply specific ones
        edit_request = EditRequest(
            session_id=request.session_id,
            text=request.text,
            edit_type=EditType.COMPREHENSIVE,
        )

        result = text_optimizer.optimize_text(edit_request)

        # Filter suggestions based on suggestion_ids
        if request.suggestion_ids:
            applied_suggestions = [
                result.suggestions[i]
                for i in request.suggestion_ids
                if i < len(result.suggestions)
            ]
            result.suggestions = applied_suggestions

        return result

    except ValueError as e:
        logger.error(f"Validation error in apply_suggestions: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Error in apply_suggestions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/versions/{session_id}", response_model=VersionHistory)
async def get_version_history(session_id: str) -> VersionHistory:
    """Get version history for a session."""
    try:
        history = version_controller.get_version_history(session_id)
        return history

    except Exception as e:
        logger.error(f"Error getting version history: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/versions/{session_id}/compare", response_model=VersionComparison)
async def compare_versions(
    session_id: str, version_a: str, version_b: str
) -> VersionComparison:
    """Compare two versions."""
    try:
        comparison = version_controller.compare_versions(
            session_id, version_a, version_b
        )
        return comparison

    except ValueError as e:
        logger.error(f"Validation error in compare_versions: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Error comparing versions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/versions/{session_id}/revert", response_model=EditResponse)
async def revert_to_version(session_id: str, request: RevertRequest) -> EditResponse:
    """Revert to a previous version."""
    try:
        reverted_version = version_controller.revert_to_version(
            session_id, request.target_version_id, request.comment
        )

        # Create response in EditResponse format
        return EditResponse(
            session_id=session_id,
            original_text="",  # Previous version text
            edited_text=reverted_version.text,
            suggestions=[],
            version_id=reverted_version.version_id,
            version_number=reverted_version.version_number,
            processing_time=0.0,
        )

    except ValueError as e:
        logger.error(f"Validation error in revert_to_version: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Error reverting version: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics() -> MetricsResponse:
    """Get service metrics."""
    try:
        total_requests = _metrics["total_edits"]
        avg_processing_time = _metrics["total_processing_time"] / max(1, total_requests)
        success_rate = (_metrics["successful_edits"] / max(1, total_requests)) * 100

        return MetricsResponse(
            total_edits=_metrics["total_edits"],
            average_processing_time=avg_processing_time,
            success_rate=success_rate,
            active_sessions=len(version_controller.versions),
        )

    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
