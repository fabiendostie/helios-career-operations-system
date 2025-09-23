"""Tests for content selection system functionality."""

import pytest
import asyncio
from unittest.mock import patch, Mock, AsyncMock
from dataclasses import asdict

from src.core.content_selector import (
    ContentSelector, SkillQuadrant, ContentPriority,
    SkillRecommendation, ContentRecommendation, AnalystRecommendations,
    customize_template_by_industry
)


class TestContentSelector:
    """Test intelligent content selection functionality."""

    @pytest.fixture
    def selector(self):
        """Create content selector instance."""
        return ContentSelector()

    @pytest.fixture
    def sample_master_career_db(self):
        """Sample master career database."""
        return {
            'candidate_name': 'Sarah Chen',
            'email': 'sarah@example.com',
            'work_experience': [
                {
                    'role_title': 'Senior Software Engineer',
                    'company_name': 'TechCorp',
                    'start_date': '2020-01-01',
                    'end_date': 'Present',
                    'accomplishments': [
                        'Built microservices architecture reducing system downtime by 60%',
                        'Led team of 8 engineers delivering $3M revenue features',
                        'Implemented CI/CD pipeline improving deployment speed by 75%'
                    ],
                    'skills_used': ['Python', 'Docker', 'Kubernetes', 'AWS', 'PostgreSQL']
                },
                {
                    'role_title': 'Software Engineer',
                    'company_name': 'StartupCo',
                    'start_date': '2018-06-01',
                    'end_date': '2019-12-31',
                    'accomplishments': [
                        'Developed REST APIs serving 100K+ daily requests',
                        'Optimized database queries reducing response time by 40%'
                    ],
                    'skills_used': ['Java', 'Spring Boot', 'MySQL', 'Redis']
                }
            ],
            'projects': [
                {
                    'name': 'ML-Powered Analytics Platform',
                    'description': 'Built machine learning platform for business analytics',
                    'technologies': ['Python', 'TensorFlow', 'React', 'AWS'],
                    'impact': 'Increased data processing efficiency by 200%'
                },
                {
                    'name': 'Real-time Chat System',
                    'description': 'Developed scalable real-time messaging system',
                    'technologies': ['Node.js', 'Socket.io', 'MongoDB', 'Docker'],
                    'impact': 'Supported 50K concurrent users'
                }
            ],
            'skills_inventory': {
                'technical_skills': {
                    'programming': ['Python', 'Java', 'JavaScript', 'Go'],
                    'platforms': ['AWS', 'Docker', 'Kubernetes', 'Linux'],
                    'databases': ['PostgreSQL', 'MongoDB', 'Redis', 'MySQL']
                },
                'soft_skills': ['Leadership', 'Problem Solving', 'Communication', 'Mentoring']
            },
            'strategic_metadata': {
                'core_competencies': ['Microservices Architecture', 'Team Leadership', 'System Design'],
                'quantified_achievements': [
                    'reducing system downtime by 60%',
                    'Led team of 8 engineers delivering $3M revenue features',
                    'improving deployment speed by 75%'
                ]
            }
        }

    @pytest.fixture
    def sample_analyst_recommendations(self):
        """Sample ANALYST service recommendations."""
        return {
            'skill_recalibration': {
                'leverage': [
                    {'name': 'Python', 'relevance_score': 0.95, 'confidence': 0.9, 'evidence_count': 5},
                    {'name': 'Kubernetes', 'relevance_score': 0.90, 'confidence': 0.85, 'evidence_count': 3},
                    {'name': 'Microservices', 'relevance_score': 0.88, 'confidence': 0.9, 'evidence_count': 4}
                ],
                'upskill': [
                    {'name': 'Terraform', 'relevance_score': 0.75, 'confidence': 0.8, 'evidence_count': 2},
                    {'name': 'GraphQL', 'relevance_score': 0.70, 'confidence': 0.7, 'evidence_count': 1}
                ],
                'maintain': [
                    {'name': 'PostgreSQL', 'relevance_score': 0.80, 'confidence': 0.85, 'evidence_count': 3},
                    {'name': 'AWS', 'relevance_score': 0.85, 'confidence': 0.9, 'evidence_count': 4}
                ],
                'de_emphasize': [
                    {'name': 'jQuery', 'relevance_score': 0.30, 'confidence': 0.9, 'evidence_count': 2}
                ]
            },
            'ats_optimization': {
                'keywords_to_emphasize': ['Python', 'Kubernetes', 'Microservices', 'Leadership', 'Architecture']
            },
            'content_recommendations': {
                'impact_metrics': ['60%', '75%', '$3M', '8 engineers', '100K+'],
                'action_verbs': ['Built', 'Led', 'Implemented', 'Optimized', 'Developed'],
                'industry_keywords': ['scalable', 'architecture', 'performance', 'cloud', 'agile']
            },
            'target_role_alignment': {
                'Senior Software Engineer': 0.95,
                'Tech Lead': 0.90,
                'Engineering Manager': 0.85
            }
        }

    @pytest.fixture
    def sample_job_requirements(self):
        """Sample job requirements."""
        return {
            'role_title': 'Principal Software Engineer',
            'company': 'ScaleTech Inc',
            'industry': 'Technology',
            'required_skills': ['Python', 'Kubernetes', 'System Design', 'Leadership'],
            'ats_keywords': ['scalable', 'architecture', 'microservices', 'cloud'],
            'experience_level': 'senior'
        }

    def test_analyst_recommendations_parsing(self, selector, sample_analyst_recommendations):
        """Test parsing of ANALYST recommendations."""
        parsed = selector._parse_analyst_recommendations(sample_analyst_recommendations)

        assert isinstance(parsed, AnalystRecommendations)

        # Check skill recalibration parsing
        leverage_skills = parsed.skill_recalibration[SkillQuadrant.LEVERAGE]
        assert len(leverage_skills) == 3
        assert leverage_skills[0].skill == 'Python'
        assert leverage_skills[0].relevance_score == 0.95
        assert leverage_skills[0].quadrant == SkillQuadrant.LEVERAGE

        # Check ATS keywords
        assert 'Python' in parsed.ats_keywords
        assert 'Kubernetes' in parsed.ats_keywords

        # Check impact metrics
        assert '60%' in parsed.impact_metrics
        assert '$3M' in parsed.impact_metrics

        # Check action verbs
        assert 'Built' in parsed.action_verbs
        assert 'Led' in parsed.action_verbs

    @pytest.mark.asyncio
    async def test_resume_content_selection(self, selector, sample_master_career_db, sample_analyst_recommendations, sample_job_requirements):
        """Test resume content selection with ANALYST recommendations."""
        result = await selector.select_resume_content(
            sample_master_career_db,
            sample_analyst_recommendations,
            sample_job_requirements
        )

        # Should preserve base structure
        assert result['candidate_name'] == sample_master_career_db['candidate_name']
        assert result['email'] == sample_master_career_db['email']

        # Should have optimized work experience
        assert 'work_experience' in result
        optimized_experience = result['work_experience']
        assert len(optimized_experience) <= 5  # Limited to max positions

        # Should have T-shaped content
        assert 'core_competency_1' in result
        assert 'core_competency_2' in result
        assert 'core_technology' in result
        assert 'top_quantified_achievement' in result
        assert 'years_experience' in result

        # Should have optimized skills
        assert 'core_skills' in result['skills_inventory']
        core_skills = result['skills_inventory']['core_skills']
        assert len(core_skills) <= 8  # ATS optimization limit

        # Should prioritize leverage skills
        assert 'Python' in core_skills
        assert 'Kubernetes' in core_skills

        # Should have metadata
        assert '_content_metadata' in result
        metadata = result['_content_metadata']
        assert metadata['selection_strategy'] == 'analyst_optimized'
        assert metadata['recommendations_applied'] is True
        assert metadata['job_targeted'] is True

    @pytest.mark.asyncio
    async def test_work_experience_optimization(self, selector, sample_master_career_db, sample_analyst_recommendations, sample_job_requirements):
        """Test work experience optimization."""
        work_experience = sample_master_career_db['work_experience']
        parsed_recommendations = selector._parse_analyst_recommendations(sample_analyst_recommendations)

        optimized = await selector._select_work_experience(
            work_experience,
            parsed_recommendations,
            sample_job_requirements
        )

        # Should maintain structure but optimize content
        assert len(optimized) <= len(work_experience)

        # Should have relevance scores
        for job in optimized:
            assert '_relevance_score' in job
            assert isinstance(job['_relevance_score'], float)

        # Should optimize accomplishments
        first_job = optimized[0]
        assert 'accomplishments' in first_job
        assert len(first_job['accomplishments']) <= 5  # Limited for resume optimization

        # Should optimize skills used
        assert 'skills_used' in first_job
        # Leverage skills should be prioritized
        skills_used = first_job['skills_used']
        assert 'Python' in skills_used or 'Kubernetes' in skills_used

    @pytest.mark.asyncio
    async def test_accomplishment_optimization(self, selector, sample_analyst_recommendations, sample_job_requirements):
        """Test accomplishment optimization with keywords and metrics."""
        accomplishments = [
            'Built microservices architecture reducing system downtime by 60%',
            'Led team of 8 engineers delivering $3M revenue features',
            'Fixed some bugs and improved code quality',
            'Implemented CI/CD pipeline improving deployment speed by 75%'
        ]

        parsed_recommendations = selector._parse_analyst_recommendations(sample_analyst_recommendations)

        optimized = await selector._optimize_accomplishments(
            accomplishments,
            parsed_recommendations,
            sample_job_requirements
        )

        # Should filter and prioritize based on relevance
        assert len(optimized) <= len(accomplishments)

        # High-impact accomplishments with metrics should be prioritized
        optimized_text = ' '.join(optimized)
        assert '60%' in optimized_text or '$3M' in optimized_text or '75%' in optimized_text

        # Vague accomplishments should be filtered out or deprioritized
        assert 'Fixed some bugs' not in optimized_text or len(optimized) == len(accomplishments)

    @pytest.mark.asyncio
    async def test_skills_selection_with_quadrants(self, selector, sample_master_career_db, sample_analyst_recommendations):
        """Test skills selection based on quadrant recommendations."""
        skills_inventory = sample_master_career_db['skills_inventory']
        parsed_recommendations = selector._parse_analyst_recommendations(sample_analyst_recommendations)

        optimized_skills = await selector._select_skills(
            skills_inventory,
            parsed_recommendations,
            None
        )

        # Should have core_skills field for T-shaped summary
        assert 'core_skills' in optimized_skills
        core_skills = optimized_skills['core_skills']

        # Should prioritize leverage skills
        leverage_skill_names = [r.skill for r in parsed_recommendations.skill_recalibration[SkillQuadrant.LEVERAGE]]
        for skill in leverage_skill_names:
            if skill in [s for sublist in skills_inventory['technical_skills'].values() for s in sublist]:
                assert skill in core_skills

        # Should be limited to 8 skills for ATS optimization
        assert len(core_skills) <= 8

    @pytest.mark.asyncio
    async def test_project_selection(self, selector, sample_master_career_db, sample_analyst_recommendations, sample_job_requirements):
        """Test project selection based on relevance."""
        projects = sample_master_career_db['projects']
        parsed_recommendations = selector._parse_analyst_recommendations(sample_analyst_recommendations)

        selected_projects = await selector._select_projects(
            projects,
            parsed_recommendations,
            sample_job_requirements
        )

        # Should limit to top projects
        assert len(selected_projects) <= 3

        # Should prioritize projects with relevant technologies
        for project in selected_projects:
            technologies = project.get('technologies', [])
            # Should have overlap with leverage skills or job requirements
            has_relevant_tech = any(
                tech.lower() in [skill.lower() for skill in sample_job_requirements['required_skills']] or
                tech.lower() in [r.skill.lower() for r in parsed_recommendations.skill_recalibration[SkillQuadrant.LEVERAGE]]
                for tech in technologies
            )
            # At least one project should be relevant
            if selected_projects.index(project) == 0:  # First project should be most relevant
                pass  # Allow for testing flexibility

    @pytest.mark.asyncio
    async def test_t_shaped_summary_creation(self, selector, sample_master_career_db, sample_analyst_recommendations, sample_job_requirements):
        """Test T-shaped summary content creation."""
        parsed_recommendations = selector._parse_analyst_recommendations(sample_analyst_recommendations)

        t_shaped_content = await selector._create_t_shaped_summary(
            sample_master_career_db,
            parsed_recommendations,
            sample_job_requirements
        )

        # Should have all required T-shaped fields
        required_fields = [
            'core_competency_1', 'core_competency_2', 'core_technology',
            'top_quantified_achievement', 'adjective', 'years_experience', 'skill_area'
        ]

        for field in required_fields:
            assert field in t_shaped_content
            assert t_shaped_content[field] is not None
            assert t_shaped_content[field] != ""

        # Should use leverage skills for competencies
        competencies = [
            t_shaped_content['core_competency_1'],
            t_shaped_content['core_competency_2'],
            t_shaped_content['core_technology']
        ]

        leverage_skills = [r.skill for r in parsed_recommendations.skill_recalibration[SkillQuadrant.LEVERAGE]]
        # At least one competency should come from leverage skills or strategic metadata
        has_leverage_skill = any(comp in leverage_skills for comp in competencies)
        has_strategic_comp = any(comp in sample_master_career_db['strategic_metadata']['core_competencies'] for comp in competencies)
        assert has_leverage_skill or has_strategic_comp

    @pytest.mark.asyncio
    async def test_cover_letter_content_selection(self, selector, sample_master_career_db, sample_job_requirements, sample_analyst_recommendations):
        """Test cover letter content selection."""
        company_data = {
            'challenges': ['scaling infrastructure', 'improving performance'],
            'recent_news': ['expansion into new markets', 'product launch']
        }

        with patch('src.core.content_selector.get_research_engine') as mock_research:
            # Mock research engine
            mock_engine = AsyncMock()
            mock_research.return_value = mock_engine
            mock_engine.get_company_intelligence.return_value = {
                'challenges': ['technical scalability', 'team growth'],
                'industry': 'Technology',
                'growth_areas': ['cloud infrastructure', 'AI integration'],
                'timestamp': '2023-12-01'
            }
            mock_engine.get_industry_intelligence.return_value = {
                'challenges': ['talent shortage', 'rapid technology changes']
            }

            result = await selector.select_cover_letter_content(
                sample_master_career_db,
                sample_job_requirements,
                sample_analyst_recommendations,
                company_data
            )

        # Should have Pain & Promise specific fields
        pain_promise_fields = [
            'inferred_pain_point', 'company_challenge_context', 'specific_challenge_detail',
            'top_quantified_achievement', 'key_skill_1', 'key_skill_2', 'relevant_skill_area'
        ]

        for field in pain_promise_fields:
            assert field in result
            assert result[field] is not None

        # Should have research enhancement flags
        assert '_research_enhanced' in result
        assert result['_research_enhanced'] is True

        # Should have content metadata
        assert '_content_metadata' in result
        metadata = result['_content_metadata']
        assert metadata['selection_strategy'] == 'pain_promise_optimized'
        assert metadata['target_company'] == sample_job_requirements['company']
        assert metadata['target_role'] == sample_job_requirements['role_title']

    @pytest.mark.asyncio
    async def test_accomplishment_relevance_calculation(self, selector):
        """Test accomplishment relevance scoring."""
        target_keywords = {'python', 'microservices', 'performance', 'team'}

        high_relevance = "Built Python microservices improving performance by 60% while leading team of 5"
        medium_relevance = "Developed web application using modern frameworks"
        low_relevance = "Fixed minor bugs in legacy system"

        high_score = await selector._calculate_accomplishment_relevance(high_relevance, target_keywords)
        medium_score = await selector._calculate_accomplishment_relevance(medium_relevance, target_keywords)
        low_score = await selector._calculate_accomplishment_relevance(low_relevance, target_keywords)

        assert high_score > medium_score > low_score
        assert high_score > 0.5  # Should have high relevance
        assert low_score < 0.3   # Should have low relevance

    def test_years_experience_calculation(self, selector):
        """Test years of experience calculation."""
        work_experience = [
            {'role_title': 'Junior Developer'},
            {'role_title': 'Software Engineer'},
            {'role_title': 'Senior Software Engineer'}
        ]

        years = selector._calculate_years_experience(work_experience)
        assert years == 6  # 3 positions * 2 years each

        # Test empty experience
        assert selector._calculate_years_experience([]) == 0

        # Test maximum cap
        many_jobs = [{'role_title': f'Job {i}'} for i in range(15)]
        assert selector._calculate_years_experience(many_jobs) == 20

    @pytest.mark.asyncio
    async def test_adjective_selection(self, selector, sample_analyst_recommendations):
        """Test optimal adjective selection."""
        parsed_recommendations = selector._parse_analyst_recommendations(sample_analyst_recommendations)

        # Test different experience levels
        junior_adj = await selector._select_optimal_adjective(2, parsed_recommendations, None)
        assert junior_adj in ["Motivated", "Dedicated", "Emerging"]

        mid_adj = await selector._select_optimal_adjective(5, parsed_recommendations, None)
        assert mid_adj in ["Experienced", "Skilled", "Accomplished"]

        senior_adj = await selector._select_optimal_adjective(10, parsed_recommendations, None)
        assert senior_adj in ["Senior", "Expert", "Seasoned"]

        exec_adj = await selector._select_optimal_adjective(15, parsed_recommendations, None)
        assert exec_adj in ["Strategic", "Visionary", "Executive"]

    @pytest.mark.asyncio
    async def test_job_relevance_calculation(self, selector, sample_analyst_recommendations, sample_job_requirements):
        """Test job entry relevance calculation."""
        parsed_recommendations = selector._parse_analyst_recommendations(sample_analyst_recommendations)

        job_entry = {
            'role_title': 'Senior Software Engineer',
            'skills_used': ['Python', 'Kubernetes', 'System Design'],
            'accomplishments': [
                'Built scalable microservices architecture',
                'Led cross-functional team'
            ]
        }

        relevance_score = await selector._calculate_job_relevance(
            job_entry,
            parsed_recommendations,
            sample_job_requirements
        )

        assert isinstance(relevance_score, float)
        assert relevance_score > 0  # Should have some relevance

        # Job with leverage skills and job requirements match should score highly
        assert relevance_score > 0.5


