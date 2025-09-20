"""Tests for document generator functionality."""

from unittest.mock import Mock, mock_open, patch

import pytest
from src.core.document_generator import (
    DocumentGenerationError,
    DocumentGenerator,
    DOCXGenerator,
    MemoryEfficientPDFGenerator,
    monitor_memory_usage,
)


class TestMemoryEfficientPDFGenerator:
    """Test PDF generation with memory optimization."""

    @pytest.fixture
    def pdf_generator(self):
        """Create PDF generator instance."""
        return MemoryEfficientPDFGenerator()

    @pytest.mark.asyncio
    async def test_pdf_generation_success(self, pdf_generator):
        """Test successful PDF generation."""
        html_content = (
            "<html><body><h1>Test Document</h1><p>Content here</p></body></html>"
        )
        mock_pdf_content = b"PDF content here"

        # Test both WeasyPrint and ReportLab fallback paths
        with patch("src.core.document_generator.WEASYPRINT_AVAILABLE", True):
            with patch("src.core.document_generator.weasyprint") as mock_weasyprint:
                mock_html = Mock()
                mock_doc = Mock()
                mock_doc.write_pdf.return_value = mock_pdf_content
                mock_html.return_value = mock_doc
                mock_weasyprint.HTML = mock_html

                async with pdf_generator.memory_managed_pdf_conversion(
                    html_content
                ) as pdf_content:
                    assert pdf_content == mock_pdf_content
                    mock_html.assert_called_once()
                    mock_doc.write_pdf.assert_called_once()

    @pytest.mark.asyncio
    async def test_pdf_generation_memory_error_recovery(self, pdf_generator):
        """Test PDF generation recovery from memory error."""
        html_content = "<html><body><h1>Large Document</h1></body></html>"

        with patch("src.core.document_generator.WEASYPRINT_AVAILABLE", True):
            with patch("src.core.document_generator.weasyprint") as mock_weasyprint:
                # Make the HTML constructor raise MemoryError
                mock_weasyprint.HTML.side_effect = MemoryError("Out of memory")

                with patch.object(
                    pdf_generator, "_generate_minimal_pdf"
                ) as mock_minimal:
                    mock_minimal.return_value = b"Minimal PDF content"

                    async with pdf_generator.memory_managed_pdf_conversion(
                        html_content
                    ) as pdf_content:
                        assert pdf_content == b"Minimal PDF content"
                        mock_minimal.assert_called_once_with(html_content)

    @pytest.mark.asyncio
    async def test_pdf_generation_reportlab_fallback(self, pdf_generator):
        """Test PDF generation using ReportLab fallback when WeasyPrint unavailable."""
        html_content = (
            "<html><body><h1>Test Document</h1><p>Content here</p></body></html>"
        )

        with patch("src.core.document_generator.WEASYPRINT_AVAILABLE", False):
            with patch.object(
                pdf_generator, "_generate_reportlab_pdf_from_html"
            ) as mock_reportlab:
                mock_reportlab.return_value = b"ReportLab PDF content"

                async with pdf_generator.memory_managed_pdf_conversion(
                    html_content
                ) as pdf_content:
                    assert pdf_content == b"ReportLab PDF content"
                    mock_reportlab.assert_called_once_with(html_content)

    def test_html_simplification(self, pdf_generator):
        """Test HTML content simplification."""
        complex_html = """
        <!-- This is a comment -->
        <html>
        <head><title>Test</title></head>
        <body>
            <h1>Title</h1>
            <p>     Multiple   spaces   </p>
            <div></div>
        </body>
        </html>
        """

        simplified = pdf_generator._simplify_html_content(complex_html)

        # Comments should be removed
        assert "<!-- This is a comment -->" not in simplified
        # Multiple spaces should be compressed
        assert "Multiple   spaces" not in simplified
        # Empty elements should be removed
        assert "<div></div>" not in simplified


