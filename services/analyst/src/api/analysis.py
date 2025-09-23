"""Analysis pipeline endpoints for the Analyst service."""

import logging
from typing import Dict, Any
import time

from fastapi import APIRouter, HTTPException, BackgroundTasks

from src.models.analysis_request import (
    AnalysisRequest,
    AnalysisResponse,
    PipelineStepResult,
)
from src.core.config import settings
from src.core.resume_deconstructor import ResumeDeconstructor
from src.core.market_analyzer import MarketAnalyzer
from src.core.ats_simulator import ATSSimulator
from src.core.skill_recalibrator import SkillRecalibrator
from src.core.career_inferencer import CareerInferencer
from src.integrations.orchestrator import AsyncOrchestratorIntegration


logger = logging.getLogger(__name__)
router = APIRouter()


class AnalysisPipeline:
    """Complete 6-step analysis pipeline."""

    def __init__(self):
        """Initialize all analysis components with 2025 enhancements."""
        self.resume_deconstructor = ResumeDeconstructor()
        self.market_analyzer = MarketAnalyzer(use_realtime_data=True)  # Enable real-time data
        self.ats_simulator = ATSSimulator()
        self.skill_recalibrator = SkillRecalibrator()
        self.career_inferencer = CareerInferencer()

    async def execute_full_pipeline(
        self, master_career_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the complete 6-step analysis pipeline."""
        start_time = time.time()
        pipeline_results = {}

        try:
            # Step 1: Resume Deconstruction
            logger.info("Starting Step 1: Resume Deconstruction")
            resume_deconstruction = self.resume_deconstructor.process_resume_sections(
                master_career_data
            )
            pipeline_results["resume_deconstruction"] = {
                "status": "completed",
                "entities_extracted": sum(
                    len(section.entities) for section in resume_deconstruction.sections
                ),
                "sections_processed": len(resume_deconstruction.sections),
                "processing_time": resume_deconstruction.processing_time_seconds,
            }

            # Step 2: Market Analysis (Enhanced with Real-time Data)
            logger.info("Starting Step 2: Market Analysis (Real-time 2025 Data)")
            market_analysis = await self.market_analyzer.analyze_market(resume_deconstruction)
            pipeline_results["market_analysis"] = {
                "status": "completed",
                "jobs_matched": len(market_analysis.job_matches),
                "top_match_score": market_analysis.job_matches[0].similarity_score
                if market_analysis.job_matches
                else 0.0,
                "processing_time": market_analysis.processing_metadata.get(
                    "processing_time_seconds", 0.0
                ),
                "realtime_data_included": market_analysis.processing_metadata.get(
                    "analysis_enhanced_2025", False
                ),
                "data_sources": market_analysis.processing_metadata.get(
                    "data_sources", ["static"]
                ),
            }

            # Step 3: ATS Simulation (using top job match)
            logger.info("Starting Step 3: ATS Simulation")
            if market_analysis.job_matches:
                target_job = market_analysis.job_matches[0].job
                ats_score = self.ats_simulator.simulate_ats_score(
                    resume_deconstruction, target_job
                )
                pipeline_results["ats_simulation"] = {
                    "status": "completed",
                    "ats_score": ats_score.percentage_score,
                    "performance_level": ats_score.performance_level.value,
                    "optimization_recommendations": len(
                        ats_score.optimization_recommendations
                    ),
                }
            else:
                pipeline_results["ats_simulation"] = {
                    "status": "skipped",
                    "reason": "No job matches found for ATS simulation",
                }
                # Create dummy ATS score for downstream processing
                from src.models.ats_scoring import ATSScore, ScoreLevel

                ats_score = ATSScore(
                    overall_score=0.5,
                    percentage_score=50,
                    performance_level=ScoreLevel.FAIR,
                    criteria_scores=[],
                    summary={},
                    optimization_recommendations=[],
                    ats_readiness_feedback={},
                )

            # Step 4: Skill Recalibration
            logger.info("Starting Step 4: Skill Recalibration")
            skill_matrix = self.skill_recalibrator.recalibrate_skills(
                resume_deconstruction, market_analysis
            )
            pipeline_results["skill_recalibration"] = {
                "status": "completed",
                "skills_analyzed": skill_matrix.matrix_insights[
                    "total_skills_analyzed"
                ],
                "leverage_skills": len(skill_matrix.leverage_skills),
                "upskill_opportunities": len(skill_matrix.upskill_skills),
            }

            # Step 5-6: Career Path Inference & Report Generation
            logger.info("Starting Step 5-6: Career Path Inference & Report Generation")
            career_report = self.career_inferencer.infer_career_paths(
                resume_deconstruction, market_analysis, skill_matrix, ats_score
            )
            pipeline_results["career_inference"] = {
                "status": "completed",
                "career_paths_generated": len(career_report.career_paths),
                "market_readiness": career_report.market_readiness["readiness_level"],
                "processing_time": career_report.processing_metadata.get(
                    "processing_time_seconds", 0.0
                ),
            }

            # Compile comprehensive recommendations
            recommendations = []
            recommendations.extend(market_analysis.recommendations)
            if (
                "ats_simulation" in pipeline_results
                and pipeline_results["ats_simulation"]["status"] == "completed"
            ):
                recommendations.extend(ats_score.optimization_recommendations[:3])
            recommendations.extend(
                [f"Develop {skill.skill}" for skill in skill_matrix.upskill_skills[:3]]
            )
            recommendations.extend(
                [path.title for path in career_report.career_paths[:3]]
            )

            total_processing_time = time.time() - start_time

            return {
                "pipeline_steps": pipeline_results,
                "recommendations": list(set(recommendations))[
                    :10
                ],  # Top 10 unique recommendations
                "processing_time_seconds": total_processing_time,
                "executive_summary": career_report.executive_summary,
                "detailed_results": {
                    "resume_analysis": {
                        "entity_summary": dict(resume_deconstruction.entity_summary),
                        "quality_metrics": resume_deconstruction.quality_metrics,
                    },
                    "market_positioning": {
                        "job_matches": len(market_analysis.job_matches),
                        "compensation_analysis": market_analysis.compensation_analysis,
                        "skill_demand": market_analysis.skill_demand_analysis,
                    },
                    "ats_readiness": {
                        "score": ats_score.percentage_score
                        if "ats_simulation" in pipeline_results
                        else 0,
                        "level": ats_score.performance_level.value
                        if "ats_simulation" in pipeline_results
                        else "unknown",
                    },
                    "skill_portfolio": {
                        "quadrant_distribution": skill_matrix.matrix_insights[
                            "quadrant_distribution"
                        ],
                        "development_roadmap": skill_matrix.development_roadmap,
                    },
                    "career_paths": {
                        "paths": [
                            {
                                "title": path.title,
                                "type": path.path_type.value,
                                "confidence": path.confidence_score,
                                "timeline": path.preparation_timeline,
                            }
                            for path in career_report.career_paths[:5]
                        ],
                        "current_positioning": career_report.current_positioning,
                    },
                },
            }

        except Exception as e:
            logger.error(f"Pipeline execution failed: {str(e)}")
            # Return partial results if possible
            return {
                "pipeline_steps": pipeline_results,
                "recommendations": ["Analysis incomplete due to error"],
                "processing_time_seconds": time.time() - start_time,
                "error": str(e),
            }


# Global pipeline instance
analysis_pipeline = AnalysisPipeline()


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_resume(
    request: AnalysisRequest, background_tasks: BackgroundTasks
) -> AnalysisResponse:
    """Execute the 6-step analysis pipeline."""
    correlation_id = request.correlation_id or "unknown"

    logger.info(
        f"Starting analysis pipeline for user {request.user_id}, correlation_id: {correlation_id}"
    )

    try:
        # Execute with orchestrator integration
        async with AsyncOrchestratorIntegration() as orchestrator:
            analysis_result = await orchestrator.execute_analysis_with_orchestrator(
                request.user_id,
                request.master_career_data,
                analysis_pipeline.execute_full_pipeline,
                correlation_id,
            )

        # Ensure response time requirement (<5s)
        processing_time = analysis_result.get("processing_time_seconds", 0.0)
        if processing_time > settings.ANALYSIS_TIMEOUT:
            logger.warning(
                f"Analysis exceeded timeout: {processing_time}s > {settings.ANALYSIS_TIMEOUT}s"
            )

        logger.info(
            f"Analysis completed in {processing_time:.2f}s for correlation_id: {correlation_id}"
        )

        # Convert pipeline steps to response format
        pipeline_steps = {}
        for step_name, step_data in analysis_result.get("pipeline_steps", {}).items():
            pipeline_steps[step_name] = PipelineStepResult(
                status=step_data.get("status", "unknown"), details=step_data
            )

        return AnalysisResponse(
            correlation_id=correlation_id,
            pipeline_steps=pipeline_steps,
            recommendations=analysis_result.get("recommendations", []),
            processing_time_seconds=processing_time,
            metadata=analysis_result.get("detailed_results", {}),
        )

    except Exception as e:
        logger.error(f"Analysis failed for correlation_id {correlation_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Analysis pipeline failed: {str(e)}"
        )


@router.get("/status/{correlation_id}")
async def get_analysis_status(correlation_id: str) -> Dict[str, Any]:
    """Get the status of an analysis operation."""
    # Check with orchestrator for operation status
    try:
        async with AsyncOrchestratorIntegration() as orchestrator:
            if await orchestrator.check_orchestrator_connectivity():
                return {
                    "correlation_id": correlation_id,
                    "status": "running",
                    "message": "Check orchestrator for detailed status",
                }
            else:
                return {
                    "correlation_id": correlation_id,
                    "status": "unknown",
                    "message": "Unable to connect to orchestrator",
                }
    except Exception as e:
        logger.error(f"Failed to check status for {correlation_id}: {str(e)}")
        return {"correlation_id": correlation_id, "status": "error", "message": str(e)}


@router.get("/health/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """Detailed health check including component status."""
    health_status = {
        "service": "analyst",
        "status": "healthy",
        "timestamp": time.time(),
        "components": {},
    }

    try:
        # Check orchestrator connectivity
        async with AsyncOrchestratorIntegration() as orchestrator:
            orchestrator_healthy = await orchestrator.check_orchestrator_connectivity()
            health_status["components"]["orchestrator"] = {
                "status": "healthy" if orchestrator_healthy else "unhealthy",
                "reachable": orchestrator_healthy,
            }
    except Exception as e:
        health_status["components"]["orchestrator"] = {
            "status": "unhealthy",
            "error": str(e),
        }

    # Check analysis components
    try:
        # Test basic component initialization
        test_components = {
            "resume_deconstructor": ResumeDeconstructor(),
            "market_analyzer": MarketAnalyzer(),
            "ats_simulator": ATSSimulator(),
            "skill_recalibrator": SkillRecalibrator(),
            "career_inferencer": CareerInferencer(),
        }

        for name, component in test_components.items():
            health_status["components"][name] = {"status": "healthy"}

    except Exception as e:
        health_status["status"] = "degraded"
        health_status["components"]["analysis_pipeline"] = {
            "status": "unhealthy",
            "error": str(e),
        }

    return health_status
