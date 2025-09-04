"""
Unit tests for the ingestion engine and file handlers.
"""

import pytest
import json
import yaml
from pathlib import Path
from unittest.mock import Mock, patch

from resume_extractor.components.ingestion import (
    IngestionEngine,
    LanguageDetector,
    PDFHandler,
    DOCXHandler,
    MarkdownHandler,
    TextHandler,
    YAMLHandler,
    JSONHandler,
)
from resume_extractor.schemas.master_schema import Document


class TestLanguageDetector:
    """Test language detection functionality."""

    def test_detect_english_text(self):
        detector = LanguageDetector()
        english_text = "This is a resume for a software engineer position with extensive experience in Python development."
        assert detector.detect_language(english_text) == "en"

    def test_detect_french_text(self):
        detector = LanguageDetector()
        french_text = "Voici un curriculum vitae pour un poste d'ingénieur logiciel avec une vaste expérience en développement Python."
        assert detector.detect_language(french_text) == "fr"

    def test_detect_short_text_defaults_to_english(self):
        detector = LanguageDetector()
        short_text = "Hello"
        assert detector.detect_language(short_text) == "en"

    def test_detect_empty_text_defaults_to_english(self):
        detector = LanguageDetector()
        assert detector.detect_language("") == "en"
        assert detector.detect_language(None) == "en"

    @patch("resume_extractor.components.ingestion.detect")
    def test_detect_unsupported_language_defaults_to_english(self, mock_detect):
        mock_detect.return_value = "es"  # Spanish
        detector = LanguageDetector()
        assert detector.detect_language("Hola mundo") == "en"

    @patch("resume_extractor.components.ingestion.detect")
    def test_detect_language_exception_defaults_to_english(self, mock_detect):
        mock_detect.side_effect = Exception("Detection failed")
        detector = LanguageDetector()
        assert detector.detect_language("Some text") == "en"


class TestTextHandler:
    """Test plain text file handler."""

    def test_extract_utf8_text(self, tmp_path):
        text_content = "Software Engineer\nPython Developer\nExperience: 5 years"
        text_file = tmp_path / "resume.txt"
        text_file.write_text(text_content, encoding="utf-8")

        handler = TextHandler()
        result = handler.extract_text(text_file)
        assert result == text_content

    def test_extract_text_with_bom(self, tmp_path):
        text_content = "\ufeffSoftware Engineer\nPython Developer"
        expected = "Software Engineer\nPython Developer"
        text_file = tmp_path / "resume_bom.txt"
        text_file.write_text(text_content, encoding="utf-8")

        handler = TextHandler()
        result = handler.extract_text(text_file)
        assert result == expected

    def test_extract_latin1_text(self, tmp_path):
        text_content = "Développeur Python"
        text_file = tmp_path / "resume_latin1.txt"
        text_file.write_bytes(text_content.encode("latin-1"))

        handler = TextHandler()
        result = handler.extract_text(text_file)
        assert result == text_content

    def test_extract_text_file_not_found(self):
        handler = TextHandler()
        result = handler.extract_text(Path("nonexistent.txt"))
        assert result == ""


class TestYAMLHandler:
    """Test YAML file handler."""

    def test_extract_yaml_simple_structure(self, tmp_path):
        yaml_data = {
            "name": "John Doe",
            "position": "Software Engineer",
            "skills": ["Python", "JavaScript", "React"],
        }
        yaml_file = tmp_path / "resume.yml"
        yaml_file.write_text(yaml.dump(yaml_data))

        handler = YAMLHandler()
        result = handler.extract_text(yaml_file)

        assert "John Doe" in result
        assert "Software Engineer" in result
        assert "Python" in result
        assert "JavaScript" in result

    def test_extract_yaml_nested_structure(self, tmp_path):
        yaml_data = {
            "personal": {"name": "Jane Smith", "email": "jane@example.com"},
            "experience": [
                {"company": "Tech Corp", "role": "Developer"},
                {"company": "Startup Inc", "role": "Lead Engineer"},
            ],
        }
        yaml_file = tmp_path / "complex_resume.yaml"
        yaml_file.write_text(yaml.dump(yaml_data))

        handler = YAMLHandler()
        result = handler.extract_text(yaml_file)

        assert "Jane Smith" in result
        assert "Tech Corp" in result
        assert "Lead Engineer" in result

    def test_extract_yaml_invalid_file(self, tmp_path):
        invalid_yaml = "invalid: yaml: content: ["
        yaml_file = tmp_path / "invalid.yml"
        yaml_file.write_text(invalid_yaml)

        handler = YAMLHandler()
        result = handler.extract_text(yaml_file)
        assert result == ""


