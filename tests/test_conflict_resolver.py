"""
Unit tests for the ConflictResolverUI module.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

from resume_extractor.ui.conflict_resolver import (
    ConflictResolverUI,
    ResolutionHistory,
    Conflict,
    Variation
)
from resume_extractor.components.consolidation import ConsolidationEngine, ParsedData


class TestResolutionHistory(unittest.TestCase):
    """Test cases for ResolutionHistory class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.history = ResolutionHistory()
    
    def test_add_resolution(self):
        """Test adding resolutions to history."""
        self.history.add_resolution("field1", "value1")
        self.assertEqual(len(self.history.history), 1)
        self.assertEqual(self.history.current_index, 0)
        
        self.history.add_resolution("field2", "value2")
        self.assertEqual(len(self.history.history), 2)
        self.assertEqual(self.history.current_index, 1)
    
    def test_undo(self):
        """Test undo functionality."""
        self.history.add_resolution("field1", "value1")
        self.history.add_resolution("field2", "value2")
        self.history.add_resolution("field3", "value3")
        
        # Test undo
        result = self.history.undo()
        self.assertEqual(result, ("field2", "value2"))
        self.assertEqual(self.history.current_index, 1)
        
        # Test multiple undos
        result = self.history.undo()
        self.assertEqual(result, ("field1", "value1"))
        self.assertEqual(self.history.current_index, 0)
        
        # Test undo at beginning
        result = self.history.undo()
        self.assertIsNone(result)
        self.assertEqual(self.history.current_index, 0)
    
    def test_redo(self):
        """Test redo functionality."""
        self.history.add_resolution("field1", "value1")
        self.history.add_resolution("field2", "value2")
        self.history.add_resolution("field3", "value3")
        
        # Undo twice
        self.history.undo()
        self.history.undo()
        
        # Test redo
        result = self.history.redo()
        self.assertEqual(result, ("field2", "value2"))
        self.assertEqual(self.history.current_index, 1)
        
        # Test redo at end
        result = self.history.redo()
        self.assertEqual(result, ("field3", "value3"))
        self.assertEqual(self.history.current_index, 2)
        
        # Test redo when at end
        result = self.history.redo()
        self.assertIsNone(result)
    
    def test_can_undo_redo(self):
        """Test can_undo and can_redo methods."""
        self.assertFalse(self.history.can_undo())
        self.assertFalse(self.history.can_redo())
        
        self.history.add_resolution("field1", "value1")
        self.assertFalse(self.history.can_undo())
        self.assertFalse(self.history.can_redo())
        
        self.history.add_resolution("field2", "value2")
        self.assertTrue(self.history.can_undo())
        self.assertFalse(self.history.can_redo())
        
        self.history.undo()
        self.assertFalse(self.history.can_undo())
        self.assertTrue(self.history.can_redo())


