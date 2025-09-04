"""
Tests for the ElicitationUI module.
"""

import pytest
import pickle
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path

from resume_extractor.ui.elicitation import ElicitationUI


@pytest.fixture
def elicitation_ui():
    """Create a clean ElicitationUI instance for testing."""
    return ElicitationUI()


@pytest.fixture
def sample_existing_data():
    """Sample existing data structure for testing."""
    return {
        "work_experience": [
            {"role": "Senior Developer", "company": "TechCorp"},
            {"role": "Junior Analyst", "company": "DataFirm"},
        ],
        "skills": ["Python", "JavaScript", "SQL"],
    }


class TestElicitationUIInit:
    """Test ElicitationUI initialization."""

    def test_init_creates_console(self, elicitation_ui):
        """Test that initialization creates a Rich console."""
        assert hasattr(elicitation_ui, "console")
        assert elicitation_ui.console is not None

    def test_init_creates_elicited_data_structure(self, elicitation_ui):
        """Test that initialization creates proper data structure."""
        expected_keys = {
            "transversal_projects",
            "professional_aspirations",
            "core_motivators",
            "personal_qualities",
        }
        assert set(elicitation_ui.elicited_data.keys()) == expected_keys
        assert isinstance(elicitation_ui.elicited_data["transversal_projects"], list)
        assert isinstance(
            elicitation_ui.elicited_data["professional_aspirations"], dict
        )
        assert isinstance(elicitation_ui.elicited_data["core_motivators"], list)
        assert isinstance(elicitation_ui.elicited_data["personal_qualities"], list)


class TestConductInterview:
    """Test the main interview conduct method."""

    @patch("resume_extractor.ui.elicitation.ElicitationUI._load_progress")
    @patch("resume_extractor.ui.elicitation.ElicitationUI._show_welcome_message")
    @patch("resume_extractor.ui.elicitation.ElicitationUI._elicit_transversal_projects")
    @patch("resume_extractor.ui.elicitation.ElicitationUI._elicit_aspirations")
    @patch("resume_extractor.ui.elicitation.ElicitationUI._elicit_motivators")
    @patch("resume_extractor.ui.elicitation.ElicitationUI._elicit_qualities")
    @patch("resume_extractor.ui.elicitation.ElicitationUI._show_completion_summary")
    @patch("resume_extractor.ui.elicitation.ElicitationUI._cleanup_progress")
    @patch("resume_extractor.ui.elicitation.ElicitationUI._save_progress")
    def test_conduct_interview_full_flow(
        self,
        mock_save,
        mock_cleanup,
        mock_summary,
        mock_qualities,
        mock_motivators,
        mock_aspirations,
        mock_projects,
        mock_welcome,
        mock_load,
        elicitation_ui,
        sample_existing_data,
    ):
        """Test complete interview flow."""
        mock_load.return_value = None

        result = elicitation_ui.conduct_interview(sample_existing_data)

        # Verify all sections were called
        mock_welcome.assert_called_once()
        mock_projects.assert_called_once_with(sample_existing_data)
        mock_aspirations.assert_called_once_with(sample_existing_data)
        mock_motivators.assert_called_once_with(sample_existing_data)
        mock_qualities.assert_called_once_with(sample_existing_data)
        mock_summary.assert_called_once()
        mock_cleanup.assert_called_once()

        # Verify progress saving called for each section
        assert mock_save.call_count == 4

        assert result == elicitation_ui.elicited_data

    @patch("resume_extractor.ui.elicitation.ElicitationUI._load_progress")
    def test_conduct_interview_loads_previous_progress(self, mock_load, elicitation_ui):
        """Test that previous progress is loaded if available."""
        previous_data = {"transversal_projects": [{"name": "Test Project"}]}
        mock_load.return_value = previous_data

        with patch.object(elicitation_ui, "_show_welcome_message"), patch.object(
            elicitation_ui, "_elicit_transversal_projects"
        ), patch.object(elicitation_ui, "_elicit_aspirations"), patch.object(
            elicitation_ui, "_elicit_motivators"
        ), patch.object(
            elicitation_ui, "_elicit_qualities"
        ), patch.object(
            elicitation_ui, "_show_completion_summary"
        ), patch.object(
            elicitation_ui, "_cleanup_progress"
        ), patch.object(
            elicitation_ui, "_save_progress"
        ):

            elicitation_ui.conduct_interview({})

            # Verify previous data was loaded
            assert elicitation_ui.elicited_data["transversal_projects"] == [
                {"name": "Test Project"}
            ]


