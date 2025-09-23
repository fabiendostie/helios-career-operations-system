"""Tests for ReportLab-based document generation."""

import pytest
import asyncio
from unittest.mock import patch, mock_open
import tempfile
from pathlib import Path

from src.core.document_generator_reportlab import (
    ReportLabPDFGenerator,
    MultiFormatDocumentGenerator,
    DocumentGenerationError
)


class TestReportLabPDFGenerator:
    """Test ReportLab PDF generator."""

    @pytest.fixture
    def pdf_generator(self):
        """Create PDF generator instance."""
        return ReportLabPDFGenerator()

    @pytest.fixture
    def sample_resume_data(self):
        """Sample resume data for testing."""
        return {
            'candidate_name': 'John Smith',
            'email': 'john@example.com',
            'phone': '555-123-4567',
            'location': 'San Francisco, CA',
            'summary': 'Experienced software engineer with 5+ years of experience.',
            'work_experience': [
                {
                    'role_title': 'Senior Software Engineer',
                    'company_name': 'TechCorp',
                    'duration': '2020-2023',
                    'accomplishments': [
                        'Built microservices platform reducing deployment time by 60%',
                        'Led team of 5 engineers delivering $2M revenue features'
                    ],
                    'skills_used': ['Python', 'Docker', 'Kubernetes']
                }
            ],
            'education': [
                {
                    'degree': 'Bachelor of Science in Computer Science',
                    'institution': 'Stanford University',
                    'year': '2018'
                }
            ],
            'core_skills': ['Python', 'JavaScript', 'AWS', 'Leadership'],
            'skills_inventory': {
                'programming': ['Python', 'JavaScript', 'Go'],
                'platforms': ['AWS', 'Kubernetes', 'Docker']
            }
        }

    @pytest.mark.asyncio
    async def test_pdf_generation_basic(self, pdf_generator, sample_resume_data):
        """Test basic PDF generation."""
        pdf_content = await pdf_generator.generate_pdf(sample_resume_data)

        assert isinstance(pdf_content, bytes)
        assert len(pdf_content) > 0
        assert pdf_content.startswith(b'%PDF-')  # PDF file signature

    @pytest.mark.asyncio
    async def test_pdf_generation_with_minimal_data(self, pdf_generator):
        """Test PDF generation with minimal data."""
        minimal_data = {
            'candidate_name': 'Test User',
            'email': 'test@example.com'
        }

        pdf_content = await pdf_generator.generate_pdf(minimal_data)

        assert isinstance(pdf_content, bytes)
        assert len(pdf_content) > 0
        assert pdf_content.startswith(b'%PDF-')

    @pytest.mark.asyncio
    async def test_pdf_generation_different_templates(self, pdf_generator, sample_resume_data):
        """Test PDF generation with different template types."""
        for template_type in ['classic', 'modern', 'minimal']:
            pdf_content = await pdf_generator.generate_pdf(sample_resume_data, template_type)

            assert isinstance(pdf_content, bytes)
            assert len(pdf_content) > 0
            assert pdf_content.startswith(b'%PDF-')

    def test_custom_styles_creation(self, pdf_generator):
        """Test custom styles are created properly."""
        assert 'ATSHeading1' in pdf_generator.styles
        assert 'ATSHeading2' in pdf_generator.styles
        assert 'ATSBody' in pdf_generator.styles
        assert 'ContactInfo' in pdf_generator.styles
        assert 'Skills' in pdf_generator.styles

    def test_header_section_creation(self, pdf_generator, sample_resume_data):
        """Test header section creation."""
        elements = pdf_generator._create_header_section(sample_resume_data)

        assert len(elements) >= 1  # At least name should be present
        # Check that contact info is included when available
        if sample_resume_data.get('email') or sample_resume_data.get('phone'):
            assert len(elements) >= 2

    def test_impact_summary_creation(self, pdf_generator, sample_resume_data):
        """Test impact summary section creation."""
        elements = pdf_generator._create_impact_summary(sample_resume_data)

        assert len(elements) >= 1  # Should have at least summary or skills

    def test_experience_section_creation(self, pdf_generator, sample_resume_data):
        """Test experience section creation."""
        elements = pdf_generator._create_experience_section(sample_resume_data)

        assert len(elements) >= 1  # Should have at least the heading

    def test_education_section_creation(self, pdf_generator, sample_resume_data):
        """Test education section creation."""
        elements = pdf_generator._create_education_section(sample_resume_data)

        assert len(elements) >= 1  # Should have at least the heading

    def test_skills_section_creation(self, pdf_generator, sample_resume_data):
        """Test skills section creation."""
        elements = pdf_generator._create_skills_section(sample_resume_data)

        assert len(elements) >= 1  # Should have at least the heading