class TestConflictResolverUI(unittest.TestCase):
    """Test cases for ConflictResolverUI class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.resolver = ConflictResolverUI()
        
    def test_initialization(self):
        """Test ConflictResolverUI initialization."""
        self.assertIsNotNone(self.resolver.console)
        self.assertIsNotNone(self.resolver.resolution_history)
        self.assertFalse(self.resolver.batch_mode)
        self.assertIsNone(self.resolver.default_strategy)
    
    def test_empty_conflicts(self):
        """Test handling empty conflict list."""
        result = self.resolver.resolve_conflicts([])
        self.assertEqual(result, {})
    
    @patch('questionary.select')
    def test_resolve_single_conflict(self, mock_select):
        """Test resolving a single conflict."""
        # Create test conflict
        conflict = Conflict(
            entity_id="test_field",
            field="Test Field",
            variations=[
                Variation(content="Value 1", source_file="file1.txt"),
                Variation(content="Value 2", source_file="file2.txt")
            ]
        )
        
        # Mock user selection
        mock_question = MagicMock()
        mock_question.ask.return_value = "Value 1"
        mock_select.return_value = mock_question
        
        # Resolve conflict
        with patch.object(self.resolver, '_display_conflict_details'):
            with patch.object(self.resolver, '_display_progress'):
                result = self.resolver.resolve_conflicts([conflict])
        
        self.assertEqual(result["test_field"], "Value 1")
    
    def test_has_recent_date(self):
        """Test date detection in content."""
        # Test with recent dates
        self.assertTrue(self.resolver._has_recent_date("Started in 2023"))
        self.assertTrue(self.resolver._has_recent_date("Jan 2024 - Present"))
        self.assertTrue(self.resolver._has_recent_date("December 2022"))
        
        # Test without recent dates
        self.assertFalse(self.resolver._has_recent_date("Started in 2019"))
        self.assertFalse(self.resolver._has_recent_date("No dates here"))
    
    def test_select_default(self):
        """Test smart default selection."""
        variations = [
            Variation(content="Short", source_file="file1.txt"),
            Variation(content="This is a much longer and more detailed description", source_file="file2.txt"),
            Variation(content={"key": "structured"}, source_file="file3.txt")
        ]
        
        default = self.resolver._select_default(variations)
        # Should prefer structured data or longer content
        self.assertIn("Version", default)
    
    def test_get_most_detailed_variation(self):
        """Test getting most detailed variation."""
        variations = [
            Variation(content="Short", source_file="file1.txt"),
            Variation(content="This is much longer", source_file="file2.txt"),
            Variation(content={"key": "value", "another": "data"}, source_file="file3.txt")
        ]
        
        result = self.resolver._get_most_detailed_variation(variations)
        # Should prefer structured data
        self.assertEqual(result, {"key": "value", "another": "data"})
    
    def test_prepare_choices(self):
        """Test choice preparation for questionary."""
        variations = [
            Variation(content="Simple text", source_file="file1.txt"),
            Variation(content=["item1", "item2", "item3"], source_file="file2.txt"),
            Variation(content={"key": "value"}, source_file="file3.txt")
        ]
        
        choices = self.resolver._prepare_choices(variations)
        
        # Check number of choices (variations + custom option)
        self.assertEqual(len(choices), 4)
        
        # Check choice formats
        self.assertIn("Simple text", choices[0]["name"])
        self.assertIn("[List with 3 items]", choices[1]["name"])
        self.assertIn("[Dict with 1 keys]", choices[2]["name"])
        self.assertEqual(choices[3]["value"], "CUSTOM")
    
    @patch('questionary.select')
    @patch('questionary.confirm')
    def test_batch_mode(self, mock_confirm, mock_select):
        """Test batch mode operations."""
        conflicts = [
            Conflict(
                entity_id="field1",
                field="Field 1",
                variations=[
                    Variation(content="A", source_file="file1.txt"),
                    Variation(content="B", source_file="file2.txt")
                ]
            ),
            Conflict(
                entity_id="field2",
                field="Field 2",
                variations=[
                    Variation(content="C", source_file="file1.txt"),
                    Variation(content="D", source_file="file2.txt")
                ]
            )
        ]
        
        # Mock user selecting batch mode
        mock_question = MagicMock()
        mock_question.ask.side_effect = ["BATCH_DETAILED", None]
        mock_select.return_value = mock_question
        mock_confirm.return_value.ask.return_value = False
        
        with patch.object(self.resolver, '_display_conflict_details'):
            with patch.object(self.resolver, '_display_progress'):
                result = self.resolver.resolve_conflicts(conflicts)
        
        # Check that batch mode was activated
        self.assertTrue(self.resolver.batch_mode)
        self.assertEqual(self.resolver.default_strategy, "most_detailed")
    
    def test_legacy_method(self):
        """Test backward compatibility with legacy method."""
        data = {"personal_info": {"name": "John"}}
        conflicts = [
            {
                "type": "name_conflict",
                "field": "personal_info.name",
                "values": ["John Doe", "J. Doe"],
                "sources": ["file1.txt", "file2.txt"]
            }
        ]
        
        with patch.object(self.resolver, 'resolve_conflicts') as mock_resolve:
            mock_resolve.return_value = {"personal_info.name": "John Doe"}
            result = self.resolver.resolve_conflicts_legacy(data, conflicts)
            
            self.assertEqual(result["personal_info"]["name"], "John Doe")


class TestConsolidationEngineIntegration(unittest.TestCase):
    """Test integration between ConsolidationEngine and ConflictResolverUI."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = ConsolidationEngine()
        
    def test_consolidate_with_resolution_no_conflicts(self):
        """Test consolidation when no conflicts exist."""
        parsed_data = [
            ParsedData(
                content={
                    "personal_info": {"name": "John Doe"},
                    "skills": ["Python", "Java"]
                },
                source_file="file1.txt",
                language="en"
            )
        ]
        
        result = self.engine.consolidate_with_resolution(parsed_data)
        
        self.assertEqual(result.conflicts_resolved, 0)
        self.assertEqual(len(result.source_documents), 1)
        self.assertIn("personal_info", result.data)
    
    def test_detect_conflicts(self):
        """Test conflict detection."""
        parsed_data = [
            ParsedData(
                content={
                    "entities": [{"label": "PERSON", "text": "John Doe"}],
                    "work_experience": [
                        {"title": "Senior Developer", "company": "Tech Corp", "dates": "2020-2022"}
                    ]
                },
                source_file="file1.txt",
                language="en"
            ),
            ParsedData(
                content={
                    "entities": [{"label": "PERSON", "text": "J. Doe"}],
                    "work_experience": [
                        {"title": "Lead Developer", "company": "Tech Corp", "dates": "2020-2023"}
                    ]
                },
                source_file="file2.txt",
                language="en"
            )
        ]
        
        conflicts = self.engine._detect_conflicts(parsed_data)
        
        # Should detect name conflict
        name_conflicts = [c for c in conflicts if c.conflict_type == "name_conflict"]
        self.assertEqual(len(name_conflicts), 1)
        
        # Should detect date conflict
        date_conflicts = [c for c in conflicts if c.conflict_type == "date_conflict"]
        self.assertEqual(len(date_conflicts), 1)
    
    def test_auto_resolve_conflicts(self):
        """Test automatic conflict resolution."""
        conflicts = [
            Conflict(
                entity_id="field1",
                field="Field 1",
                variations=[
                    Variation(content="Short", source_file="file1.txt"),
                    Variation(content="Much longer and detailed", source_file="file2.txt")
                ]
            )
        ]
        
        resolutions = self.engine._auto_resolve_conflicts(conflicts)
        
        # Should choose the longer variation
        self.assertEqual(resolutions["field1"], "Much longer and detailed")
    
    def test_apply_resolutions(self):
        """Test applying resolutions to data."""
        parsed_data = [
            ParsedData(
                content={"personal_info": {"name": "John"}},
                source_file="file1.txt",
                language="en"
            )
        ]
        
        resolutions = {"personal_info.name": "John Doe"}
        
        result = self.engine._apply_resolutions(parsed_data, resolutions)
        
        self.assertEqual(result["personal_info"]["name"], "John Doe")


class TestConflictResolverEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions for ConflictResolverUI."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.resolver = ConflictResolverUI()
    
    def test_empty_variation_list(self):
        """Test handling of conflict with no variations."""
        conflict = Conflict(
            entity_id="test",
            field="Test",
            variations=[]
        )
        
        # Should handle empty variations gracefully
        choices = self.resolver._prepare_choices([])
        self.assertEqual(len(choices), 1)  # Only custom option
        self.assertEqual(choices[0]["value"], "CUSTOM")
    
    def test_single_variation(self):
        """Test conflict with only one variation."""
        conflict = Conflict(
            entity_id="test",
            field="Test",
            variations=[
                Variation(content="Only option", source_file="file.txt")
            ]
        )
        
        default = self.resolver._select_default(conflict.variations)
        self.assertEqual(default, "Version 1")
    
    def test_very_long_content(self):
        """Test handling of very long content strings."""
        long_content = "x" * 10000
        variations = [
            Variation(content=long_content, source_file="file1.txt"),
            Variation(content="short", source_file="file2.txt")
        ]
        
        choices = self.resolver._prepare_choices(variations)
        # Should truncate long content in preview
        self.assertIn("...", choices[0]["name"])
        self.assertEqual(len(choices[0]["name"]) < 200, True)
    
    def test_none_content(self):
        """Test handling of None values in content."""
        variations = [
            Variation(content=None, source_file="file1.txt"),
            Variation(content="valid", source_file="file2.txt")
        ]
        
        result = self.resolver._get_most_detailed_variation(variations)
        self.assertEqual(result, "valid")
    
    def test_mixed_data_types(self):
        """Test scoring with mixed data types."""
        variations = [
            Variation(content=42, source_file="file1.txt"),
            Variation(content=3.14, source_file="file2.txt"),
            Variation(content=True, source_file="file3.txt"),
            Variation(content=[1, 2, 3], source_file="file4.txt")
        ]
        
        default = self.resolver._select_default(variations)
        # Should prefer the list
        self.assertEqual(default, "Version 4")
    
    def test_date_patterns(self):
        """Test comprehensive date pattern detection."""
        test_cases = [
            ("2024-01-01", True),
            ("Jan 2023", True),
            ("December 2025", True),
            ("March 2019", True),  # This matches 20[12][0-9]
            ("2018", False),  # Outside our pattern
            ("2026", False),
            ("Not a date", False)
        ]
        
        for content, expected in test_cases:
            result = self.resolver._has_recent_date(content)
            self.assertEqual(
                result, expected,
                f"Failed for content: {content}"
            )
    
    @patch('questionary.text')
    def test_custom_entry_validation(self, mock_text):
        """Test custom entry validation."""
        conflict = Conflict(
            entity_id="test",
            field="test_field",
            variations=[]
        )
        
        # Mock valid input
        mock_question = MagicMock()
        mock_question.ask.return_value = "Valid input"
        mock_text.return_value = mock_question
        
        result = self.resolver._handle_custom_entry(conflict)
        self.assertEqual(result, "Valid input")
    
    def test_batch_mode_persistence(self):
        """Test that batch mode persists across conflicts."""
        self.resolver.batch_mode = True
        self.resolver.default_strategy = "most_detailed"
        
        conflict = Conflict(
            entity_id="test",
            field="Test",
            variations=[
                Variation(content="short", source_file="f1.txt"),
                Variation(content="much longer content", source_file="f2.txt")
            ]
        )
        
        with patch.object(self.resolver, '_display_conflict_details'):
            result = self.resolver._resolve_single_conflict(conflict)
        
        self.assertEqual(result, "much longer content")
        self.assertTrue(self.resolver.batch_mode)
    
    def test_resolution_history_edge_cases(self):
        """Test resolution history with edge cases."""
        history = ResolutionHistory()
        
        # Test adding after undo
        history.add_resolution("field1", "value1")
        history.add_resolution("field2", "value2")
        history.undo()
        history.add_resolution("field3", "value3")
        
        # Should have removed future history
        self.assertEqual(len(history.history), 2)
        self.assertEqual(history.history[1], ("field3", "value3"))
        
        # Test multiple redo at end
        history.redo()  # Should return None
        self.assertIsNone(history.redo())
        self.assertIsNone(history.redo())
    
    def test_apply_resolution_nested_paths(self):
        """Test applying resolutions to deeply nested paths."""
        data = {
            "level1": {
                "level2": {
                    "level3": {}
                }
            }
        }
        
        self.resolver._apply_resolution(
            data,
            "level1.level2.level3.level4",
            "deep_value"
        )
        
        self.assertEqual(
            data["level1"]["level2"]["level3"]["level4"],
            "deep_value"
        )
    
    def test_display_progress_boundaries(self):
        """Test progress display at boundaries."""
        # Capture console output
        import io
        from contextlib import redirect_stdout
        
        f = io.StringIO()
        
        # Test at start
        self.resolver._display_progress(0, 10)
        
        # Test at middle
        self.resolver._display_progress(5, 10)
        
        # Test at end
        self.resolver._display_progress(10, 10)
        
        # Test edge case
        self.resolver._display_progress(1, 1)


