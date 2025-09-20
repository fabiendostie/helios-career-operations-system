"""Tests for template engine functionality."""

import pytest
import asyncio
from unittest.mock import patch, mock_open
import tempfile
import os
from pathlib import Path

from src.core.template_engine import (
    TemplateEngine, MemoryOptimizedTemplateEngine, 
    TemplateRenderError
)


class TestMemoryOptimizedTemplateEngine:
    """Test memory optimized template engine."""
    
    @pytest.fixture
    def engine(self):
        """Create template engine instance."""
        return MemoryOptimizedTemplateEngine(max_cache_size=10)
    
    @pytest.fixture
    def sample_career_data(self):
        """Sample career data for testing."""
        return {
            'candidate_name': 'John Smith',
            'email': 'john@example.com',
            'phone': '555-123-4567',
            'location': 'San Francisco, CA',
            'work_experience': [
                {
                    'role_title': 'Senior Software Engineer',
                    'company_name': 'TechCorp',
                    'start_date': '2020-01-01',
                    'end_date': '2023-12-31',
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
            'skills_inventory': {
                'technical_skills': {
                    'programming': ['Python', 'JavaScript', 'Go'],
                    'platforms': ['AWS', 'Kubernetes', 'Docker']
                },
                'soft_skills': ['Leadership', 'Communication']
            }
        }
    
    @pytest.mark.asyncio
    async def test_template_compilation(self, engine):
        """Test template compilation with caching."""
        template_content = "<h1>{{ name }}</h1>"
        
        with patch('builtins.open', mock_open(read_data=template_content)):
            with patch('os.path.exists', return_value=True):
                template1 = engine.get_compiled_template('test.j2')
                template2 = engine.get_compiled_template('test.j2')
                
                # Should return the same cached template
                assert template1 is template2
    
    @pytest.mark.asyncio
    async def test_template_rendering_with_context(self, engine):
        """Test template rendering with context data."""
        template_content = "<h1>Hello {{ name }}!</h1><p>Age: {{ age }}</p>"
        
        with patch('builtins.open', mock_open(read_data=template_content)):
            with patch('os.path.exists', return_value=True):
                with patch('os.path.join', return_value='/fake/path/test.j2'):
                    result = await engine.render_template_with_memory_management(
                        'test.j2',
                        {'name': 'John', 'age': 30}
                    )
                    
                    assert 'Hello John!' in result
                    assert 'Age: 30' in result
    
    @pytest.mark.asyncio
    async def test_memory_cleanup_on_large_context(self, engine):
        """Test memory cleanup for large contexts."""
        template_content = "{% for item in items %}{{ item.name }}{% endfor %}"
        
        # Create large context to trigger streaming
        large_context = {
            'items': [{'name': f'item_{i}'} for i in range(100)]
        }
        
        with patch('builtins.open', mock_open(read_data=template_content)):
            with patch('os.path.exists', return_value=True):
                with patch('os.path.join', return_value='/fake/path/test.j2'):
                    with patch.object(engine, '_estimate_context_size', return_value=100):
                        result = await engine.render_template_with_memory_management(
                            'test.j2',
                            large_context
                        )
                        
                        # Should complete without memory errors
                        assert 'item_0' in result
                        assert 'item_99' in result
    
    def test_custom_filters(self, engine):
        """Test custom Jinja2 filters."""
        # Test format_duration filter
        result = engine._format_duration('2020-01', '2023-12')
        assert result == '2020-01 - 2023-12'
        
        result = engine._format_duration('2020-01', None)
        assert result == '2020-01 - Present'
        
        # Test join_with_comma filter
        result = engine._join_with_comma(['Python', 'JavaScript', 'Go'])
        assert result == 'Python, JavaScript, and Go'
        
        result = engine._join_with_comma(['Python', 'JavaScript'])
        assert result == 'Python and JavaScript'
        
        result = engine._join_with_comma(['Python'])
        assert result == 'Python'
        
        # Test truncate_text filter
        long_text = "This is a very long text that should be truncated properly"
        result = engine._truncate_text(long_text, 30)
        assert len(result) <= 33  # 30 + "..."
        assert result.endswith('...')
    
    def test_cache_statistics(self, engine):
        """Test cache statistics tracking."""
        stats = engine.get_cache_stats()
        
        assert 'cache_hits' in stats
        assert 'cache_misses' in stats
        assert 'hit_rate_percent' in stats
        assert 'cache_size' in stats
        
        # Initially should be 0/0
        assert stats['cache_hits'] == 0
        assert stats['cache_misses'] >= 0


class TestTemplateEngine:
    """Test high-level template engine interface."""
    
    @pytest.fixture
    def engine(self):
        """Create template engine instance."""
        return TemplateEngine()
    
    @pytest.fixture
    def sample_career_data(self):
        """Sample career data for testing."""
        return {
            'candidate_name': 'Jane Doe',
            'email': 'jane@example.com',
            'phone': '555-987-6543',
            'location': 'New York, NY',
            'work_experience': [
                {
                    'role_title': 'Product Manager',
                    'company_name': 'InnovateCorp',
                    'start_date': '2019-03-01',
                    'end_date': 'Present',
                    'accomplishments': [
                        'Launched 3 major product features increasing user engagement by 45%',
                        'Managed cross-functional team of 12 professionals'
                    ],
                    'skills_used': ['Product Strategy', 'Agile', 'Analytics']
                }
            ],
            'education': [
                {
                    'degree': 'MBA',
                    'institution': 'Harvard Business School',
                    'year': '2019'
                }
            ],
            'skills_inventory': {
                'technical_skills': {
                    'analytics': ['Tableau', 'SQL', 'Python'],
                    'tools': ['Jira', 'Confluence', 'Figma']
                },
                'soft_skills': ['Leadership', 'Strategic Thinking', 'Communication']
            },
            'strategic_metadata': {
                'core_competencies': ['Product Strategy', 'Team Leadership', 'Data Analysis'],
                'quantified_achievements': [
                    'increased user engagement by 45%',
                    'managed cross-functional team of 12 professionals'
                ]
            }
        }
    
    @pytest.mark.asyncio
    async def test_resume_template_rendering(self, engine, sample_career_data):
        """Test resume template rendering."""
        template_content = """
        <h1>{{ candidate_name }}</h1>
        <p>{{ email }} | {{ phone }}</p>
        <h2>Experience</h2>
        {% for job in work_experience %}
        <h3>{{ job.role_title }} - {{ job.company_name }}</h3>
        {% endfor %}
        """
        
        with patch.object(engine._memory_engine, 'render_template_with_memory_management') as mock_render:
            # Create a realistic rendered output
            mock_render.return_value = f"""
        <h1>{sample_career_data['candidate_name']}</h1>
        <p>{sample_career_data['email']} | {sample_career_data['phone']}</p>
        <h2>Experience</h2>
        <h3>Product Manager - Innovation Corp</h3>
        """
            
            result = await engine.render_resume_template(
                'test_template',
                sample_career_data
            )
            
            assert sample_career_data['candidate_name'] in result
            assert sample_career_data['email'] in result
            mock_render.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cover_letter_template_rendering(self, engine, sample_career_data):
        """Test cover letter template rendering."""
        job_requirements = {
            'role_title': 'Senior Product Manager',
            'company': 'TechStart Inc',
            'required_skills': ['Product Strategy', 'Analytics', 'Leadership']
        }
        
        template_content = """
        <h1>{{ candidate_name }}</h1>
        <p>Dear Hiring Manager,</p>
        <p>I am interested in the {{ role_title }} position at {{ company_name }}.</p>
        """
        
        with patch.object(engine._memory_engine, 'render_template_with_memory_management') as mock_render:
            mock_render.return_value = template_content
            
            result = await engine.render_cover_letter_template(
                'pain_promise',
                sample_career_data,
                job_requirements
            )
            
            mock_render.assert_called_once()
            call_args = mock_render.call_args[0]
            context = call_args[1]
            
            assert context['candidate_name'] == sample_career_data['candidate_name']
            assert context['role_title'] == job_requirements['role_title']
            assert context['company_name'] == job_requirements['company']
    
    def test_t_shaped_context_preparation(self, engine, sample_career_data):
        """Test T-shaped resume context preparation."""
        context = engine._prepare_t_shaped_context(sample_career_data)
        
        assert 'target_role_title' in context
        assert 'adjective' in context
        assert 'years_experience' in context
        assert 'core_competency_1' in context
        assert 'core_competency_2' in context
        assert 'core_technology' in context
        assert 'top_quantified_achievement' in context
        assert 'skill_area' in context
        
        # Check that quantified achievement is properly selected
        assert context['top_quantified_achievement'] in [
            'increased user engagement by 45%',
            'managed cross-functional team of 12 professionals'
        ]
    
    def test_pain_promise_context_preparation(self, engine, sample_career_data):
        """Test Pain & Promise cover letter context preparation."""
        job_requirements = {
            'role_title': 'VP of Product',
            'company': 'ScaleUp Corp',
            'industry': 'Technology'
        }
        
        context = engine._prepare_pain_promise_context(
            sample_career_data,
            job_requirements,
            None
        )
        
        assert 'inferred_pain_point' in context
        assert 'company_challenge_context' in context
        assert 'specific_challenge_detail' in context
        assert 'top_quantified_achievement' in context
        assert 'key_skill_1' in context
        assert 'key_skill_2' in context
        assert 'relevant_skill_area' in context
        
        # Should infer appropriate pain point for VP role
        pain_point = context['inferred_pain_point'].lower()
        assert any(keyword in pain_point for keyword in ['efficiency', 'performance', 'scaling', 'growth', 'operations'])
    
    def test_years_experience_calculation(self, engine):
        """Test years of experience calculation."""
        work_experience = [
            {'role_title': 'Junior Dev', 'company_name': 'StartupA'},
            {'role_title': 'Senior Dev', 'company_name': 'CompanyB'},
            {'role_title': 'Tech Lead', 'company_name': 'CompanyC'}
        ]
        
        years = engine._calculate_years_experience(work_experience)
        
        # Should be 3 positions * 2 years = 6 years
        assert years == 6
        
        # Test empty experience
        assert engine._calculate_years_experience([]) == 0
        
        # Test cap at 20 years
        many_jobs = [{'role_title': f'Job {i}'} for i in range(15)]
        assert engine._calculate_years_experience(many_jobs) == 20
    
    def test_adjective_selection_by_experience(self, engine):
        """Test adjective selection based on experience level."""
        assert engine._select_adjective_by_experience(1) == "Motivated"
        assert engine._select_adjective_by_experience(5) == "Experienced"
        assert engine._select_adjective_by_experience(10) == "Senior"
        assert engine._select_adjective_by_experience(15) == "Strategic"
    
    def test_core_skills_extraction(self, engine):
        """Test core skills extraction from skills inventory."""
        skills_inventory = {
            'technical_skills': {
                'programming': ['Python', 'Java', 'JavaScript'],
                'platforms': ['AWS', 'Azure'],
                'tools': ['Docker', 'Kubernetes']
            },
            'soft_skills': ['Leadership', 'Communication', 'Problem Solving']
        }
        
        core_skills = engine._extract_core_skills(skills_inventory)
        
        # Should get top 8 skills
        assert len(core_skills) <= 8
        assert 'Python' in core_skills
        assert 'Leadership' in core_skills
        
        # Test with empty inventory
        empty_skills = engine._extract_core_skills({})
        assert len(empty_skills) == 0
    
    @pytest.mark.asyncio
    async def test_template_error_handling(self, engine, sample_career_data):
        """Test error handling in template rendering."""
        with patch.object(engine._memory_engine, 'render_template_with_memory_management') as mock_render:
            mock_render.side_effect = Exception("Template rendering failed")
            
            with pytest.raises(TemplateRenderError):
                await engine.render_resume_template(
                    'invalid_template',
                    sample_career_data
                )
    
    @pytest.mark.asyncio
    async def test_cache_management(self, engine):
        """Test template cache management."""
        # Test cache warming
        with patch.object(engine._memory_engine, 'get_compiled_template') as mock_compile:
            await engine.warm_cache()
            
            # Should attempt to warm common templates
            assert mock_compile.call_count >= 4  # At least 4 default templates
        
        # Test cache clearing
        await engine.clear_cache()
        
        cache_stats = engine.get_cache_stats()
        assert cache_stats['cache_hits'] == 0
        assert cache_stats['cache_misses'] == 0


@pytest.mark.asyncio
async def test_template_integration_with_real_files():
    """Integration test with actual template files."""
    # This test would require actual template files
    # For now, we'll test the file path resolution
    
    engine = MemoryOptimizedTemplateEngine()
    
    # Test that template path resolution works
    with patch('os.path.exists', return_value=False):
        with pytest.raises(TemplateRenderError):
            engine.get_compiled_template('nonexistent.j2')


if __name__ == '__main__':
    pytest.main([__file__])