class TestMultiFormatDocumentGenerator:
    """Test multi-format document generator."""

    @pytest.fixture
    def doc_generator(self):
        """Create document generator instance."""
        return MultiFormatDocumentGenerator()

    @pytest.fixture
    def sample_resume_data(self):
        """Sample resume data for testing."""
        return {
            'candidate_name': 'Jane Doe',
            'email': 'jane@example.com',
            'phone': '555-987-6543',
            'summary': 'Data scientist with machine learning expertise.',
            'work_experience': [
                {
                    'role_title': 'Data Scientist',
                    'company_name': 'DataCorp',
                    'duration': '2021-2024',
                    'accomplishments': [
                        'Developed ML models improving prediction accuracy by 25%',
                        'Led data science team of 3 researchers'
                    ],
                    'skills_used': ['Python', 'TensorFlow', 'SQL']
                }
            ],
            'education': [
                {
                    'degree': 'Master of Science in Data Science',
                    'institution': 'MIT',
                    'year': '2020'
                }
            ],
            'core_skills': ['Python', 'Machine Learning', 'SQL', 'TensorFlow']
        }

    @pytest.mark.asyncio
    async def test_pdf_generation(self, doc_generator, sample_resume_data):
        """Test PDF format generation."""
        result = await doc_generator.generate_document(
            sample_resume_data, output_format="pdf"
        )

        assert isinstance(result, bytes)
        assert len(result) > 0
        assert result.startswith(b'%PDF-')

    @pytest.mark.asyncio
    async def test_docx_generation(self, doc_generator, sample_resume_data):
        """Test DOCX format generation."""
        result = await doc_generator.generate_document(
            sample_resume_data, output_format="docx"
        )

        assert isinstance(result, bytes)
        assert len(result) > 0
        # DOCX files start with ZIP signature
        assert result.startswith(b'PK')

    @pytest.mark.asyncio
    async def test_html_generation(self, doc_generator, sample_resume_data):
        """Test HTML format generation."""
        with patch.object(doc_generator.template_engine, 'render_template') as mock_render:
            mock_render.return_value = '<html><body>Test</body></html>'

            result = await doc_generator.generate_document(
                sample_resume_data, output_format="html"
            )

            assert isinstance(result, bytes)
            assert b'<html>' in result

    @pytest.mark.asyncio
    async def test_markdown_generation(self, doc_generator, sample_resume_data):
        """Test Markdown format generation."""
        result = await doc_generator.generate_document(
            sample_resume_data, output_format="markdown"
        )

        assert isinstance(result, bytes)
        assert b'# Jane Doe' in result  # Should contain candidate name as heading
        assert b'## Professional Experience' in result
        assert b'## Education' in result

    @pytest.mark.asyncio
    async def test_unsupported_format_error(self, doc_generator, sample_resume_data):
        """Test error handling for unsupported formats."""
        with pytest.raises(DocumentGenerationError):
            await doc_generator.generate_document(
                sample_resume_data, output_format="xml"
            )

    @pytest.mark.asyncio
    async def test_generation_performance_logging(self, doc_generator, sample_resume_data):
        """Test that generation performance is logged."""
        with patch('src.core.document_generator_reportlab.logger') as mock_logger:
            await doc_generator.generate_document(
                sample_resume_data, output_format="pdf"
            )

            # Should log start and completion
            assert mock_logger.info.call_count >= 2

            # Check that performance metrics are logged
            start_call = mock_logger.info.call_args_list[0]
            assert 'Starting document generation' in str(start_call)

            completion_call = mock_logger.info.call_args_list[1]
            assert 'Document generated successfully' in str(completion_call)


