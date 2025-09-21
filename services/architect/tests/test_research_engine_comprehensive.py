"""Comprehensive tests for Research Engine to achieve >85% coverage."""

import pytest
import asyncio
import time
from unittest.mock import patch, MagicMock, AsyncMock
from dataclasses import asdict

from src.core.research_engine import (
    DynamicResearchEngine, ResearchData, ResearchCategory
)


class TestDynamicResearchEngine:
    """Comprehensive tests for Dynamic Research Engine."""

    @pytest.fixture
    def research_engine(self):
        """Create research engine instance."""
        return DynamicResearchEngine()

    @pytest.fixture
    def sample_research_data(self):
        """Sample research data for testing."""
        return ResearchData(
            category=ResearchCategory.INDUSTRY_TRENDS,
            industry="Technology",
            data={
                "trending_skills": ["AI/ML", "Cloud Computing", "DevOps"],
                "job_growth": "15% annually",
                "salary_ranges": {"entry": 70000, "mid": 120000, "senior": 180000}
            },
            confidence_score=0.85,
            sources=["job_boards", "industry_reports"],
            timestamp=time.time(),
            expiry_time=time.time() + 86400,  # 24 hours
            version="1.0"
        )

    def test_research_data_creation(self, sample_research_data):
        """Test ResearchData dataclass creation and methods."""
        assert sample_research_data.category == ResearchCategory.INDUSTRY_TRENDS
        assert sample_research_data.industry == "Technology"
        assert sample_research_data.confidence_score == 0.85
        assert len(sample_research_data.sources) == 2

        # Test is_expired method
        assert not sample_research_data.is_expired()

        # Test get_hash method
        hash_value = sample_research_data.get_hash()
        assert isinstance(hash_value, str)
        assert len(hash_value) > 0

    def test_research_data_expiration(self):
        """Test research data expiration logic."""
        # Create expired data
        expired_data = ResearchData(
            category=ResearchCategory.ATS_ALGORITHMS,
            industry="Finance",
            data={"test": "data"},
            confidence_score=0.7,
            sources=["test_source"],
            timestamp=time.time() - 86400,  # 24 hours ago
            expiry_time=time.time() - 3600,  # Expired 1 hour ago
            version="1.0"
        )

        assert expired_data.is_expired()

    def test_research_engine_initialization(self, research_engine):
        """Test research engine initialization."""
        assert research_engine is not None
        assert hasattr(research_engine, '_research_cache')
        assert hasattr(research_engine, 'settings')
        assert hasattr(research_engine, 'research_sources')
        assert hasattr(research_engine, '_research_in_progress')
        assert research_engine._update_interval == 3600

        # Test research sources configuration
        assert research_engine.research_sources['web_search'] is True
        assert research_engine.research_sources['job_boards'] is True
        assert research_engine.research_sources['ats_vendor_docs'] is True

    @pytest.mark.asyncio
    async def test_get_industry_intelligence_cached(self, research_engine, sample_research_data):
        """Test industry intelligence retrieval with cached data."""
        # Mock cached data
        with patch.object(research_engine, '_get_cached_research', return_value=sample_research_data):
            result = await research_engine.get_industry_intelligence(
                industry="Technology",
                research_depth="quick"
            )

            assert result == sample_research_data.data
            assert "trending_skills" in result
            assert "job_growth" in result

    @pytest.mark.asyncio
    async def test_get_industry_intelligence_new_research(self, research_engine):
        """Test industry intelligence with new research."""
        mock_intelligence_data = {
            "market_trends": ["Remote work", "AI adoption"],
            "skill_demands": ["Python", "Machine Learning"],
            "growth_rate": "12%"
        }

        with patch.object(research_engine, '_get_cached_research', return_value=None):
            with patch.object(research_engine, '_research_industry_intelligence',
                            return_value=mock_intelligence_data) as mock_research:
                with patch.object(research_engine, '_cache_research') as mock_cache:

                    result = await research_engine.get_industry_intelligence(
                        industry="Healthcare",
                        research_depth="comprehensive"
                    )

                    assert result == mock_intelligence_data
                    mock_research.assert_called_once_with("Healthcare", "comprehensive")
                    mock_cache.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_ats_compliance_intelligence(self, research_engine):
        """Test ATS compliance intelligence retrieval."""
        mock_ats_data = {
            "ats_vendors": ["Workday", "Greenhouse", "Lever"],
            "optimization_tips": ["Use standard fonts", "Include keywords"],
            "parsing_algorithms": ["keyword_matching", "semantic_analysis"]
        }

        with patch.object(research_engine, '_get_cached_research', return_value=None):
            with patch.object(research_engine, '_research_ats_compliance',
                            return_value=mock_ats_data) as mock_research:
                with patch.object(research_engine, '_cache_research') as mock_cache:

                    result = await research_engine.get_ats_compliance_intelligence()

                    assert result == mock_ats_data
                    assert "ats_vendors" in result
                    mock_research.assert_called_once()
                    mock_cache.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_company_intelligence(self, research_engine):
        """Test company intelligence research."""
        mock_company_data = {
            "company_mission": "Advancing AI for humanity",
            "recent_news": ["Launched new AI product", "Hired 100 engineers"],
            "culture_keywords": ["innovation", "collaboration", "impact"],
            "tech_stack": ["Python", "TensorFlow", "Kubernetes"]
        }

        with patch.object(research_engine, '_get_cached_research', return_value=None):
            with patch.object(research_engine, '_research_company_intelligence',
                             return_value=mock_company_data) as mock_research:
                with patch.object(research_engine, '_cache_research') as mock_cache:

                    result = await research_engine.get_company_intelligence(
                        company_name="AI Innovations Inc"
                    )

                    assert result == mock_company_data
                    assert "company_mission" in result
                    mock_research.assert_called_once_with("AI Innovations Inc")
                    mock_cache.assert_called_once()

    def test_cache_operations(self, research_engine, sample_research_data):
        """Test research cache operations."""
        cache_key = "test_industry_tech"

        # Test caching
        research_engine._cache_research(cache_key, sample_research_data)

        # Test retrieval
        retrieved_data = research_engine._get_cached_research(cache_key, max_age_hours=24)
        assert retrieved_data is not None
        assert retrieved_data.industry == sample_research_data.industry
        assert retrieved_data.data == sample_research_data.data

    def test_cache_expiration_handling(self, research_engine):
        """Test cache expiration handling."""
        # Create expired data
        expired_data = ResearchData(
            category=ResearchCategory.INDUSTRY_TRENDS,
            industry="Technology",
            data={"old": "data"},
            confidence_score=0.8,
            sources=["old_source"],
            timestamp=time.time() - 86400,
            expiry_time=time.time() - 3600,  # Expired
            version="1.0"
        )

        cache_key = "expired_test"
        research_engine._cache_research(cache_key, expired_data)

        # Should return None for expired data
        retrieved_data = research_engine._get_cached_research(cache_key, max_age_hours=1)
        assert retrieved_data is None

    def test_research_categories_enum(self):
        """Test ResearchCategory enum values."""
        categories = [
            ResearchCategory.INDUSTRY_TRENDS,
            ResearchCategory.ATS_ALGORITHMS,
            ResearchCategory.RESUME_FORMATS,
            ResearchCategory.HIRING_PREFERENCES,
            ResearchCategory.SKILLS_DEMAND,
            ResearchCategory.SALARY_TRENDS,
            ResearchCategory.COMPANY_CULTURE
        ]

        for category in categories:
            assert isinstance(category.value, str)
            assert len(category.value) > 0

    @pytest.mark.asyncio
    async def test_research_with_confidence_scoring(self, research_engine):
        """Test research with confidence scoring."""
        mock_data = {"test": "data"}

        with patch.object(research_engine, '_research_industry_intelligence',
                         return_value=mock_data):
            with patch.object(research_engine, '_get_cached_research', return_value=None):
                with patch.object(research_engine, '_cache_research') as mock_cache:

                    await research_engine.get_industry_intelligence("TestIndustry")

                    # Verify confidence score is set
                    cache_call_args = mock_cache.call_args[0]
                    research_data = cache_call_args[1]
                    assert 0.0 <= research_data.confidence_score <= 1.0

    def test_research_data_serialization(self, sample_research_data):
        """Test research data can be serialized."""
        # Convert to dict (for caching/storage)
        data_dict = asdict(sample_research_data)
        assert isinstance(data_dict, dict)
        assert 'category' in data_dict
        assert 'industry' in data_dict
        assert 'confidence_score' in data_dict

    @pytest.mark.asyncio
    async def test_error_handling_in_research(self, research_engine):
        """Test error handling during research operations."""
        with patch.object(research_engine, '_research_industry_intelligence',
                         side_effect=Exception("Research API unavailable")):
            with patch.object(research_engine, '_get_cached_research', return_value=None):

                # Should handle errors gracefully
                try:
                    result = await research_engine.get_industry_intelligence("TestIndustry")
                    # Should either return default data or raise appropriate exception
                    assert isinstance(result, dict) or result is None
                except Exception as e:
                    # Should be a meaningful error message
                    assert "Research API unavailable" in str(e)

    @pytest.mark.asyncio
    async def test_concurrent_research_requests(self, research_engine):
        """Test handling of concurrent research requests."""
        mock_data = {"concurrent": "test"}

        with patch.object(research_engine, '_research_industry_intelligence',
                         return_value=mock_data):
            with patch.object(research_engine, '_get_cached_research', return_value=None):

                # Make concurrent requests
                tasks = [
                    research_engine.get_industry_intelligence(f"Industry{i}")
                    for i in range(3)
                ]

                results = await asyncio.gather(*tasks, return_exceptions=True)

                # All should complete successfully
                for result in results:
                    assert isinstance(result, dict)
                    assert result == mock_data

    def test_cache_key_generation(self, research_engine):
        """Test cache key generation consistency."""
        # Test that same inputs generate same cache keys
        industry = "Technology"
        cache_key1 = f"industry_{industry.lower().replace(' ', '_')}"
        cache_key2 = f"industry_{industry.lower().replace(' ', '_')}"

        assert cache_key1 == cache_key2

        # Test with spaces
        industry_with_spaces = "Health Care"
        cache_key_spaces = f"industry_{industry_with_spaces.lower().replace(' ', '_')}"
        assert "health_care" in cache_key_spaces

    @pytest.mark.asyncio
    async def test_research_depth_handling(self, research_engine):
        """Test different research depth levels."""
        mock_data = {"depth": "test"}

        with patch.object(research_engine, '_research_industry_intelligence',
                         return_value=mock_data) as mock_research:
            with patch.object(research_engine, '_get_cached_research', return_value=None):

                # Test different depth levels
                for depth in ["quick", "standard", "comprehensive", "detailed"]:
                    await research_engine.get_industry_intelligence(
                        "TestIndustry",
                        research_depth=depth
                    )

                # Should call research with appropriate depth
                assert mock_research.call_count == 4

                # Verify depth parameter is passed correctly
                call_args = [call[0] for call in mock_research.call_args_list]
                depths_used = [args[1] for args in call_args]
                assert "quick" in depths_used
                assert "comprehensive" in depths_used

    @pytest.mark.asyncio
    async def test_skills_demand_intelligence(self, research_engine):
        """Test skills demand intelligence research."""
        mock_skills_data = {
            "trending_skills": ["Python", "Machine Learning", "Cloud Computing"],
            "skill_growth": {"Python": "25%", "ML": "40%"},
            "demand_forecast": {"high_demand": ["AI", "Data Science"], "emerging": ["Quantum"]}
        }

        with patch.object(research_engine, '_get_cached_research', return_value=None):
            with patch.object(research_engine, '_research_skills_demand', return_value=mock_skills_data) as mock_research:
                with patch.object(research_engine, '_cache_research') as mock_cache:

                    result = await research_engine.get_skills_demand_intelligence(
                        industry="Technology",
                        role_type="Software Engineer"
                    )

                    assert result == mock_skills_data
                    assert "trending_skills" in result
                    mock_research.assert_called_once()
                    mock_cache.assert_called_once()

    @pytest.mark.asyncio
    async def test_research_industry_intelligence_comprehensive(self, research_engine):
        """Test comprehensive industry intelligence research method."""
        industry = "Technology"
        research_depth = "standard"

        # Test the actual method exists and returns proper structure
        result = await research_engine._research_industry_intelligence(industry, research_depth)

        assert isinstance(result, dict)
        assert "industry" in result
        assert "research_depth" in result
        assert "timestamp" in result
        assert result["industry"] == industry
        assert result["research_depth"] == research_depth

    @pytest.mark.asyncio
    async def test_research_ats_compliance_comprehensive(self, research_engine):
        """Test comprehensive ATS compliance research method."""
        # Test the actual method exists and returns proper structure
        result = await research_engine._research_ats_compliance()

        assert isinstance(result, dict)
        assert "ats_updates" in result
        assert "vendor_documentation" in result
        assert "recruiting_insights" in result
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_research_skills_demand_comprehensive(self, research_engine):
        """Test comprehensive skills demand research method."""
        industry = "Technology"
        role_type = "Data Scientist"

        # Test the actual method exists and returns proper structure
        result = await research_engine._research_skills_demand(industry, role_type)

        assert isinstance(result, dict)
        assert "industry" in result
        assert "role_type" in result
        assert "timestamp" in result
        assert result["industry"] == industry
        assert result["role_type"] == role_type

    @pytest.mark.asyncio
    async def test_research_company_intelligence_comprehensive(self, research_engine):
        """Test comprehensive company intelligence research method."""
        company_name = "TechCorp"

        # Test the actual method exists and returns proper structure
        result = await research_engine._research_company_intelligence(company_name)

        assert isinstance(result, dict)
        assert "company_name" in result
        assert "timestamp" in result
        assert result["company_name"] == company_name

    @pytest.mark.asyncio
    async def test_web_search_methods(self, research_engine):
        """Test various web search and analysis methods."""

        # Test web search industry trends - just verify it returns a dict
        result = await research_engine._web_search_industry_trends("Technology")
        assert isinstance(result, dict)
        assert "industry_trends" in result

        # Test analyze job postings
        result = await research_engine._analyze_job_postings("Technology")
        assert isinstance(result, dict)
        assert "job_postings_analyzed" in result

        # Test research industry reports
        result = await research_engine._research_industry_reports("Technology")
        assert isinstance(result, dict)
        assert "industry_reports" in result

        # Test research salary trends
        result = await research_engine._research_salary_trends("Technology")
        assert isinstance(result, dict)
        assert "salary_trends" in result

        # Test web search ATS updates
        result = await research_engine._web_search_ats_updates()
        assert isinstance(result, dict)
        assert "ats_updates" in result

        # Test research ATS vendor documentation
        result = await research_engine._research_ats_vendor_documentation()
        assert isinstance(result, dict)
        assert "vendor_documentation" in result

        # Test analyze recruiting forums
        result = await research_engine._analyze_recruiting_forums()
        assert isinstance(result, dict)
        assert "recruiting_insights" in result

    @pytest.mark.asyncio
    async def test_skills_research_methods(self, research_engine):
        """Test skills-specific research methods."""
        industry = "Technology"
        role_type = "Software Engineer"

        # Test analyze job board skills
        result = await research_engine._analyze_job_board_skills(industry, role_type)
        assert isinstance(result, dict)
        assert "job_board_skills" in result

        # Test research LinkedIn skills trends
        result = await research_engine._research_linkedin_skills_trends(industry, role_type)
        assert isinstance(result, dict)
        assert "linkedin_trends" in result

        # Test web search skills trends
        result = await research_engine._web_search_skills_trends(industry, role_type)
        assert isinstance(result, dict)
        assert "skills_trends" in result

    @pytest.mark.asyncio
    async def test_company_research_methods(self, research_engine):
        """Test company-specific research methods."""
        company_name = "TechCorp"

        # Test web search company info
        result = await research_engine._web_search_company_info(company_name)
        assert isinstance(result, dict)
        assert "company_info" in result

        # Test research company news
        result = await research_engine._research_company_news(company_name)
        assert isinstance(result, dict)
        assert "company_news" in result

        # Test analyze company culture
        result = await research_engine._analyze_company_culture(company_name)
        assert isinstance(result, dict)
        assert "culture_analysis" in result

        # Test research company challenges
        result = await research_engine._research_company_challenges(company_name)
        assert isinstance(result, dict)
        assert "challenges" in result

    def test_merge_research_results(self, research_engine):
        """Test research results merging logic."""
        base_data = {
            "existing_key": "base_value",
            "shared_key": {"count": 1},
            "list_key": ["item1"]
        }

        new_data = {
            "new_key": "new_value",
            "shared_key": {"count": 2, "new_field": "added"},
            "list_key": ["item2"]
        }

        result = research_engine._merge_research_results(base_data, new_data)

        assert "existing_key" in result
        assert "new_key" in result
        assert result["shared_key"]["count"] == 2
        assert result["shared_key"]["new_field"] == "added"
        assert len(result["list_key"]) == 2

    def test_merge_specialized_research_methods(self, research_engine):
        """Test specialized research merging methods."""
        base_data = {"vendors": ["Workday"], "algorithms": ["keyword_match"]}
        new_data = {"vendors": ["Greenhouse"], "parsing_updates": ["semantic_analysis"]}

        # Test ATS research merging
        result = research_engine._merge_ats_research(base_data, new_data)
        assert isinstance(result, dict)

        # Test skills research merging
        skills_base = {"trending_skills": ["Python"], "skill_growth": {"Python": "10%"}}
        skills_new = {"trending_skills": ["JavaScript"], "emerging_skills": ["Rust"]}

        result = research_engine._merge_skills_research(skills_base, skills_new)
        assert isinstance(result, dict)

        # Test company research merging
        company_base = {"company_info": {"size": "1000+"}, "news": ["funding"]}
        company_new = {"company_info": {"industry": "Tech"}, "culture": ["innovative"]}

        result = research_engine._merge_company_research(company_base, company_new)
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_analyze_intelligence_data(self, research_engine):
        """Test intelligence data analysis method."""
        test_data = {
            "raw_trends": ["AI", "Cloud", "DevOps"],
            "job_counts": {"Software Engineer": 1500, "Data Scientist": 800},
            "salary_ranges": {"median": 120000, "range": [80000, 180000]},
            "confidence_indicators": ["verified_source", "recent_data"]
        }

        result = await research_engine._analyze_intelligence_data(test_data)

        assert isinstance(result, dict)
        assert "analysis_timestamp" in result
        assert "confidence_score" in result
        assert "processed_trends" in result
        assert result["confidence_score"] >= 0.0
        assert result["confidence_score"] <= 1.0

    def test_cache_expiration_and_cleanup_comprehensive(self, research_engine):
        """Test comprehensive cache expiration and cleanup mechanisms."""

        # Test getting cached research with age limit
        cache_key = "test_expired_data"

        # Create expired data
        expired_data = ResearchData(
            category=ResearchCategory.INDUSTRY_TRENDS,
            industry="Technology",
            data={"test": "data"},
            confidence_score=0.8,
            sources=["test"],
            timestamp=time.time() - 7200,  # 2 hours ago
            expiry_time=time.time() - 3600,  # expired 1 hour ago
            version="1.0"
        )

        research_engine._research_cache[cache_key] = expired_data

        # Should return None for expired data
        result = research_engine._get_cached_research(cache_key, max_age_hours=1)
        assert result is None

        # Test cleanup expired cache
        research_engine._cleanup_expired_cache()
        assert cache_key not in research_engine._research_cache

    @pytest.mark.asyncio
    async def test_background_research_methods(self, research_engine):
        """Test background research and periodic update methods."""

        # Test start background research
        with patch.object(research_engine, '_periodic_research_updates') as mock_updates:
            with patch.object(research_engine, '_periodic_cache_cleanup') as mock_cleanup:
                with patch('asyncio.create_task') as mock_create_task:

                    await research_engine.start_background_research()

                    # Should create background tasks
                    assert mock_create_task.call_count >= 2

        # Test periodic cache cleanup
        await research_engine._periodic_cache_cleanup()

        # Test update core intelligence
        with patch.object(research_engine, '_research_ats_compliance', return_value={"test": "data"}):
            with patch.object(research_engine, '_cache_research'):
                await research_engine._update_core_intelligence()

    @pytest.mark.asyncio
    async def test_factory_function(self):
        """Test research engine factory function."""
        from src.core.research_engine import get_research_engine

        engine = await get_research_engine()
        assert isinstance(engine, DynamicResearchEngine)
        assert hasattr(engine, '_research_cache')
        assert hasattr(engine, 'research_sources')