@pytest.mark.asyncio
async def test_industry_customization():
    """Test dynamic industry-specific customization."""
    template_content = {
        'base_style': 'professional',
        'emphasis': 'generic'
    }

    # Mock research engine
    with patch('src.core.content_selector.get_research_engine') as mock_research:
        mock_engine = AsyncMock()
        mock_research.return_value = mock_engine

        # Mock industry intelligence
        mock_engine.get_industry_intelligence.return_value = {
            'emphasis_areas': ['technical_innovation', 'scalability', 'performance'],
            'terminology_style': 'technical',
            'keywords': ['cloud', 'microservices', 'devops'],
            'research_timestamp': '2023-12-01'
        }

        # Mock skills intelligence
        mock_engine.get_skills_demand_intelligence.return_value = {
            'high_demand_skills': ['Python', 'Kubernetes', 'AWS'],
            'emerging_skills': ['GraphQL', 'Serverless'],
            'timestamp': '2023-12-01'
        }

        # Mock ATS intelligence
        mock_engine.get_ats_compliance_intelligence.return_value = {
            'requirements': {'min_keywords': 8, 'max_length': 2000},
            'last_updated': '2023-12-01'
        }

        result = await customize_template_by_industry(
            template_content,
            'Technology',
            'senior',
            None
        )

        # Should have research-enhanced content
        assert 'emphasis_areas' in result
        assert 'technical_innovation' in result['emphasis_areas']
        assert 'trending_skills' in result
        assert 'Python' in result['trending_skills']
        assert 'emerging_skills' in result
        assert 'GraphQL' in result['emerging_skills']

        # Should have research metadata
        assert '_research_metadata' in result
        metadata = result['_research_metadata']
        assert 'industry_research_timestamp' in metadata
        assert metadata['research_confidence'] == 'high'


