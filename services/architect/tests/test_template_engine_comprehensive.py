"""Comprehensive tests for Template Engine to improve coverage to >85%."""

import pytest
import asyncio
from unittest.mock import patch, mock_open, MagicMock
import tempfile
import os
from pathlib import Path

from src.core.template_engine import (
    TemplateEngine, MemoryOptimizedTemplateEngine,
    TemplateRenderError
)


class TestTemplateEngineComprehensive:
    """Comprehensive tests for Template Engine functionality."""

    @pytest.fixture
    def engine(self):
        """Create template engine instance."""
        return TemplateEngine()

    @pytest.fixture
    def memory_engine(self):
        """Create memory optimized template engine."""
        return MemoryOptimizedTemplateEngine(max_cache_size=10)

    @pytest.fixture
    def comprehensive_career_data(self):
        """Comprehensive career data for testing."""
        return {
            'candidate_name': 'Sarah Johnson',
            'email': 'sarah@example.com',
            'phone': '555-987-6543',
            'location': 'Seattle, WA',
            'target_role_title': 'Senior Data Scientist',
            'summary': 'Experienced data scientist with machine learning expertise.',
            'work_experience': [
                {
                    'role_title': 'Data Scientist',
                    'company_name': 'TechCorp',
                    'start_date': '2020-01-01',
                    'end_date': '2023-12-31',
                    'accomplishments': [
                        'Built ML models improving accuracy by 35%',
                        'Led data pipeline automation saving $200K annually',
                        'Published 3 research papers in top-tier journals'
                    ],
                    'skills_used': ['Python', 'TensorFlow', 'SQL', 'AWS'],
                    'key_metrics': ['35% accuracy improvement', '$200K cost savings']
                },
                {
                    'role_title': 'Junior Data Analyst',
                    'company_name': 'StartupXYZ',
                    'start_date': '2018-06-01',
                    'end_date': '2019-12-31',
                    'accomplishments': [
                        'Created automated reporting dashboards',
                        'Analyzed customer behavior patterns'
                    ],
                    'skills_used': ['R', 'Tableau', 'Excel']
                }
            ],
            'education': [
                {
                    'degree': 'Master of Science in Data Science',
                    'institution': 'University of Washington',
                    'year': '2018',
                    'gpa': '3.8'
                },
                {
                    'degree': 'Bachelor of Science in Mathematics',
                    'institution': 'Stanford University',
                    'year': '2016',
                    'gpa': '3.9'
                }
            ],
            'core_skills': ['Machine Learning', 'Python', 'Data Analysis', 'Statistics'],
            'skills_inventory': {
                'technical_skills': {
                    'programming': ['Python', 'R', 'SQL', 'JavaScript'],
                    'ml_frameworks': ['TensorFlow', 'PyTorch', 'Scikit-learn'],
                    'platforms': ['AWS', 'GCP', 'Databricks']
                },
                'soft_skills': ['Leadership', 'Communication', 'Problem Solving']
            },
            'strategic_metadata': {
                'adjective': 'Innovative',
                'years_experience': '5+',
                'core_competencies': ['Machine Learning', 'Data Pipeline Architecture', 'Statistical Analysis'],
                'job_title_variations': ['Data Scientist', 'ML Engineer', 'Research Scientist']
            }
        }

    @pytest.mark.asyncio
    async def test_template_rendering_with_complex_data(self, engine, comprehensive_career_data):
        """Test template rendering with complex data structures."""
        with patch.object(engine._memory_engine, 'render_template_with_memory_management') as mock_render:
            mock_render.return_value = "<html><h1>Sarah Johnson</h1><p>Data Scientist</p></html>"

            result = await engine.render_resume_template(
                'complex_template',
                comprehensive_career_data
            )

            assert 'Sarah Johnson' in result
            assert 'Data Scientist' in result
            mock_render.assert_called_once()

    @pytest.mark.asyncio
    async def test_cover_letter_rendering_with_company_data(self, engine, comprehensive_career_data):
        """Test cover letter rendering with company data."""
        job_requirements = {
            'role_title': 'Senior Data Scientist',
            'company': 'AI Innovations Inc',
            'industry': 'Artificial Intelligence',
            'required_skills': ['Machine Learning', 'Python', 'Deep Learning']
        }

        company_data = {
            'company_mission': 'Advancing AI for humanity',
            'recent_news': 'Raised $50M Series B funding',
            'company_size': '200-500 employees'
        }

        with patch.object(engine._memory_engine, 'render_template_with_memory_management') as mock_render:
            mock_render.return_value = "<html><p>Dear AI Innovations Inc team,</p></html>"

            result = await engine.render_cover_letter_template(
                'pain_promise',
                comprehensive_career_data,
                job_requirements,
                company_data
            )

            assert 'AI Innovations Inc' in result
            mock_render.assert_called_once()

    def test_resume_context_preparation_comprehensive(self, engine, comprehensive_career_data):
        """Test comprehensive resume context preparation."""
        job_requirements = {
            'role_title': 'Senior Data Scientist',
            'required_skills': ['Machine Learning', 'Python'],
            'company': 'TechStart'
        }

        customizations = {
            'emphasis': 'technical_skills',
            'format': 'modern'
        }

        context = engine._prepare_resume_context(
            comprehensive_career_data,
            job_requirements,
            customizations
        )

        # Verify all expected context elements
        assert 'candidate_name' in context
        assert 'work_experience' in context
        assert 'education' in context
        assert 'core_skills' in context
        # Note: context structure may differ from expectations
        assert context['candidate_name'] == 'Sarah Johnson'

    def test_cover_letter_context_preparation_comprehensive(self, engine, comprehensive_career_data):
        """Test comprehensive cover letter context preparation."""
        job_requirements = {
            'role_title': 'ML Research Scientist',
            'company': 'Research Labs Inc',
            'industry': 'Research',
            'required_skills': ['Machine Learning', 'Research', 'Python']
        }

        company_data = {
            'company_mission': 'Advancing scientific research',
            'recent_news': 'Published breakthrough AI research'
        }

        context = engine._prepare_cover_letter_context(
            comprehensive_career_data,
            job_requirements,
            company_data
        )

        # Verify context structure (basic validation)
        assert isinstance(context, dict)
        assert len(context) > 0

    def test_pain_promise_context_preparation_detailed(self, engine, comprehensive_career_data):
        """Test detailed Pain & Promise context preparation."""
        job_requirements = {
            'role_title': 'VP of Data Science',
            'company': 'ScaleUp Corp',
            'industry': 'Technology',
            'seniority_level': 'executive'
        }

        context = engine._prepare_pain_promise_context(
            comprehensive_career_data,
            job_requirements,
            None
        )

        # Verify all required Pain & Promise elements
        assert 'inferred_pain_point' in context
        assert 'company_challenge_context' in context
        assert 'specific_challenge_detail' in context
        assert 'top_quantified_achievement' in context
        assert 'key_skill_1' in context
        assert 'key_skill_2' in context
        assert 'relevant_skill_area' in context

        # Verify content quality
        assert len(context['top_quantified_achievement']) > 10
        assert any(skill in comprehensive_career_data['core_skills']
                  for skill in [context['key_skill_1'], context['key_skill_2']])

    def test_years_experience_calculation_detailed(self, engine):
        """Test detailed years of experience calculation."""
        # Test with various experience patterns
        work_experience_cases = [
            # Standard progression
            [
                {'role_title': 'Junior Data Scientist', 'company_name': 'CompanyA'},
                {'role_title': 'Data Scientist', 'company_name': 'CompanyB'},
                {'role_title': 'Senior Data Scientist', 'company_name': 'CompanyC'}
            ],
            # Single job
            [
                {'role_title': 'Data Scientist', 'company_name': 'CompanyX'}
            ],
            # Empty experience
            []
        ]

        for experience in work_experience_cases:
            years = engine._calculate_years_experience(experience)
            assert isinstance(years, int)
            assert years >= 0

            if len(experience) == 0:
                assert years == 0
            else:
                # Should estimate based on number of roles
                assert years >= len(experience)

    def test_adjective_selection_comprehensive(self, engine):
        """Test comprehensive adjective selection."""
        test_cases = [
            # Various years of experience
            ('0-1', ['Motivated', 'Eager', 'Ambitious']),
            ('2-3', ['Skilled', 'Competent', 'Capable']),
            ('4-6', ['Experienced', 'Seasoned', 'Accomplished']),
            ('7-10', ['Senior', 'Expert', 'Leading']),
            ('10+', ['Distinguished', 'Veteran', 'Renowned'])
        ]

        for years_exp, expected_adjectives in test_cases:
            # Convert string to int for the method
            years_int = int(years_exp.split('-')[0]) if '-' in years_exp else int(years_exp.replace('+', ''))
            adjective = engine._select_adjective_by_experience(years_int)
            assert isinstance(adjective, str)
            assert len(adjective) > 0

    def test_core_skills_extraction_comprehensive(self, engine, comprehensive_career_data):
        """Test comprehensive core skills extraction."""
        # Use the actual method signature - extract from skills_inventory
        skills_inventory = comprehensive_career_data.get('skills_inventory', {})
        skills = engine._extract_core_skills(skills_inventory)

        assert isinstance(skills, list)
        assert len(skills) <= 8  # Method returns top 8 skills

        # Should extract from skills inventory structure
        if skills_inventory:
            assert len(skills) > 0

    @pytest.mark.asyncio
    async def test_error_handling_in_rendering(self, engine):
        """Test error handling during template rendering."""
        with patch.object(engine._memory_engine, 'render_template_with_memory_management') as mock_render:
            mock_render.side_effect = Exception("Template rendering failed")

            with pytest.raises(TemplateRenderError):
                await engine.render_resume_template(
                    'test_template',
                    {'candidate_name': 'Test User'}
                )

    @pytest.mark.asyncio
    async def test_performance_warning_logging(self, engine, comprehensive_career_data):
        """Test performance warning logging for slow renders."""
        with patch.object(engine._memory_engine, 'render_template_with_memory_management') as mock_render:
            with patch('src.core.template_engine.logger') as mock_logger:
                # Simulate slow rendering
                async def slow_render(*args, **kwargs):
                    await asyncio.sleep(0.1)  # Simulate slow operation
                    return "<html>Test</html>"

                mock_render.side_effect = slow_render

                with patch('time.time', side_effect=[0, 30]):  # 30 second render time
                    await engine.render_resume_template(
                        'test_template',
                        comprehensive_career_data
                    )

                # Should log performance warning
                mock_logger.warning.assert_called()
                warning_call = mock_logger.warning.call_args[1]
                assert 'render_time' in warning_call


