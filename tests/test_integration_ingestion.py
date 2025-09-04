"""
Integration tests for ingestion engine with real sample files.
"""

import pytest
from pathlib import Path

from resume_extractor.components.ingestion import IngestionEngine
from resume_extractor.schemas.master_schema import Document


class TestIngestionEngineIntegration:
    """Integration tests using real sample resume files."""

    def test_ingest_english_sample_files(self):
        """Test ingestion of English sample resume files."""
        engine = IngestionEngine()
        sample_dir = Path("tests/sample_resumes/english")

        if not sample_dir.exists():
            pytest.skip("English sample files directory not found")

        documents = engine.ingest_files(sample_dir)

        # Should have 3 English files (txt, json, md)
        assert len(documents) >= 1

        # Check that all documents are processed correctly
        for doc in documents:
            assert isinstance(doc, Document)
            assert doc.content.strip()  # Should have content
            assert doc.language == "en"  # Should detect as English
            assert doc.file_type in [".txt", ".json", ".md"]
            assert doc.metadata is not None
            assert "file_size" in doc.metadata
            assert "modified_time" in doc.metadata

    def test_ingest_french_sample_files(self):
        """Test ingestion of French sample resume files."""
        engine = IngestionEngine()
        sample_dir = Path("tests/sample_resumes/french")

        if not sample_dir.exists():
            pytest.skip("French sample files directory not found")

        documents = engine.ingest_files(sample_dir)

        # Should have 2 French files (txt, yml)
        assert len(documents) >= 1

        # Check that documents are processed correctly
        for doc in documents:
            assert isinstance(doc, Document)
            assert doc.content.strip()
            assert doc.language == "fr"  # Should detect as French
            assert doc.file_type in [".txt", ".yml"]

    def test_ingest_mixed_sample_files(self):
        """Test ingestion of mixed language sample files."""
        engine = IngestionEngine()
        sample_dir = Path("tests/sample_resumes/mixed")

        if not sample_dir.exists():
            pytest.skip("Mixed sample files directory not found")

        documents = engine.ingest_files(sample_dir)

        # Should have 1 bilingual file (json)
        assert len(documents) >= 1

        # Check document processing
        for doc in documents:
            assert isinstance(doc, Document)
            assert doc.content.strip()
            # Language detection might vary for mixed content
            assert doc.language in ["en", "fr"]

    def test_ingest_all_sample_files(self):
        """Test ingestion of all sample resume files recursively."""
        engine = IngestionEngine()
        sample_dir = Path("tests/sample_resumes")

        if not sample_dir.exists():
            pytest.skip("Sample files directory not found")

        documents = engine.ingest_files(sample_dir)

        # Should find files in all subdirectories
        assert len(documents) >= 4  # At least 4 sample files total

        # Verify diversity of file types
        file_types = {doc.file_type for doc in documents}
        assert ".txt" in file_types
        assert ".json" in file_types

        # Verify language detection variety
        languages = {doc.language for doc in documents}
        assert "en" in languages  # Should have English documents
        # May or may not have French depending on detection accuracy

    def test_ingest_specific_file_content(self):
        """Test that specific content is correctly extracted."""
        engine = IngestionEngine()

        # Test English text file
        english_txt = Path("tests/sample_resumes/english/resume_1.txt")
        if english_txt.exists():
            documents = engine.ingest_files(english_txt.parent)

            # Find the text resume
            txt_doc = next(
                (d for d in documents if d.file_path.name == "resume_1.txt"), None
            )
            if txt_doc:
                assert "JOHN DOE" in txt_doc.content
                assert "Software Engineer" in txt_doc.content
                assert "Python" in txt_doc.content
                assert txt_doc.language == "en"

        # Test French text file
        french_txt = Path("tests/sample_resumes/french/cv_1.txt")
        if french_txt.exists():
            documents = engine.ingest_files(french_txt.parent)

            # Find the French CV
            fr_doc = next(
                (d for d in documents if d.file_path.name == "cv_1.txt"), None
            )
            if fr_doc:
                assert "MARIE DUBOIS" in fr_doc.content
                assert "Développeuse" in fr_doc.content
                assert "JavaScript" in fr_doc.content
                assert fr_doc.language == "fr"

    def test_ingest_structured_data_extraction(self):
        """Test extraction from structured data files."""
        engine = IngestionEngine()

        # Test JSON file
        json_file = Path("tests/sample_resumes/english/resume_2.json")
        if json_file.exists():
            documents = engine.ingest_files(json_file.parent)

            json_doc = next(
                (d for d in documents if d.file_path.name == "resume_2.json"), None
            )
            if json_doc:
                assert "Sarah Smith" in json_doc.content
                assert "Full Stack Developer" in json_doc.content
                assert "React" in json_doc.content

        # Test YAML file
        yaml_file = Path("tests/sample_resumes/french/cv_2.yml")
        if yaml_file.exists():
            documents = engine.ingest_files(yaml_file.parent)

            yaml_doc = next(
                (d for d in documents if d.file_path.name == "cv_2.yml"), None
            )
            if yaml_doc:
                assert "Pierre Martin" in yaml_doc.content
                assert "DevOps" in yaml_doc.content
                assert "AWS" in yaml_doc.content

    def test_file_metadata_extraction(self):
        """Test that file metadata is correctly extracted."""
        engine = IngestionEngine()
        sample_dir = Path("tests/sample_resumes/english")

        if not sample_dir.exists():
            pytest.skip("English sample directory not found")

        documents = engine.ingest_files(sample_dir)

        for doc in documents:
            # Check required metadata fields
            assert "file_size" in doc.metadata
            assert "modified_time" in doc.metadata
            assert doc.metadata["file_size"] > 0  # Should have some file size
            assert doc.metadata["modified_time"] > 0  # Should have modification time

    def test_error_handling_with_empty_directory(self, tmp_path):
        """Test behavior with empty directory."""
        engine = IngestionEngine()

        # Create empty directory
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        documents = engine.ingest_files(empty_dir)
        assert len(documents) == 0


if __name__ == "__main__":
    pytest.main([__file__])