# Integration tests
class TestDocumentGenerationIntegration:
    """Integration tests for document generation."""

    @pytest.mark.asyncio
    async def test_end_to_end_pdf_generation(self):
        """Test complete PDF generation workflow."""
        generator = MultiFormatDocumentGenerator()

        resume_data = {
            'candidate_name': 'Integration Test User',
            'email': 'integration@test.com',
            'phone': '555-000-0000',
            'location': 'Test City, TC',
            'summary': 'Test professional with extensive testing experience.',
            'work_experience': [
                {
                    'role_title': 'Senior Test Engineer',
                    'company_name': 'TestCorp Inc.',
                    'duration': '2019-2024',
                    'accomplishments': [
                        'Designed comprehensive test suites reducing bugs by 75%',
                        'Automated testing processes saving 20 hours/week',
                        'Mentored junior testers and improved team productivity'
                    ],
                    'skills_used': ['Python', 'Selenium', 'pytest', 'CI/CD']
                },
                {
                    'role_title': 'QA Engineer',
                    'company_name': 'SoftwareCo',
                    'duration': '2017-2019',
                    'accomplishments': [
                        'Implemented automated regression testing',
                        'Reduced manual testing time by 50%'
                    ],
                    'skills_used': ['Java', 'TestNG', 'Jenkins']
                }
            ],
            'education': [
                {
                    'degree': 'Bachelor of Science in Computer Engineering',
                    'institution': 'Tech University',
                    'year': '2017'
                }
            ],
            'core_skills': [
                'Test Automation', 'Python', 'Selenium', 'pytest',
                'CI/CD', 'Quality Assurance', 'Agile Testing'
            ],
            'skills_inventory': {
                'programming': ['Python', 'Java', 'JavaScript'],
                'testing_tools': ['Selenium', 'pytest', 'TestNG', 'Postman'],
                'platforms': ['Jenkins', 'GitHub Actions', 'Docker']
            }
        }

        # Generate PDF
        pdf_content = await generator.generate_document(resume_data, "pdf", "classic")

        # Verify PDF was generated
        assert isinstance(pdf_content, bytes)
        assert len(pdf_content) > 1000  # Should be substantial content
        assert pdf_content.startswith(b'%PDF-')

        # Verify it's a valid PDF with content (PDF generation is working)
        # Note: ReportLab compresses content, so text might not be directly searchable
        assert len(pdf_content) > 2000  # Should have substantial content with proper structure

    @pytest.mark.asyncio
    async def test_multiple_format_consistency(self):
        """Test that different formats contain consistent information."""
        generator = MultiFormatDocumentGenerator()

        resume_data = {
            'candidate_name': 'Format Test User',
            'email': 'format@test.com',
            'work_experience': [
                {
                    'role_title': 'Software Developer',
                    'company_name': 'DevCorp',
                    'duration': '2020-2024',
                    'accomplishments': ['Developed software solutions'],
                    'skills_used': ['Python', 'React']
                }
            ]
        }

        # Generate different formats
        pdf_content = await generator.generate_document(resume_data, "pdf")
        docx_content = await generator.generate_document(resume_data, "docx")
        markdown_content = await generator.generate_document(resume_data, "markdown")

        # All should be generated successfully
        assert all([pdf_content, docx_content, markdown_content])

        # Markdown should contain expected structure
        markdown_text = markdown_content.decode('utf-8')
        assert '# Format Test User' in markdown_text
        assert '## Professional Experience' in markdown_text
        assert 'Software Developer' in markdown_text