class TestConflictResolverDisplayMethods(unittest.TestCase):
    """Test display and UI methods for full coverage."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.resolver = ConflictResolverUI()
    
    def test_display_conflict_details(self):
        """Test Rich table display formatting."""
        conflict = Conflict(
            entity_id="test",
            field="Test Field",
            variations=[
                Variation(content="Short content", source_file="file1.txt"),
                Variation(content="x" * 300, source_file="file2.txt"),  # Long content
                Variation(content={"key": "structured"}, source_file="file3.txt"),
                Variation(content=[1, 2, 3], source_file="file4.txt")
            ]
        )
        
        # This should run without error and format the table
        try:
            self.resolver._display_conflict_details(conflict)
        except Exception as e:
            self.fail(f"_display_conflict_details raised {e}")
    
    def test_display_progress_various_values(self):
        """Test progress display with different values."""
        test_cases = [
            (0, 10),
            (5, 10),
            (10, 10),
            (1, 1),
            (3, 7)
        ]
        
        for current, total in test_cases:
            try:
                self.resolver._display_progress(current, total)
            except Exception as e:
                self.fail(f"_display_progress({current}, {total}) raised {e}")
    
    @patch('questionary.confirm')
    def test_offer_undo_true_false(self, mock_confirm):
        """Test undo offer with both responses."""
        # Test accepting undo
        mock_confirm.return_value.ask.return_value = True
        result = self.resolver._offer_undo()
        self.assertTrue(result)
        
        # Test declining undo
        mock_confirm.return_value.ask.return_value = False
        result = self.resolver._offer_undo()
        self.assertFalse(result)
    
    @patch('questionary.text')
    def test_handle_custom_entry_multiline(self, mock_text):
        """Test custom entry for description fields (multiline)."""
        conflict = Conflict(
            entity_id="test",
            field="job_description",  # Contains 'description' keyword
            variations=[]
        )
        
        # Mock multiline input ending with END
        mock_text.return_value.ask.side_effect = [
            "First line of description",
            "Second line continues here", 
            "END"
        ]
        
        result = self.resolver._handle_custom_entry(conflict)
        expected = "First line of description\nSecond line continues here"
        self.assertEqual(result, expected)
    
    @patch('questionary.text')
    def test_handle_custom_entry_empty_lines(self, mock_text):
        """Test custom entry with empty lines ending input."""
        conflict = Conflict(
            entity_id="test",
            field="summary",  # Contains 'summary' keyword  
            variations=[]
        )
        
        # Mock input with empty lines to trigger double-enter exit
        mock_text.return_value.ask.side_effect = [
            "Some text",
            "",
            ""  # Second empty line should trigger exit
        ]
        
        result = self.resolver._handle_custom_entry(conflict)
        self.assertEqual(result, "Some text")
    
    def test_get_most_recent_variation_no_dates(self):
        """Test fallback to most detailed when no recent dates."""
        variations = [
            Variation(content="Short", source_file="file1.txt"),
            Variation(content="Much longer content here", source_file="file2.txt")
        ]
        
        result = self.resolver._get_most_recent_variation(variations)
        # Should fallback to most detailed
        self.assertEqual(result, "Much longer content here")
    
    def test_get_most_recent_variation_with_dates(self):
        """Test getting variation with recent dates."""
        variations = [
            Variation(content="Old content from 2018", source_file="file1.txt"),
            Variation(content="Recent content from 2024", source_file="file2.txt")
        ]
        
        result = self.resolver._get_most_recent_variation(variations)
        self.assertEqual(result, "Recent content from 2024")
    
    @patch('questionary.select')
    def test_resolve_conflicts_with_batch_options(self, mock_select):
        """Test resolve_conflicts with batch options."""
        conflicts = [
            Conflict(
                entity_id="field1",
                field="Field 1",
                variations=[
                    Variation(content="Short", source_file="f1.txt"),
                    Variation(content="Much longer detailed content", source_file="f2.txt")
                ]
            )
        ]
        
        batch_options = {
            "batch_mode": True,
            "strategy": "most_detailed"
        }
        
        with patch.object(self.resolver, '_display_progress'):
            result = self.resolver.resolve_conflicts(conflicts, batch_options)
        
        self.assertEqual(result["field1"], "Much longer detailed content")
        self.assertTrue(self.resolver.batch_mode)
        self.assertEqual(self.resolver.default_strategy, "most_detailed")
    
    @patch('questionary.select')  
    def test_resolve_conflicts_with_undo_flow(self, mock_select):
        """Test resolve_conflicts with undo functionality."""
        # Add some history first
        self.resolver.resolution_history.add_resolution("prev_field", "prev_value")
        
        conflicts = [
            Conflict(
                entity_id="current_field", 
                field="Current Field",
                variations=[
                    Variation(content="Option A", source_file="f1.txt"),
                    Variation(content="Option B", source_file="f2.txt") 
                ]
            )
        ]
        
        mock_question = MagicMock()
        mock_question.ask.return_value = "Option A"
        mock_select.return_value = mock_question
        
        with patch.object(self.resolver, '_display_progress'):
            with patch.object(self.resolver, '_offer_undo', return_value=False):
                result = self.resolver.resolve_conflicts(conflicts)
        
        self.assertEqual(result["current_field"], "Option A")
    
    @patch('questionary.select')
    def test_resolve_single_conflict_batch_similar(self, mock_select):
        """Test batch similar option in single conflict resolution."""
        conflict = Conflict(
            entity_id="test_field",
            field="Test Field", 
            variations=[
                Variation(content="Value A", source_file="f1.txt"),
                Variation(content="Value B", source_file="f2.txt")
            ]
        )
        
        mock_question = MagicMock()
        mock_question.ask.return_value = "BATCH_SIMILAR"
        mock_select.return_value = mock_question
        
        with patch.object(self.resolver, '_display_conflict_details'):
            result = self.resolver._resolve_single_conflict(conflict)
        
        # Should return first variation and set batch mode
        self.assertEqual(result, "Value A")
        self.assertTrue(self.resolver.batch_mode)
        self.assertEqual(self.resolver.default_strategy, "current")
    
    @patch('questionary.select')
    def test_resolve_single_conflict_most_recent_strategy(self, mock_select):
        """Test batch mode with most_recent strategy."""
        self.resolver.batch_mode = True
        self.resolver.default_strategy = "most_recent"
        
        conflict = Conflict(
            entity_id="test_field",
            field="Test Field",
            variations=[
                Variation(content="Old content 2018", source_file="f1.txt"),
                Variation(content="New content 2024", source_file="f2.txt")
            ]
        )
        
        with patch.object(self.resolver, '_display_conflict_details'):
            result = self.resolver._resolve_single_conflict(conflict)
        
        # Should use most recent strategy
        self.assertEqual(result, "New content 2024")


class TestConsolidationEngineEdgeCases(unittest.TestCase):
    """Test edge cases for ConsolidationEngine."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = ConsolidationEngine()
    
    def test_empty_parsed_data(self):
        """Test consolidation with empty data."""
        result = self.engine.consolidate_with_resolution([])
        
        self.assertEqual(result.data, {})
        self.assertEqual(result.conflicts_resolved, 0)
        self.assertEqual(result.source_documents, [])
    
    def test_single_document_no_conflicts(self):
        """Test with single document (no conflicts possible)."""
        parsed_data = [
            ParsedData(
                content={"test": "data"},
                source_file="single.txt",
                language="en"
            )
        ]
        
        conflicts = self.engine._detect_conflicts(parsed_data)
        self.assertEqual(len(conflicts), 0)
    
    def test_detect_conflicts_missing_fields(self):
        """Test conflict detection with missing fields."""
        parsed_data = [
            ParsedData(
                content={},  # Empty content
                source_file="empty.txt",
                language="en"
            ),
            ParsedData(
                content={"work_experience": []},  # Empty work experience
                source_file="partial.txt",
                language="en"
            )
        ]
        
        # Should handle missing fields gracefully
        conflicts = self.engine._detect_conflicts(parsed_data)
        self.assertIsInstance(conflicts, list)
    
    def test_skill_mapper_missing_file(self):
        """Test SkillMapper with missing skill map file."""
        from resume_extractor.components.consolidation import SkillMapper
        
        mapper = SkillMapper("nonexistent/path.json")
        
        # Should return original skill when map is empty
        result = mapper.normalize_skill("Python")
        self.assertEqual(result, "Python")
    
    def test_consolidate_skills_empty_list(self):
        """Test skill consolidation with empty list."""
        result = self.engine._consolidate_skills([])
        self.assertEqual(result, [])
    
    def test_consolidate_skills_duplicates(self):
        """Test skill consolidation with duplicates."""
        skills = ["Python", "python", "py", "JavaScript", "js"]
        result = self.engine._consolidate_skills(skills)
        
        # Should normalize and deduplicate using skill map
        self.assertIn("Python", result)
        self.assertIn("JavaScript", result)
        # Should have 2 canonical skills after normalization
        self.assertEqual(len(result), 2)
    
    def test_merge_document_comprehensive(self):
        """Test merge document functionality."""
        # Create base consolidated data
        consolidated = {
            "personal_info": {"name": "John Doe", "contact": {}},
            "work_experience": [{"title": "Developer", "company": "TechCorp"}],
            "education": [{"degree": "BS Computer Science"}],
            "skills": ["Python", "Java"],
            "projects": [{"name": "Project A"}],
            "source_documents": ["file1.txt"]
        }
        
        # Create new document data
        new_doc = {
            "entities": [{"label": "PERSON", "text": "J. Doe"}],
            "work_experience": [{"title": "Senior Developer", "company": "TechCorp"}],
            "education": [{"degree": "MS Computer Science"}],
            "skills": ["JavaScript", "React"],
            "projects": [{"name": "Project B"}],
            "source_file": "file2.txt"
        }
        
        conflicts = self.engine._merge_document(consolidated, new_doc, 1)
        
        # Should detect name conflict
        self.assertTrue(any(c["type"] == "name_conflict" for c in conflicts))
        
        # Should merge lists
        self.assertEqual(len(consolidated["work_experience"]), 2)
        self.assertEqual(len(consolidated["education"]), 2)
        self.assertEqual(len(consolidated["skills"]), 4)
        self.assertEqual(len(consolidated["projects"]), 2)
        self.assertEqual(len(consolidated["source_documents"]), 2)
    
    def test_extract_personal_info_no_entities(self):
        """Test personal info extraction with no entities."""
        document_data = {"content": "Some text without entities"}
        result = self.engine._extract_personal_info(document_data)
        self.assertEqual(result["name"], "Unknown")
        self.assertEqual(result["contact"], {})
    
    def test_extract_personal_info_with_person(self):
        """Test personal info extraction with person entity."""
        document_data = {
            "entities": [
                {"label": "PERSON", "text": "Jane Smith"},
                {"label": "ORG", "text": "Company Inc"}
            ]
        }
        result = self.engine._extract_personal_info(document_data)
        self.assertEqual(result["name"], "Jane Smith")
        self.assertEqual(result["contact"], {})
    
    def test_initialize_base_structure(self):
        """Test base structure initialization."""
        base_doc = {
            "entities": [{"label": "PERSON", "text": "Test User"}],
            "work_experience": [{"title": "Engineer"}],
            "education": [{"degree": "Bachelor"}],
            "skills": ["Python"],
            "projects": [{"name": "Test Project"}],
            "source_file": "test.txt"
        }
        
        result = self.engine._initialize_base_structure(base_doc)
        
        # Check structure
        self.assertIn("personal_info", result)
        self.assertIn("work_experience", result)
        self.assertIn("education", result)
        self.assertIn("skills", result)
        self.assertIn("projects", result)
        self.assertIn("source_documents", result)
        
        # Check values
        self.assertEqual(result["personal_info"]["name"], "Test User")
        self.assertEqual(len(result["work_experience"]), 1)
        self.assertEqual(result["source_documents"], ["test.txt"])
    
    def test_consolidate_legacy_with_parsed_data(self):
        """Test legacy consolidate method with ParsedData objects."""
        parsed_data = [
            ParsedData(
                content={
                    "entities": [{"label": "PERSON", "text": "John"}],
                    "work_experience": [{"title": "Dev"}],
                    "skills": ["Python"]
                },
                source_file="file1.txt",
                language="en"
            ),
            ParsedData(
                content={
                    "entities": [{"label": "PERSON", "text": "John"}],
                    "work_experience": [{"title": "Senior Dev"}],
                    "skills": ["Java"]
                },
                source_file="file2.txt", 
                language="en"
            )
        ]
        
        consolidated, conflicts = self.engine.consolidate(parsed_data)
        
        # Should handle ParsedData objects
        self.assertIsInstance(consolidated, dict)
        self.assertIsInstance(conflicts, list)
        self.assertIn("personal_info", consolidated)
        self.assertIn("work_experience", consolidated)
        self.assertEqual(len(consolidated["work_experience"]), 2)


if __name__ == "__main__":
    unittest.main()