class TestTransversalProjects:
    """Test transversal projects elicitation."""

    @patch("resume_extractor.ui.elicitation.questionary.confirm")
    @patch("resume_extractor.ui.elicitation.ElicitationUI._get_project_details")
    def test_elicit_transversal_projects_single_project(
        self, mock_get_details, mock_confirm, elicitation_ui
    ):
        """Test adding a single transversal project."""
        project_data = {
            "name": "Open Source Library",
            "description": "Created a Python utility library",
            "skills_demonstrated": ["Python", "Git"],
            "link": "https://github.com/user/project",
        }

        mock_get_details.return_value = project_data
        mock_confirm.return_value.ask.return_value = False  # Don't add more projects

        with patch.object(elicitation_ui.console, "print"):
            elicitation_ui._elicit_transversal_projects({})

        assert len(elicitation_ui.elicited_data["transversal_projects"]) == 1
        assert elicitation_ui.elicited_data["transversal_projects"][0] == project_data

    @patch("resume_extractor.ui.elicitation.questionary.confirm")
    @patch("resume_extractor.ui.elicitation.ElicitationUI._get_project_details")
    def test_elicit_transversal_projects_multiple_projects(
        self, mock_get_details, mock_confirm, elicitation_ui
    ):
        """Test adding multiple transversal projects."""
        projects = [
            {
                "name": "Project 1",
                "description": "Desc 1",
                "skills_demonstrated": [],
                "link": None,
            },
            {
                "name": "Project 2",
                "description": "Desc 2",
                "skills_demonstrated": [],
                "link": None,
            },
        ]

        mock_get_details.side_effect = projects
        mock_confirm.return_value.ask.side_effect = [
            True,
            False,
        ]  # Add one more, then stop

        with patch.object(elicitation_ui.console, "print"):
            elicitation_ui._elicit_transversal_projects({})

        assert len(elicitation_ui.elicited_data["transversal_projects"]) == 2
        assert elicitation_ui.elicited_data["transversal_projects"] == projects


class TestGetProjectDetails:
    """Test project details collection."""

    @patch("resume_extractor.ui.elicitation.questionary.text")
    @patch("resume_extractor.ui.elicitation.ElicitationUI._get_multiline_input")
    def test_get_project_details_complete(
        self, mock_multiline, mock_text, elicitation_ui
    ):
        """Test collecting complete project details."""
        mock_text.return_value.ask.side_effect = [
            "My Awesome Project",  # name
            "Python, React, Docker",  # skills
            "https://github.com/user/project",  # link
        ]
        mock_multiline.return_value = (
            "A comprehensive web application for managing tasks"
        )

        result = elicitation_ui._get_project_details()

        expected = {
            "name": "My Awesome Project",
            "description": "A comprehensive web application for managing tasks",
            "skills_demonstrated": ["Python", "React", "Docker"],
            "link": "https://github.com/user/project",
        }

        assert result == expected

    @patch("resume_extractor.ui.elicitation.questionary.text")
    def test_get_project_details_cancelled(self, mock_text, elicitation_ui):
        """Test cancelling project details collection."""
        mock_text.return_value.ask.return_value = None  # User cancels at name prompt

        result = elicitation_ui._get_project_details()

        assert result is None

    @patch("resume_extractor.ui.elicitation.questionary.text")
    @patch("resume_extractor.ui.elicitation.ElicitationUI._get_multiline_input")
    def test_get_project_details_minimal(
        self, mock_multiline, mock_text, elicitation_ui
    ):
        """Test collecting minimal project details."""
        mock_text.return_value.ask.side_effect = [
            "Simple Project",  # name
            "",  # no skills
            "",  # no link
        ]
        mock_multiline.return_value = "Basic description"

        result = elicitation_ui._get_project_details()

        expected = {
            "name": "Simple Project",
            "description": "Basic description",
            "skills_demonstrated": [],
            "link": None,
        }

        assert result == expected


