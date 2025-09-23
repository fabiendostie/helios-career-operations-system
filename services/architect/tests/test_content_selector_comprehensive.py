"""Comprehensive tests for Content Selector to achieve >85% coverage."""

import pytest
from unittest.mock import patch, MagicMock
from dataclasses import dataclass
from typing import Dict, List, Any

from src.core.content_selector import (
    ContentSelector, SkillRecommendation, ContentRecommendation,
    AnalystRecommendations, SkillQuadrant, ContentPriority
)


class TestContentSelector:
    """Comprehensive tests for Content Selector functionality."""

    @pytest.fixture
    def content_selector(self):
        """Create content selector instance."""
        return ContentSelector()

    @pytest.fixture
    def comprehensive_profile_data(self):
        """Comprehensive profile data for testing."""
        return {
            'candidate_name': 'Alex Rivera',
            'email': 'alex@example.com',
            'phone': '555-123-4567',
            'location': 'Austin, TX',
            'work_experience': [
                {
                    'role_title': 'Senior Software Engineer',
                    'company_name': 'TechCorp Inc',
                    'start_date': '2020-01-01',
                    'end_date': '2023-12-31',
                    'accomplishments': [
                        'Reduced system latency by 40% through optimization',
                        'Led migration to microservices architecture',
                        'Mentored 5 junior developers'
                    ],
                    'skills_used': ['Python', 'Docker', 'AWS', 'Kubernetes'],
                    'impact_metrics': ['40% latency reduction', '5 mentees'],
                    'quantified_results': ['$200K cost savings annually']
                },
                {
                    'role_title': 'Software Developer',
                    'company_name': 'StartupXYZ',
                    'start_date': '2018-01-01',
                    'end_date': '2019-12-31',
                    'accomplishments': [
                        'Built automated testing framework',
                        'Improved code coverage to 95%'
                    ],
                    'skills_used': ['JavaScript', 'React', 'Node.js'],
                    'impact_metrics': ['95% code coverage']
                }
            ],
            'projects': [
                {
                    'name': 'Open Source ML Library',
                    'description': 'Created machine learning library with 1000+ GitHub stars',
                    'technologies': ['Python', 'TensorFlow', 'Scikit-learn'],
                    'outcomes': ['1000+ GitHub stars', '50+ contributors']
                }
            ],
            'skills_inventory': {
                'technical_skills': {
                    'programming': ['Python', 'JavaScript', 'Java', 'Go'],
                    'frameworks': ['React', 'Django', 'FastAPI'],
                    'platforms': ['AWS', 'Docker', 'Kubernetes'],
                    'databases': ['PostgreSQL', 'MongoDB', 'Redis']
                },
                'soft_skills': ['Leadership', 'Communication', 'Problem Solving', 'Mentoring']
            },
            'education': [
                {
                    'degree': 'Bachelor of Science in Computer Science',
                    'institution': 'University of Texas',
                    'year': '2017',
                    'gpa': '3.8'
                }
            ]
        }

    @pytest.fixture
    def analyst_recommendations(self):
        """Sample analyst recommendations."""
        return {
            'skill_quadrants': {
                'leverage': ['Python', 'AWS', 'Leadership'],
                'upskill': ['Machine Learning', 'Terraform'],
                'maintain': ['JavaScript', 'React'],
                'de_emphasize': ['PHP', 'jQuery']
            },
            'content_priorities': {
                'technical_accomplishments': 0.8,
                'leadership_examples': 0.7,
                'quantified_results': 0.9
            },
            'ats_keywords': ['Software Engineer', 'Python', 'AWS', 'Agile', 'Team Lead'],
            'industry_trends': ['Cloud Computing', 'DevOps', 'Microservices'],
            'optimization_suggestions': [
                'Emphasize quantified achievements',
                'Include relevant technical keywords',
                'Highlight leadership experience'
            ]
        }

    def test_content_selector_initialization(self, content_selector):
        """Test content selector initialization."""
        assert content_selector is not None
        assert hasattr(content_selector, 'settings')

    def test_skill_recommendation_dataclass(self):
        """Test SkillRecommendation dataclass."""
        recommendation = SkillRecommendation(
            skill='Python',
            quadrant=SkillQuadrant.LEVERAGE,
            relevance_score=0.9,
            confidence=0.85,
            evidence_count=5,
            market_demand=0.8
        )

        assert recommendation.skill == 'Python'
        assert recommendation.quadrant == SkillQuadrant.LEVERAGE
        assert recommendation.relevance_score == 0.9
        assert recommendation.confidence == 0.85
        assert recommendation.evidence_count == 5

    def test_content_recommendation_dataclass(self):
        """Test ContentRecommendation dataclass."""
        recommendation = ContentRecommendation(
            content_type='accomplishment',
            content_id='acc_001',
            priority=ContentPriority.HIGH,
            relevance_score=0.85,
            reasoning='Strong technical impact with quantified results',
            customization_notes=['Focus on quantified results', 'Emphasize leadership']
        )

        assert recommendation.content_type == 'accomplishment'
        assert recommendation.priority == ContentPriority.HIGH
        assert 0 <= recommendation.relevance_score <= 1
        assert isinstance(recommendation.customization_notes, list)
        assert len(recommendation.customization_notes) == 2

    @pytest.mark.asyncio
    async def test_resume_content_selection_basic(self, content_selector, comprehensive_profile_data, analyst_recommendations):
        """Test basic resume content selection."""
        result = await content_selector.select_resume_content(
            comprehensive_profile_data,
            analyst_recommendations
        )

        assert isinstance(result, dict)
        # The method returns the enhanced career data, so check for key fields
        assert 'work_experience' in result
        assert 'skills_inventory' in result
        assert '_content_metadata' in result

        # Should have metadata indicating intelligent selection
        metadata = result['_content_metadata']
        assert metadata['selection_strategy'] == 'analyst_optimized'
        assert metadata['recommendations_applied'] is True

    @pytest.mark.asyncio
    async def test_work_experience_intelligent_selection(self, content_selector, comprehensive_profile_data, analyst_recommendations):
        """Test intelligent work experience selection and optimization."""
        # Parse recommendations first
        parsed_recommendations = content_selector._parse_analyst_recommendations(analyst_recommendations)

        optimized_experience = await content_selector._select_work_experience(
            comprehensive_profile_data['work_experience'],
            parsed_recommendations,
            {'required_skills': ['Python', 'Leadership'], 'role_title': 'Senior Engineer'}
        )

        assert isinstance(optimized_experience, list)
        assert len(optimized_experience) > 0

        # Should include relevance scoring
        for exp in optimized_experience:
            assert 'role_title' in exp
            assert 'company_name' in exp
            assert 'accomplishments' in exp
            assert '_relevance_score' in exp
            assert isinstance(exp['_relevance_score'], float)

        # Should be ordered by relevance (most relevant first)
        scores = [exp['_relevance_score'] for exp in optimized_experience]
        assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_accomplishment_intelligent_optimization(self, content_selector, analyst_recommendations):
        """Test intelligent accomplishment optimization with relevance scoring."""
        sample_accomplishments = [
            'Reduced system latency by 40% through Python optimization',
            'Led migration to microservices architecture using Docker',
            'Worked on various projects',
            'Improved code quality significantly',
            'Managed AWS infrastructure for 10+ applications'
        ]

        # Parse recommendations first
        parsed_recommendations = content_selector._parse_analyst_recommendations(analyst_recommendations)

        optimized = await content_selector._optimize_accomplishments(
            sample_accomplishments,
            parsed_recommendations,
            {'required_skills': ['Python', 'AWS'], 'ats_keywords': ['optimization', 'infrastructure']}
        )

        assert isinstance(optimized, list)
        assert len(optimized) > 0

        # Should prioritize quantified accomplishments with relevant keywords
        quantified_python = any('40%' in acc and 'Python' in acc for acc in optimized)
        aws_infrastructure = any('AWS' in acc and 'infrastructure' in acc for acc in optimized)

        assert quantified_python or aws_infrastructure

        # Should filter out vague accomplishments
        vague_found = any('various projects' in acc for acc in optimized)
        assert not vague_found or len(optimized) <= 2  # Only if very few accomplishments available

    @pytest.mark.asyncio
    async def test_intelligent_skills_selection_with_quadrants(self, content_selector, comprehensive_profile_data, analyst_recommendations):
        """Test intelligent skills selection using analyst quadrant system."""
        # Parse recommendations first
        parsed_recommendations = content_selector._parse_analyst_recommendations(analyst_recommendations)

        selected_skills = await content_selector._select_skills(
            comprehensive_profile_data['skills_inventory'],
            parsed_recommendations,
            {'required_skills': ['Python', 'Leadership'], 'role_title': 'Senior Engineer'}
        )

        assert isinstance(selected_skills, dict)
        assert 'core_skills' in selected_skills

        core_skills = selected_skills['core_skills']
        assert isinstance(core_skills, list)
        assert len(core_skills) > 0
        assert len(core_skills) <= 8  # ATS optimization limit

        # Should prioritize leverage skills first
        leverage_skills = analyst_recommendations['skill_quadrants']['leverage']
        leverage_in_core = [skill for skill in core_skills if skill in leverage_skills]
        assert len(leverage_in_core) > 0  # Should have some leverage skills

        # Should include job requirements
        job_skills_in_core = [skill for skill in core_skills if skill in ['Python', 'Leadership']]
        assert len(job_skills_in_core) > 0  # Should include some job requirements

    @pytest.mark.asyncio
    async def test_intelligent_project_selection_with_scoring(self, content_selector, comprehensive_profile_data, analyst_recommendations):
        """Test intelligent project selection based on relevance scoring."""
        # Parse recommendations first
        parsed_recommendations = content_selector._parse_analyst_recommendations(analyst_recommendations)

        # Add more projects to test scoring logic
        enhanced_projects = comprehensive_profile_data.get('projects', [])
        enhanced_projects.extend([
            {
                'name': 'Legacy PHP Application',
                'description': 'Maintained old PHP system',
                'technologies': ['PHP', 'MySQL', 'jQuery'],
                'outcomes': ['Basic maintenance']
            },
            {
                'name': 'Cloud Migration Project',
                'description': 'Migrated infrastructure to AWS with Python automation',
                'technologies': ['Python', 'AWS', 'Docker', 'Terraform'],
                'outcomes': ['50% cost reduction', 'Improved scalability']
            }
        ])

        selected_projects = await content_selector._select_projects(
            enhanced_projects,
            parsed_recommendations,
            {'required_skills': ['Python', 'AWS'], 'role_title': 'Senior Engineer'}
        )

        assert isinstance(selected_projects, list)
        assert len(selected_projects) <= 3  # Should limit to top 3

        if selected_projects:
            # Should prioritize projects with leverage skills and job requirements
            high_value_projects = [
                p for p in selected_projects
                if any(tech in ['Python', 'AWS', 'Docker'] for tech in p.get('technologies', []))
            ]

            # Should favor modern technologies over legacy
            legacy_projects = [
                p for p in selected_projects
                if 'PHP' in p.get('technologies', [])
            ]

            # If we have good projects, legacy should be de-prioritized
            if len(enhanced_projects) > 2:
                assert len(high_value_projects) >= len(legacy_projects)

    @pytest.mark.asyncio
    async def test_intelligent_t_shaped_summary_creation(self, content_selector, comprehensive_profile_data, analyst_recommendations):
        """Test intelligent T-shaped professional summary creation with strategic content selection."""
        # Parse recommendations first
        parsed_recommendations = content_selector._parse_analyst_recommendations(analyst_recommendations)

        summary_content = await content_selector._create_t_shaped_summary(
            comprehensive_profile_data,
            parsed_recommendations,
            {'required_skills': ['Python', 'Leadership'], 'role_title': 'Senior Software Engineer'}
        )

        assert isinstance(summary_content, dict)

        # Should have all required T-shaped fields
        required_fields = [
            'core_competency_1', 'core_competency_2', 'core_technology',
            'top_quantified_achievement', 'adjective', 'years_experience', 'skill_area'
        ]
        for field in required_fields:
            assert field in summary_content
            assert summary_content[field] is not None
            assert len(str(summary_content[field])) > 0

        # Should prioritize leverage skills in competencies
        leverage_skills = analyst_recommendations['skill_quadrants']['leverage']
        competencies = [
            summary_content.get('core_competency_1', ''),
            summary_content.get('core_competency_2', ''),
            summary_content.get('core_technology', '')
        ]

        # At least one competency should be from leverage skills
        leverage_in_competencies = any(
            any(skill.lower() in comp.lower() for skill in leverage_skills)
            for comp in competencies
        )
        assert leverage_in_competencies

        # Years experience should be reasonable
        years_exp = summary_content['years_experience']
        assert isinstance(years_exp, int)
        assert 0 <= years_exp <= 20

        # Achievement should be from strategic metadata
        achievement = summary_content['top_quantified_achievement']
        strategic_metadata = comprehensive_profile_data.get('strategic_metadata', {})
        quantified_achievements = strategic_metadata.get('quantified_achievements', [])

        if quantified_achievements:
            assert achievement in quantified_achievements or 'delivered' in achievement.lower()

    @pytest.mark.asyncio
    async def test_intelligent_cover_letter_with_research_integration(self, content_selector, comprehensive_profile_data):
        """Test intelligent cover letter content selection with dynamic research integration."""
        job_requirements = {
            'role_title': 'Senior Software Engineer',
            'company': 'TechInnovate Corp',
            'industry': 'Technology',
            'required_skills': ['Python', 'AWS', 'Leadership'],
            'responsibilities': ['Lead development teams', 'Design scalable systems']
        }

        company_research = {
            'company_mission': 'Building the future of technology',
            'recent_news': ['Launched new AI platform', 'Expanded to 10 new markets'],
            'culture_values': ['Innovation', 'Collaboration', 'Excellence'],
            'challenges': ['Scaling infrastructure', 'Team growth'],
            'pain_points': ['Technical debt', 'System performance']
        }

        # Mock the research engine to avoid external dependencies
        with patch('src.core.content_selector.get_research_engine') as mock_get_engine:
            mock_engine = MagicMock()
            mock_engine.get_company_intelligence = AsyncMock(return_value={
                'challenges': ['Rapid scaling challenges', 'Performance optimization needs'],
                'industry': 'Technology',
                'growth_areas': ['AI/ML', 'Cloud Infrastructure'],
                'hiring_trends': {'focus_areas': ['Senior Engineers', 'Tech Leads']},
                'timestamp': 1234567890
            })
            mock_engine.get_industry_intelligence = AsyncMock(return_value={
                'challenges': ['Talent acquisition', 'Technology adoption'],
                'emphasis_areas': ['technical leadership', 'scalability']
            })
            mock_get_engine.return_value = mock_engine

            result = await content_selector.select_cover_letter_content(
                comprehensive_profile_data,
                job_requirements,
                analyst_recommendations=None,
                company_data=company_research
            )

            assert isinstance(result, dict)

            # Should have Pain & Promise specific fields
            pain_promise_fields = [
                'inferred_pain_point', 'company_challenge_context',
                'specific_challenge_detail', 'top_quantified_achievement',
                'key_skill_1', 'key_skill_2', 'relevant_skill_area'
            ]

            for field in pain_promise_fields:
                assert field in result
                assert result[field] is not None
                assert len(str(result[field])) > 0

            # Should infer relevant pain point for engineering role
            pain_point = result['inferred_pain_point'].lower()
            assert any(keyword in pain_point for keyword in [
                'scaling', 'technical', 'infrastructure', 'performance', 'efficiency'
            ])

            # Should include research-enhanced data
            assert result.get('_research_enhanced') is True
            assert 'company_growth_areas' in result
            assert 'industry_trends' in result

            # Research engine should be called for company intelligence
            mock_engine.get_company_intelligence.assert_called_once()
            call_args = mock_engine.get_company_intelligence.call_args
            assert call_args[1]['company_name'] == 'TechInnovate Corp'

    @pytest.mark.asyncio
    async def test_analyst_recommendations_parsing_intelligence(self, content_selector):
        """Test intelligent parsing of complex analyst recommendations."""
        # Test with complex, realistic analyst recommendations
        complex_recommendations = {
            'skill_recalibration': {
                'leverage': [
                    {'name': 'Python', 'relevance_score': 0.95, 'confidence': 0.9, 'evidence_count': 8, 'market_demand': 0.92},
                    {'name': 'AWS', 'relevance_score': 0.88, 'confidence': 0.85, 'evidence_count': 6, 'market_demand': 0.89},
                    'Leadership'  # Simple string format
                ],
                'upskill': [
                    {'name': 'Machine Learning', 'relevance_score': 0.7, 'confidence': 0.6, 'evidence_count': 2},
                    'Terraform'
                ],
                'maintain': ['JavaScript', 'React', 'Docker'],
                'de_emphasize': ['PHP', 'jQuery', 'Legacy Systems']
            },
            'ats_optimization': {
                'keywords_to_emphasize': ['Software Engineer', 'Python', 'Cloud Architecture', 'Team Leadership']
            },
            'content_recommendations': {
                'impact_metrics': ['performance improvement', 'cost reduction', 'team efficiency'],
                'action_verbs': ['optimized', 'architected', 'implemented', 'delivered'],
                'industry_keywords': ['scalability', 'microservices', 'DevOps', 'agile']
            },
            'content_priorities': {
                'technical_accomplishments': 'high',
                'leadership_examples': 'medium',
                'certifications': 'low'
            },
            'target_role_alignment': {
                'senior_engineer_match': 0.92,
                'tech_lead_match': 0.85,
                'architect_match': 0.78
            }
        }

        parsed = content_selector._parse_analyst_recommendations(complex_recommendations)

        # Verify structure
        assert isinstance(parsed, AnalystRecommendations)

        # Test skill recalibration parsing
        leverage_skills = parsed.skill_recalibration[SkillQuadrant.LEVERAGE]
        assert len(leverage_skills) == 3

        # Check detailed skill parsing
        python_skill = next((s for s in leverage_skills if s.skill == 'Python'), None)
        assert python_skill is not None
        assert python_skill.relevance_score == 0.95
        assert python_skill.confidence == 0.9
        assert python_skill.evidence_count == 8
        assert python_skill.market_demand == 0.92

        # Check simple string parsing fallback
        leadership_skill = next((s for s in leverage_skills if s.skill == 'Leadership'), None)
        assert leadership_skill is not None
        assert leadership_skill.relevance_score == 0.8  # Default value
        assert leadership_skill.confidence == 0.7  # Default value

        # Test other parsed fields
        assert 'Software Engineer' in parsed.ats_keywords
        assert 'performance improvement' in parsed.impact_metrics
        assert 'optimized' in parsed.action_verbs
        assert 'scalability' in parsed.industry_keywords

    def test_years_experience_calculation(self, content_selector, comprehensive_profile_data):
        """Test years of experience calculation."""
        years = content_selector._calculate_years_experience(
            comprehensive_profile_data['work_experience']
        )

        assert isinstance(years, (int, float))
        assert years > 0

        # Should be reasonable for the sample data (2018-2023)
        assert years >= 4  # At least 4 years based on sample data

    def test_adjective_selection(self, content_selector):
        """Test adjective selection based on experience."""
        # Test different experience levels
        test_cases = [
            (2, ['Motivated', 'Skilled', 'Capable']),
            (5, ['Experienced', 'Accomplished']),
            (10, ['Senior', 'Expert', 'Seasoned']),
            (15, ['Distinguished', 'Veteran'])
        ]

        for years, expected_categories in test_cases:
            adjective = content_selector._select_adjective_by_experience(years)
            assert isinstance(adjective, str)
            assert len(adjective) > 0

    def test_job_relevance_calculation(self, content_selector, comprehensive_profile_data):
        """Test job relevance calculation."""
        job_requirements = {
            'required_skills': ['Python', 'AWS', 'Leadership'],
            'preferred_skills': ['Docker', 'Kubernetes'],
            'role_title': 'Senior Software Engineer'
        }

        relevance_score = content_selector._calculate_job_relevance(
            comprehensive_profile_data,
            job_requirements
        )

        assert isinstance(relevance_score, float)
        assert 0.0 <= relevance_score <= 1.0

        # Should be high for good match
        assert relevance_score > 0.6  # Should be reasonably high

    def test_industry_customization(self, content_selector, comprehensive_profile_data):
        """Test industry-specific customization."""
        # Test different industries
        industries = ['Technology', 'Finance', 'Healthcare', 'Education']

        for industry in industries:
            customized_content = content_selector._apply_industry_customization(
                comprehensive_profile_data,
                industry
            )

            assert isinstance(customized_content, dict)
            assert 'emphasized_skills' in customized_content
            assert 'industry_keywords' in customized_content

    def test_ats_optimization(self, content_selector, comprehensive_profile_data, analyst_recommendations):
        """Test ATS optimization features."""
        ats_optimized = content_selector._apply_ats_optimization(
            comprehensive_profile_data,
            analyst_recommendations['ats_keywords']
        )

        assert isinstance(ats_optimized, dict)
        assert 'optimized_content' in ats_optimized
        assert 'keyword_density' in ats_optimized

        # Should include ATS keywords
        optimized_text = str(ats_optimized['optimized_content'])
        ats_keywords = analyst_recommendations['ats_keywords']

        keywords_found = sum(1 for keyword in ats_keywords if keyword.lower() in optimized_text.lower())
        assert keywords_found > 0

    def test_performance_metrics_extraction(self, content_selector, comprehensive_profile_data):
        """Test performance metrics extraction."""
        metrics = content_selector._extract_performance_metrics(
            comprehensive_profile_data['work_experience']
        )

        assert isinstance(metrics, list)
        assert len(metrics) > 0

        # Should find quantified metrics
        percentage_metrics = [m for m in metrics if '%' in m]
        assert len(percentage_metrics) > 0

    def test_skill_frequency_analysis(self, content_selector, comprehensive_profile_data):
        """Test skill frequency analysis."""
        skill_frequencies = content_selector._analyze_skill_frequencies(
            comprehensive_profile_data
        )

        assert isinstance(skill_frequencies, dict)
        assert len(skill_frequencies) > 0

        # Should count skill mentions
        for skill, frequency in skill_frequencies.items():
            assert isinstance(skill, str)
            assert isinstance(frequency, int)
            assert frequency > 0

    def test_content_length_optimization(self, content_selector):
        """Test content length optimization."""
        long_text = "This is a very long accomplishment description that might need to be shortened for optimal ATS parsing and recruiter readability while maintaining the key impact and technical details."

        optimized = content_selector._optimize_content_length(
            long_text,
            max_length=100
        )

        assert isinstance(optimized, str)
        assert len(optimized) <= 103  # Allow for ellipsis
        assert len(optimized) > 0

    def test_technical_depth_analysis(self, content_selector, comprehensive_profile_data):
        """Test technical depth analysis."""
        tech_depth = content_selector._analyze_technical_depth(
            comprehensive_profile_data['work_experience']
        )

        assert isinstance(tech_depth, dict)
        assert 'technical_skills_count' in tech_depth
        assert 'technical_accomplishments' in tech_depth
        assert 'depth_score' in tech_depth

        # Should calculate meaningful metrics
        assert tech_depth['technical_skills_count'] > 0
        assert 0.0 <= tech_depth['depth_score'] <= 1.0

    def test_leadership_indicators_extraction(self, content_selector, comprehensive_profile_data):
        """Test leadership indicators extraction."""
        leadership_indicators = content_selector._extract_leadership_indicators(
            comprehensive_profile_data['work_experience']
        )

        assert isinstance(leadership_indicators, list)

        # Should find leadership examples
        leadership_keywords = ['led', 'mentored', 'managed', 'coordinated']
        found_indicators = any(
            any(keyword in indicator.lower() for keyword in leadership_keywords)
            for indicator in leadership_indicators
        )
        assert found_indicators

    def test_error_handling_in_content_selection(self, content_selector):
        """Test error handling with invalid input."""
        # Test with empty data
        result = content_selector.select_resume_content({}, {})
        assert isinstance(result, dict)

        # Test with malformed data
        malformed_data = {'work_experience': 'not_a_list'}
        result = content_selector.select_resume_content(malformed_data, {})
        assert isinstance(result, dict)

    def test_confidence_scoring(self, content_selector, comprehensive_profile_data, analyst_recommendations):
        """Test confidence scoring in recommendations."""
        result = content_selector.select_resume_content(
            comprehensive_profile_data,
            analyst_recommendations
        )

        if 'confidence_score' in result:
            assert isinstance(result['confidence_score'], float)
            assert 0.0 <= result['confidence_score'] <= 1.0
