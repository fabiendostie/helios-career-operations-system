"""Tests for version control functionality."""

from datetime import datetime

import pytest
from src.core.version_control import VersionController
from src.models.version_control import (
    ChangeLog,
    DiffOperation,
    TextDiff,
    Version,
    VersionHistory,
)


class TestVersionController:
    """Test cases for VersionController."""

    @pytest.fixture
    def controller(self):
        """Create VersionController instance."""
        return VersionController()

    @pytest.fixture
    def sample_session_id(self):
        """Sample session ID for testing."""
        return "test-session-123"

    def test_controller_initialization(self, controller):
        """Test that version controller initializes correctly."""
        assert controller is not None
        assert hasattr(controller, "create_version")
        assert hasattr(controller, "get_version_history")
        assert hasattr(controller, "compare_versions")

    def test_create_initial_version(self, controller, sample_session_id):
        """Test creating the initial version."""
        text = "This is the initial text."

        version = controller.create_version(
            session_id=sample_session_id,
            text=text,
            edit_type="initial",
            comment="Initial version",
        )

        assert isinstance(version, Version)
        assert version.session_id == sample_session_id
        assert version.text == text
        assert version.version_number == 1
        assert version.is_current is True
        assert version.parent_version_id is None
        assert version.comment == "Initial version"

    def test_create_subsequent_version(self, controller, sample_session_id):
        """Test creating subsequent versions."""
        # Create initial version
        initial_text = "This is the initial text."
        version1 = controller.create_version(
            session_id=sample_session_id, text=initial_text, edit_type="initial"
        )

        # Create second version
        edited_text = "This is the edited text."
        version2 = controller.create_version(
            session_id=sample_session_id,
            text=edited_text,
            edit_type="grammar",
            comment="Grammar corrections",
        )

        assert version2.version_number == 2
        assert version2.parent_version_id == version1.version_id
        assert version2.is_current is True
        assert version1.is_current is False  # Should be updated

    def test_get_version_history(self, controller, sample_session_id):
        """Test retrieving version history."""
        # Create multiple versions
        texts = ["Initial text.", "First edit.", "Second edit.", "Final edit."]

        for i, text in enumerate(texts):
            controller.create_version(
                session_id=sample_session_id, text=text, edit_type=f"edit_{i}"
            )

        history = controller.get_version_history(sample_session_id)

        assert isinstance(history, VersionHistory)
        assert history.session_id == sample_session_id
        assert len(history.versions) == 4
        assert history.total_versions == 4
        assert all(v.version_number == i + 1 for i, v in enumerate(history.versions))

    def test_compare_versions(self, controller, sample_session_id):
        """Test comparing two versions."""
        # Create two versions
        text1 = "The quick brown fox jumps over the lazy dog."
        text2 = "The quick red fox jumps over the sleepy dog."

        version1 = controller.create_version(sample_session_id, text1, "initial")
        version2 = controller.create_version(sample_session_id, text2, "edit")

        comparison = controller.compare_versions(
            session_id=sample_session_id,
            version_a_id=version1.version_id,
            version_b_id=version2.version_id,
        )

        assert comparison.version_a_id == version1.version_id
        assert comparison.version_b_id == version2.version_id
        assert len(comparison.diff) > 0
        assert 0 <= comparison.similarity_score <= 1
        assert comparison.modifications > 0

    def test_generate_diff(self, controller):
        """Test diff generation between texts."""
        text1 = "Hello world"
        text2 = "Hello beautiful world"

        diff = controller.generate_diff(text1, text2)

        assert isinstance(diff, list)
        assert len(diff) > 0
        assert all(isinstance(d, TextDiff) for d in diff)

        # Should have an insertion for "beautiful "
        insertions = [d for d in diff if d.operation == DiffOperation.INSERT]
        assert len(insertions) > 0

    def test_diff_operations(self, controller):
        """Test different types of diff operations."""
        text1 = "The quick brown fox"
        text2 = "The fast red fox"

        diff = controller.generate_diff(text1, text2)

        operations = [d.operation for d in diff]

        # Should have different operations
        assert DiffOperation.EQUAL in operations  # "The" and "fox" should be equal
        assert DiffOperation.REPLACE in operations or DiffOperation.DELETE in operations

    def test_version_limit_enforcement(self, controller, sample_session_id):
        """Test that version limit is enforced."""
        # Create more versions than the limit
        max_versions = 5
        controller.max_versions = max_versions

        for i in range(max_versions + 3):
            controller.create_version(
                session_id=sample_session_id, text=f"Version {i} text", edit_type="edit"
            )

        history = controller.get_version_history(sample_session_id)
        assert len(history.versions) <= max_versions

    def test_create_change_log(self, controller, sample_session_id):
        """Test change log creation."""
        text1 = "Original text with errors."
        text2 = "Corrected text without errors."

        version1 = controller.create_version(sample_session_id, text1, "initial")
        version2 = controller.create_version(sample_session_id, text2, "grammar")

        change_log = controller.create_change_log(
            session_id=sample_session_id,
            version_from=version1.version_number,
            version_to=version2.version_number,
            editor_type="grammar_checker",
        )

        assert isinstance(change_log, ChangeLog)
        assert change_log.session_id == sample_session_id
        assert change_log.version_from == 1
        assert change_log.version_to == 2
        assert len(change_log.changes) > 0
        assert change_log.change_count > 0

    def test_get_current_version(self, controller, sample_session_id):
        """Test getting the current version."""
        # Create multiple versions
        for i in range(3):
            controller.create_version(
                session_id=sample_session_id, text=f"Version {i + 1}", edit_type="edit"
            )

        current = controller.get_current_version(sample_session_id)
        assert current.version_number == 3
        assert current.is_current is True

    def test_revert_to_version(self, controller, sample_session_id):
        """Test reverting to a previous version."""
        # Create multiple versions
        texts = ["Version 1", "Version 2", "Version 3"]
        versions = []

        for text in texts:
            version = controller.create_version(sample_session_id, text, "edit")
            versions.append(version)

        # Revert to version 2
        reverted = controller.revert_to_version(
            session_id=sample_session_id,
            target_version_id=versions[1].version_id,
            comment="Reverted to version 2",
        )

        assert reverted.text == "Version 2"
        assert reverted.version_number == 4  # Should be a new version
        assert reverted.parent_version_id == versions[1].version_id

    def test_version_metadata(self, controller, sample_session_id):
        """Test version metadata is properly stored."""
        text = "Test text for metadata"

        version = controller.create_version(
            session_id=sample_session_id,
            text=text,
            edit_type="grammar",
            comment="Test comment",
            author="test_user",
        )

        assert version.word_count == len(text.split())
        assert version.character_count == len(text)
        assert version.edit_type == "grammar"
        assert version.comment == "Test comment"
        assert version.author == "test_user"
        assert isinstance(version.created_at, datetime)

    def test_similarity_calculation(self, controller):
        """Test similarity score calculation."""
        text1 = "The quick brown fox"
        text2 = "The quick brown fox"  # Identical
        text3 = "A slow red cat"  # Very different

        # Identical texts should have similarity of 1.0
        sim1 = controller.calculate_similarity(text1, text2)
        assert sim1 == 1.0

        # Different texts should have lower similarity
        sim2 = controller.calculate_similarity(text1, text3)
        assert 0 <= sim2 < 1.0

    def test_empty_text_handling(self, controller, sample_session_id):
        """Test handling of empty text."""
        with pytest.raises(ValueError, match="Text cannot be empty"):
            controller.create_version(sample_session_id, "", "edit")

    def test_invalid_session_id(self, controller):
        """Test handling of invalid session ID."""
        with pytest.raises(ValueError, match="Session ID cannot be empty"):
            controller.create_version("", "test text", "edit")

    def test_version_history_empty_session(self, controller):
        """Test version history for non-existent session."""
        history = controller.get_version_history("non-existent-session")
        assert history.total_versions == 0
        assert len(history.versions) == 0

    def test_concurrent_version_creation(self, controller, sample_session_id):
        """Test handling of concurrent version creation."""
        # This test simulates race conditions
        import threading

        results = []

        def create_version_worker(worker_id):
            try:
                version = controller.create_version(
                    session_id=sample_session_id,
                    text=f"Worker {worker_id} text",
                    edit_type="concurrent",
                )
                results.append(version)
            except Exception as e:
                results.append(e)

        threads = []
        for i in range(5):
            thread = threading.Thread(target=create_version_worker, args=(i,))
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All should succeed or handle conflicts gracefully
        successful_versions = [r for r in results if isinstance(r, Version)]
        assert len(successful_versions) > 0