class TestAspirations:
    """Test professional aspirations elicitation."""

    @patch("resume_extractor.ui.elicitation.ElicitationUI._get_list_input")
    @patch("resume_extractor.ui.elicitation.ElicitationUI._suggest_roles_from_data")
    def test_elicit_aspirations(
        self, mock_suggest, mock_list_input, elicitation_ui, sample_existing_data
    ):
        """Test collecting professional aspirations."""
        mock_suggest.return_value = ["Lead Developer", "Principal Engineer"]
        mock_list_input.side_effect = [
            ["Software Architect", "Tech Lead"],  # target_roles
            ["Technology", "Finance"],  # industries
            ["Go", "Kubernetes"],  # technologies_to_learn
        ]

        with patch.object(elicitation_ui.console, "print"):
            elicitation_ui._elicit_aspirations(sample_existing_data)

        expected = {
            "target_roles": ["Software Architect", "Tech Lead"],
            "industries_of_interest": ["Technology", "Finance"],
            "technologies_to_learn": ["Go", "Kubernetes"],
        }

        assert elicitation_ui.elicited_data["professional_aspirations"] == expected

    def test_suggest_roles_from_data_senior_roles(self, elicitation_ui):
        """Test role suggestion for senior positions."""
        data = {
            "work_experience": [
                {"role": "Senior Software Engineer"},
                {"role": "Senior Data Analyst"},
            ]
        }

        suggestions = elicitation_ui._suggest_roles_from_data(data)

        expected_suggestions = {
            "Lead Software Engineer",
            "Principal Software Engineer",
            "Lead Data Analyst",
            "Principal Data Analyst",
        }

        assert set(suggestions) == expected_suggestions

    def test_suggest_roles_from_data_junior_roles(self, elicitation_ui):
        """Test role suggestion for junior positions."""
        data = {
            "work_experience": [
                {"role": "Junior Developer"},
                {"role": "Junior Designer"},
            ]
        }

        suggestions = elicitation_ui._suggest_roles_from_data(data)

        expected_suggestions = {
            " Developer",
            "Senior Developer",  # Note the space from replace
            " Designer",
            "Senior Designer",
        }

        assert set(suggestions) == expected_suggestions

    def test_suggest_roles_from_data_no_experience(self, elicitation_ui):
        """Test role suggestion with no work experience."""
        data = {"skills": ["Python"]}

        suggestions = elicitation_ui._suggest_roles_from_data(data)

        assert suggestions == []


class TestMotivators:
    """Test core motivators elicitation."""

    @patch("resume_extractor.ui.elicitation.questionary.text")
    def test_elicit_motivators(self, mock_text, elicitation_ui):
        """Test collecting core motivators."""
        responses = [
            "Building products that impact millions",  # Impact
            "Learning new frameworks every quarter",  # Learning
            "",  # Challenge (skipped)
            "Working with diverse, collaborative teams",  # Team
            "",  # Recognition (skipped)
        ]
        mock_text.return_value.ask.side_effect = responses

        with patch.object(elicitation_ui.console, "print"):
            elicitation_ui._elicit_motivators({})

        expected = [
            {
                "category": "Impact",
                "description": "Building products that impact millions",
            },
            {
                "category": "Learning",
                "description": "Learning new frameworks every quarter",
            },
            {
                "category": "Team",
                "description": "Working with diverse, collaborative teams",
            },
        ]

        assert elicitation_ui.elicited_data["core_motivators"] == expected

    @patch("resume_extractor.ui.elicitation.questionary.text")
    def test_elicit_motivators_all_skipped(self, mock_text, elicitation_ui):
        """Test when all motivator prompts are skipped."""
        mock_text.return_value.ask.side_effect = [""] * 5  # Skip all prompts

        with patch.object(elicitation_ui.console, "print"):
            elicitation_ui._elicit_motivators({})

        assert elicitation_ui.elicited_data["core_motivators"] == []


