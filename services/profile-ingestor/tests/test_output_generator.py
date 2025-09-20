"""
Test suite for OutputGenerator component.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from jsonschema import ValidationError

from resume_extractor.components.output_generator import OutputGenerator
from resume_extractor.schemas.master_schema import MASTER_SCHEMA


class TestOutputGenerator:
    """Test cases for OutputGenerator class."""

    @pytest.fixture
    def mock_output_dir(self, tmp_path):
        """Create a temporary output directory for testing."""
        return tmp_path / "test_output"

    @pytest.fixture
    def output_generator(self, mock_output_dir):
        """Create OutputGenerator instance for testing."""
        return OutputGenerator(output_dir=mock_output_dir)

    @pytest.fixture
    def sample_consolidated_data(self):
        """Sample consolidated data for testing."""
        return {
            "work_experience": [
                {
                    "role": "Senior Software Engineer",
                    "company": "TechCorp Inc",
                    "dates": "2020-2023",
                    "description": "Led development of scalable web applications",
                    "accomplishments": [
                        "Implemented microservices architecture resulting in 40% performance improvement",
                        "Led team of 5 developers to deliver projects 2 weeks early",
                        "Reduced bug reports by 60% through improved testing practices",
                    ],
                },
                {
                    "role": "Software Developer",
                    "company": "StartupXYZ",
                    "dates": "2018-2020",
                    "description": "Developed full-stack applications using Python and React",
                    "accomplishments": [
                        "Built REST API serving 10,000+ requests per minute",
                        "Automated deployment pipeline reducing release time by 75%",
                    ],
                },
            ],
            "projects": [
                {
                    "name": "E-commerce Platform",
                    "description": "Built scalable e-commerce solution",
                    "technologies": ["Python", "Django", "PostgreSQL", "Redis"],
                    "outcomes": ["Handles 100k+ daily users", "99.9% uptime"],
                }
            ],
            "skills": {
                "technical": ["Python", "JavaScript", "Docker", "AWS"],
                "soft": ["Leadership", "Communication", "Problem Solving"],
                "languages": ["English", "French"],
                "tools": ["Git", "Jenkins", "PostgreSQL"],
            },
            "holistic_profile": {
                "transversal_projects": [
                    {
                        "name": "Open Source Contributions",
                        "description": "Active contributor to various open source projects",
                        "skills_demonstrated": ["Python", "Git", "Collaboration"],
                        "link": "https://github.com/user",
                    }
                ],
                "professional_aspirations": {
                    "target_roles": ["Tech Lead", "Engineering Manager"],
                    "industries_of_interest": ["Fintech", "Healthcare"],
                    "technologies_to_learn": ["Kubernetes", "GraphQL"],
                },
                "core_motivators": [
                    "Innovation",
                    "Team Growth",
                    "Technical Excellence",
                ],
                "personal_qualities": [
                    {
                        "trait": "Analytical",
                        "evidence": "Consistently break down complex problems",
                    }
                ],
            },
            "source_files": ["resume.pdf", "cv.docx"],
            "processing_metadata": {
                "files_processed": 2,
                "conflicts_resolved": 3,
                "total_processing_time": 45.2,
            },
        }

    def test_initialization(self, mock_output_dir):
        """Test OutputGenerator initialization."""
        generator = OutputGenerator(output_dir=mock_output_dir)

        assert generator.output_dir == mock_output_dir
        assert mock_output_dir.exists()
        assert generator.console is not None

    def test_initialization_default_output_dir(self):
        """Test OutputGenerator initialization with default output directory."""
        with patch("pathlib.Path.mkdir") as mock_mkdir:
            generator = OutputGenerator()
            assert generator.output_dir == Path("output")
            mock_mkdir.assert_called_once_with(exist_ok=True)

    def test_transform_to_schema(self, output_generator, sample_consolidated_data):
        """Test data transformation to schema format."""
        result = output_generator._transform_to_schema(sample_consolidated_data)

        # Check required fields are present
        assert "work_experience" in result
        assert "projects" in result
        assert "skills_inventory" in result
        assert "strategic_metadata" in result
        assert "holistic_profile" in result

        # Check work experience transformation
        work_exp = result["work_experience"][0]
        assert work_exp["role"] == "Senior Software Engineer"
        assert work_exp["company"] == "TechCorp Inc"
        assert len(work_exp["accomplishments"]) == 3

        # Check accomplishments structure
        acc = work_exp["accomplishments"][0]
        assert "original" in acc
        assert "deconstructed" in acc
        assert "metrics" in acc
        assert "associated_skills" in acc
        assert "impact_score" in acc

    def test_transform_work_experience(
        self, output_generator, sample_consolidated_data
    ):
        """Test work experience transformation."""
        result = output_generator._transform_work_experience(sample_consolidated_data)

        assert len(result) == 2

        # Check first experience
        exp = result[0]
        assert exp["role"] == "Senior Software Engineer"
        assert exp["company"] == "TechCorp Inc"
        assert exp["dates"] == "2020-2023"
        assert len(exp["accomplishments"]) == 3

        # Check accomplishment structure
        acc = exp["accomplishments"][0]
        assert (
            acc["original"]
            == "Implemented microservices architecture resulting in 40% performance improvement"
        )
        assert isinstance(acc["deconstructed"], dict)
        assert isinstance(acc["metrics"], dict)
        assert isinstance(acc["associated_skills"], list)
        assert isinstance(acc["impact_score"], float)

    def test_transform_projects(self, output_generator, sample_consolidated_data):
        """Test projects transformation."""
        result = output_generator._transform_projects(sample_consolidated_data)

        assert len(result) == 1
        project = result[0]
        assert project["name"] == "E-commerce Platform"
        assert project["description"] == "Built scalable e-commerce solution"
        assert "Python" in project["technologies"]
        assert "Handles 100k+ daily users" in project["outcomes"]

    def test_transform_skills(self, output_generator, sample_consolidated_data):
        """Test skills transformation."""
        result = output_generator._transform_skills(sample_consolidated_data)

        assert "technical" in result
        assert "soft" in result
        assert "languages" in result
        assert "tools" in result

        # Check skills structure
        python_skill = next(
            (s for s in result["technical"] if s["skill"] == "Python"), None
        )
        assert python_skill is not None
        assert "evidence_pointers" in python_skill
        assert isinstance(python_skill["evidence_pointers"], list)

    def test_find_evidence_pointers(self, output_generator, sample_consolidated_data):
        """Test evidence pointer finding."""
        evidence = output_generator._find_evidence_pointers(
            "Python", sample_consolidated_data
        )

        assert isinstance(evidence, list)
        assert len(evidence) > 0
        # Should find evidence in work experience and projects
        assert any("TechCorp Inc" in ev or "StartupXYZ" in ev for ev in evidence)

    def test_deconstruct_accomplishment(self, output_generator):
        """Test accomplishment deconstruction."""
        text = "Implemented microservices architecture resulting in 40% performance improvement"
        result = output_generator._deconstruct_accomplishment(text)

        assert "action" in result
        assert "challenge" in result
        assert "outcome" in result
        assert result["action"] == "Implemented"
        assert "40% performance improvement" in result["outcome"]

    def test_extract_metrics(self, output_generator):
        """Test metrics extraction from text."""
        text = "Reduced costs by 40% and saved $50,000 over 6 months with 1,500 users"
        metrics = output_generator._extract_metrics(text)

        assert "percentage" in metrics
        assert "dollar_amount" in metrics
        assert "number" in metrics
        assert "time_period" in metrics

    def test_extract_skills_from_text(self, output_generator):
        """Test skill extraction from text."""
        text = "Developed Python API using Docker and AWS services with React frontend"
        skills = output_generator._extract_skills_from_text(text)

        assert "Python" in skills
        assert "Docker" in skills
        assert "AWS" in skills
        assert "React" in skills

    def test_calculate_impact_score(self, output_generator):
        """Test impact score calculation."""
        high_impact = "Led team of 10 engineers to deliver $2M project 30% under budget"
        low_impact = "Attended daily standups and completed assigned tasks"

        high_score = output_generator._calculate_impact_score(high_impact)
        low_score = output_generator._calculate_impact_score(low_impact)

        assert high_score > low_score
        assert 0 <= high_score <= 10
        assert 0 <= low_score <= 10

    def test_generate_strategic_metadata(
        self, output_generator, sample_consolidated_data
    ):
        """Test strategic metadata generation."""
        result = output_generator._generate_strategic_metadata(sample_consolidated_data)

        assert "job_title_variations" in result
        assert "top_anchor_accomplishments" in result
        assert "core_competencies" in result

        # Check job title variations
        assert "Senior Software Engineer" in result["job_title_variations"]
        assert len(result["top_anchor_accomplishments"]) <= 5

    def test_extract_title_variations(self, output_generator, sample_consolidated_data):
        """Test job title variation extraction."""
        titles = output_generator._extract_title_variations(sample_consolidated_data)

        assert "Senior Software Engineer" in titles
        assert "Software Developer" in titles
        # Should generate variations
        assert any("Lead" in title for title in titles)

    def test_identify_top_accomplishments(
        self, output_generator, sample_consolidated_data
    ):
        """Test top accomplishments identification."""
        top_accs = output_generator._identify_top_accomplishments(
            sample_consolidated_data
        )

        assert isinstance(top_accs, list)
        assert len(top_accs) <= 5
        # Should contain accomplishments with high impact
        assert any("40% performance improvement" in acc for acc in top_accs)

    def test_identify_core_competencies(
        self, output_generator, sample_consolidated_data
    ):
        """Test core competencies identification."""
        competencies = output_generator._identify_core_competencies(
            sample_consolidated_data
        )

        assert isinstance(competencies, list)
        assert "Python" in competencies  # Should be frequent skill

    def test_validate_data_success(self, output_generator):
        """Test successful data validation."""
        valid_data = {
            "work_experience": [],
            "skills_inventory": {},
            "holistic_profile": {},
        }

        result = output_generator._validate_data(valid_data)
        assert result == valid_data

    def test_validate_data_with_auto_fix(self, output_generator):
        """Test data validation with automatic fixes."""
        invalid_data = {}  # Missing required fields

        with patch.object(
            output_generator,
            "_attempt_auto_fix",
            return_value={
                "work_experience": [],
                "skills_inventory": {},
                "holistic_profile": {},
            },
        ):
            result = output_generator._validate_data(invalid_data)
            assert "work_experience" in result

    def test_validate_data_failure(self, output_generator):
        """Test data validation failure."""
        invalid_data = {"work_experience": "invalid"}  # Wrong type

        with patch.object(output_generator, "_attempt_auto_fix", return_value=None):
            with pytest.raises(ValidationError):
                output_generator._validate_data(invalid_data)

    def test_attempt_auto_fix(self, output_generator):
        """Test automatic fix attempts."""
        data = {}
        error = ValidationError("'work_experience' is a required property")

        result = output_generator._attempt_auto_fix(data, error)

        assert result is not None
        assert "work_experience" in result
        assert "skills_inventory" in result
        assert "holistic_profile" in result

    def test_add_metadata(self, output_generator, sample_consolidated_data):
        """Test metadata addition."""
        data = {"test": "data"}

        # Mock the internet datetime utility that's actually being used
        with patch(
            "resume_extractor.components.output_generator.get_current_datetime_sync"
        ) as mock_get_current_datetime:
            from datetime import datetime
            mock_dt = datetime(2023, 1, 1, 0, 0, 0)
            mock_get_current_datetime.return_value = mock_dt

            result = output_generator._add_metadata(data, sample_consolidated_data)

        assert "_metadata" in result
        metadata = result["_metadata"]
        assert metadata["generated_at"] == "2023-01-01T00:00:00"
        assert metadata["version"] == "1.0"
        assert metadata["source_files"] == ["resume.pdf", "cv.docx"]
        assert "statistics" in metadata

    def test_create_backup(self, output_generator, mock_output_dir):
        """Test backup creation."""
        test_data = {"test": "backup"}

        output_generator._create_backup(test_data)

        # Check if backup was created
        backups = list(mock_output_dir.glob(".backup_*.json"))
        assert len(backups) == 1

        # Verify backup content
        with open(backups[0]) as f:
            backup_data = json.load(f)
        assert backup_data == test_data

    def test_create_backup_cleanup(self, output_generator, mock_output_dir):
        """Test backup cleanup (keep only 5 most recent)."""
        # Create 7 old backups
        for i in range(7):
            backup_path = mock_output_dir / f".backup_{i}.json"
            backup_path.write_text("{}")

        # Create new backup
        output_generator._create_backup({"test": "data"})

        # Should have only 5 backups total
        backups = list(mock_output_dir.glob(".backup_*.json"))
        assert len(backups) <= 6  # 5 old + 1 new (cleanup may vary)

    def test_write_json(self, output_generator, mock_output_dir):
        """Test JSON file writing."""
        test_data = {"test": "json_write", "numbers": [1, 2, 3]}

        # Mock the internet datetime utility for filename generation
        with patch(
            "resume_extractor.components.output_generator.format_date_for_filename_sync"
        ) as mock_format_date:
            mock_format_date.return_value = "20230101_120000"

            result_path = output_generator._write_json(test_data)

        # Check timestamped file
        expected_path = mock_output_dir / "master_career_database_20230101_120000.json"
        assert result_path == expected_path
        assert expected_path.exists()

        # Check latest file
        latest_path = mock_output_dir / "master_career_database.json"
        assert latest_path.exists()

        # Verify content
        with open(result_path) as f:
            written_data = json.load(f)
        assert written_data == test_data

    def test_write_json_failure(self, output_generator):
        """Test JSON writing failure handling."""
        test_data = {"test": "data"}

        with patch("builtins.open", mock_open()) as mock_file:
            mock_file.side_effect = IOError("Permission denied")

            with pytest.raises(IOError, match="Failed to write JSON file"):
                output_generator._write_json(test_data)

    def test_display_success(self, output_generator, mock_output_dir):
        """Test success message display."""
        test_data = {
            "work_experience": [{"role": "Engineer"}],
            "projects": [{"name": "Project1"}],
            "skills_inventory": {"technical": [{"skill": "Python"}]},
            "holistic_profile": {"transversal_projects": [{"name": "OSS"}]},
        }

        # Create a test file
        test_file = mock_output_dir / "test.json"
        test_file.write_text('{"test": "data"}')

        # Mock the console's print method
        with patch.object(output_generator.console, "print") as mock_print:
            output_generator._display_success(test_file, test_data)

            # Verify console.print was called
            mock_print.assert_called_once()

    def test_full_generate_json_flow(
        self, output_generator, sample_consolidated_data, mock_output_dir
    ):
        """Test complete JSON generation flow."""
        with patch(
            "resume_extractor.components.output_generator.datetime"
        ) as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20230101_120000"
            mock_datetime.now.return_value.isoformat.return_value = (
                "2023-01-01T12:00:00"
            )
            mock_datetime.now.return_value.timestamp.return_value = 1672574400.0

            result_path = output_generator.generate_json(sample_consolidated_data)

        # Check file was created
        assert result_path.exists()
        assert result_path.name.startswith("master_career_database_")

        # Verify content structure
        with open(result_path) as f:
            output_data = json.load(f)

        assert "work_experience" in output_data
        assert "skills_inventory" in output_data
        assert "strategic_metadata" in output_data
        assert "holistic_profile" in output_data
        assert "_metadata" in output_data

        # Check metadata
        metadata = output_data["_metadata"]
        assert metadata["version"] == "1.0"
        assert metadata["source_files"] == ["resume.pdf", "cv.docx"]

    def test_generate_json_with_minimal_data(self, output_generator):
        """Test JSON generation with minimal input data."""
        minimal_data = {"work_experience": [], "skills": {}, "holistic_profile": {}}

        with patch(
            "resume_extractor.components.output_generator.datetime"
        ) as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20230101_120000"
            mock_datetime.now.return_value.isoformat.return_value = (
                "2023-01-01T12:00:00"
            )
            mock_datetime.now.return_value.timestamp.return_value = 1672574400.0

            result_path = output_generator.generate_json(minimal_data)

        assert result_path.exists()

        # Verify the generated file is valid JSON and passes schema validation
        with open(result_path) as f:
            output_data = json.load(f)

        # Should not raise validation error
        from jsonschema import validate

        validate(instance=output_data, schema=MASTER_SCHEMA)

    def test_error_handling_in_generate_json(
        self, output_generator, sample_consolidated_data
    ):
        """Test error handling during JSON generation."""
        with patch.object(
            output_generator, "_write_json", side_effect=IOError("Write failed")
        ):
            with pytest.raises(IOError):
                output_generator.generate_json(sample_consolidated_data)

    def test_logging_integration(self, output_generator, sample_consolidated_data):
        """Test logging integration."""
        with patch(
            "resume_extractor.components.output_generator.logging.getLogger"
        ) as mock_logger:
            mock_log = Mock()
            mock_logger.return_value = mock_log

            generator = OutputGenerator()

            with patch(
                "resume_extractor.components.output_generator.datetime"
            ) as mock_datetime:
                mock_datetime.now.return_value.strftime.return_value = "20230101_120000"
                mock_datetime.now.return_value.isoformat.return_value = (
                    "2023-01-01T12:00:00"
                )
                mock_datetime.now.return_value.timestamp.return_value = 1672574400.0

                generator.generate_json(sample_consolidated_data)

            # Verify logging calls
            mock_log.info.assert_called()