class TestJSONHandler:
    """Test JSON file handler."""

    def test_extract_json_simple_structure(self, tmp_path):
        json_data = {
            "name": "Alice Johnson",
            "role": "Data Scientist",
            "skills": ["Python", "Machine Learning", "SQL"],
        }
        json_file = tmp_path / "resume.json"
        json_file.write_text(json.dumps(json_data))

        handler = JSONHandler()
        result = handler.extract_text(json_file)

        assert "Alice Johnson" in result
        assert "Data Scientist" in result
        assert "Machine Learning" in result

    def test_extract_json_nested_structure(self, tmp_path):
        json_data = {
            "personal_info": {
                "name": "Bob Wilson",
                "contact": {"email": "bob@example.com", "phone": "123-456-7890"},
            },
            "work_experience": [
                {"company": "BigTech", "position": "Senior Developer"},
                {"company": "StartupCorp", "position": "Tech Lead"},
            ],
        }
        json_file = tmp_path / "detailed_resume.json"
        json_file.write_text(json.dumps(json_data))

        handler = JSONHandler()
        result = handler.extract_text(json_file)

        assert "Bob Wilson" in result
        assert "BigTech" in result
        assert "Senior Developer" in result
        assert "bob@example.com" in result

    def test_extract_json_invalid_file(self, tmp_path):
        invalid_json = "{'invalid': json content"
        json_file = tmp_path / "invalid.json"
        json_file.write_text(invalid_json)

        handler = JSONHandler()
        result = handler.extract_text(json_file)
        assert result == ""


class TestMarkdownHandler:
    """Test Markdown file handler."""

    def test_extract_markdown_simple(self, tmp_path):
        markdown_content = """# John Developer

## Experience
- Software Engineer at TechCorp
- Python specialist with 3 years experience

### Skills
- Python
- Django
- React
"""
        md_file = tmp_path / "resume.md"
        md_file.write_text(markdown_content)

        handler = MarkdownHandler()
        result = handler.extract_text(md_file)

        assert "John Developer" in result
        assert "Software Engineer" in result
        assert "Python" in result

    def test_extract_markdown_with_tables(self, tmp_path):
        markdown_content = """# Resume

| Company | Role | Duration |
|---------|------|----------|
| TechCorp | Developer | 2020-2023 |
| StartupInc | Lead | 2023-Present |
"""
        md_file = tmp_path / "resume_table.md"
        md_file.write_text(markdown_content)

        handler = MarkdownHandler()
        result = handler.extract_text(md_file)

        assert "TechCorp" in result
        assert "Developer" in result

    def test_extract_markdown_encoding_fallback(self, tmp_path):
        # Test latin-1 fallback
        markdown_content = "# Développeur Python"
        md_file = tmp_path / "resume_latin1.md"
        md_file.write_bytes(markdown_content.encode("latin-1"))

        handler = MarkdownHandler()
        result = handler.extract_text(md_file)

        assert "Développeur" in result


class TestPDFHandler:
    """Test PDF file handler."""

    @patch("resume_extractor.components.ingestion.PdfReader")
    def test_extract_pdf_success(self, mock_pdf_reader):
        # Mock PDF reader
        mock_page1 = Mock()
        mock_page1.extract_text.return_value = "Page 1 content\nSoftware Engineer"
        mock_page2 = Mock()
        mock_page2.extract_text.return_value = "Page 2 content\nPython Developer"

        mock_reader = Mock()
        mock_reader.pages = [mock_page1, mock_page2]
        mock_pdf_reader.return_value = mock_reader

        handler = PDFHandler()
        result = handler.extract_text(Path("test.pdf"))

        expected = "Page 1 content\nSoftware Engineer\nPage 2 content\nPython Developer"
        assert result == expected

    @patch("resume_extractor.components.ingestion.PdfReader")
    def test_extract_pdf_exception(self, mock_pdf_reader):
        mock_pdf_reader.side_effect = Exception("PDF read error")

        handler = PDFHandler()
        result = handler.extract_text(Path("corrupted.pdf"))
        assert result == ""


class TestDOCXHandler:
    """Test DOCX file handler."""

    @patch("resume_extractor.components.ingestion.DocxDocument")
    def test_extract_docx_success(self, mock_docx_document):
        # Mock paragraphs
        mock_para1 = Mock()
        mock_para1.text = "John Doe"
        mock_para2 = Mock()
        mock_para2.text = "Software Engineer"

        # Mock table
        mock_cell1 = Mock()
        mock_cell1.text = "Python"
        mock_cell2 = Mock()
        mock_cell2.text = "5 years"
        mock_row = Mock()
        mock_row.cells = [mock_cell1, mock_cell2]
        mock_table = Mock()
        mock_table.rows = [mock_row]

        mock_doc = Mock()
        mock_doc.paragraphs = [mock_para1, mock_para2]
        mock_doc.tables = [mock_table]
        mock_docx_document.return_value = mock_doc

        handler = DOCXHandler()
        result = handler.extract_text(Path("test.docx"))

        assert "John Doe" in result
        assert "Software Engineer" in result
        assert "Python" in result
        assert "5 years" in result

    @patch("resume_extractor.components.ingestion.DocxDocument")
    def test_extract_docx_exception(self, mock_docx_document):
        mock_docx_document.side_effect = Exception("DOCX read error")

        handler = DOCXHandler()
        result = handler.extract_text(Path("corrupted.docx"))
        assert result == ""