class TestQualities:
    """Test personal qualities elicitation."""

    @patch("resume_extractor.ui.elicitation.questionary.confirm")
    @patch("resume_extractor.ui.elicitation.questionary.checkbox")
    @patch("resume_extractor.ui.elicitation.questionary.text")
    def test_elicit_qualities_standard_only(
        self, mock_text, mock_checkbox, mock_confirm, elicitation_ui
    ):
        """Test collecting standard personal qualities only."""
        mock_checkbox.return_value.ask.return_value = ["Leadership", "Communication"]
        mock_text.return_value.ask.side_effect = [
            "Led a team of 5 developers",
            "Presented to executive leadership",
        ]
        mock_confirm.return_value.ask.return_value = False  # Don't add custom qualities

        with patch.object(elicitation_ui.console, "print"):
            elicitation_ui._elicit_qualities({})

        expected = [
            {"trait": "Leadership", "evidence": "Led a team of 5 developers"},
            {"trait": "Communication", "evidence": "Presented to executive leadership"},
        ]

        assert elicitation_ui.elicited_data["personal_qualities"] == expected

    @patch("resume_extractor.ui.elicitation.ElicitationUI._add_custom_qualities")
    @patch("resume_extractor.ui.elicitation.questionary.confirm")
    @patch("resume_extractor.ui.elicitation.questionary.checkbox")
    @patch("resume_extractor.ui.elicitation.questionary.text")
    def test_elicit_qualities_with_custom(
        self, mock_text, mock_checkbox, mock_confirm, mock_add_custom, elicitation_ui
    ):
        """Test collecting qualities with custom additions."""
        mock_checkbox.return_value.ask.return_value = ["Creativity"]
        mock_text.return_value.ask.return_value = "Designed innovative solutions"
        mock_confirm.return_value.ask.return_value = True  # Add custom qualities

        with patch.object(elicitation_ui.console, "print"):
            elicitation_ui._elicit_qualities({})

        mock_add_custom.assert_called_once()

        expected = [
            {"trait": "Creativity", "evidence": "Designed innovative solutions"}
        ]

        assert elicitation_ui.elicited_data["personal_qualities"] == expected


class TestHelperMethods:
    """Test helper methods."""

    @patch("builtins.input")
    def test_get_multiline_input_simple(self, mock_input, elicitation_ui):
        """Test collecting simple multiline input."""
        mock_input.side_effect = [
            "Line 1",
            "Line 2",
            "",  # First empty line
            "",  # Second empty line (triggers end)
        ]

        with patch.object(elicitation_ui.console, "print"):
            result = elicitation_ui._get_multiline_input("Test prompt:")

        assert result == "Line 1\nLine 2"

    @patch("builtins.input")
    def test_get_multiline_input_with_breaks(self, mock_input, elicitation_ui):
        """Test collecting multiline input with line breaks."""
        mock_input.side_effect = [
            "Paragraph 1",
            "",  # Line break
            "Paragraph 2",
            "",  # First empty line
            "",  # Second empty line (triggers end)
        ]

        with patch.object(elicitation_ui.console, "print"):
            result = elicitation_ui._get_multiline_input("Test prompt:")

        assert result == "Paragraph 1\n\nParagraph 2"

    @patch("resume_extractor.ui.elicitation.questionary.text")
    def test_get_list_input_minimum_items(self, mock_text, elicitation_ui):
        """Test collecting list input with minimum requirements."""
        mock_text.return_value.ask.side_effect = [
            "",  # First empty (should prompt for more)
            "Item 1",
            "Item 2",
            "",  # Final empty (should accept)
        ]

        with patch.object(elicitation_ui.console, "print"):
            result = elicitation_ui._get_list_input("Test:", "Enter item:", min_items=2)

        assert result == ["Item 1", "Item 2"]

    @patch("resume_extractor.ui.elicitation.questionary.text")
    def test_get_list_input_with_suggestions(self, mock_text, elicitation_ui):
        """Test collecting list input with suggestions displayed."""
        mock_text.return_value.ask.side_effect = ["Suggested Item", ""]
        suggestions = ["Suggested Item", "Another Option"]

        with patch.object(elicitation_ui.console, "print") as mock_print:
            result = elicitation_ui._get_list_input(
                "Test:", "Enter item:", suggestions=suggestions
            )

        # Verify suggestions were displayed
        suggestion_calls = [
            call for call in mock_print.call_args_list if "Suggestions:" in str(call)
        ]
        assert len(suggestion_calls) > 0

        assert result == ["Suggested Item"]


