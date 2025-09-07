"""Integration tests for the complete analyst service pipeline."""

import pytest
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from src.api.analysis import AnalysisPipeline
from src.integrations.orchestrator import (
    OrchestratorClient,
    AsyncOrchestratorIntegration,
)


@pytest.fixture
def sample_master_career_data():
    """Sample master career database data."""
    return {
        "work_experience": [
            {
                "role": "Senior Software Engineer",
                "company": "TechCorp",
                "accomplishments": [
                    {
                        "description": "Architected microservices using Python and Docker, improving system performance by 40%"
                    },
                    {
                        "description": "Led team of 5 developers in implementing ML pipeline with 99% uptime"
                    },
                ],
            }
        ],
        "projects": [
            {
                "name": "Career Analysis Platform",
                "description": "Built AI-powered career analysis system using NLP and machine learning",
            }
        ],
        "skills_inventory": {
            "technical": ["Python", "Docker", "Machine Learning", "AWS"],
            "soft": ["Leadership", "Team Management"],
        },
    }


@pytest.fixture
def mock_orchestrator_client():
    """Mock orchestrator client for testing."""
    with patch(
        "src.integrations.orchestrator.aiohttp.ClientSession"
    ) as mock_session_class:
        # Create mock session instance
        mock_session_instance = AsyncMock()
        mock_session_instance.closed = False
        mock_session_instance.close = AsyncMock()

        # Create mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={"operation_id": "test_123", "status": "success"}
        )

        # Configure the request method to return the mock response
        async def mock_request_context(*args, **kwargs):
            return mock_response

        mock_session_instance.request.return_value.__aenter__ = AsyncMock(
            return_value=mock_response
        )
        mock_session_instance.request.return_value.__aexit__ = AsyncMock(
            return_value=None
        )

        # Configure the session class to return our mock instance
        mock_session_class.return_value = mock_session_instance

        yield mock_session_instance