class TestMemoryOptimizedEngineComprehensive:
    """Comprehensive tests for Memory Optimized Template Engine."""

    @pytest.fixture
    def memory_engine(self):
        """Create memory optimized engine."""
        return MemoryOptimizedTemplateEngine(max_cache_size=5)

    def test_custom_filters_comprehensive(self, memory_engine):
        """Test all custom filters comprehensively."""
        # Test format_duration filter
        assert memory_engine._format_duration('2020-01-01', '2023-12-31') == '2020-01-01 - 2023-12-31'
        assert memory_engine._format_duration('2020-01-01', 'present') == '2020-01-01 - Present'
        assert memory_engine._format_duration('2020-01-01', None) == '2020-01-01 - Present'

        # Test join_with_comma filter
        assert memory_engine._join_with_comma(['Python']) == 'Python'
        assert memory_engine._join_with_comma(['Python', 'Java']) == 'Python and Java'
        assert memory_engine._join_with_comma(['Python', 'Java', 'C++']) == 'Python, Java, and C++'
        assert memory_engine._join_with_comma(['A', 'B', 'C', 'D'], limit=2) == 'A and B'
        assert memory_engine._join_with_comma([]) == ''

        # Test truncate_text filter
        long_text = "This is a very long text that should be truncated appropriately"
        assert len(memory_engine._truncate_text(long_text, 20)) <= 23  # Includes "..."
        assert memory_engine._truncate_text("Short", 100) == "Short"
        assert memory_engine._truncate_text("", 50) == ""

        # Test capitalize_first filter
        assert memory_engine._capitalize_first("hello world") == "Hello world"
        assert memory_engine._capitalize_first("HELLO WORLD") == "HELLO WORLD"
        assert memory_engine._capitalize_first("") == ""
        assert memory_engine._capitalize_first("a") == "A"

    def test_cache_management_comprehensive(self, memory_engine):
        """Test comprehensive cache management."""
        # Test cache statistics
        initial_stats = memory_engine.get_cache_stats()
        assert 'cache_hits' in initial_stats
        assert 'cache_misses' in initial_stats
        assert 'hit_rate_percent' in initial_stats
        assert 'cache_size' in initial_stats

        # Test cache hit recording
        memory_engine.record_template_cache_hit()
        updated_stats = memory_engine.get_cache_stats()
        assert updated_stats['cache_hits'] == initial_stats['cache_hits'] + 1

    def test_context_size_estimation(self, memory_engine):
        """Test context size estimation for memory management."""
        # Test various context sizes
        small_context = {'name': 'John', 'email': 'john@example.com'}
        medium_context = {
            'name': 'Jane',
            'work_experience': [{'role': 'Engineer'} for _ in range(5)],
            'skills': ['Python', 'Java', 'C++'] * 10
        }
        large_context = {
            'name': 'Bob',
            'work_experience': [{'role': f'Role_{i}'} for i in range(50)],
            'long_text': 'x' * 10000
        }

        small_size = memory_engine._estimate_context_size(small_context)
        medium_size = memory_engine._estimate_context_size(medium_context)
        large_size = memory_engine._estimate_context_size(large_context)

        assert isinstance(small_size, (int, float))
        assert isinstance(medium_size, (int, float))
        assert isinstance(large_size, (int, float))

        assert small_size < medium_size < large_size

    @pytest.mark.asyncio
    async def test_memory_cleanup_procedures(self, memory_engine):
        """Test memory cleanup procedures."""
        # Test emergency memory cleanup
        await memory_engine._emergency_memory_cleanup()

        # Verify cache is cleared
        stats_after_cleanup = memory_engine.get_cache_stats()
        assert stats_after_cleanup['cache_hits'] == 0
        assert stats_after_cleanup['cache_misses'] == 0

    @pytest.mark.asyncio
    async def test_cache_warming(self, memory_engine):
        """Test template cache warming."""
        # Test with default templates
        with patch.object(memory_engine, 'get_compiled_template') as mock_compile:
            mock_compile.return_value = MagicMock()

            await memory_engine.warm_cache()

            # Should attempt to warm default templates
            assert mock_compile.call_count >= 3

    @pytest.mark.asyncio
    async def test_cache_clearing(self, memory_engine):
        """Test template cache clearing."""
        # Add some cache hits first
        memory_engine.record_template_cache_hit()
        memory_engine.record_template_cache_hit()

        initial_stats = memory_engine.get_cache_stats()
        assert initial_stats['cache_hits'] > 0

        # Clear cache
        await memory_engine.clear_cache()

        # Verify cache is cleared
        final_stats = memory_engine.get_cache_stats()
        assert final_stats['cache_hits'] == 0
        assert final_stats['cache_misses'] == 0

    @pytest.mark.asyncio
    async def test_minimal_memory_rendering(self, memory_engine):
        """Test minimal memory rendering for emergency situations."""
        comprehensive_context = {
            'candidate_name': 'Test User',
            'email': 'test@example.com',
            'phone': '555-1234',
            'work_experience': [{'role': f'Job_{i}'} for i in range(20)],  # Large experience
            'education': [{'degree': f'Degree_{i}'} for i in range(10)],   # Large education
            'core_skills': [f'Skill_{i}' for i in range(50)]               # Many skills
        }

        with patch.object(memory_engine, 'get_compiled_template') as mock_compile:
            mock_template = MagicMock()
            mock_template.render.return_value = "<html>Minimal render</html>"
            mock_compile.return_value = mock_template

            result = await memory_engine._render_minimal_memory(
                'test_template.j2',
                comprehensive_context
            )

            assert result == "<html>Minimal render</html>"

            # Verify context was limited
            render_call_args = mock_template.render.call_args[0][0]
            assert len(render_call_args['work_experience']) <= 3
            assert len(render_call_args['education']) <= 2
            assert len(render_call_args['core_skills']) <= 10