class TestDOCXGenerator:
    """Test DOCX document generation."""

    @pytest.fixture
    def docx_generator(self):
        """Create DOCX generator instance."""
        return DOCXGenerator()

    @pytest.fixture
    def sample_career_data(self):
        """Sample career data for testing."""
        return {
            "candidate_name": "Alice Johnson",
            "email": "alice@example.com",
            "phone": "555-111-2222",
            "location": "Boston, MA",
            "work_experience": [
                {
                    "role_title": "Data Scientist",
                    "company_name": "DataCorp",
                    "start_date": "2020-01-01",
                    "end_date": "Present",
                    "accomplishments": [
                        "Developed ML models improving prediction accuracy by 30%",
                        "Led data science team of 4 analysts",
                    ],
                    "skills_used": ["Python", "TensorFlow", "SQL"],
                }
            ],
            "education": [
                {"degree": "MS in Data Science", "institution": "MIT", "year": "2019"}
            ],
            "skills_inventory": {
                "technical_skills": {
                    "programming": ["Python", "R", "SQL"],
                    "ml_tools": ["TensorFlow", "Scikit-learn", "Pytorch"],
                },
                "soft_skills": ["Analytical Thinking", "Communication"],
            },
            "strategic_metadata": {
                "core_competencies": [
                    "Machine Learning",
                    "Data Analysis",
                    "Team Leadership",
                ],
                "quantified_achievements": ["improved prediction accuracy by 30%"],
            },
        }

    @pytest.mark.asyncio
    async def test_docx_generation_success(self, docx_generator, sample_career_data):
        """Test successful DOCX generation."""
        with patch("docx.Document") as mock_doc_class:
            mock_doc = Mock()
            mock_doc_class.return_value = mock_doc
            mock_doc.sections = []
            mock_doc.core_properties.title = None
            mock_doc.core_properties.author = None
            mock_doc.core_properties.created = None

            # Mock paragraph and run creation
            mock_paragraph = Mock()
            mock_run = Mock()
            mock_paragraph.add_run.return_value = mock_run
            mock_doc.add_paragraph.return_value = mock_paragraph

            # Mock font attributes
            mock_run.font.size = None
            mock_run.bold = False

            with patch("tempfile.NamedTemporaryFile") as mock_temp:
                mock_file = Mock()
                mock_file.read.return_value = b"DOCX content"
                mock_temp.return_value.__enter__.return_value = mock_file

                result = await docx_generator.generate_docx_from_data(
                    sample_career_data
                )

                assert result == b"DOCX content"
                mock_doc.save.assert_called_once()

    def test_header_section_creation(self, docx_generator, sample_career_data):
        """Test header section creation."""
        with patch("docx.Document") as mock_doc_class:
            mock_doc = Mock()
            mock_doc_class.return_value = mock_doc

            mock_paragraph = Mock()
            mock_run = Mock()
            mock_paragraph.add_run.return_value = mock_run
            mock_doc.add_paragraph.return_value = mock_paragraph

            docx_generator._add_header_section(mock_doc, sample_career_data)

            # Should create paragraphs for name and contact info
            assert mock_doc.add_paragraph.call_count >= 2
            mock_paragraph.add_run.assert_called()

    def test_impact_summary_creation(self, docx_generator, sample_career_data):
        """Test impact summary creation."""
        with patch("docx.Document") as mock_doc_class:
            mock_doc = Mock()
            mock_doc_class.return_value = mock_doc

            mock_paragraph = Mock()
            mock_run = Mock()
            mock_paragraph.add_run.return_value = mock_run
            mock_doc.add_paragraph.return_value = mock_paragraph

            docx_generator._add_impact_summary(mock_doc, sample_career_data)

            # Should create summary paragraph
            mock_doc.add_paragraph.assert_called()
            mock_paragraph.add_run.assert_called()

    def test_experience_section_creation(self, docx_generator, sample_career_data):
        """Test experience section creation."""
        with patch("docx.Document") as mock_doc_class:
            mock_doc = Mock()
            mock_doc_class.return_value = mock_doc

            mock_paragraph = Mock()
            mock_run = Mock()
            mock_paragraph.add_run.return_value = mock_run
            mock_doc.add_paragraph.return_value = mock_paragraph

            docx_generator._add_experience_section(mock_doc, sample_career_data)

            # Should create multiple paragraphs for experience
            assert mock_doc.add_paragraph.call_count >= 3  # Header + job entries

    def test_years_experience_calculation(self, docx_generator):
        """Test years of experience calculation."""
        work_experience = [
            {"role_title": "Junior Analyst"},
            {"role_title": "Senior Analyst"},
            {"role_title": "Lead Analyst"},
        ]

        years = docx_generator._calculate_years_experience(work_experience)
        assert years == 6  # 3 positions * 2 years each

        # Test empty experience
        assert docx_generator._calculate_years_experience([]) == 0

        # Test maximum cap
        many_jobs = [{"role_title": f"Job {i}"} for i in range(15)]
        assert docx_generator._calculate_years_experience(many_jobs) == 20

    def test_core_skills_extraction(self, docx_generator):
        """Test core skills extraction."""
        skills_inventory = {
            "technical_skills": {
                "programming": ["Python", "Java"],
                "tools": ["Docker", "Kubernetes"],
            },
            "soft_skills": ["Leadership", "Communication"],
        }

        core_skills = docx_generator._extract_core_skills(skills_inventory)

        assert len(core_skills) <= 8
        assert "Python" in core_skills
        assert "Leadership" in core_skills

    @pytest.mark.asyncio
    async def test_docx_generation_error_handling(
        self, docx_generator, sample_career_data
    ):
        """Test error handling in DOCX generation."""
        with patch("docx.Document", side_effect=Exception("DOCX creation failed")):
            with pytest.raises(DocumentGenerationError):
                await docx_generator.generate_docx_from_data(sample_career_data)


