"""
Tests for the pipeline orchestration.
"""

import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch
from resume_extractor.pipeline import Pipeline


class TestPipeline:
    """Test cases for Pipeline."""

    def setup_method(self):
        """Setup test fixtures."""
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.output_file = "test_output.json"

        # Create sample test files
        self._create_sample_files()

        # Initialize pipeline
        self.pipeline = Pipeline(
            input_directory=self.temp_path, output_file=self.output_file
        )

    def _create_sample_files(self):
        """Create sample resume files for testing."""
        # Sample text resume
        (self.temp_path / "resume.txt").write_text(
            "John Doe\\nSoftware Engineer\\nGoogle Inc.\\n2020-2023\\nPython, JavaScript",
            encoding="utf-8",
        )

        # Sample markdown resume
        (self.temp_path / "resume.md").write_text(
            "# Jane Smith\\n## Experience\\n- **Senior Developer** at Microsoft (2019-2022)\\n- Python, React",
            encoding="utf-8",
        )

    def test_pipeline_initialization(self):
        """Test pipeline initializes correctly."""
        assert self.pipeline.input_directory == self.temp_path
        assert self.pipeline.output_file == self.output_file
        assert self.pipeline.ingestion_engine is not None
        assert self.pipeline.parsing_service is not None
        assert self.pipeline.consolidation_engine is not None

    def test_pipeline_run_without_conflicts(self):
        """Test pipeline runs successfully without conflicts."""
        # Mock UI components to avoid interactive prompts
        with patch("resume_extractor.ui.elicitation.questionary") as mock_questionary, \
             patch("resume_extractor.ui.conflict_resolver.questionary") as mock_quest_conflict:

            # Set up mock to skip all interactive parts
            mock_questionary.confirm.return_value.ask.return_value = False
            mock_quest_conflict.confirm.return_value.ask.return_value = False

            # Mock the UI components at the pipeline level
            mock_elicitation = Mock()
            mock_elicitation.conduct_interview.return_value = {
                "personal_info": {"name": "Test User"},
                "aspirations": [],
                "motivators": [],
            }
            self.pipeline.elicitation_ui = mock_elicitation

            mock_resolver = Mock()
            mock_resolver.resolve_conflicts_legacy.return_value = {
                "work_experience": [],
                "skills_inventory": {},
                "strategic_metadata": {},
            }
            self.pipeline.conflict_resolver = mock_resolver

            # Run pipeline
            self.pipeline.run()

        # Check output file was created
        output_path = Path(self.output_file)
        assert output_path.exists()

        # Verify JSON structure
        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert isinstance(data, dict)

        # Cleanup
        output_path.unlink(missing_ok=True)

    def test_write_output(self):
        """Test output writing functionality."""
        test_data = {"personal_info": {"name": "Test User"}, "work_experience": []}

        self.pipeline._write_output(test_data)

        # Verify file was created and contains correct data
        output_path = Path(self.output_file)
        assert output_path.exists()

        with open(output_path, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)

        assert loaded_data == test_data

        # Cleanup
        output_path.unlink(missing_ok=True)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

        # Clean up output file if it exists
        output_path = Path(self.output_file)
        output_path.unlink(missing_ok=True)