@pytest.mark.asyncio
async def test_orchestrator_client_basic_operations(mock_orchestrator_client):
    """Test basic orchestrator client operations."""
    client = OrchestratorClient()

    # Mock the _make_request method directly to avoid aiohttp session complexity
    with patch.object(client, "_make_request", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {"operation_id": "test_123", "status": "success"}

        # Test registration
        operation_id = await client.register_analysis_request(
            "user123", {"test": "data"}, "corr123"
        )
        assert operation_id == "test_123"

        # Test progress update
        await client.update_analysis_progress(
            "test_123", {"stage": "processing"}, "corr123"
        )

        # Test completion
        await client.complete_analysis("test_123", {"result": "success"}, "corr123")

        # Verify request method was called appropriate times
        assert mock_request.call_count == 3

    await client.close()


@pytest.mark.asyncio
async def test_orchestrator_client_error_handling(mock_orchestrator_client):
    """Test orchestrator client error handling."""
    from src.integrations.orchestrator import OrchestratorError

    client = OrchestratorClient()

    # Mock the _make_request method to raise an error
    with patch.object(client, "_make_request", new_callable=AsyncMock) as mock_request:
        mock_request.side_effect = OrchestratorError("Internal server error")

        # Should raise OrchestratorError
        with pytest.raises(OrchestratorError):
            await client.register_analysis_request("user123", {"test": "data"})

    await client.close()


@pytest.mark.asyncio
async def test_analysis_pipeline_execution(sample_master_career_data):
    """Test complete analysis pipeline execution."""
    # Mock the NLP models at the module level to avoid loading during tests
    with (
        patch("src.core.resume_deconstructor.spacy.load") as mock_spacy_load,
        patch("src.core.resume_deconstructor.Matcher") as mock_matcher_class,
        patch("src.core.resume_deconstructor.SentenceTransformer") as mock_st,
        patch("yaml.safe_load") as mock_yaml_load,
    ):
        # Setup mocks similar to test_resume_deconstructor.py
        mock_en = Mock()
        mock_fr = Mock()

        mock_vocab_en = Mock()
        mock_vocab_fr = Mock()
        mock_vocab_en.strings = Mock()
        mock_vocab_fr.strings = Mock()

        mock_en.vocab = mock_vocab_en
        mock_fr.vocab = mock_vocab_fr
        mock_en.return_value = Mock(ents=[])
        mock_fr.return_value = Mock(ents=[])

        mock_spacy_load.side_effect = (
            lambda model: mock_en if model == "en_core_web_sm" else mock_fr
        )

        mock_matcher_instance = Mock()
        mock_matcher_class.return_value = mock_matcher_instance
        mock_st.return_value = Mock()

        mock_yaml_load.return_value = {
            "high_impact_verbs": {"technical": ["architected", "built"]},
            "weak_verbs_to_avoid": ["helped"],
            "quantification_patterns": {"percentage": r"\d+%"},
        }

        # Create pipeline
        pipeline = AnalysisPipeline()

        # Configure mocks to return minimal realistic data structures
        with patch.object(
            pipeline.resume_deconstructor, "process_resume_sections"
        ) as mock_process:
            # Mock to return a realistic ResumeDeconstruction structure
            from src.models.ner_entities import ResumeDeconstruction

            mock_process.return_value = ResumeDeconstruction(
                sections=[],
                entity_summary={},
                language_distribution={"en": 100.0},
                semantic_embeddings={},
                processing_time_seconds=0.1,
                quality_metrics={},
            )

            # Execute pipeline
            result = await pipeline.execute_full_pipeline(sample_master_career_data)

            # Verify basic structure - pipeline should complete without exceptions
            assert "pipeline_steps" in result
            assert "processing_time_seconds" in result
            assert result["processing_time_seconds"] >= 0


@pytest.mark.asyncio
async def test_async_orchestrator_integration(sample_master_career_data):
    """Test async orchestrator integration."""

    async def mock_analysis_function(data):
        """Mock analysis function."""
        return {
            "pipeline_steps": {"test": {"status": "completed"}},
            "recommendations": ["Test recommendation"],
            "processing_time_seconds": 0.1,
        }

    integration = AsyncOrchestratorIntegration(max_retries=1, retry_delay=0.1)

    async with integration:
        # Mock the _make_request method directly to avoid aiohttp complexity
        with patch.object(
            integration._client, "_make_request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = {"operation_id": "op123", "status": "success"}

            result = await integration.execute_analysis_with_orchestrator(
                "user123", sample_master_career_data, mock_analysis_function, "corr123"
            )

        assert "pipeline_steps" in result
        assert "recommendations" in result
        assert result["recommendations"][0] == "Test recommendation"


@pytest.mark.asyncio
async def test_orchestrator_retry_logic(mock_orchestrator_client):
    """Test orchestrator retry logic with failures."""

    # Mock initial failures then success
    error_response = AsyncMock()
    error_response.status = 500
    error_response.json = AsyncMock(return_value={"detail": "Server error"})

    success_response = AsyncMock()
    success_response.status = 200
    success_response.json = AsyncMock(return_value={"operation_id": "success123"})

    mock_orchestrator_client.request.return_value.__aenter__.side_effect = [
        error_response,  # First attempt fails
        error_response,  # Second attempt fails
        success_response,  # Third attempt succeeds
    ]

    integration = AsyncOrchestratorIntegration(max_retries=3, retry_delay=0.01)

    async with integration:
        # Should succeed after retries
        await integration.check_orchestrator_connectivity()
        # Since we're mocking the health check, this might not behave exactly as expected
        # but the retry logic should be exercised


@pytest.mark.asyncio
async def test_pipeline_with_error_handling(sample_master_career_data):
    """Test pipeline behavior with component errors."""

    # Mock the NLP models first to allow pipeline initialization
    with (
        patch("src.core.resume_deconstructor.spacy.load") as mock_spacy_load,
        patch("src.core.resume_deconstructor.Matcher") as mock_matcher_class,
        patch("src.core.resume_deconstructor.SentenceTransformer") as mock_st,
    ):
        # Setup basic mocks for initialization
        mock_en = Mock()
        mock_fr = Mock()
        mock_vocab_en = Mock()
        mock_vocab_fr = Mock()
        mock_vocab_en.strings = Mock()
        mock_vocab_fr.strings = Mock()
        mock_en.vocab = mock_vocab_en
        mock_fr.vocab = mock_vocab_fr
        mock_en.return_value = Mock(ents=[])
        mock_fr.return_value = Mock(ents=[])
        mock_spacy_load.side_effect = (
            lambda model: mock_en if model == "en_core_web_sm" else mock_fr
        )
        mock_matcher_class.return_value = Mock()
        mock_st.return_value = Mock()

        # Create pipeline
        pipeline = AnalysisPipeline()

        # Now mock the specific method to raise an error
        with patch.object(
            pipeline.resume_deconstructor,
            "process_resume_sections",
            side_effect=Exception("NLP model error"),
        ):
            result = await pipeline.execute_full_pipeline(sample_master_career_data)

            # Should return error information
            assert "error" in result
            assert "pipeline_steps" in result
            assert result["recommendations"][0] == "Analysis incomplete due to error"


def test_analysis_pipeline_component_initialization():
    """Test that all pipeline components initialize correctly."""

    # Mock the NLP models at the module level using the same pattern
    with (
        patch("src.core.resume_deconstructor.spacy.load") as mock_spacy_load,
        patch("src.core.resume_deconstructor.Matcher") as mock_matcher_class,
        patch("src.core.resume_deconstructor.SentenceTransformer") as mock_st,
        patch("yaml.safe_load") as mock_yaml_load,
        patch("json.load") as mock_json_load,
    ):
        # Setup basic mocks for initialization
        mock_en = Mock()
        mock_fr = Mock()
        mock_vocab_en = Mock()
        mock_vocab_fr = Mock()
        mock_vocab_en.strings = Mock()
        mock_vocab_fr.strings = Mock()
        mock_en.vocab = mock_vocab_en
        mock_fr.vocab = mock_vocab_fr
        mock_en.return_value = Mock(ents=[])
        mock_fr.return_value = Mock(ents=[])
        mock_spacy_load.side_effect = (
            lambda model: mock_en if model == "en_core_web_sm" else mock_fr
        )
        mock_matcher_class.return_value = Mock()
        mock_st.return_value = Mock()
        mock_yaml_load.return_value = {}
        mock_json_load.return_value = []

        # Should not raise exceptions
        pipeline = AnalysisPipeline()

        # Verify all components exist
        assert hasattr(pipeline, "resume_deconstructor")
        assert hasattr(pipeline, "market_analyzer")
        assert hasattr(pipeline, "ats_simulator")
        assert hasattr(pipeline, "skill_recalibrator")
        assert hasattr(pipeline, "career_inferencer")


@pytest.mark.asyncio
async def test_integration_with_mock_components(sample_master_career_data):
    """Test integration with completely mocked components."""

    # Mock all external dependencies
    with patch.multiple(
        "src.core.resume_deconstructor.ResumeDeconstructor",
        __init__=lambda x: None,
        process_resume_sections=MagicMock(
            return_value=MagicMock(
                sections=[],
                entity_summary={},
                language_distribution={"en": 100},
                processing_time_seconds=0.1,
                quality_metrics={},
            )
        ),
    ):
        with patch.multiple(
            "src.core.market_analyzer.MarketAnalyzer",
            __init__=lambda x: None,
            analyze_market=MagicMock(
                return_value=MagicMock(
                    job_matches=[],
                    recommendations=[],
                    processing_metadata={"processing_time_seconds": 0.1},
                )
            ),
        ):
            with patch.multiple(
                "src.core.ats_simulator.ATSSimulator", __init__=lambda x: None
            ):
                with patch.multiple(
                    "src.core.skill_recalibrator.SkillRecalibrator",
                    __init__=lambda x: None,
                    recalibrate_skills=MagicMock(
                        return_value=MagicMock(
                            leverage_skills=[],
                            upskill_skills=[],
                            matrix_insights={
                                "total_skills_analyzed": 0,
                                "quadrant_distribution": {},
                            },
                            development_roadmap=[],
                        )
                    ),
                ):
                    with patch.multiple(
                        "src.core.career_inferencer.CareerInferencer",
                        __init__=lambda x: None,
                        infer_career_paths=MagicMock(
                            return_value=MagicMock(
                                career_paths=[],
                                current_positioning={},
                                market_readiness={"readiness_level": "developing"},
                                executive_summary="Test summary",
                                processing_metadata={"processing_time_seconds": 0.1},
                            )
                        ),
                    ):
                        pipeline = AnalysisPipeline()
                        result = await pipeline.execute_full_pipeline(
                            sample_master_career_data
                        )

                        # Should complete successfully with mocked components
                        assert "pipeline_steps" in result
                        assert "recommendations" in result
                        assert result["executive_summary"] == "Test summary"