class TestDocumentGenerator:
    """Test high-level document generator interface."""

    @pytest.fixture
    def doc_generator(self):
        """Create document generator instance."""
        return DocumentGenerator()

    @pytest.fixture
    def sample_career_data(self):
        """Sample career data for testing."""
        return {
            "candidate_name": "Bob Wilson",
            "email": "bob@example.com",
            "phone": "555-333-4444",
            "work_experience": [
                {
                    "role_title": "Marketing Manager",
                    "company_name": "MarketingCorp",
                    "accomplishments": [
                        "Increased lead generation by 40%",
                        "Managed $500K marketing budget",
                    ],
                }
            ],
            "skills_inventory": {
                "technical_skills": {"marketing": ["Google Ads", "Analytics", "CRM"]}
            },
        }

    @pytest.mark.asyncio
    async def test_html_document_generation(self, doc_generator, sample_career_data):
        """Test HTML document generation."""
        with patch.object(
            doc_generator.template_engine, "render_resume_template"
        ) as mock_render:
            mock_render.return_value = "<html><body>Resume content</body></html>"

            result = await doc_generator.generate_document(
                template_name="t_shaped_classic",
                career_data=sample_career_data,
                output_format="html",
            )

            assert result["mime_type"] == "text/html"
            assert result["content"] == b"<html><body>Resume content</body></html>"
            assert result["metadata"]["output_format"] == "html"
            assert result["metadata"]["template_name"] == "t_shaped_classic"

    @pytest.mark.asyncio
    async def test_pdf_document_generation(self, doc_generator, sample_career_data):
        """Test PDF document generation."""
        html_content = "<html><body>Resume content</body></html>"
        pdf_content = b"PDF binary content"

        with patch.object(
            doc_generator.template_engine, "render_resume_template"
        ) as mock_render:
            mock_render.return_value = html_content

            with patch.object(
                doc_generator.pdf_generator, "memory_managed_pdf_conversion"
            ) as mock_pdf:
                mock_pdf.return_value.__aenter__.return_value = pdf_content
                mock_pdf.return_value.__aexit__.return_value = None

                result = await doc_generator.generate_document(
                    template_name="t_shaped_modern",
                    career_data=sample_career_data,
                    output_format="pdf",
                )

                assert result["mime_type"] == "application/pdf"
                assert result["content"] == pdf_content
                assert result["metadata"]["output_format"] == "pdf"

    @pytest.mark.asyncio
    async def test_markdown_document_generation(
        self, doc_generator, sample_career_data
    ):
        """Test Markdown document generation."""
        html_content = "<html><body><h1>Resume</h1><p>Content</p></body></html>"

        with patch.object(
            doc_generator.template_engine, "render_resume_template"
        ) as mock_render:
            mock_render.return_value = html_content

            result = await doc_generator.generate_document(
                template_name="t_shaped_minimal",
                career_data=sample_career_data,
                output_format="markdown",
            )

            assert result["mime_type"] == "text/markdown"
            markdown_content = result["content"].decode("utf-8")
            assert "# Resume" in markdown_content
            assert "Content" in markdown_content

    @pytest.mark.asyncio
    async def test_docx_document_generation(self, doc_generator, sample_career_data):
        """Test DOCX document generation."""
        docx_content = b"DOCX binary content"

        with patch.object(
            doc_generator.docx_generator, "generate_docx_from_data"
        ) as mock_docx:
            mock_docx.return_value = docx_content

            result = await doc_generator.generate_document(
                template_name="t_shaped_classic",
                career_data=sample_career_data,
                output_format="docx",
            )

            assert (
                result["mime_type"]
                == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            assert result["content"] == docx_content
            assert result["metadata"]["output_format"] == "docx"

    @pytest.mark.asyncio
    async def test_cover_letter_generation(self, doc_generator, sample_career_data):
        """Test cover letter generation."""
        job_requirements = {
            "role_title": "Senior Marketing Manager",
            "company": "TechStart",
            "required_skills": ["Marketing", "Analytics"],
        }

        with patch.object(
            doc_generator.template_engine, "render_cover_letter_template"
        ) as mock_render:
            mock_render.return_value = "<html><body>Cover letter content</body></html>"

            result = await doc_generator.generate_document(
                template_name="pain_promise",
                career_data=sample_career_data,
                output_format="html",
                job_requirements=job_requirements,
                document_type="cover_letter",
            )

            assert result["metadata"]["document_type"] == "cover_letter"
            mock_render.assert_called_once_with(
                "pain_promise",
                sample_career_data,
                job_requirements,
                None,  # customizations
            )

    @pytest.mark.asyncio
    async def test_unsupported_format_error(self, doc_generator, sample_career_data):
        """Test error handling for unsupported output format."""
        with pytest.raises(DocumentGenerationError):
            await doc_generator.generate_document(
                template_name="test",
                career_data=sample_career_data,
                output_format="unsupported_format",
            )

    @pytest.mark.asyncio
    async def test_unsupported_document_type_error(
        self, doc_generator, sample_career_data
    ):
        """Test error handling for unsupported document type."""
        with pytest.raises(DocumentGenerationError):
            await doc_generator.generate_document(
                template_name="test",
                career_data=sample_career_data,
                output_format="html",
                document_type="unsupported_type",
            )

    def test_html_to_markdown_conversion(self, doc_generator):
        """Test HTML to Markdown conversion."""
        html_content = """
        <html>
        <head><title>Test</title></head>
        <body>
            <h1>Main Title</h1>
            <h2>Section Title</h2>
            <p>This is a paragraph with <strong>bold</strong> and <em>italic</em> text.</p>
            <ul>
                <li>Item 1</li>
                <li>Item 2</li>
            </ul>
        </body>
        </html>
        """

        markdown = doc_generator._html_to_markdown(html_content)

        assert "# Main Title" in markdown
        assert "## Section Title" in markdown
        assert "**bold**" in markdown
        assert "*italic*" in markdown
        assert "- Item 1" in markdown
        assert "- Item 2" in markdown

    @pytest.mark.asyncio
    async def test_output_format_validation(self, doc_generator):
        """Test output format validation."""
        # Mock settings to have specific supported formats
        with patch.object(
            doc_generator.settings, "supported_formats", ["html", "pdf", "docx"]
        ):
            assert await doc_generator.validate_output_format("html") is True
            assert (
                await doc_generator.validate_output_format("PDF") is True
            )  # Case insensitive
            assert await doc_generator.validate_output_format("txt") is False

    @pytest.mark.asyncio
    async def test_template_info_retrieval(self, doc_generator):
        """Test template information retrieval."""
        mock_config = {
            "templates": {
                "t_shaped_classic": {
                    "name": "T-Shaped Classic",
                    "description": "Traditional professional resume",
                    "target_industries": ["Technology", "Finance"],
                }
            }
        }

        with patch("yaml.safe_load", return_value=mock_config):
            with patch("os.path.exists", return_value=True):
                with patch("builtins.open", mock_open(read_data="mock yaml")):
                    template_info = await doc_generator.get_template_info(
                        "t_shaped_classic"
                    )

                    assert template_info is not None
                    assert template_info["name"] == "T-Shaped Classic"
                    assert "Technology" in template_info["target_industries"]

    @pytest.mark.asyncio
    async def test_template_list_retrieval(self, doc_generator):
        """Test available templates list retrieval."""
        mock_config = {
            "templates": {
                "t_shaped_classic": {
                    "name": "T-Shaped Classic",
                    "category": "resume",
                    "description": "Traditional professional resume",
                },
                "pain_promise": {
                    "name": "Pain & Promise",
                    "category": "cover_letter",
                    "description": "Persuasive cover letter format",
                },
            }
        }

        with patch("yaml.safe_load", return_value=mock_config):
            with patch("os.path.exists", return_value=True):
                with patch("builtins.open", mock_open(read_data="mock yaml")):
                    # Get all templates
                    all_templates = await doc_generator.list_available_templates()
                    assert len(all_templates) == 2

                    # Filter by document type
                    resume_templates = await doc_generator.list_available_templates(
                        "resume"
                    )
                    assert len(resume_templates) == 1
                    assert resume_templates[0]["id"] == "t_shaped_classic"

                    cover_letter_templates = (
                        await doc_generator.list_available_templates("cover_letter")
                    )
                    assert len(cover_letter_templates) == 1
                    assert cover_letter_templates[0]["id"] == "pain_promise"

    @pytest.mark.asyncio
    async def test_performance_monitoring(self, doc_generator, sample_career_data):
        """Test performance monitoring and metrics collection."""
        with patch.object(
            doc_generator.template_engine, "render_resume_template"
        ) as mock_render:
            mock_render.return_value = "<html><body>Test content</body></html>"

            result = await doc_generator.generate_document(
                template_name="test",
                career_data=sample_career_data,
                output_format="html",
            )

            # Should have performance metadata
            metadata = result["metadata"]
            assert "generation_time" in metadata
            assert "memory_usage_mb" in metadata
            assert "timestamp" in metadata
            assert isinstance(metadata["generation_time"], float)


@pytest.mark.asyncio
async def test_memory_usage_monitoring():
    """Test memory usage monitoring function."""
    # Mock psutil to return different memory percentages
    with patch("psutil.Process") as mock_process:
        mock_instance = Mock()
        mock_process.return_value = mock_instance

        # Test normal memory usage
        mock_instance.memory_percent.return_value = 50.0
        assert await monitor_memory_usage() is True

        # Test high memory usage (warning threshold)
        mock_instance.memory_percent.return_value = 85.0
        assert await monitor_memory_usage() is True

        # Test critical memory usage
        mock_instance.memory_percent.return_value = 95.0
        assert await monitor_memory_usage() is False


if __name__ == "__main__":
    pytest.main([__file__])
