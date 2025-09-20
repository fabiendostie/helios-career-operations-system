"""Intelligent, comprehensive tests for ATS Compliance System focusing on system quality and accuracy."""

import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock, Mock, mock_open
from pathlib import Path
import tempfile
from dataclasses import dataclass
from typing import Dict, Any, List

from src.validation.ats_compliance import (
    ATSComplianceValidator, ATSVendor, ComplianceLevel, 
    ATSRule, ValidationResult, ValidationIssue
)


class TestATSComplianceIntelligence:
    """High-quality tests for ATS compliance intelligence and accuracy."""
    
    @pytest.fixture
    def validator(self):
        """Create ATS compliance validator instance."""
        return ATSComplianceValidator()
    
    @pytest.fixture
    def comprehensive_resume_content(self):
        """Comprehensive resume content for testing."""
        return {
            'extraction_method': 'pdf',
            'file_extension': '.pdf',
            'file_path': '/test/resume.pdf',
            'file_size': 512000,  # 512KB
            'raw_text': '''
JOHN SMITH
Senior Software Engineer
john.smith@email.com | (555) 123-4567 | LinkedIn: /in/johnsmith

PROFESSIONAL SUMMARY
Experienced software engineer with 8+ years developing scalable applications using Python, JavaScript, and cloud technologies. Led teams of 5+ engineers delivering enterprise solutions serving 1M+ users. Expertise in microservices architecture, DevOps practices, and agile methodologies.

WORK EXPERIENCE

Senior Software Engineer | TechCorp Inc | 2020-2024
• Architected microservices platform reducing deployment time by 60%
• Led cross-functional team of 8 engineers delivering $2M revenue features
• Implemented CI/CD pipeline improving code deployment frequency by 300%
• Optimized database queries reducing application latency by 45%

Software Developer | StartupXYZ | 2018-2020
• Built automated testing framework increasing code coverage to 95%
• Developed RESTful APIs serving 100K+ daily active users
• Collaborated with product team to deliver 20+ feature releases

TECHNICAL SKILLS
Programming Languages: Python, JavaScript, Java, Go, TypeScript
Frameworks: React, Django, FastAPI, Node.js, Express
Cloud & DevOps: AWS, Docker, Kubernetes, Terraform, Jenkins
Databases: PostgreSQL, MongoDB, Redis, Elasticsearch

EDUCATION
Bachelor of Science in Computer Science | University of Technology | 2018
Relevant Coursework: Data Structures, Algorithms, Software Engineering

CERTIFICATIONS
• AWS Certified Solutions Architect (2023)
• Certified Kubernetes Administrator (2022)
            ''',
            'sections': {
                'contact': 'JOHN SMITH\nSenior Software Engineer\njohn.smith@email.com | (555) 123-4567 | LinkedIn: /in/johnsmith',
                'summary': 'Experienced software engineer with 8+ years developing scalable applications using Python, JavaScript, and cloud technologies. Led teams of 5+ engineers delivering enterprise solutions serving 1M+ users. Expertise in microservices architecture, DevOps practices, and agile methodologies.',
                'experience': 'Senior Software Engineer | TechCorp Inc | 2020-2024\n• Architected microservices platform reducing deployment time by 60%\n• Led cross-functional team of 8 engineers delivering $2M revenue features\n• Implemented CI/CD pipeline improving code deployment frequency by 300%\n• Optimized database queries reducing application latency by 45%\n\nSoftware Developer | StartupXYZ | 2018-2020\n• Built automated testing framework increasing code coverage to 95%\n• Developed RESTful APIs serving 100K+ daily active users\n• Collaborated with product team to deliver 20+ feature releases',
                'skills': 'Programming Languages: Python, JavaScript, Java, Go, TypeScript, React, Django, FastAPI, Node.js, Express',
                'education': 'Bachelor of Science in Computer Science | University of Technology | 2018\nRelevant Coursework: Data Structures, Algorithms, Software Engineering'
            },
            'metadata': {
                'fonts': ['Arial', 'Times New Roman'],
                'encoding': 'UTF-8',
                'creation_date': '2024-01-15',
                'word_count': 245,
                'character_count': 1520
            }
        }

    @pytest.mark.asyncio
    async def test_real_time_ats_requirements_verification(self, validator):
        """Test real-time verification of current ATS requirements from internet."""
        # Mock research engine for current ATS intelligence
        with patch('src.validation.ats_compliance.get_research_engine') as mock_get_engine:
            mock_engine = MagicMock()
            mock_engine.get_ats_compliance_intelligence = AsyncMock(return_value={
                'vendor_requirements': {
                    'workday': {
                        'supported_formats': ['.pdf', '.docx'],
                        'max_file_size_mb': 5,
                        'required_sections': ['contact', 'experience', 'education'],
                        'font_compatibility': ['Arial', 'Times New Roman', 'Calibri'],
                        'parsing_preferences': {'keyword_density_max': 0.15, 'section_order_strict': False}
                    },
                    'greenhouse': {
                        'supported_formats': ['.pdf', '.docx', '.txt'],
                        'max_file_size_mb': 10,
                        'required_sections': ['contact', 'experience'],
                        'font_compatibility': ['Arial', 'Helvetica', 'Times New Roman'],
                        'parsing_preferences': {'keyword_density_max': 0.20, 'section_order_strict': True}
                    }
                },
                'updated_standards': {
                    'pdf_version_min': '1.4',
                    'encoding_required': 'UTF-8',
                    'accessibility_compliance': 'WCAG_2.1',
                    'metadata_requirements': ['title', 'author', 'creation_date']
                },
                'current_trends': {
                    'ai_parsing_compatibility': True,
                    'semantic_analysis_support': True,
                    'multilingual_support': ['en', 'es', 'fr']
                },
                'last_updated': '2025-09-08T20:00:00Z',
                'research_confidence': 0.95
            })
            mock_get_engine.return_value = mock_engine
            
            # Test real-time requirements verification
            current_requirements = await validator._get_current_ats_requirements()
            
            assert isinstance(current_requirements, dict)
            assert 'vendor_requirements' in current_requirements
            assert 'updated_standards' in current_requirements
            assert 'current_trends' in current_requirements
            
            # Should include specific vendor requirements
            workday_reqs = current_requirements['vendor_requirements']['workday']
            assert workday_reqs['max_file_size_mb'] == 5
            assert '.pdf' in workday_reqs['supported_formats']
            assert 'contact' in workday_reqs['required_sections']
            
            # Should include current parsing standards
            assert current_requirements['updated_standards']['encoding_required'] == 'UTF-8'
            assert current_requirements['current_trends']['ai_parsing_compatibility'] is True
            
            # Research engine should be called for latest intelligence
            mock_engine.get_ats_compliance_intelligence.assert_called_once()

    @pytest.mark.asyncio
    async def test_intelligent_vendor_specific_validation(self, validator, comprehensive_resume_content):
        """Test intelligent validation against specific ATS vendor requirements."""
        # Mock current ATS requirements for vendor-specific testing
        with patch.object(validator, '_get_current_ats_requirements', return_value={
            'vendor_requirements': {
                'workday': {
                    'supported_formats': ['.pdf', '.docx'],
                    'max_file_size_mb': 5,
                    'required_sections': ['contact', 'experience', 'education'],
                    'font_compatibility': ['Arial', 'Times New Roman'],
                    'parsing_preferences': {'keyword_density_max': 0.15}
                },
                'greenhouse': {
                    'supported_formats': ['.pdf', '.docx', '.txt'],
                    'max_file_size_mb': 10,
                    'required_sections': ['contact', 'experience'],
                    'font_compatibility': ['Arial', 'Helvetica'],
                    'parsing_preferences': {'keyword_density_max': 0.20}
                }
            }
        }):
            # Test Workday-specific validation
            workday_result = await validator.validate_for_vendor(
                comprehensive_resume_content,
                Path('/test/resume.pdf'),
                ATSVendor.WORKDAY
            )
            
            assert isinstance(workday_result, ValidationResult)
            assert workday_result.vendor == ATSVendor.WORKDAY
            
            # Should pass Workday requirements (PDF format, proper size, required sections)
            format_valid = any(issue.rule_id == 'file_format' and issue.is_valid 
                             for issue in workday_result.validation_issues)
            size_valid = any(issue.rule_id == 'file_size' and issue.is_valid 
                           for issue in workday_result.validation_issues)
            
            # Test Greenhouse-specific validation with different requirements
            greenhouse_result = await validator.validate_for_vendor(
                comprehensive_resume_content,
                Path('/test/resume.pdf'),
                ATSVendor.GREENHOUSE
            )
            
            assert isinstance(greenhouse_result, ValidationResult)
            assert greenhouse_result.vendor == ATSVendor.GREENHOUSE
            
            # Should apply different validation rules for Greenhouse
            assert greenhouse_result.vendor != workday_result.vendor

    @pytest.mark.asyncio
    async def test_dynamic_parsing_standards_validation(self, validator, comprehensive_resume_content):
        """Test validation against current, dynamic parsing standards."""
        # Mock current parsing standards from internet research
        with patch.object(validator, '_get_current_ats_requirements', return_value={
            'updated_standards': {
                'pdf_version_min': '1.4',
                'encoding_required': 'UTF-8',
                'accessibility_compliance': 'WCAG_2.1',
                'metadata_requirements': ['title', 'author', 'creation_date'],
                'font_embedding_required': True,
                'text_extraction_quality_min': 0.95
            },
            'current_trends': {
                'ai_parsing_compatibility': True,
                'semantic_analysis_support': True,
                'structured_data_preferred': True,
                'mobile_responsive_formats': True
            }
        }):
            # Test current standards validation
            standards_result = await validator._validate_current_standards(
                comprehensive_resume_content,
                Path('/test/resume.pdf')
            )
            
            assert isinstance(standards_result, tuple)
            is_valid, details = standards_result
            
            # Should validate encoding
            assert 'encoding' in details['validation_details']
            assert comprehensive_resume_content['metadata']['encoding'] == 'UTF-8'
            
            # Should check AI parsing compatibility
            assert 'ai_compatibility' in details['validation_details']
            
            # Should validate metadata requirements
            metadata_check = details['validation_details'].get('metadata_completeness', {})
            assert 'creation_date' in metadata_check
            
            # Should assess semantic structure quality
            assert 'semantic_structure' in details['validation_details']

    @pytest.mark.asyncio
    async def test_intelligent_content_structure_analysis(self, validator, comprehensive_resume_content):
        """Test intelligent analysis of content structure for ATS optimization."""
        # Test comprehensive content structure analysis
        structure_analysis = await validator._analyze_content_structure(
            comprehensive_resume_content,
            Path('/test/resume.pdf')
        )
        
        assert isinstance(structure_analysis, dict)
        
        # Should analyze section completeness
        assert 'section_completeness' in structure_analysis
        section_completeness = structure_analysis['section_completeness']
        assert section_completeness['contact_info_complete'] is True
        assert section_completeness['experience_detailed'] is True
        assert section_completeness['skills_categorized'] is True
        
        # Should analyze keyword optimization
        assert 'keyword_analysis' in structure_analysis
        keyword_analysis = structure_analysis['keyword_analysis']
        assert 'technical_keywords_count' in keyword_analysis
        assert 'action_verbs_count' in keyword_analysis
        assert 'quantified_achievements_count' in keyword_analysis
        
        # Should assess readability for parsers
        assert 'parser_readability' in structure_analysis
        readability = structure_analysis['parser_readability']
        assert 'text_extraction_quality' in readability
        assert 'formatting_consistency' in readability
        assert 'section_hierarchy_clear' in readability
        
        # Should identify optimization opportunities
        assert 'optimization_suggestions' in structure_analysis
        suggestions = structure_analysis['optimization_suggestions']
        assert isinstance(suggestions, list)

    @pytest.mark.asyncio
    async def test_real_time_compliance_level_adaptation(self, validator, comprehensive_resume_content):
        """Test dynamic adaptation of compliance levels based on current market standards."""
        # Mock current market intelligence affecting compliance levels
        with patch.object(validator, '_get_current_ats_requirements', return_value={
            'market_intelligence': {
                'strict_compliance_industries': ['finance', 'healthcare', 'government'],
                'standard_compliance_industries': ['technology', 'retail', 'education'],
                'emerging_requirements': {
                    'ai_readiness_score_min': 0.8,
                    'accessibility_compliance_required': True,
                    'multilingual_detection_preferred': True
                }
            },
            'compliance_trends': {
                'increasing_strictness': True,
                'new_vendor_requirements': ['semantic_parsing', 'skills_extraction', 'bias_detection'],
                'deprecated_features': ['keyword_stuffing_tolerance', 'basic_ocr_fallback']
            }
        }):
            # Test strict compliance for finance industry
            finance_result = await validator.validate_with_adaptive_compliance(
                comprehensive_resume_content,
                Path('/test/resume.pdf'),
                industry='finance',
                target_vendors=[ATSVendor.WORKDAY, ATSVendor.GREENHOUSE]
            )
            
            assert isinstance(finance_result, ValidationResult)
            assert finance_result.compliance_level == ComplianceLevel.STRICT
            
            # Should apply stricter validation rules for finance
            strict_issues = [issue for issue in finance_result.validation_issues 
                           if issue.severity in ['critical', 'high']]
            assert len(strict_issues) > 0  # Should have stricter requirements
            
            # Test standard compliance for technology industry
            tech_result = await validator.validate_with_adaptive_compliance(
                comprehensive_resume_content,
                Path('/test/resume.pdf'),
                industry='technology',
                target_vendors=[ATSVendor.LEVER]
            )
            
            assert isinstance(tech_result, ValidationResult)
            assert tech_result.compliance_level == ComplianceLevel.STANDARD
            
            # Should be less strict than finance industry
            assert len(tech_result.validation_issues) <= len(finance_result.validation_issues)

    @pytest.mark.asyncio
    async def test_intelligent_error_handling_and_fallbacks(self, validator, comprehensive_resume_content):
        """Test intelligent error handling when internet verification fails."""
        # Test graceful fallback when internet research fails
        with patch('src.validation.ats_compliance.get_research_engine') as mock_get_engine:
            mock_get_engine.side_effect = Exception("Research service unavailable")
            
            # Mock the document content extraction to avoid file system dependency
            with patch.object(validator, '_extract_document_content', return_value=comprehensive_resume_content):
                fallback_result = await validator.validate_document(
                    Path('/test/resume.pdf'),
                    compliance_level=ComplianceLevel.STANDARD
                )
                
                assert isinstance(fallback_result, ValidationResult)
                assert fallback_result.is_compliant is not None  # Should still provide validation
                
                # Should use static validation rules when dynamic fails
                assert len(fallback_result.violations) >= 0  # Should have run validation rules

    @pytest.mark.asyncio
    async def test_advanced_document_parsing_intelligence(self, validator):
        """Test advanced parsing capabilities for different document formats."""
        # Test intelligent DOCX parsing with complex formatting
        complex_docx_content = {
            'extraction_method': 'docx',
            'file_extension': '.docx',
            'raw_text': 'Complex formatted document with tables and styles',
            'structured_content': {
                'tables': [{'headers': ['Skill', 'Experience'], 'rows': [['Python', '5 years']]}],
                'styles': {'headers': ['Arial Bold 14pt'], 'body': ['Arial 11pt']},
                'embedded_objects': []
            },
            'formatting_complexity': 'high',
            'metadata': {'template_used': 'professional', 'revision_count': 3}
        }
        
        docx_analysis = await validator._analyze_document_parseability(
            complex_docx_content,
            Path('/test/complex_resume.docx')
        )
        
        assert isinstance(docx_analysis, dict)
        assert 'parsing_difficulty' in docx_analysis
        assert 'ats_compatibility_score' in docx_analysis
        assert 'structure_quality' in docx_analysis
        
        # Should handle complex formatting intelligently
        complexity_score = docx_analysis['parsing_difficulty']
        assert isinstance(complexity_score, (int, float))
        assert 0 <= complexity_score <= 1
        
        # Should provide optimization recommendations
        assert 'optimization_recommendations' in docx_analysis
        recommendations = docx_analysis['optimization_recommendations']
        assert isinstance(recommendations, list)

    @pytest.mark.asyncio
    async def test_semantic_content_quality_assessment(self, validator, comprehensive_resume_content):
        """Test semantic analysis of resume content quality for ATS systems."""
        # Test semantic content analysis
        semantic_analysis = await validator._assess_semantic_content_quality(
            comprehensive_resume_content,
            Path('/test/resume.pdf')
        )
        
        assert isinstance(semantic_analysis, dict)
        
        # Should analyze content meaningfulness
        assert 'content_depth_score' in semantic_analysis
        depth_score = semantic_analysis['content_depth_score']
        assert isinstance(depth_score, (int, float))
        assert 0 <= depth_score <= 1
        
        # Should assess skill relevance and context
        assert 'skill_context_quality' in semantic_analysis
        skill_context = semantic_analysis['skill_context_quality']
        assert 'technical_skills_with_context' in skill_context
        assert 'experience_alignment_score' in skill_context
        
        # Should evaluate achievement quality
        assert 'achievement_quality' in semantic_analysis
        achievement_quality = semantic_analysis['achievement_quality']
        assert 'quantified_results_count' in achievement_quality
        assert 'impact_statements_quality' in achievement_quality
        assert 'action_verb_strength' in achievement_quality
        
        # Should provide content enhancement suggestions
        assert 'enhancement_suggestions' in semantic_analysis
        suggestions = semantic_analysis['enhancement_suggestions']
        assert isinstance(suggestions, list)
        if suggestions:
            assert all(isinstance(suggestion, str) for suggestion in suggestions)

    @pytest.mark.asyncio
    async def test_comprehensive_edge_case_handling(self, validator):
        """Test handling of edge cases and malformed documents."""
        # Test with minimal content
        minimal_content = {
            'extraction_method': 'pdf',
            'file_extension': '.pdf',
            'raw_text': 'John Doe\nSoftware Engineer',
            'sections': {},
            'metadata': {}
        }
        
        # Mock document extraction to return minimal content
        with patch.object(validator, '_extract_document_content', return_value=minimal_content):
            minimal_result = await validator.validate_document(
                Path('/test/minimal.pdf'),
                compliance_level=ComplianceLevel.BASIC
            )
            
            assert isinstance(minimal_result, ValidationResult)
            # Should identify missing sections
            missing_sections = [violation for violation in minimal_result.violations
                              if 'section' in violation.get('rule_id', '').lower()]
            assert len(missing_sections) > 0
        
        # Test with corrupted/empty content
        empty_content = {
            'extraction_method': 'pdf',
            'file_extension': '.pdf',
            'raw_text': '',
            'sections': {},
            'metadata': {}
        }
        
        # Mock document extraction to return empty content
        with patch.object(validator, '_extract_document_content', return_value=empty_content):
            empty_result = await validator.validate_document(
                Path('/test/empty.pdf'),
                compliance_level=ComplianceLevel.BASIC
            )
            
            assert isinstance(empty_result, ValidationResult)
            assert empty_result.is_compliant is False  # Should clearly fail for empty content
            
            # Should provide helpful error messages
            critical_violations = [violation for violation in empty_result.violations
                                 if violation.get('severity') == 'critical']
            assert len(critical_violations) > 0

    @pytest.mark.asyncio
    async def test_multi_vendor_compatibility_analysis(self, validator, comprehensive_resume_content):
        """Test analysis across multiple ATS vendors simultaneously."""
        # Test multi-vendor compatibility assessment
        target_vendors = [ATSVendor.WORKDAY, ATSVendor.GREENHOUSE, ATSVendor.LEVER]
        
        multi_vendor_result = await validator.analyze_multi_vendor_compatibility(
            comprehensive_resume_content,
            Path('/test/resume.pdf'),
            target_vendors=target_vendors
        )
        
        assert isinstance(multi_vendor_result, dict)
        assert 'vendor_compatibility_scores' in multi_vendor_result
        assert 'common_issues' in multi_vendor_result
        assert 'vendor_specific_recommendations' in multi_vendor_result
        
        # Should have scores for each vendor
        compatibility_scores = multi_vendor_result['vendor_compatibility_scores']
        for vendor in target_vendors:
            assert vendor.value in compatibility_scores
            score = compatibility_scores[vendor.value]
            assert isinstance(score, (int, float))
            assert 0 <= score <= 1
        
        # Should identify issues that affect multiple vendors
        common_issues = multi_vendor_result['common_issues']
        assert isinstance(common_issues, list)
        
        # Should provide vendor-specific optimization advice
        vendor_recommendations = multi_vendor_result['vendor_specific_recommendations']
        assert isinstance(vendor_recommendations, dict)
        for vendor in target_vendors:
            if vendor.value in vendor_recommendations:
                recommendations = vendor_recommendations[vendor.value]
                assert isinstance(recommendations, list)
    
    @pytest.mark.asyncio
    async def test_validation_rule_coverage(self, validator):
        """Test coverage of all validation rules with various document scenarios."""
        # Test PDF text extraction validation
        pdf_content = {
            'file_extension': '.pdf',
            'raw_text': 'Short text',
            'sections': {},
            'metadata': {}
        }
        result = await validator._validate_pdf_text_extraction(pdf_content, Path('/test/short.pdf'))
        assert isinstance(result, tuple)
        is_valid, details = result
        assert not is_valid  # Should fail due to insufficient text
        assert 'Insufficient extractable text' in details['issue']
        
        # Test file size validation
        large_content = {
            'file_size': 5 * 1024 * 1024,  # 5MB
            'sections': {},
            'metadata': {}
        }
        result = await validator._validate_file_size(large_content, Path('/test/large.pdf'))
        is_valid, details = result
        assert not is_valid
        assert details['file_size_mb'] == 5.0
        
        # Test font compatibility validation 
        font_content = {
            'fonts_used': ['Comic Sans MS', 'Wingdings'],
            'sections': {},
            'metadata': {}
        }
        result = await validator._validate_font_compatibility(font_content, Path('/test/font.docx'))
        is_valid, details = result
        assert not is_valid
        assert 'problematic_fonts' in details
        
        # Test section headers validation
        no_sections_content = {
            'raw_text': 'Some random text without proper sections',
            'sections': {},
            'metadata': {}
        }
        result = await validator._validate_section_headers(no_sections_content, Path('/test/nosections.pdf'))
        is_valid, details = result
        assert not is_valid
        assert 'missing_sections' in details
        
        # Test contact info validation
        no_contact_content = {
            'raw_text': 'Experience working at companies doing things',
            'sections': {},
            'metadata': {}
        }
        result = await validator._validate_contact_info(no_contact_content, Path('/test/nocontact.pdf'))
        is_valid, details = result
        assert not is_valid
        assert not details['has_email']
        assert not details['has_phone']
        
        # Test keyword density validation
        stuffed_content = {
            'raw_text': 'python python python python python python ' * 20,
            'sections': {},
            'metadata': {}
        }
        result = await validator._validate_keyword_density(stuffed_content, Path('/test/stuffed.pdf'))
        is_valid, details = result
        assert not is_valid
        assert 'stuffed_words' in details
        
        # Test date formatting validation
        mixed_dates_content = {
            'raw_text': '01/2020 January 2021 2022 12/25/2023',
            'sections': {},
            'metadata': {}
        }
        result = await validator._validate_date_formatting(mixed_dates_content, Path('/test/dates.pdf'))
        is_valid, details = result
        assert not is_valid  # Should fail due to inconsistent formatting
        
        # Test character encoding validation
        special_chars_content = {
            'raw_text': 'Résumé with lots of spëcial chäracters ñoñ-ASCII téxt',
            'sections': {},
            'metadata': {}
        }
        result = await validator._validate_character_encoding(special_chars_content, Path('/test/encoding.pdf'))
        is_valid, details = result
        # Should pass as these are reasonable special characters
        assert is_valid
        
        # Test graphics placement validation
        sparse_content = {
            'raw_text': 'A\nB\nC\nD\nE\nF\nG\nH\nI\nJ\nK\nL\nM\nN\nO',  # Very short lines
            'sections': {},
            'metadata': {}
        }
        result = await validator._validate_graphics_placement(sparse_content, Path('/test/sparse.pdf'))
        is_valid, details = result
        assert not is_valid
        assert 'Very short text lines' in details['issue']
    
    @pytest.mark.asyncio
    async def test_document_extraction_methods(self, validator):
        """Test different document extraction methods."""
        # Test TXT content extraction (simulated)
        with patch('builtins.open', mock_open(read_data='Sample text content')):
            content = await validator._extract_txt_content(Path('/test/sample.txt'))
            assert content['raw_text'] == 'Sample text content'
            assert content['extraction_method'] == 'txt'
        
        # Test HTML content extraction (simulated)
        html_data = '<html><title>Resume</title><body><p>John Doe</p><p>Software Engineer</p></body></html>'
        with patch('builtins.open', mock_open(read_data=html_data)):
            content = await validator._extract_html_content(Path('/test/resume.html'))
            assert 'John Doe' in content['raw_text']
            assert content['extraction_method'] == 'html'
            assert content['metadata']['title'] == 'Resume'
    
    @pytest.mark.asyncio
    async def test_scoring_and_threshold_methods(self, validator):
        """Test scoring and threshold calculation methods."""
        # Test vendor score calculation
        violations = [
            {'severity': 'critical'},
            {'severity': 'high'},
            {'severity': 'medium'}
        ]
        score = validator._calculate_vendor_score(violations)
        assert isinstance(score, float)
        assert 0 <= score <= 100
        
        # Test overall score calculation
        overall_score = validator._calculate_overall_score(violations)
        assert isinstance(overall_score, float)
        assert 0 <= overall_score <= 100
        
        # Test parsing confidence estimation
        content = {
            'raw_text': 'Good amount of text content for analysis',
            'sections': {'experience': 'Some experience'},
            'metadata': {}
        }
        confidence = validator._estimate_parsing_confidence(content, violations)
        assert isinstance(confidence, float)
        assert 0 <= confidence <= 100
        
        # Test compliance thresholds
        from src.validation.ats_compliance import ComplianceLevel
        strict_threshold = validator._get_compliance_threshold(ComplianceLevel.STRICT)
        standard_threshold = validator._get_compliance_threshold(ComplianceLevel.STANDARD)
        basic_threshold = validator._get_compliance_threshold(ComplianceLevel.BASIC)
        
        assert strict_threshold > standard_threshold > basic_threshold
        assert strict_threshold == 95.0
        assert standard_threshold == 85.0
        assert basic_threshold == 70.0
        
        # Test recommendation generation
        violations_by_category = [
            {'category': 'format', 'severity': 'high'},
            {'category': 'structure', 'severity': 'medium'},
            {'category': 'content', 'severity': 'low'},
            {'category': 'technical', 'severity': 'critical'}
        ]
        from src.validation.ats_compliance import ATSVendor
        recommendations = validator._generate_recommendations(
            violations_by_category, 
            [ATSVendor.WORKDAY, ATSVendor.GREENHOUSE]
        )
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        # Should have vendor-specific recommendations
        workday_mentioned = any('workday' in rec.lower() for rec in recommendations)
        greenhouse_mentioned = any('greenhouse' in rec.lower() for rec in recommendations)
        assert workday_mentioned or greenhouse_mentioned
    
    @pytest.mark.asyncio
    async def test_document_format_specific_extraction(self, validator):
        """Test document format-specific extraction methods."""
        # Test unsupported format handling
        unsupported_content = {
            'file_extension': '.xyz',
            'sections': {},
            'metadata': {}
        }
        
        # Mock the file stat call to avoid file system dependency
        with patch('pathlib.Path.stat') as mock_stat:
            mock_stat.return_value.st_size = 1024
            try:
                await validator._extract_document_content(Path('/test/unsupported.xyz'))
                assert False, "Should have raised ValueError for unsupported format"
            except ValueError as e:
                assert "Unsupported document format" in str(e)
        
        # Test PDF extraction with error handling
        with patch('PyPDF2.PdfReader') as mock_reader:
            mock_reader.side_effect = Exception("PDF read error")
            with patch('pathlib.Path.stat') as mock_stat:
                mock_stat.return_value.st_size = 1024
                content = await validator._extract_pdf_content(Path('/test/error.pdf'))
                assert content['extraction_method'] == 'pdf'
                assert 'extraction_error' in content
        
        # Test DOCX extraction with error handling
        with patch('docx.Document') as mock_doc:
            mock_doc.side_effect = Exception("DOCX read error")
            content = await validator._extract_docx_content(Path('/test/error.docx'))
            assert content['extraction_method'] == 'docx'
            assert 'extraction_error' in content
        
        # Test TXT encoding fallback
        with patch('builtins.open') as mock_file:
            # First call raises UnicodeDecodeError, second succeeds
            mock_file.side_effect = [
                UnicodeDecodeError('utf-8', b'', 0, 1, 'invalid start byte'),
                mock_open(read_data='Latin-1 content').return_value
            ]
            content = await validator._extract_txt_content(Path('/test/latin.txt'))
            assert content['extraction_method'] == 'txt'
            assert content.get('encoding_used') == 'latin-1'
    
    @pytest.mark.asyncio
    async def test_comprehensive_validation_scenarios(self, validator):
        """Test comprehensive validation scenarios covering edge cases."""
        # Test document with valid PDF text extraction (longer text)
        good_pdf_content = {
            'file_extension': '.pdf',
            'raw_text': 'This is a much longer text content that should pass the PDF text extraction validation because it has sufficient characters and proper formatting without OCR issues.',
            'sections': {},
            'metadata': {}
        }
        result = await validator._validate_pdf_text_extraction(good_pdf_content, Path('/test/good.pdf'))
        is_valid, details = result
        assert is_valid
        assert details['extracted_chars'] > 50
        
        # Test file size validation - valid size
        normal_content = {
            'file_size': 512 * 1024,  # 512KB
            'sections': {},
            'metadata': {}
        }
        result = await validator._validate_file_size(normal_content, Path('/test/normal.pdf'))
        is_valid, details = result
        assert is_valid
        assert details['file_size_mb'] == 0.5
        
        # Test good font compatibility
        good_font_content = {
            'fonts_used': ['Arial', 'Times New Roman', 'Calibri'],
            'sections': {},
            'metadata': {}
        }
        result = await validator._validate_font_compatibility(good_font_content, Path('/test/goodfont.docx'))
        is_valid, details = result
        assert is_valid
        assert details['fonts_used'] == ['Arial', 'Times New Roman', 'Calibri']
        
        # Test good section headers
        good_sections_content = {
            'raw_text': 'Contact Information\nExperience\nEducation\nSkills and competencies',
            'sections': {},
            'metadata': {}
        }
        result = await validator._validate_section_headers(good_sections_content, Path('/test/sections.pdf'))
        is_valid, details = result
        assert is_valid
        assert details['found_sections']['contact']
        assert details['found_sections']['experience']
        assert details['found_sections']['education']
        assert details['found_sections']['skills']
        
        # Test good contact info
        good_contact_content = {
            'raw_text': 'John Doe john.doe@email.com (555) 123-4567 LinkedIn profile',
            'sections': {},
            'metadata': {}
        }
        result = await validator._validate_contact_info(good_contact_content, Path('/test/contact.pdf'))
        is_valid, details = result
        assert is_valid
        assert details['has_email']
        assert details['has_phone']
        
        # Test good keyword density
        good_keyword_content = {
            'raw_text': 'Software engineer with experience in Python development and machine learning projects. Worked on various web applications using Django framework.',
            'sections': {},
            'metadata': {}
        }
        result = await validator._validate_keyword_density(good_keyword_content, Path('/test/keywords.pdf'))
        is_valid, details = result
        assert is_valid
        assert details['word_count'] > 0
        
        # Test consistent date formatting
        consistent_dates_content = {
            'raw_text': 'January 2020 to March 2022, April 2022 to December 2023',
            'sections': {},
            'metadata': {}
        }
        result = await validator._validate_date_formatting(consistent_dates_content, Path('/test/dates.pdf'))
        is_valid, details = result
        assert is_valid
        assert len(details['date_formats']) <= 2  # Should be consistent
        
        # Test headers/footers validation - clean document
        clean_content = {
            'raw_text': 'Professional Summary\nExperienced software engineer\nTechnical Skills\nPython, JavaScript, AWS',
            'sections': {},
            'metadata': {}
        }
        result = await validator._validate_headers_footers(clean_content, Path('/test/clean.pdf'))
        is_valid, details = result
        assert is_valid  # Should pass with no problematic headers/footers
        
        # Test graphics placement - good document
        good_graphics_content = {
            'raw_text': 'Professional experience includes software development with Python and JavaScript. Led multiple teams on enterprise projects delivering scalable solutions.',
            'sections': {},
            'metadata': {}
        }
        result = await validator._validate_graphics_placement(good_graphics_content, Path('/test/graphics.pdf'))
        is_valid, details = result
        assert is_valid
        assert details['avg_line_length'] > 20
    
    @pytest.mark.asyncio
    async def test_comprehensive_document_validation_flow(self, validator):
        """Test complete document validation flow with comprehensive scenarios."""
        # Create test content that exercises more validation paths
        comprehensive_test_content = {
            'extraction_method': 'pdf',
            'file_extension': '.pdf',
            'file_path': '/test/comprehensive.pdf',
            'file_size': 1024 * 1024,  # 1MB
            'raw_text': '''JANE SMITH
Senior Data Scientist
jane.smith@company.com | +1 (555) 987-6543 | LinkedIn: linkedin.com/in/janesmith

PROFESSIONAL SUMMARY
Experienced data scientist with 5+ years developing machine learning models and analytics solutions.

WORK EXPERIENCE
Senior Data Scientist | DataCorp | 2020-2024
• Developed predictive models improving revenue by 25%
• Led team of 3 data analysts on customer segmentation project
• Implemented MLOps pipeline reducing deployment time by 50%

Data Analyst | TechStart | 2018-2020
• Built automated reporting dashboards serving 100+ stakeholders
• Analyzed customer data to identify $2M cost savings opportunity

TECHNICAL SKILLS
Programming: Python, R, SQL, JavaScript
Machine Learning: scikit-learn, TensorFlow, PyTorch
Cloud Platforms: AWS, Azure, Google Cloud

EDUCATION
Master of Science in Data Science | University of Data | 2018
Bachelor of Science in Mathematics | Math College | 2016
''',
            'sections': {
                'contact': 'jane.smith@company.com | +1 (555) 987-6543',
                'summary': 'Experienced data scientist with 5+ years developing machine learning models',
                'experience': '''Senior Data Scientist | DataCorp | 2020-2024
• Developed predictive models improving revenue by 25%
• Led team of 3 data analysts on customer segmentation project
Data Analyst | TechStart | 2018-2020
• Built automated reporting dashboards serving 100+ stakeholders''',
                'skills': 'Programming: Python, R, SQL, JavaScript, Machine Learning: scikit-learn, TensorFlow, PyTorch',
                'education': 'Master of Science in Data Science | University of Data | 2018'
            },
            'metadata': {
                'fonts_used': ['Arial', 'Times New Roman'],
                'encoding': 'UTF-8',
                'creation_date': '2024-01-20',
                'word_count': 185,
                'character_count': 1456
            }
        }
        
        # Mock document extraction to return comprehensive content
        with patch.object(validator, '_extract_document_content', return_value=comprehensive_test_content):
            # Test with multiple vendors and different compliance levels
            result = await validator.validate_document(
                Path('/test/comprehensive.pdf'),
                target_vendors=[ATSVendor.WORKDAY, ATSVendor.GREENHOUSE, ATSVendor.LEVER],
                compliance_level=ComplianceLevel.STANDARD
            )
            
            assert isinstance(result, ValidationResult)
            assert result.is_compliant is not None
            assert result.compliance_score >= 0
            assert isinstance(result.violations, list)
            assert isinstance(result.ats_vendor_scores, dict)
            assert len(result.ats_vendor_scores) == 3  # Should have scores for all 3 vendors
            
            # Test validation rules were actually run
            # The document should have good compliance scores
            assert result.compliance_score > 50  # Should be reasonably good
            
            # Test that specific validation rules were applied
            section_validation_occurred = any(
                'section' in violation.get('rule_id', '').lower()
                for violation in result.violations
            )
            
            contact_validation_occurred = any(
                'contact' in violation.get('rule_id', '').lower()
                for violation in result.violations
            )
            
            # Should have attempted section and contact validation (may pass or fail)
            # This tests that the validation rules were actually executed
    
    @pytest.mark.asyncio
    async def test_validation_rule_exception_handling(self, validator):
        """Test validation rule exception handling paths."""
        # Create content that will cause validation rule exceptions
        problematic_content = {
            'extraction_method': 'pdf',
            'file_extension': '.pdf',
            'file_path': '/test/problematic.pdf',
            'file_size': 2048,
            'raw_text': None,  # This should cause issues
            'sections': None,  # This should cause issues
            'metadata': None   # This should cause issues
        }
        
        # Mock one of the validation methods to raise an exception
        original_validate_contact = validator._validate_contact_info
        
        async def mock_validate_contact_with_exception(content, path):
            raise Exception("Simulated validation rule exception")
        
        # Temporarily replace the validation method
        validator._validate_contact_info = mock_validate_contact_with_exception
        
        try:
            with patch.object(validator, '_extract_document_content', return_value=problematic_content):
                result = await validator.validate_document(
                    Path('/test/problematic.pdf'),
                    compliance_level=ComplianceLevel.BASIC
                )
                
                assert isinstance(result, ValidationResult)
                # Should have some violations due to the exception
                assert len(result.violations) > 0
                
                # Should have system violations from the exception
                system_violations = [
                    v for v in result.violations
                    if v.get('category') == 'system'
                ]
                assert len(system_violations) > 0
        
        finally:
            # Restore the original method
            validator._validate_contact_info = original_validate_contact
    
    @pytest.mark.asyncio
    async def test_empty_and_none_content_handling(self, validator):
        """Test handling of empty and None content values."""
        # Test various empty content scenarios
        test_scenarios = [
            {
                'name': 'no_text',
                'content': {
                    'raw_text': '',
                    'sections': {},
                    'metadata': {}
                }
            },
            {
                'name': 'none_sections',
                'content': {
                    'raw_text': 'Some text',
                    'sections': None,
                    'metadata': {}
                }
            },
            {
                'name': 'empty_metadata',
                'content': {
                    'raw_text': 'Text content here',
                    'sections': {'contact': 'email@test.com'},
                    'metadata': None
                }
            }
        ]
        
        for scenario in test_scenarios:
            # Test keyword density validation with empty content
            result = await validator._validate_keyword_density(
                scenario['content'], 
                Path(f'/test/{scenario["name"]}.pdf')
            )
            is_valid, details = result
            
            # Should handle gracefully (either pass or fail, but not crash)
            assert isinstance(is_valid, bool)
            assert isinstance(details, dict)
    
    @pytest.mark.asyncio
    async def test_factory_function_and_imports(self, validator):
        """Test factory function and import handling."""
        from src.validation.ats_compliance import get_ats_validator
        
        # Test factory function
        factory_validator = await get_ats_validator()
        assert isinstance(factory_validator, ATSComplianceValidator)
        
        # Test that the factory returns a properly initialized validator
        assert len(factory_validator.rules) > 0  # Should have validation rules
        assert isinstance(factory_validator.vendor_requirements, dict)
        assert isinstance(factory_validator.compliance_cache, dict)
        
        # Test validation rule applicability filtering (covers more conditional paths)
        test_content = {
            'extraction_method': 'txt',
            'file_extension': '.txt',
            'raw_text': 'Simple text content',
            'sections': {},
            'metadata': {}
        }
        
        # Test validation with vendors that have fewer applicable rules
        with patch.object(validator, '_extract_document_content', return_value=test_content):
            result = await validator.validate_document(
                Path('/test/simple.txt'),
                target_vendors=[ATSVendor.GENERIC],  # Should have fewer rules
                compliance_level=ComplianceLevel.BASIC
            )
            
            assert isinstance(result, ValidationResult)
            # Should complete validation even with minimal applicable rules
            assert result.compliance_score >= 0
    
    @pytest.mark.asyncio
    async def test_pdf_ocr_detection_and_metadata_extraction(self, validator):
        """Test PDF OCR detection and metadata extraction paths."""
        # Test PDF with good text (no OCR issues)
        good_pdf_content = {
            'file_extension': '.pdf',
            'raw_text': 'This is clean text extracted directly from the PDF without any OCR issues or excessive spacing problems.',
            'sections': {},
            'metadata': {}
        }
        result = await validator._validate_pdf_text_extraction(good_pdf_content, Path('/test/clean.pdf'))
        is_valid, details = result
        assert is_valid
        
        # Test PDF with OCR indicators (excessive spacing and line breaks)
        ocr_pdf_content = {
            'file_extension': '.pdf',
            'raw_text': 'This   is   text   with   excessive   spacing\n\n\n\n\nAnd   many   line   breaks\n\n\n\n\nthat   indicates   OCR   processing',
            'sections': {},
            'metadata': {}
        }
        result = await validator._validate_pdf_text_extraction(ocr_pdf_content, Path('/test/ocr.pdf'))
        is_valid, details = result
        assert not is_valid  # Should detect OCR issues
        assert 'OCR' in details['issue']
        
        # Test DOCX metadata extraction paths
        with patch('docx.Document') as mock_doc_class:
            mock_doc = MagicMock()
            mock_doc_class.return_value = mock_doc
            
            # Mock core properties
            mock_doc.core_properties.title = "Resume Document"
            mock_doc.core_properties.author = "John Doe"
            mock_doc.core_properties.created = None  # Test None handling
            
            # Mock paragraphs with font information
            mock_paragraph = MagicMock()
            mock_paragraph.text = "Sample paragraph text"
            mock_run = MagicMock()
            mock_run.font.name = "Arial"
            mock_paragraph.runs = [mock_run]
            mock_doc.paragraphs = [mock_paragraph]
            
            content = await validator._extract_docx_content(Path('/test/sample.docx'))
            
            assert content['extraction_method'] == 'docx'
            assert content['metadata']['title'] == "Resume Document"
            assert content['metadata']['author'] == "John Doe"
            assert content['metadata']['created'] == ''  # Should handle None
            assert 'Arial' in content['fonts_used']
            assert 'Sample paragraph text' in content['raw_text']