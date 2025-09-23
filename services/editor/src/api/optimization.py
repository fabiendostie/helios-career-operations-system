"""Text optimization endpoints for the Editor service."""

import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from src.core.text_optimizer_2025 import TextOptimizer2025, OptimizationLevel, OptimizationResult
from src.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Global optimizer instance
text_optimizer = TextOptimizer2025()


class OptimizationRequest(BaseModel):
    """Request model for text optimization."""
    text: str
    optimization_level: str = "standard"  # light, standard, aggressive
    context: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    correlation_id: Optional[str] = None


class OptimizationResponse(BaseModel):
    """Response model for text optimization."""
    original_text: str
    optimized_text: str
    improvements: list[str]
    readability_score: float
    impact_score: float
    processing_time: float
    optimization_level: str
    correlation_id: Optional[str] = None


class SuggestionsRequest(BaseModel):
    """Request model for optimization suggestions."""
    text: str
    user_id: Optional[str] = None


class SuggestionsResponse(BaseModel):
    """Response model for optimization suggestions."""
    suggestions: list[str]
    text_length: int
    has_metrics: bool
    has_strong_verbs: bool


@router.post("/optimize", response_model=OptimizationResponse)
async def optimize_text(
    request: OptimizationRequest,
    background_tasks: BackgroundTasks
) -> OptimizationResponse:
    """Optimize text using 2025 standards and best practices."""

    correlation_id = request.correlation_id or "unknown"

    logger.info(
        f"Starting text optimization for user {request.user_id}, "
        f"level: {request.optimization_level}, correlation_id: {correlation_id}"
    )

    try:
        # Validate text length
        if len(request.text) > settings.MAX_TEXT_LENGTH:
            raise HTTPException(
                status_code=400,
                detail=f"Text too long. Maximum {settings.MAX_TEXT_LENGTH} characters allowed."
            )

        # Validate optimization level
        try:
            opt_level = OptimizationLevel(request.optimization_level)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid optimization level. Use: light, standard, or aggressive"
            )

        # Perform optimization
        result = text_optimizer.optimize_text(
            text=request.text,
            optimization_level=opt_level,
            context=request.context
        )

        # Validate performance requirements
        if result.processing_time > settings.OPTIMIZATION_TIMEOUT:
            logger.warning(
                f"Optimization exceeded timeout: {result.processing_time}s > "
                f"{settings.OPTIMIZATION_TIMEOUT}s for correlation_id: {correlation_id}"
            )

        # Check if targets are met
        if result.impact_score < settings.TARGET_IMPACT_SCORE:
            logger.info(
                f"Impact score ({result.impact_score}) below target "
                f"({settings.TARGET_IMPACT_SCORE}) for correlation_id: {correlation_id}"
            )

        if result.readability_score < settings.TARGET_READABILITY_SCORE:
            logger.info(
                f"Readability score ({result.readability_score}) below target "
                f"({settings.TARGET_READABILITY_SCORE}) for correlation_id: {correlation_id}"
            )

        logger.info(
            f"Text optimization completed in {result.processing_time:.2f}s "
            f"with impact score: {result.impact_score} for correlation_id: {correlation_id}"
        )

        return OptimizationResponse(
            original_text=result.original_text,
            optimized_text=result.optimized_text,
            improvements=result.improvements,
            readability_score=result.readability_score,
            impact_score=result.impact_score,
            processing_time=result.processing_time,
            optimization_level=result.optimization_level.value,
            correlation_id=correlation_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Text optimization failed for correlation_id {correlation_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Text optimization failed: {str(e)}"
        )


@router.post("/bullet-point", response_model=OptimizationResponse)
async def optimize_bullet_point(
    request: OptimizationRequest,
    background_tasks: BackgroundTasks
) -> OptimizationResponse:
    """Optimize a single bullet point for maximum impact (aggressive optimization)."""

    correlation_id = request.correlation_id or "unknown"

    logger.info(
        f"Starting bullet point optimization for user {request.user_id}, "
        f"correlation_id: {correlation_id}"
    )

    try:
        # Validate text length
        if len(request.text) > 500:  # Bullet points should be shorter
            raise HTTPException(
                status_code=400,
                detail="Bullet point too long. Maximum 500 characters allowed."
            )

        # Use specialized bullet point optimization
        result = text_optimizer.optimize_bullet_point(
            bullet_point=request.text,
            context=request.context
        )

        logger.info(
            f"Bullet point optimization completed in {result.processing_time:.2f}s "
            f"with impact score: {result.impact_score} for correlation_id: {correlation_id}"
        )

        return OptimizationResponse(
            original_text=result.original_text,
            optimized_text=result.optimized_text,
            improvements=result.improvements,
            readability_score=result.readability_score,
            impact_score=result.impact_score,
            processing_time=result.processing_time,
            optimization_level=result.optimization_level.value,
            correlation_id=correlation_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bullet point optimization failed for correlation_id {correlation_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Bullet point optimization failed: {str(e)}"
        )


@router.post("/summary", response_model=OptimizationResponse)
async def optimize_summary(
    request: OptimizationRequest,
    background_tasks: BackgroundTasks
) -> OptimizationResponse:
    """Optimize professional summary text (standard optimization)."""

    correlation_id = request.correlation_id or "unknown"

    logger.info(
        f"Starting summary optimization for user {request.user_id}, "
        f"correlation_id: {correlation_id}"
    )

    try:
        # Validate text length for summaries
        if len(request.text) > 1000:  # Summaries should be concise
            raise HTTPException(
                status_code=400,
                detail="Summary too long. Maximum 1000 characters allowed."
            )

        # Use specialized summary optimization
        result = text_optimizer.optimize_summary(
            summary=request.text,
            context=request.context
        )

        logger.info(
            f"Summary optimization completed in {result.processing_time:.2f}s "
            f"with impact score: {result.impact_score} for correlation_id: {correlation_id}"
        )

        return OptimizationResponse(
            original_text=result.original_text,
            optimized_text=result.optimized_text,
            improvements=result.improvements,
            readability_score=result.readability_score,
            impact_score=result.impact_score,
            processing_time=result.processing_time,
            optimization_level=result.optimization_level.value,
            correlation_id=correlation_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Summary optimization failed for correlation_id {correlation_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Summary optimization failed: {str(e)}"
        )


@router.post("/suggestions", response_model=SuggestionsResponse)
async def get_optimization_suggestions(
    request: SuggestionsRequest
) -> SuggestionsResponse:
    """Get optimization suggestions without applying them."""

    try:
        suggestions = text_optimizer.get_optimization_suggestions(request.text)

        # Analyze text characteristics
        text_length = len(request.text.split())
        has_metrics = any(
            text_optimizer._calculate_metrics_density(request.text) > 0
            for pattern in text_optimizer.metric_patterns
        )
        has_strong_verbs = any(
            verb in request.text.lower()
            for verb in text_optimizer.strong_action_verbs
        )

        return SuggestionsResponse(
            suggestions=suggestions,
            text_length=text_length,
            has_metrics=has_metrics,
            has_strong_verbs=has_strong_verbs
        )

    except Exception as e:
        logger.error(f"Failed to generate suggestions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate suggestions: {str(e)}"
        )


@router.get("/optimization-levels")
async def get_optimization_levels() -> Dict[str, Any]:
    """Get available optimization levels and their descriptions."""
    return {
        "optimization_levels": [
            {
                "level": "light",
                "name": "Light Optimization",
                "description": "Basic improvements - weak word elimination",
                "features": ["Remove weak phrases", "Basic improvements"],
                "recommended_for": ["Quick reviews", "Minimal changes needed"]
            },
            {
                "level": "standard",
                "name": "Standard Optimization",
                "description": "Comprehensive optimization with strong verbs and quantification",
                "features": [
                    "Weak word elimination",
                    "Action verb strengthening",
                    "Quantification enhancement",
                    "Readability improvement"
                ],
                "recommended_for": ["Most resume bullets", "Professional summaries"]
            },
            {
                "level": "aggressive",
                "name": "Aggressive Optimization",
                "description": "Maximum optimization with Verb + Metric + Outcome transformation",
                "features": [
                    "All standard features",
                    "Verb + Metric + Outcome structure",
                    "AI/ML keyword integration",
                    "Maximum impact scoring"
                ],
                "recommended_for": ["Critical achievements", "Key accomplishments"]
            }
        ],
        "2025_features": [
            "80% more visual fixation with VMO structure",
            "65% information retention improvement",
            "91% recruiter preference for strong verbs",
            "15.85% salary premium with AI skills integration"
        ]
    }


@router.get("/health/optimization")
async def optimization_health_check() -> Dict[str, Any]:
    """Health check specific to text optimization capabilities."""
    return {
        "text_optimizer": "operational",
        "2025_optimizations": "enabled",
        "supported_levels": ["light", "standard", "aggressive"],
        "max_text_length": settings.MAX_TEXT_LENGTH,
        "optimization_timeout": f"{settings.OPTIMIZATION_TIMEOUT} seconds",
        "target_impact_score": f"{settings.TARGET_IMPACT_SCORE}%",
        "target_readability_score": f"{settings.TARGET_READABILITY_SCORE}%",
        "features": [
            "weak_word_elimination",
            "action_verb_strengthening",
            "quantification_enhancement",
            "verb_metric_outcome_transformation",
            "ai_ml_skill_integration"
        ]
    }