"""Focused, high-quality tests for Content Selector that improve system quality."""

import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from dataclasses import dataclass
from typing import Dict, List, Any

from src.core.content_selector import (
    ContentSelector, SkillRecommendation, ContentRecommendation,
    AnalystRecommendations, SkillQuadrant, ContentPriority
)


class TestContentSelectorIntelligence:
    """High-quality tests focusing on intelligent functionality."""

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
                        'Reduced system latency by 40% through Python optimization',
                        'Led migration to microservices architecture using Docker',
                        'Mentored 5 junior developers in agile practices'
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
                        'Built automated testing framework increasing coverage to 95%',
                        'Improved deployment pipeline reducing release time by 60%'
                    ],
                    'skills_used': ['JavaScript', 'React', 'Node.js', 'Jenkins']
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
            'strategic_metadata': {
                'core_competencies': ['Python Development', 'Cloud Architecture', 'Team Leadership'],
                'quantified_achievements': [
                    'reduced system latency by 40%',
                    'increased test coverage to 95%',
                    'led team of 5 engineers'
                ]
            }
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

    @pytest.mark.asyncio
    async def test_intelligent_resume_content_selection(self, content_selector, comprehensive_profile_data, analyst_recommendations):
        """Test intelligent resume content selection with ANALYST integration."""
        result = await content_selector.select_resume_content(
            comprehensive_profile_data,
            analyst_recommendations
        )

        assert isinstance(result, dict)
        # Should enhance the original data structure
        assert 'work_experience' in result
        assert 'skills_inventory' in result
        assert '_content_metadata' in result

        # Should have metadata indicating intelligent selection
        metadata = result['_content_metadata']
        assert metadata['selection_strategy'] == 'analyst_optimized'
        assert metadata['recommendations_applied'] is True

        # Work experience should be optimized and scored
        work_exp = result['work_experience']
        assert isinstance(work_exp, list)
        assert len(work_exp) > 0

        # Should include relevance scoring
        for exp in work_exp:
            assert '_relevance_score' in exp
            assert isinstance(exp['_relevance_score'], float)
            assert 0.0 <= exp['_relevance_score'] <= 10.0

    @pytest.mark.asyncio
    async def test_analyst_recommendations_parsing_intelligence(self, content_selector):
        """Test intelligent parsing of complex analyst recommendations."""
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
        with patch('src.core.research_engine.get_research_engine') as mock_get_engine:
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

    @pytest.mark.asyncio
    async def test_intelligent_work_experience_optimization(self, content_selector, comprehensive_profile_data, analyst_recommendations):
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
    async def test_accomplishment_relevance_scoring(self, content_selector, analyst_recommendations):
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

        # Should filter out vague accomplishments when better options exist
        vague_found = any('various projects' in acc for acc in optimized)
        if len(sample_accomplishments) > 3:  # If we have choices
            assert not vague_found  # Should filter out vague ones

    @pytest.mark.asyncio
    async def test_intelligent_skills_prioritization(self, content_selector, comprehensive_profile_data, analyst_recommendations):
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

    def test_years_experience_calculation_logic(self, content_selector, comprehensive_profile_data):
        """Test years of experience calculation logic."""
        years = content_selector._calculate_years_experience(
            comprehensive_profile_data['work_experience']
        )

        assert isinstance(years, int)
        assert years > 0
        assert years <= 20  # Should cap at 20 years

        # Should be reasonable for the sample data (2018-2023 = ~5 years)
        assert years >= 4  # At least 4 years based on sample data

    @pytest.mark.asyncio
    async def test_error_handling_graceful_degradation(self, content_selector):
        """Test graceful error handling with invalid input."""
        # Test with empty data - should not crash
        result = await content_selector.select_resume_content({}, {})
        assert isinstance(result, dict)

        # Test with malformed data - should handle gracefully
        malformed_data = {'work_experience': 'not_a_list'}
        result = await content_selector.select_resume_content(malformed_data, {})
        assert isinstance(result, dict)

        # Should include fallback content when data is missing
        assert 'work_experience' in result  # Should provide fallback

    @pytest.mark.asyncio
    async def test_project_selection_scoring_logic(self, content_selector, comprehensive_profile_data, analyst_recommendations):
        """Test project selection scoring and filtering logic."""
        # Parse recommendations first
        parsed_recommendations = content_selector._parse_analyst_recommendations(analyst_recommendations)

        # Add diverse projects to test scoring
        enhanced_projects = [
            {
                'name': 'Legacy System Maintenance',
                'description': 'Basic maintenance work',
                'technologies': ['PHP', 'MySQL'],
                'outcomes': ['Kept system running']
            },
            {
                'name': 'Modern Cloud Platform',
                'description': 'Built scalable microservices platform with Python and AWS',
                'technologies': ['Python', 'AWS', 'Docker', 'Kubernetes'],
                'outcomes': ['50% performance improvement', 'Reduced infrastructure costs']
            },
            {
                'name': 'Machine Learning Pipeline',
                'description': 'Implemented ML pipeline for data analysis',
                'technologies': ['Python', 'TensorFlow', 'AWS'],
                'outcomes': ['Automated decision making', '80% accuracy improvement']
            }
        ]

        selected_projects = await content_selector._select_projects(
            enhanced_projects,
            parsed_recommendations,
            {'required_skills': ['Python', 'AWS'], 'role_title': 'Senior Engineer'}
        )

        assert isinstance(selected_projects, list)
        assert len(selected_projects) <= 3  # Should limit to top 3

        # Should prioritize projects with leverage skills and modern technologies
        if selected_projects:
            # Should favor projects with Python/AWS over legacy PHP
            modern_projects = [
                p for p in selected_projects
                if any(tech in ['Python', 'AWS'] for tech in p.get('technologies', []))
            ]
            legacy_projects = [
                p for p in selected_projects
                if 'PHP' in p.get('technologies', [])
            ]

            # Modern projects should be prioritized
            assert len(modern_projects) >= len(legacy_projects)

    @pytest.mark.asyncio
    async def test_accomplishment_relevance_scoring_edge_cases(self, content_selector):
        """Test accomplishment relevance calculation with various edge cases."""
        target_keywords = {'python', 'aws', 'performance', 'leadership'}

        # Test highly relevant accomplishment (multiple keywords + quantified + action verb)
        high_relevance = "Led Python team optimizing AWS performance by 60%"
        high_score = await content_selector._calculate_accomplishment_relevance(
            high_relevance, target_keywords
        )

        # Test medium relevance accomplishment (some keywords + action verb)
        medium_relevance = "Improved Python application performance significantly"
        medium_score = await content_selector._calculate_accomplishment_relevance(
            medium_relevance, target_keywords
        )

        # Test low relevance accomplishment (no keywords but action verb)
        low_relevance = "Delivered minor bug fixes"
        low_score = await content_selector._calculate_accomplishment_relevance(
            low_relevance, target_keywords
        )

        # Test empty accomplishment
        empty_score = await content_selector._calculate_accomplishment_relevance(
            "", target_keywords
        )

        # Verify scoring logic
        assert high_score > medium_score > low_score >= empty_score
        assert 0.0 <= high_score <= 1.0
        assert 0.0 <= medium_score <= 1.0
        assert 0.0 <= low_score <= 1.0
        assert empty_score == 0.0

        # Check that high relevance gets substantial score
        assert high_score >= 0.7  # Should have multiple scoring components

    @pytest.mark.asyncio
    async def test_pain_point_inference_role_based(self, content_selector):
        """Test pain point inference for different role types."""
        # Test engineer role
        engineer_pain = await content_selector._infer_pain_point(
            'Senior Software Engineer', 'Technology', ['Scaling issues', 'Performance problems']
        )
        assert engineer_pain['category'] == 'technical'
        assert 'scaling' in engineer_pain['description'].lower()

        # Test manager role (avoid any 'engineer' substring)
        manager_pain = await content_selector._infer_pain_point(
            'Project Manager', 'Technology', ['Team coordination', 'Process inefficiency']
        )
        assert manager_pain['category'] == 'operational'
        assert 'team' in manager_pain['description'].lower() or 'operational' in manager_pain['description'].lower()

        # Test other role (defaults to strategic)
        other_pain = await content_selector._infer_pain_point(
            'Product Specialist', 'Finance', ['Market challenges']
        )
        assert other_pain['category'] == 'strategic'
        assert 'operational' in other_pain['description'].lower() or 'business' in other_pain['description'].lower()

    @pytest.mark.asyncio
    async def test_bridge_skills_selection_logic(self, content_selector, analyst_recommendations):
        """Test bridge skills selection with various scenarios."""
        # Parse recommendations first
        parsed_recommendations = content_selector._parse_analyst_recommendations(analyst_recommendations)

        # Test with rich job requirements
        rich_job_requirements = {
            'required_skills': ['Python', 'Kubernetes', 'Leadership', 'Machine Learning'],
            'role_title': 'Tech Lead'
        }

        bridge_skills = await content_selector._select_bridge_skills(
            parsed_recommendations, rich_job_requirements
        )

        assert isinstance(bridge_skills, list)
        assert len(bridge_skills) <= 3  # Should limit to 3
        assert len(bridge_skills) >= 2  # Should have at least 2

        # Should include some leverage skills
        leverage_skills = analyst_recommendations['skill_quadrants']['leverage']
        has_leverage = any(skill in bridge_skills for skill in leverage_skills)
        assert has_leverage

        # Test with empty job requirements
        empty_job_requirements = {'required_skills': [], 'role_title': ''}

        empty_bridge_skills = await content_selector._select_bridge_skills(
            parsed_recommendations, empty_job_requirements
        )

        assert isinstance(empty_bridge_skills, list)
        assert len(empty_bridge_skills) >= 2  # Should have fallback skills

        # Should include fallback skills when no good matches
        fallback_found = any(skill in ['expertise', 'leadership', 'problem-solving']
                           for skill in empty_bridge_skills)
        assert fallback_found

    @pytest.mark.asyncio
    async def test_top_achievement_selection_scoring(self, content_selector, comprehensive_profile_data, analyst_recommendations):
        """Test top achievement selection with scoring logic."""
        # Parse recommendations first
        parsed_recommendations = content_selector._parse_analyst_recommendations(analyst_recommendations)

        job_requirements = {
            'required_skills': ['Python', 'Leadership'],
            'role_title': 'Senior Engineer'
        }

        top_achievement = await content_selector._select_top_achievement(
            comprehensive_profile_data,
            job_requirements,
            parsed_recommendations
        )

        assert isinstance(top_achievement, str)
        assert len(top_achievement) > 0

        # Should select from strategic metadata if available
        strategic_metadata = comprehensive_profile_data.get('strategic_metadata', {})
        achievements = strategic_metadata.get('quantified_achievements', [])

        if achievements:
            # Should be one of the actual achievements or a fallback
            is_actual_achievement = top_achievement in achievements
            is_fallback = 'delivered' in top_achievement.lower() or 'results' in top_achievement.lower()
            assert is_actual_achievement or is_fallback

    @pytest.mark.asyncio
    async def test_research_engine_failure_handling(self, content_selector, comprehensive_profile_data):
        """Test graceful handling when research engine fails."""
        job_requirements = {
            'role_title': 'Senior Software Engineer',
            'company': 'TechCorp',
            'industry': 'Technology',
            'required_skills': ['Python', 'AWS']
        }

        # Mock research engine to fail
        with patch('src.core.research_engine.get_research_engine') as mock_get_engine:
            mock_engine = MagicMock()
            mock_engine.get_company_intelligence = AsyncMock(side_effect=Exception("Research service unavailable"))
            mock_engine.get_industry_intelligence = AsyncMock(side_effect=Exception("Research service unavailable"))
            mock_get_engine.return_value = mock_engine

            # Should handle failures gracefully and use fallback logic
            result = await content_selector.select_cover_letter_content(
                comprehensive_profile_data,
                job_requirements,
                analyst_recommendations=None,
                company_data={'challenges': ['Scaling issues']}
            )

            assert isinstance(result, dict)
            # Should still have pain point fields with fallback content
            assert 'inferred_pain_point' in result
            assert 'company_challenge_context' in result

            # Should fallback to basic logic when research fails
            pain_point = result['inferred_pain_point'].lower()
            assert any(keyword in pain_point for keyword in [
                'scaling', 'technical', 'infrastructure', 'efficiency'
            ])

    @pytest.mark.asyncio
    async def test_pain_addressing_achievement_selection_logic(self, content_selector, comprehensive_profile_data, analyst_recommendations):
        """Test intelligent selection of achievements that address specific pain points."""
        # Parse recommendations first
        parsed_recommendations = content_selector._parse_analyst_recommendations(analyst_recommendations)

        # Create work experience with diverse achievements
        work_experience = [
            {
                'role_title': 'Senior Engineer',
                'accomplishments': [
                    'Built high-performance distributed system handling 1M+ requests',
                    'Optimized database queries reducing latency by 50%',
                    'Led team of 8 engineers across multiple projects'
                ]
            }
        ]

        strategic_metadata = {
            'quantified_achievements': [
                'reduced system latency by 50%',
                'led team of 8 engineers',
                'built system handling 1M+ requests'
            ]
        }

        # Test technical pain point
        technical_pain = {
            'category': 'technical',
            'description': 'scaling technical infrastructure'
        }

        technical_achievement = await content_selector._select_pain_addressing_achievement(
            work_experience, strategic_metadata, technical_pain, parsed_recommendations
        )

        assert isinstance(technical_achievement, str)
        # Should select achievement relevant to technical scaling
        assert any(keyword in technical_achievement.lower() for keyword in [
            'system', 'performance', 'latency', 'distributed', 'requests'
        ])

        # Test operational pain point
        operational_pain = {
            'category': 'operational',
            'description': 'optimizing team performance'
        }

        operational_achievement = await content_selector._select_pain_addressing_achievement(
            work_experience, strategic_metadata, operational_pain, parsed_recommendations
        )

        assert isinstance(operational_achievement, str)
        # Should select achievement relevant to team/operational efficiency
        team_relevant = 'team' in operational_achievement.lower() or 'led' in operational_achievement.lower()
        efficiency_relevant = any(keyword in operational_achievement.lower() for keyword in [
            'efficiency', 'process', 'operational'
        ])
        assert team_relevant or efficiency_relevant

    @pytest.mark.asyncio
    async def test_bridge_skills_with_research_enhancement(self, content_selector, analyst_recommendations):
        """Test bridge skills selection enhanced with market research intelligence."""
        # Parse recommendations first
        parsed_recommendations = content_selector._parse_analyst_recommendations(analyst_recommendations)

        job_requirements = {
            'required_skills': ['Python', 'Leadership'],
            'role_title': 'Tech Lead'
        }

        # Mock research engine with trending skills data
        with patch('src.core.research_engine.get_research_engine') as mock_get_engine:
            mock_engine = MagicMock()
            mock_engine.get_skills_demand_intelligence = AsyncMock(return_value={
                'high_demand_skills': ['Python', 'Kubernetes', 'Machine Learning'],
                'emerging_skills': ['Terraform', 'AI/ML', 'DevOps'],
                'timestamp': 1234567890
            })
            mock_get_engine.return_value = mock_engine

            enhanced_skills = await content_selector._select_bridge_skills_with_research(
                parsed_recommendations, job_requirements, 'Technology'
            )

            assert isinstance(enhanced_skills, list)
            assert len(enhanced_skills) <= 3

            # Should include some leverage skills
            leverage_skills = analyst_recommendations['skill_quadrants']['leverage']
            has_leverage = any(skill in enhanced_skills for skill in leverage_skills)
            assert has_leverage

            # Research engine should be called for skills intelligence
            mock_engine.get_skills_demand_intelligence.assert_called_once()
            call_args = mock_engine.get_skills_demand_intelligence.call_args
            assert call_args[1]['industry'] == 'Technology'

    @pytest.mark.asyncio
    async def test_research_enhanced_pain_point_inference(self, content_selector):
        """Test pain point inference enhanced with company intelligence data."""
        company_intelligence = {
            'growth_areas': ['AI/ML', 'Cloud Infrastructure'],
            'challenges': ['Rapid scaling', 'Performance optimization'],
            'hiring_trends': {'focus_areas': ['Senior Engineers', 'Tech Leads']}
        }

        # Test AI/ML growth area enhancement
        ai_enhanced_pain = await content_selector._infer_pain_point_with_research(
            'Senior Software Engineer',
            'Technology',
            ['Scaling issues'],
            company_intelligence
        )

        assert ai_enhanced_pain['category'] == 'technical'
        # Should be enhanced with AI/ML context
        description = ai_enhanced_pain['description'].lower()
        context = ai_enhanced_pain['context'].lower()
        assert 'ai' in description or 'ml' in description or 'intelligent' in description
        assert 'ai' in context or 'machine learning' in context

        # Test scaling challenges enhancement
        scaling_company_intelligence = {
            'growth_areas': ['Enterprise Solutions'],
            'challenges': ['Rapid growth', 'Scaling operations'],
            'hiring_trends': {}
        }

        scaling_enhanced_pain = await content_selector._infer_pain_point_with_research(
            'Engineering Manager',
            'Technology',
            ['Team coordination'],
            scaling_company_intelligence
        )

        # Should be enhanced with scaling context
        enhanced_context = scaling_enhanced_pain['context'].lower()
        enhanced_detail = scaling_enhanced_pain['specific_detail'].lower()
        assert 'scaling' in enhanced_context or 'growth' in enhanced_context
        assert 'growth' in enhanced_detail or 'scaling' in enhanced_detail

    @pytest.mark.asyncio
    async def test_job_skills_optimization_edge_cases(self, content_selector, analyst_recommendations):
        """Test job skills optimization with various edge cases."""
        # Parse recommendations first
        parsed_recommendations = content_selector._parse_analyst_recommendations(analyst_recommendations)

        # Test with many skills (should filter intelligently)
        many_skills = [
            'Python', 'JavaScript', 'Java', 'C++', 'Go', 'Rust',
            'React', 'Angular', 'Vue', 'Django', 'Flask', 'FastAPI',
            'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'Terraform'
        ]

        optimized_many = await content_selector._optimize_job_skills(
            many_skills, parsed_recommendations
        )

        assert isinstance(optimized_many, list)
        assert len(optimized_many) <= 8  # Should limit to reasonable number

        # Should prioritize leverage skills
        leverage_skills = analyst_recommendations['skill_quadrants']['leverage']
        leverage_count = sum(1 for skill in optimized_many if skill in leverage_skills)
        assert leverage_count > 0

        # Test with no skills
        empty_optimized = await content_selector._optimize_job_skills(
            [], parsed_recommendations
        )
        assert isinstance(empty_optimized, list)
        assert len(empty_optimized) == 0

        # Test with skills matching de-emphasize quadrant
        de_emphasize_skills = analyst_recommendations['skill_quadrants']['de_emphasize']
        de_emphasize_optimized = await content_selector._optimize_job_skills(
            de_emphasize_skills, parsed_recommendations
        )

        # Should still return skills but with lower priority
        assert isinstance(de_emphasize_optimized, list)

    @pytest.mark.asyncio
    async def test_optimal_adjective_selection_intelligence(self, content_selector, analyst_recommendations):
        """Test intelligent adjective selection based on experience and role context."""
        # Parse recommendations first
        parsed_recommendations = content_selector._parse_analyst_recommendations(analyst_recommendations)

        # Test senior role targeting
        senior_job = {
            'role_title': 'Senior Software Engineer',
            'required_skills': ['Python', 'Leadership']
        }

        senior_adjective = await content_selector._select_optimal_adjective(
            8, parsed_recommendations, senior_job
        )
        assert senior_adjective in ['Strategic', 'Experienced', 'Senior', 'Expert']

        # Test lead role targeting
        lead_job = {
            'role_title': 'Tech Lead',
            'required_skills': ['Leadership', 'Architecture']
        }

        lead_adjective = await content_selector._select_optimal_adjective(
            6, parsed_recommendations, lead_job
        )
        assert lead_adjective in ['Strategic', 'Experienced', 'Senior']

        # Test principal/architect role targeting
        architect_job = {
            'role_title': 'Principal Engineer',
            'required_skills': ['Architecture', 'System Design']
        }

        architect_adjective = await content_selector._select_optimal_adjective(
            10, parsed_recommendations, architect_job
        )
        assert architect_adjective in ['Expert', 'Strategic', 'Senior']

        # Test with no job requirements (default behavior)
        default_adjective = await content_selector._select_optimal_adjective(
            5, parsed_recommendations, None
        )
        assert isinstance(default_adjective, str)
        assert len(default_adjective) > 0

    @pytest.mark.asyncio
    async def test_comprehensive_t_shaped_summary_edge_cases(self, content_selector, analyst_recommendations):
        """Test T-shaped summary creation with edge cases and comprehensive scenarios."""
        # Parse recommendations first
        parsed_recommendations = content_selector._parse_analyst_recommendations(analyst_recommendations)

        # Test with minimal profile data
        minimal_profile = {
            'work_experience': [],
            'strategic_metadata': {}
        }

        minimal_summary = await content_selector._create_t_shaped_summary(
            minimal_profile, parsed_recommendations, None
        )

        assert isinstance(minimal_summary, dict)
        # Should provide defaults when data is missing
        assert minimal_summary['core_competency_1'] == 'expertise'
        assert minimal_summary['core_competency_2'] == 'expertise'
        assert minimal_summary['core_technology'] == 'expertise'
        assert minimal_summary['years_experience'] == 0

        # Test with rich strategic metadata
        rich_profile = {
            'work_experience': [
                {'role_title': 'Senior Engineer', 'company': 'TechCorp'},
                {'role_title': 'Lead Developer', 'company': 'StartupXYZ'},
                {'role_title': 'Principal Architect', 'company': 'BigTech'}
            ],
            'strategic_metadata': {
                'core_competencies': ['Cloud Architecture', 'Team Leadership', 'System Design'],
                'quantified_achievements': [
                    'architected system serving 10M+ users',
                    'reduced infrastructure costs by 40%',
                    'led cross-functional team of 15 engineers'
                ]
            }
        }

        rich_summary = await content_selector._create_t_shaped_summary(
            rich_profile, parsed_recommendations,
            {'required_skills': ['Architecture', 'Leadership'], 'role_title': 'Principal Engineer'}
        )

        assert isinstance(rich_summary, dict)
        # Should use rich data when available
        assert rich_summary['core_competency_1'] in ['Cloud Architecture', 'Team Leadership', 'System Design']
        assert rich_summary['years_experience'] == 6  # 3 positions * 2 years each

        # Should select achievement with best alignment
        achievement = rich_summary['top_quantified_achievement']
        assert any(keyword in achievement for keyword in [
            'architected', 'reduced', 'led', '10M+', '40%', '15'
        ])

    @pytest.mark.asyncio
    async def test_industry_customization_with_research_intelligence(self, content_selector):
        """Test dynamic industry-specific customization using real-time research intelligence."""
        # Import the industry customization function
        from src.core.content_selector import customize_template_by_industry

        base_template_content = {
            'base_style': 'professional',
            'achievement_format': 'standard',
            'terminology_style': 'general'
        }

        # Test Technology industry with successful research
        with patch('src.core.research_engine.get_research_engine') as mock_get_engine:
            mock_engine = MagicMock()
            mock_engine.get_industry_intelligence = AsyncMock(return_value={
                'emphasis_areas': ['technical_skills', 'innovation', 'scalability'],
                'terminology_style': 'technical',
                'achievement_format': 'metric_driven',
                'keywords': ['performance', 'scalability', 'architecture'],
                'research_timestamp': 1234567890
            })
            mock_engine.get_ats_compliance_intelligence = AsyncMock(return_value={
                'requirements': {'keyword_density': 'high', 'section_order': 'skills_first'},
                'last_updated': 1234567890
            })
            mock_engine.get_skills_demand_intelligence = AsyncMock(return_value={
                'high_demand_skills': ['Python', 'Kubernetes', 'DevOps'],
                'emerging_skills': ['AI/ML', 'Edge Computing'],
                'timestamp': 1234567890
            })
            mock_get_engine.return_value = mock_engine

            # Test technology industry customization
            tech_customized = await customize_template_by_industry(
                base_template_content, 'Technology', 'senior', None
            )

            assert isinstance(tech_customized, dict)
            # Should include research-driven enhancements
            assert 'emphasis_areas' in tech_customized
            assert 'trending_skills' in tech_customized
            assert 'ats_requirements' in tech_customized
            assert '_research_metadata' in tech_customized

            # Should prioritize technical elements for technology industry
            assert 'technical_skills' in tech_customized['emphasis_areas']
            assert tech_customized['terminology_style'] == 'technical'
            assert tech_customized['achievement_format'] == 'metric_driven'

            # Should include market intelligence
            assert 'Python' in tech_customized['trending_skills']
            assert 'AI/ML' in tech_customized['emerging_skills']

            # Research engines should be called
            mock_engine.get_industry_intelligence.assert_called_once()
            mock_engine.get_ats_compliance_intelligence.assert_called_once()
            mock_engine.get_skills_demand_intelligence.assert_called_once()

        # Test Finance industry with different characteristics
        with patch('src.core.research_engine.get_research_engine') as mock_get_engine:
            mock_engine = MagicMock()
            mock_engine.get_industry_intelligence = AsyncMock(return_value={
                'emphasis_areas': ['regulatory_compliance', 'risk_management', 'financial_impact'],
                'terminology_style': 'business',
                'achievement_format': 'financial_impact',
                'keywords': ['compliance', 'risk', 'revenue', 'cost_reduction'],
                'research_timestamp': 1234567890
            })
            mock_engine.get_ats_compliance_intelligence = AsyncMock(return_value={
                'requirements': {'keyword_density': 'medium', 'compliance_focus': 'high'},
                'last_updated': 1234567890
            })
            mock_engine.get_skills_demand_intelligence = AsyncMock(return_value={
                'high_demand_skills': ['Risk Management', 'Compliance', 'Financial Analysis'],
                'emerging_skills': ['RegTech', 'FinTech', 'Blockchain'],
                'timestamp': 1234567890
            })
            mock_get_engine.return_value = mock_engine

            finance_customized = await customize_template_by_industry(
                base_template_content, 'Finance', 'executive', None
            )

            assert isinstance(finance_customized, dict)
            # Should customize for finance industry
            assert 'regulatory_compliance' in finance_customized['emphasis_areas']
            assert finance_customized['terminology_style'] == 'business'
            assert finance_customized['achievement_format'] == 'financial_impact'

            # Should include executive-level customizations
            assert finance_customized['focus_areas'] == ['vision', 'transformation', 'organizational_leadership', 'strategic_results']
            assert finance_customized['summary_style'] == 'executive_brief'

        # Test research failure fallback (static customizations)
        with patch('src.core.research_engine.get_research_engine') as mock_get_engine:
            mock_get_engine.side_effect = Exception("Research service unavailable")

            fallback_customized = await customize_template_by_industry(
                base_template_content, 'Healthcare', 'senior', None
            )

            assert isinstance(fallback_customized, dict)
            # Should fallback to static customizations for healthcare
            assert 'patient_outcomes' in fallback_customized['emphasis_areas']
            assert fallback_customized['terminology_style'] == 'clinical'
            assert fallback_customized['achievement_format'] == 'outcome_focused'

            # Should include senior-level static adjustments
            assert fallback_customized['focus_areas'] == ['leadership', 'strategic_impact', 'mentoring', 'complex_projects']
            assert fallback_customized['summary_style'] == 'comprehensive'

    @pytest.mark.asyncio
    async def test_comprehensive_edge_case_coverage(self, content_selector, analyst_recommendations):
        """Test remaining edge cases to achieve full coverage."""
        # Parse recommendations first
        parsed_recommendations = content_selector._parse_analyst_recommendations(analyst_recommendations)

        # Test empty accomplishments list edge case
        empty_accomplishments = []
        optimized_empty = await content_selector._optimize_accomplishments(
            empty_accomplishments, parsed_recommendations, None
        )
        assert isinstance(optimized_empty, list)
        assert len(optimized_empty) == 0

        # Test skills selection with empty job requirements but leverage skills available
        empty_job_skills = await content_selector._select_skills(
            {'technical_skills': {'programming': []}, 'soft_skills': []},
            parsed_recommendations,
            {'required_skills': [], 'role_title': ''}
        )
        assert isinstance(empty_job_skills, dict)
        assert 'core_skills' in empty_job_skills

        # Test project selection with empty projects
        empty_projects = await content_selector._select_projects(
            [], parsed_recommendations, {'required_skills': ['Python']}
        )
        assert isinstance(empty_projects, list)
        assert len(empty_projects) == 0

        # Test accomplishment relevance with empty keyword set
        relevance_empty_keywords = await content_selector._calculate_accomplishment_relevance(
            "Built amazing software system", set()
        )
        assert isinstance(relevance_empty_keywords, float)
        assert relevance_empty_keywords >= 0.0

        # Test job relevance calculation edge cases
        empty_job_entry = {'skills_used': [], 'accomplishments': []}
        job_relevance = await content_selector._calculate_job_relevance(
            empty_job_entry, parsed_recommendations, None
        )
        assert isinstance(job_relevance, float)
        assert job_relevance >= 0.0