class TestProgressSaving:
    """Test progress saving and loading functionality."""

    @patch("pathlib.Path.exists")
    @patch("builtins.open", create=True)
    @patch("pickle.dump")
    def test_save_progress(self, mock_dump, mock_open, mock_exists, elicitation_ui):
        """Test saving progress to file."""
        elicitation_ui.elicited_data = {"test": "data"}

        elicitation_ui._save_progress()

        mock_open.assert_called_once()
        mock_dump.assert_called_once_with({"test": "data"}, mock_open().__enter__())

    @patch("pathlib.Path.exists")
    @patch("resume_extractor.ui.elicitation.questionary.confirm")
    @patch("builtins.open", create=True)
    @patch("pickle.load")
    def test_load_progress_resume(
        self, mock_load, mock_open, mock_confirm, mock_exists, elicitation_ui
    ):
        """Test loading progress when user chooses to resume."""
        mock_exists.return_value = True
        mock_confirm.return_value.ask.return_value = True
        mock_load.return_value = {"loaded": "data"}

        result = elicitation_ui._load_progress()

        assert result == {"loaded": "data"}
        mock_confirm.assert_called_once()
        mock_load.assert_called_once()

    @patch("pathlib.Path.exists")
    @patch("resume_extractor.ui.elicitation.questionary.confirm")
    def test_load_progress_decline(self, mock_confirm, mock_exists, elicitation_ui):
        """Test loading progress when user declines to resume."""
        mock_exists.return_value = True
        mock_confirm.return_value.ask.return_value = False

        result = elicitation_ui._load_progress()

        assert result is None

    @patch("pathlib.Path.exists")
    def test_load_progress_no_file(self, mock_exists, elicitation_ui):
        """Test loading progress when no file exists."""
        mock_exists.return_value = False

        result = elicitation_ui._load_progress()

        assert result is None

    @patch("pathlib.Path.unlink")
    def test_cleanup_progress(self, mock_unlink, elicitation_ui):
        """Test cleaning up progress file."""
        elicitation_ui._cleanup_progress()

        mock_unlink.assert_called_once_with(missing_ok=True)


class TestLegacyCompatibility:
    """Test backward compatibility with legacy interface."""

    @patch("resume_extractor.ui.elicitation.ElicitationUI.conduct_interview")
    def test_gather_additional_info_legacy(self, mock_conduct, elicitation_ui):
        """Test legacy gather_additional_info method."""
        mock_conduct.return_value = {
            "transversal_projects": [],
            "professional_aspirations": {},
            "core_motivators": [],
            "personal_qualities": [],
        }

        input_data = {"work_experience": []}
        result = elicitation_ui.gather_additional_info(input_data)

        mock_conduct.assert_called_once_with(input_data)
        assert "holistic_profile" in result
        assert result["work_experience"] == []  # Original data preserved
