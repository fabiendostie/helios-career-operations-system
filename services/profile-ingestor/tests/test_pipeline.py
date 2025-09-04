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

    @patch("resume_extractor.pipeline.ConflictResolverUI")
    @patch("resume_extractor.pipeline.ElicitationUI")
    def test_pipeline_run_without_conflicts(
        self, mock_elicitation, mock_conflict_resolver
    ):
        """Test pipeline runs successfully without conflicts."""
        # Mock UI components to avoid interactive prompts
        mock_elicitation_instance = Mock()
        mock_elicitation_instance.gather_additional_info.return_value = {
            "personal_info": {"name": "Test User"},
            "work_experience": [],
            "holistic_profile": {},
        }
        mock_elicitation.return_value = mock_elicitation_instance

        mock_conflict_resolver_instance = Mock()
        mock_conflict_resolver_instance.resolve_conflicts.return_value = {}
        mock_conflict_resolver.return_value = mock_conflict_resolver_instance

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