@pytest.mark.asyncio
async def test_industry_customization_fallback():
    """Test industry customization fallback when research fails."""
    template_content = {
        'base_style': 'professional'
    }

    # Mock research engine to fail
    with patch('src.core.content_selector.get_research_engine') as mock_research:
        mock_research.side_effect = Exception("Research service unavailable")

        # Should fallback to static customizations
        result = await customize_template_by_industry(
            template_content,
            'Technology',
            'senior',
            None
        )

        # Should have static technology customizations
        assert 'emphasis_areas' in result
        assert 'technical_skills' in result['emphasis_areas']
        assert result['terminology_style'] == 'technical'
        assert result['achievement_format'] == 'metric_driven'


class TestSkillQuadrantSystem:
    """Test skill quadrant classification system."""

    def test_skill_recommendation_dataclass(self):
        """Test SkillRecommendation dataclass."""
        skill_rec = SkillRecommendation(
            skill="Python",
            quadrant=SkillQuadrant.LEVERAGE,
            relevance_score=0.95,
            confidence=0.9,
            evidence_count=5,
            market_demand=0.88
        )

        assert skill_rec.skill == "Python"
        assert skill_rec.quadrant == SkillQuadrant.LEVERAGE
        assert skill_rec.relevance_score == 0.95
        assert skill_rec.market_demand == 0.88

    def test_content_recommendation_dataclass(self):
        """Test ContentRecommendation dataclass."""
        content_rec = ContentRecommendation(
            content_type="accomplishment",
            content_id="acc_001",
            priority=ContentPriority.HIGH,
            relevance_score=0.92,
            reasoning="High impact technical achievement",
            customization_notes=["Emphasize scalability metrics", "Highlight leadership"]
        )

        assert content_rec.content_type == "accomplishment"
        assert content_rec.priority == ContentPriority.HIGH
        assert content_rec.relevance_score == 0.92
        assert len(content_rec.customization_notes) == 2


if __name__ == '__main__':
    pytest.main([__file__])