class TestIngestionEngine:
    """Test main ingestion engine."""

    def test_init_creates_handlers(self):
        engine = IngestionEngine()

        assert ".pdf" in engine.file_handlers
        assert ".docx" in engine.file_handlers
        assert ".md" in engine.file_handlers
        assert ".txt" in engine.file_handlers
        assert ".yml" in engine.file_handlers
        assert ".yaml" in engine.file_handlers
        assert ".json" in engine.file_handlers

    def test_ingest_files_directory_not_found(self):
        engine = IngestionEngine()

        with pytest.raises(FileNotFoundError):
            engine.ingest_files(Path("nonexistent_directory"))

    def test_ingest_files_path_not_directory(self, tmp_path):
        # Create a file, not directory
        test_file = tmp_path / "not_a_directory.txt"
        test_file.write_text("test")

        engine = IngestionEngine()

        with pytest.raises(ValueError):
            engine.ingest_files(test_file)

    def test_ingest_files_success(self, tmp_path):
        # Create test files
        (tmp_path / "resume1.txt").write_text(
            "English resume content for a software engineer position"
        )
        (tmp_path / "resume2.json").write_text(
            '{"name": "John Doe", "role": "Developer"}'
        )
        (tmp_path / "resume3.md").write_text(
            "# French Resume\nDéveloppeur Python avec expérience"
        )

        # Create unsupported file (should be ignored)
        (tmp_path / "unsupported.exe").write_text("binary content")

        engine = IngestionEngine()
        documents = engine.ingest_files(tmp_path)

        assert len(documents) == 3

        # Check that all documents are Document instances
        for doc in documents:
            assert isinstance(doc, Document)
            assert doc.content
            assert doc.language in ["en", "fr"]
            assert doc.file_type in [".txt", ".json", ".md"]
            assert doc.metadata

    def test_ingest_files_with_subdirectories(self, tmp_path):
        # Create subdirectory with files
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "nested_resume.txt").write_text("Nested resume content")
        (tmp_path / "root_resume.txt").write_text("Root resume content")

        engine = IngestionEngine()
        documents = engine.ingest_files(tmp_path)

        assert len(documents) == 2
        file_names = [doc.file_path.name for doc in documents]
        assert "nested_resume.txt" in file_names
        assert "root_resume.txt" in file_names

    def test_read_file_unsupported_extension(self, tmp_path):
        unsupported_file = tmp_path / "test.xyz"
        unsupported_file.write_text("content")

        engine = IngestionEngine()
        result = engine._read_file(unsupported_file)
        assert result is None

    def test_read_file_empty_content(self, tmp_path):
        empty_file = tmp_path / "empty.txt"
        empty_file.write_text("")

        engine = IngestionEngine()
        result = engine._read_file(empty_file)
        assert result is None

    @patch("resume_extractor.components.ingestion.LanguageDetector.detect_language")
    def test_read_file_success(self, mock_detect_language, tmp_path):
        mock_detect_language.return_value = "en"

        test_file = tmp_path / "test.txt"
        test_content = "Test resume content"
        test_file.write_text(test_content)

        engine = IngestionEngine()
        result = engine._read_file(test_file)

        assert result is not None
        assert isinstance(result, Document)
        assert result.content == test_content
        assert result.language == "en"
        assert result.file_type == ".txt"
        assert "file_size" in result.metadata
        assert "modified_time" in result.metadata

    def test_ingest_files_handles_file_processing_errors(self, tmp_path):
        # Create a file that will cause an error during processing
        problem_file = tmp_path / "problem.txt"
        problem_file.write_text("content")

        engine = IngestionEngine()

        # Mock the _read_file method to raise an exception
        original_read_file = engine._read_file

        def mock_read_file(file_path):
            if file_path.name == "problem.txt":
                raise Exception("Processing error")
            return original_read_file(file_path)

        engine._read_file = mock_read_file

        # Should handle the error gracefully and return empty list
        documents = engine.ingest_files(tmp_path)
        assert len(documents) == 0


if __name__ == "__main__":
    pytest.main([__file__])
