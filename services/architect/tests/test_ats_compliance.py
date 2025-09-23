"""Tests for ATS compliance validation functionality."""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, Mock, mock_open

from src.validation.ats_compliance import (
    ATSComplianceValidator, ATSVendor, ComplianceLevel,
    ValidationResult, ATSRule, get_ats_validator
)


class TestATSComplianceValidator:
    """Test ATS compliance validation system."""

    @pytest.fixture
    def validator(self):
        """Create ATS validator instance."""
        return ATSComplianceValidator()

    @pytest.fixture
    def sample_pdf_content(self):
        """Sample PDF content for testing."""
        return {
            'file_path': '/test/resume.pdf',
            'file_size': 1024 * 1024,  # 1MB
            'file_extension': '.pdf',
            'raw_text': 'John Smith\nSenior Software Engineer\njohn@example.com | 555-123-4567\n\nPROFESSIONAL EXPERIENCE\n\nSoftware Engineer - TechCorp (2020-Present)\n• Built microservices architecture\n• Led team of 5 engineers\n\nEDUCATION\nBS Computer Science - University (2018)',
            'metadata': {'title': 'John Smith Resume'},
            'page_count': 1,
            'extraction_method': 'pdf'
        }

    @pytest.fixture
    def sample_docx_content(self):
        """Sample DOCX content for testing."""
        return {
            'file_path': '/test/resume.docx',
            'file_size': 512 * 1024,  # 512KB
            'file_extension': '.docx',
            'raw_text': 'Jane Doe\nProduct Manager\njane@example.com | 555-987-6543\n\nEXPERIENCE\nProduct Manager - InnovateCorp (2019-Present)\n• Launched 3 product features\n• Managed team of 8\n\nSKILLS\nProduct Strategy, Analytics, Leadership\n\nEDUCATION\nMBA - Business School (2019)',
            'metadata': {'title': 'Jane Doe Resume', 'author': 'Jane Doe'},
            'fonts_used': ['Arial', 'Calibri'],
            'extraction_method': 'docx'
        }

    def test_validator_initialization(self, validator):
        """Test validator initialization with rules."""
        assert len(validator.rules) > 0

        # Should have different categories of rules
        categories = set(rule.category for rule in validator.rules)
        expected_categories = {'format', 'structure', 'content', 'technical'}
        assert expected_categories.issubset(categories)

        # Should have rules for different severities
        severities = set(rule.severity for rule in validator.rules)
        expected_severities = {'critical', 'high', 'medium', 'low'}
        assert expected_severities.issubset(severities)

    @pytest.mark.asyncio
    async def test_pdf_content_extraction(self, validator):
        """Test PDF content extraction."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)

            # Mock PyPDF2 for PDF extraction
            mock_metadata = {'/Title': 'Test Resume', '/Author': 'Test User'}
            mock_page = Mock()
            mock_page.extract_text.return_value = "Sample PDF text content"
            mock_reader = Mock()
            mock_reader.metadata = mock_metadata
            mock_reader.pages = [mock_page]

            with patch('PyPDF2.PdfReader', return_value=mock_reader):
                content = await validator._extract_pdf_content(tmp_path)

                assert content['extraction_method'] == 'pdf'
                assert content['raw_text'] == "Sample PDF text content"
                assert content['metadata']['title'] == 'Test Resume'
                assert content['page_count'] == 1

        # Cleanup
        try:
            os.unlink(tmp_path)
        except:
            pass

    @pytest.mark.asyncio
    async def test_docx_content_extraction(self, validator):
        """Test DOCX content extraction."""
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)

            # Mock python-docx
            mock_paragraph = Mock()
            mock_paragraph.text = "Sample DOCX paragraph"

            mock_run = Mock()
            mock_run.font.name = "Arial"
            mock_paragraph.runs = [mock_run]

            mock_doc = Mock()
            mock_doc.paragraphs = [mock_paragraph]
            mock_doc.core_properties.title = "Test Document"
            mock_doc.core_properties.author = "Test Author"
            mock_doc.core_properties.created = None

            with patch('docx.Document', return_value=mock_doc):
                content = await validator._extract_docx_content(tmp_path)

                assert content['extraction_method'] == 'docx'
                assert "Sample DOCX paragraph" in content['raw_text']
                assert content['metadata']['title'] == "Test Document"
                assert "Arial" in content['fonts_used']

        # Cleanup
        try:
            os.unlink(tmp_path)
        except:
            pass

    @pytest.mark.asyncio
    async def test_html_content_extraction(self, validator):
        """Test HTML content extraction."""
        html_content = """
        <html>
        <head><title>Resume - John Smith</title></head>
        <body>
            <h1>John Smith</h1>
            <p>Software Engineer</p>
            <style>body { font-family: Arial; }</style>
        </body>
        </html>
        """

        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as tmp_file:
            tmp_file.write(html_content)
            tmp_path = Path(tmp_file.name)

        content = await validator._extract_html_content(tmp_path)

        assert content['extraction_method'] == 'html'
        assert 'John Smith' in content['raw_text']
        assert 'Software Engineer' in content['raw_text']
        assert content['metadata']['title'] == 'Resume - John Smith'
        assert content['has_complex_styling'] is True  # Has style tags

        # Cleanup
        try:
            os.unlink(tmp_path)
        except:
            pass

    @pytest.mark.asyncio
    async def test_pdf_text_extraction_validation(self, validator, sample_pdf_content):
        """Test PDF text extraction validation rule."""
        # Test valid PDF
        is_valid, details = await validator._validate_pdf_text_extraction(
            sample_pdf_content,
            Path('/test/resume.pdf')
        )

        assert is_valid is True
        assert 'extracted_chars' in details
        assert details['extracted_chars'] > 50

        # Test PDF with insufficient text
        insufficient_content = sample_pdf_content.copy()
        insufficient_content['raw_text'] = 'Short'

        is_valid, details = await validator._validate_pdf_text_extraction(
            insufficient_content,
            Path('/test/resume.pdf')
        )

        assert is_valid is False
        assert 'issue' in details
        assert 'Insufficient extractable text' in details['issue']

    @pytest.mark.asyncio
    async def test_file_size_validation(self, validator, sample_pdf_content):
        """Test file size validation rule."""
        # Test acceptable file size (1MB)
        is_valid, details = await validator._validate_file_size(
            sample_pdf_content,
            Path('/test/resume.pdf')
        )

        assert is_valid is True
        assert details['file_size_mb'] == 1.0

        # Test oversized file (5MB)
        oversized_content = sample_pdf_content.copy()
        oversized_content['file_size'] = 5 * 1024 * 1024

        is_valid, details = await validator._validate_file_size(
            oversized_content,
            Path('/test/resume.pdf')
        )

        assert is_valid is False
        assert details['file_size_mb'] == 5.0
        assert 'exceeds ATS processing limits' in details['issue']

    @pytest.mark.asyncio
    async def test_font_compatibility_validation(self, validator, sample_docx_content):
        """Test font compatibility validation rule."""
        # Test ATS-friendly fonts
        is_valid, details = await validator._validate_font_compatibility(
            sample_docx_content,
            Path('/test/resume.docx')
        )

        assert is_valid is True
        assert 'Arial' in details['fonts_used']

        # Test problematic fonts
        problematic_content = sample_docx_content.copy()
        problematic_content['fonts_used'] = ['Comic Sans MS', 'Papyrus']

        is_valid, details = await validator._validate_font_compatibility(
            problematic_content,
            Path('/test/resume.docx')
        )

        assert is_valid is False
        assert 'Comic Sans MS' in details['problematic_fonts']
        assert 'recommended_fonts' in details

    @pytest.mark.asyncio
    async def test_section_headers_validation(self, validator, sample_pdf_content):
        """Test section headers validation rule."""
        # Test content with all required sections
        is_valid, details = await validator._validate_section_headers(
            sample_pdf_content,
            Path('/test/resume.pdf')
        )

        assert is_valid is True
        found_sections = details['found_sections']
        assert found_sections['experience'] is True
        assert found_sections['education'] is True

        # Test content missing sections
        incomplete_content = sample_pdf_content.copy()
        incomplete_content['raw_text'] = 'John Smith\nSoftware Engineer\njohn@example.com'

        is_valid, details = await validator._validate_section_headers(
            incomplete_content,
            Path('/test/resume.pdf')
        )

        assert is_valid is False
        assert 'missing_sections' in details
        assert 'experience' in details['missing_sections']

    @pytest.mark.asyncio
    async def test_contact_info_validation(self, validator, sample_pdf_content):
        """Test contact information validation rule."""
        # Test content with email and phone
        is_valid, details = await validator._validate_contact_info(
            sample_pdf_content,
            Path('/test/resume.pdf')
        )

        assert is_valid is True
        assert details['has_email'] is True
        assert details['has_phone'] is True

        # Test content missing contact info
        no_contact_content = sample_pdf_content.copy()
        no_contact_content['raw_text'] = 'John Smith\nSoftware Engineer\nGreat developer with experience'

        is_valid, details = await validator._validate_contact_info(
            no_contact_content,
            Path('/test/resume.pdf')
        )

        assert is_valid is False
        assert details['has_email'] is False
        assert details['has_phone'] is False
        assert 'No email address found' in details['issues']

    @pytest.mark.asyncio
    async def test_keyword_density_validation(self, validator):
        """Test keyword density validation rule."""
        # Test normal content
        normal_content = {
            'raw_text': 'Software engineer with Python experience developing applications using Python frameworks and Python libraries for enterprise solutions'
        }

        is_valid, details = await validator._validate_keyword_density(
            normal_content,
            Path('/test/resume.pdf')
        )

        # Python appears 4 times out of ~15 words (>20% frequency) - should flag keyword stuffing
        assert is_valid is False
        assert 'stuffed_words' in details

        # Test balanced content
        balanced_content = {
            'raw_text': 'Experienced software engineer with expertise in Python, Java, and JavaScript. Built scalable web applications using modern frameworks and cloud technologies. Led development teams and implemented best practices.'
        }

        is_valid, details = await validator._validate_keyword_density(
            balanced_content,
            Path('/test/resume.pdf')
        )

        assert is_valid is True
        assert 'word_count' in details

    @pytest.mark.asyncio
    async def test_date_formatting_validation(self, validator):
        """Test date formatting validation rule."""
        # Test consistent date formatting
        consistent_content = {
            'raw_text': 'Software Engineer - TechCorp (01/2020 - 12/2023)\nSenior Developer - StartupCo (06/2018 - 12/2019)'
        }

        is_valid, details = await validator._validate_date_formatting(
            consistent_content,
            Path('/test/resume.pdf')
        )

        assert is_valid is True
        assert len(details['date_formats']) <= 2

        # Test inconsistent date formatting
        inconsistent_content = {
            'raw_text': 'Engineer (01/2020 - Dec 2023)\nDeveloper (June 2018 - 2019)\nIntern (6/1/2017 - 8/31/2017)'
        }

        is_valid, details = await validator._validate_date_formatting(
            inconsistent_content,
            Path('/test/resume.pdf')
        )

        assert is_valid is False
        assert 'Inconsistent date formatting' in details['issue']

    @pytest.mark.asyncio
    async def test_character_encoding_validation(self, validator):
        """Test character encoding validation rule."""
        # Test content with acceptable characters
        normal_content = {
            'raw_text': 'John Smith – Software Engineer with "excellent" communication skills'
        }

        is_valid, details = await validator._validate_character_encoding(
            normal_content,
            Path('/test/resume.pdf')
        )

        assert is_valid is True

        # Test content with many problematic characters
        problematic_content = {
            'raw_text': 'Jøhn Smîth — Söftwarë Engínëér with spëcîál characters ñ á é í ó ú ü ç'
        }

        is_valid, details = await validator._validate_character_encoding(
            problematic_content,
            Path('/test/resume.pdf')
        )

        assert is_valid is False
        assert 'problematic_chars' in details
        assert 'non-ASCII characters' in details['issue']

    @pytest.mark.asyncio
    async def test_full_document_validation(self, validator, sample_pdf_content):
        """Test complete document validation workflow."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)
            tmp_path.write_text("dummy content")  # Just for file existence

            # Mock content extraction to return our sample content
            with patch.object(validator, '_extract_document_content', return_value=sample_pdf_content):
                result = await validator.validate_document(
                    tmp_path,
                    target_vendors=[ATSVendor.WORKDAY, ATSVendor.GREENHOUSE],
                    compliance_level=ComplianceLevel.STANDARD
                )

                assert isinstance(result, ValidationResult)
                assert isinstance(result.compliance_score, float)
                assert 0 <= result.compliance_score <= 100
                assert isinstance(result.violations, list)
                assert isinstance(result.recommendations, list)
                assert ATSVendor.WORKDAY in result.ats_vendor_scores
                assert ATSVendor.GREENHOUSE in result.ats_vendor_scores

        # Cleanup
        try:
            os.unlink(tmp_path)
        except:
            pass

    @pytest.mark.asyncio
    async def test_vendor_specific_scoring(self, validator):
        """Test vendor-specific compliance scoring."""
        # Test with no violations
        no_violations = []
        score = validator._calculate_vendor_score(no_violations)
        assert score == 100.0

        # Test with various severity violations
        violations = [
            {'severity': 'critical'},
            {'severity': 'high'},
            {'severity': 'medium'},
            {'severity': 'low'}
        ]

        score = validator._calculate_vendor_score(violations)

        # Should be less than 100 due to penalties
        # critical=25, high=15, medium=10, low=5 = total penalty 55
        expected_score = 100 - 55
        assert score == expected_score

    @pytest.mark.asyncio
    async def test_overall_compliance_scoring(self, validator):
        """Test overall compliance score calculation."""
        violations = [
            {'severity': 'critical'},
            {'severity': 'high'},
            {'severity': 'medium'}
        ]

        score = validator._calculate_overall_score(violations)

        # Should calculate based on different weights than vendor scoring
        # critical=20, high=12, medium=8 = total penalty 40
        expected_score = 100 - 40
        assert score == expected_score

    @pytest.mark.asyncio
    async def test_parsing_confidence_estimation(self, validator, sample_pdf_content):
        """Test ATS parsing confidence estimation."""
        # Test with no violations
        confidence = validator._estimate_parsing_confidence(sample_pdf_content, [])
        assert confidence == 90.0  # Base confidence

        # Test with critical violations
        critical_violations = [
            {'severity': 'critical'},
            {'severity': 'critical'}
        ]

        confidence = validator._estimate_parsing_confidence(sample_pdf_content, critical_violations)
        assert confidence == 50.0  # 90 - (2 * 20)

        # Test with extraction errors
        error_content = sample_pdf_content.copy()
        error_content['extraction_error'] = 'Failed to extract'

        confidence = validator._estimate_parsing_confidence(error_content, [])
        assert confidence == 50.0  # 90 - 40

    @pytest.mark.asyncio
    async def test_recommendations_generation(self, validator):
        """Test recommendation generation based on violations."""
        violations = [
            {'category': 'format', 'severity': 'high'},
            {'category': 'structure', 'severity': 'medium'},
            {'category': 'content', 'severity': 'medium'},
            {'category': 'technical', 'severity': 'low'}
        ]

        recommendations = validator._generate_recommendations(
            violations,
            [ATSVendor.WORKDAY, ATSVendor.GREENHOUSE]
        )

        assert len(recommendations) > 0

        # Should have category-specific recommendations
        rec_text = ' '.join(recommendations)
        assert 'PDF format' in rec_text or 'DOCX' in rec_text  # Format recommendations
        assert 'section headers' in rec_text.lower()  # Structure recommendations
        assert 'keyword' in rec_text.lower()  # Content recommendations
        assert 'fonts' in rec_text.lower()  # Technical recommendations

        # Should have vendor-specific recommendations
        assert 'Workday' in rec_text or 'Greenhouse' in rec_text

    @pytest.mark.asyncio
    async def test_compliance_thresholds(self, validator):
        """Test compliance level thresholds."""
        assert validator._get_compliance_threshold(ComplianceLevel.STRICT) == 95.0
        assert validator._get_compliance_threshold(ComplianceLevel.STANDARD) == 85.0
        assert validator._get_compliance_threshold(ComplianceLevel.BASIC) == 70.0

    @pytest.mark.asyncio
    async def test_unsupported_format_error(self, validator):
        """Test error handling for unsupported document formats."""
        with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)

            result = await validator.validate_document(tmp_path)

            assert result.is_compliant is False
            assert result.compliance_score == 0.0
            assert len(result.violations) > 0
            assert 'extraction_failed' in result.violations[0]['rule_id']

        # Cleanup
        try:
            os.unlink(tmp_path)
        except:
            pass

    @pytest.mark.asyncio
    async def test_rule_vendor_filtering(self, validator, sample_pdf_content):
        """Test that rules are properly filtered by target vendors."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)

            # Mock content extraction
            with patch.object(validator, '_extract_document_content', return_value=sample_pdf_content):
                # Test with specific vendor
                result = await validator.validate_document(
                    tmp_path,
                    target_vendors=[ATSVendor.WORKDAY]
                )

                # Should only run rules applicable to Workday
                workday_applicable_rules = [
                    rule for rule in validator.rules
                    if ATSVendor.WORKDAY in rule.applicable_vendors
                ]

                # The result should reflect only Workday-applicable validations
                assert ATSVendor.WORKDAY in result.ats_vendor_scores

        # Cleanup
        try:
            os.unlink(tmp_path)
        except:
            pass


class TestATSRule:
    """Test ATSRule dataclass functionality."""

    def test_ats_rule_creation(self):
        """Test ATSRule creation and properties."""
        def mock_validator(content, path):
            return True, {}

        rule = ATSRule(
            rule_id="test_rule",
            description="Test rule description",
            category="test",
            severity="medium",
            validator_func=mock_validator,
            applicable_vendors=[ATSVendor.WORKDAY, ATSVendor.GREENHOUSE]
        )

        assert rule.rule_id == "test_rule"
        assert rule.description == "Test rule description"
        assert rule.category == "test"
        assert rule.severity == "medium"
        assert rule.validator_func is mock_validator
        assert len(rule.applicable_vendors) == 2
        assert ATSVendor.WORKDAY in rule.applicable_vendors


class TestValidationResult:
    """Test ValidationResult dataclass functionality."""

    def test_validation_result_creation(self):
        """Test ValidationResult creation and properties."""
        result = ValidationResult(
            is_compliant=True,
            compliance_score=87.5,
            violations=[],
            recommendations=["Use standard fonts"],
            ats_vendor_scores={ATSVendor.WORKDAY: 90.0},
            parsing_confidence=85.0
        )

        assert result.is_compliant is True
        assert result.compliance_score == 87.5
        assert len(result.violations) == 0
        assert "Use standard fonts" in result.recommendations
        assert result.ats_vendor_scores[ATSVendor.WORKDAY] == 90.0
        assert result.parsing_confidence == 85.0


@pytest.mark.asyncio
async def test_get_ats_validator_factory():
    """Test ATS validator factory function."""
    validator = await get_ats_validator()

    assert isinstance(validator, ATSComplianceValidator)
    assert len(validator.rules) > 0


if __name__ == '__main__':
    pytest.main([__file__])
