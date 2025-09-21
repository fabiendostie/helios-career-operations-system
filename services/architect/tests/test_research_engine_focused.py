"""Focused tests for Research Engine to achieve 85+ coverage efficiently."""

import pytest
import time
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

from src.core.research_engine import (
    DynamicResearchEngine, ResearchData, ResearchCategory, get_research_engine
)


class TestResearchEngineFocused:
    """Focused tests for Research Engine coverage."""

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
            data={"test": "data", "trends": ["AI", "Cloud"]},
            confidence_score=0.85,
            sources=["test_source"],
            timestamp=time.time(),
            expiry_time=time.time() + 3600,
            version="1.0"
        )

    def test_research_data_methods(self, sample_research_data):
        """Test ResearchData methods."""
        # Test is_expired
        assert not sample_research_data.is_expired()

        # Test expired data
        expired_data = ResearchData(
            category=ResearchCategory.ATS_ALGORITHMS,
            industry="Finance",
            data={"expired": True},
            confidence_score=0.7,
            sources=["old_source"],
            timestamp=time.time() - 7200,
            expiry_time=time.time() - 3600,  # Expired
            version="1.0"
        )
        assert expired_data.is_expired()

        # Test get_hash
        hash1 = sample_research_data.get_hash()
        hash2 = sample_research_data.get_hash()
        assert hash1 == hash2
        assert isinstance(hash1, str)
        assert len(hash1) == 32  # MD5 hash length

    def test_research_engine_initialization(self, research_engine):
        """Test research engine initialization and properties."""
        assert research_engine is not None
        assert hasattr(research_engine, '_research_cache')
        assert hasattr(research_engine, '_research_in_progress')
        assert hasattr(research_engine, 'settings')
        assert hasattr(research_engine, 'research_sources')

        # Test research sources
        assert research_engine.research_sources['web_search'] is True
        assert research_engine.research_sources['job_boards'] is True
        assert research_engine.research_sources['ats_vendor_docs'] is True

        # Test update interval
        assert research_engine._update_interval == 3600
        assert research_engine._last_update_check == 0

    @pytest.mark.asyncio
    async def test_get_industry_intelligence_flow(self, research_engine, sample_research_data):
        """Test industry intelligence retrieval flow."""
        # Test with cached data
        with patch.object(research_engine, '_get_cached_research', return_value=sample_research_data):
            result = await research_engine.get_industry_intelligence("Technology")
            assert result == sample_research_data.data
            assert "test" in result
            assert "trends" in result

        # Test with real research - verify actual system behavior
        real_result = await research_engine.get_industry_intelligence("Technology", "quick")
        assert isinstance(real_result, dict)
        # System produces real intelligence data with confidence indicators
        assert 'confidence_indicators' in real_result
        assert isinstance(real_result['confidence_indicators'], list)
        assert len(real_result['confidence_indicators']) > 0

        # Test with no cached data - mock the research method
        with patch.object(research_engine, '_get_cached_research', return_value=None):
            with patch.object(research_engine, '_research_industry_intelligence',
                            return_value={"new_data": True, "industry": "Technology"}) as mock_research:
                with patch.object(research_engine, '_cache_research'):
                    result = await research_engine.get_industry_intelligence("Technology", "standard")
                    assert "new_data" in result
                    mock_research.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_ats_compliance_intelligence_flow(self, research_engine):
        """Test ATS compliance intelligence flow."""
        mock_ats_data = {
            "vendor_requirements": ["format_check", "keyword_analysis"],
            "parsing_algorithms": ["semantic", "keyword"],
            "optimization_tips": ["use_standard_fonts", "include_contact"]
        }

        with patch.object(research_engine, '_get_cached_research', return_value=None):
            with patch.object(research_engine, '_research_ats_compliance',
                            return_value=mock_ats_data) as mock_research:
                with patch.object(research_engine, '_cache_research'):
                    result = await research_engine.get_ats_compliance_intelligence()
                    assert result == mock_ats_data
                    mock_research.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_skills_demand_intelligence_flow(self, research_engine):
        """Test skills demand intelligence flow."""
        mock_skills_data = {
            "trending_skills": ["Python", "AI", "Cloud"],
            "skill_demand": {"Python": "high", "AI": "very_high"},
            "growth_forecast": {"AI": "40%", "Cloud": "25%"}
        }

        with patch.object(research_engine, '_get_cached_research', return_value=None):
            with patch.object(research_engine, '_research_skills_demand',
                            return_value=mock_skills_data) as mock_research:
                with patch.object(research_engine, '_cache_research'):
                    result = await research_engine.get_skills_demand_intelligence(
                        "Technology", "Software Engineer"
                    )
                    assert result == mock_skills_data
                    mock_research.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_company_intelligence_flow(self, research_engine):
        """Test company intelligence flow."""
        mock_company_data = {
            "company_info": {"name": "TechCorp", "industry": "Software"},
            "recent_news": ["expansion", "funding"],
            "culture_insights": ["innovative", "fast-paced"]
        }

        with patch.object(research_engine, '_get_cached_research', return_value=None):
            with patch.object(research_engine, '_research_company_intelligence',
                            return_value=mock_company_data) as mock_research:
                with patch.object(research_engine, '_cache_research'):
                    result = await research_engine.get_company_intelligence("TechCorp")
                    assert result == mock_company_data
                    mock_research.assert_called_once()

    def test_intelligent_cache_management_for_performance(self, research_engine, sample_research_data):
        """Test intelligent cache management ensures data freshness and system performance."""
        cache_key = "industry_technology_standard"

        # Test cache storage for performance optimization
        research_engine._cache_research(cache_key, sample_research_data)
        assert cache_key in research_engine._research_cache

        # Verify cached data maintains integrity
        cached = research_engine._get_cached_research(cache_key, max_age_hours=24)
        assert cached == sample_research_data
        assert cached.confidence_score == 0.85  # Data quality is preserved
        assert cached.industry == "Technology"  # Content integrity maintained

        # Test intelligent expiration based on data staleness
        stale_research = ResearchData(
            category=ResearchCategory.SKILLS_DEMAND,
            industry="Technology",
            data={"stale_skills": ["jQuery", "Flash"]},
            confidence_score=0.4,
            sources=["outdated_source"],
            timestamp=time.time() - 86400,
            expiry_time=time.time() - 3600,  # Already expired
            version="1.0"
        )

        research_engine._cache_research("stale_skills", stale_research)

        # System should reject expired data
        fresh_request = research_engine._get_cached_research("stale_skills", max_age_hours=12)
        assert fresh_request is None, "System should reject expired intelligence"

        # Verify expired data is cleaned up
        research_engine._cleanup_expired_cache()
        assert "stale_skills" not in research_engine._research_cache, "Expired intelligence should be purged"

    def test_merge_research_methods(self, research_engine):
        """Test all merge research methods."""
        # Test general merge
        base = {"key1": "value1", "shared": {"count": 1}, "list": ["item1"]}
        new = {"key2": "value2", "shared": {"count": 2, "new_field": "added"}, "list": ["item2"]}

        result = research_engine._merge_research_results(base, new)
        assert "key1" in result
        assert "key2" in result
        assert result["shared"]["count"] == 2
        assert result["shared"]["new_field"] == "added"

        # Test ATS merge
        ats_base = {"vendors": ["Workday"], "algorithms": ["keyword"]}
        ats_new = {"vendors": ["Greenhouse"], "updates": ["semantic_parsing"]}
        ats_result = research_engine._merge_ats_research(ats_base, ats_new)
        assert isinstance(ats_result, dict)

        # Test skills merge
        skills_base = {"trending": ["Python"], "growth": {"Python": "10%"}}
        skills_new = {"trending": ["AI"], "emerging": ["Quantum"]}
        skills_result = research_engine._merge_skills_research(skills_base, skills_new)
        assert isinstance(skills_result, dict)

        # Test company merge
        company_base = {"info": {"size": "1000+"}, "news": ["funding"]}
        company_new = {"info": {"industry": "Tech"}, "culture": ["innovative"]}
        company_result = research_engine._merge_company_research(company_base, company_new)
        assert isinstance(company_result, dict)

    @pytest.mark.asyncio
    async def test_research_methods_direct_calls(self, research_engine):
        """Test direct calls to research methods to increase coverage."""

        # Test industry intelligence research
        industry_result = await research_engine._research_industry_intelligence("Technology", "quick")
        assert isinstance(industry_result, dict)
        assert "industry" in industry_result
        assert "research_depth" in industry_result

        # Test ATS compliance research
        ats_result = await research_engine._research_ats_compliance()
        assert isinstance(ats_result, dict)
        assert "ats_updates" in ats_result

        # Test skills demand research
        skills_result = await research_engine._research_skills_demand("Technology", "Engineer")
        assert isinstance(skills_result, dict)
        assert "industry" in skills_result
        assert "role_type" in skills_result

        # Test company intelligence research
        company_result = await research_engine._research_company_intelligence("TestCorp")
        assert isinstance(company_result, dict)
        assert "company_name" in company_result

    @pytest.mark.asyncio
    async def test_intelligent_industry_research_quality(self, research_engine):
        """Test that industry research provides meaningful, intelligent insights."""

        # Test technology industry research - verify it provides actionable intelligence
        tech_result = await research_engine._research_industry_intelligence("Technology", "standard")

        # Verify the research produces meaningful industry intelligence
        assert isinstance(tech_result, dict)
        assert tech_result["industry"] == "Technology"
        assert tech_result["research_depth"] == "standard"

        # System produces comprehensive intelligence data - verify real structure
        assert "confidence_indicators" in tech_result, "Research should include confidence metrics"
        assert isinstance(tech_result["confidence_indicators"], list)

        # Verify intelligence quality indicators
        key_intelligence_fields = ["emphasis_areas", "trending_skills", "market_analysis", "achievement_format"]
        found_fields = [field for field in key_intelligence_fields if field in tech_result]
        assert len(found_fields) >= 2, f"Research should provide actionable intelligence, found: {found_fields}"

    @pytest.mark.asyncio
    async def test_intelligent_ats_compliance_research_depth(self, research_engine):
        """Test ATS compliance research provides current, actionable intelligence."""

        ats_result = await research_engine._research_ats_compliance()

        # ATS research should provide current vendor requirements and parsing insights
        assert isinstance(ats_result, dict)

        # Verify real ATS intelligence structure produced by the system
        assert "last_updated" in ats_result, "ATS research should have timestamp information"
        assert "optimization_tips" in ats_result, "ATS research should provide optimization guidance"
        assert isinstance(ats_result["optimization_tips"], list)

        # Verify ATS research provides actionable intelligence
        key_ats_areas = ["ats_updates", "vendor_documentation", "recruiting_insights", "optimization_tips"]
        ats_coverage = [area for area in key_ats_areas if area in ats_result]
        assert len(ats_coverage) >= 2, f"ATS research should provide multiple types of compliance intelligence, found: {ats_coverage}"

        # Verify the research is current
        assert ats_result["last_updated"] > time.time() - 300, "ATS research should be current"

    @pytest.mark.asyncio
    async def test_intelligent_skills_demand_analysis(self, research_engine):
        """Test skills demand research provides career-relevant intelligence."""

        # Test with realistic career parameters
        skills_result = await research_engine._research_skills_demand("Technology", "Software Engineer")

        assert isinstance(skills_result, dict)
        assert skills_result["industry"] == "Technology"
        assert skills_result["role_type"] == "Software Engineer"
        assert "timestamp" in skills_result

        # Skills research should provide intelligence on market demand, trending skills, and growth forecasts
        skills_intelligence_areas = ["job_board_analysis", "linkedin_trends", "market_trends"]
        skills_coverage = [area for area in skills_intelligence_areas if area in skills_result]
        assert len(skills_coverage) >= 1, f"Skills research should provide market intelligence, found: {list(skills_result.keys())}"

    @pytest.mark.asyncio
    async def test_intelligent_company_research_for_customization(self, research_engine):
        """Test company research provides insights needed for Pain & Promise customization."""

        company_result = await research_engine._research_company_intelligence("Microsoft")

        assert isinstance(company_result, dict)
        assert company_result["company_name"] == "Microsoft"
        assert "timestamp" in company_result

        # Company research should provide insights for tailoring applications
        # This intelligence enables Pain & Promise methodology customization
        company_intelligence_areas = ["company_info", "recent_news", "culture_analysis", "challenges"]
        company_coverage = [area for area in company_intelligence_areas if area in company_result]
        assert len(company_coverage) >= 2, f"Company research should provide customization insights, found: {list(company_result.keys())}"

    @pytest.mark.asyncio
    async def test_analyze_intelligence_data(self, research_engine):
        """Test intelligence data analysis."""
        test_data = {
            "trends": ["AI", "Cloud", "DevOps"],
            "metrics": {"growth": "15%", "demand": "high"},
            "sources": ["reliable_source1", "verified_source2"]
        }

        result = await research_engine._analyze_intelligence_data(test_data)
        assert isinstance(result, dict)
        assert "analysis_timestamp" in result
        assert "confidence_score" in result
        assert "processed_trends" in result
        assert isinstance(result["confidence_score"], float)
        assert 0 <= result["confidence_score"] <= 1

    @pytest.mark.asyncio
    async def test_background_research_and_updates(self, research_engine):
        """Test background research functionality."""

        # Test start background research
        with patch('asyncio.create_task') as mock_create_task:
            await research_engine.start_background_research()
            assert mock_create_task.call_count >= 2  # Should create multiple background tasks

        # Test periodic cache cleanup
        await research_engine._periodic_cache_cleanup()

        # Test update core intelligence
        with patch.object(research_engine, '_research_ats_compliance',
                         return_value={"updated": "intelligence"}):
            with patch.object(research_engine, '_cache_research'):
                await research_engine._update_core_intelligence()

    @pytest.mark.asyncio
    async def test_factory_function(self):
        """Test research engine factory function."""
        engine = await get_research_engine()
        assert isinstance(engine, DynamicResearchEngine)
        assert hasattr(engine, '_research_cache')
        assert hasattr(engine, 'research_sources')

    def test_research_categories_comprehensive(self):
        """Test research category enumeration."""
        # Test all categories exist
        assert ResearchCategory.INDUSTRY_TRENDS == "industry_trends"
        assert ResearchCategory.ATS_ALGORITHMS == "ats_algorithms"
        assert ResearchCategory.RESUME_FORMATS == "resume_formats"
        assert ResearchCategory.HIRING_PREFERENCES == "hiring_preferences"
        assert ResearchCategory.SKILLS_DEMAND == "skills_demand"
        assert ResearchCategory.SALARY_TRENDS == "salary_trends"
        assert ResearchCategory.COMPANY_CULTURE == "company_culture"

        # Test category usage in ResearchData
        for category in ResearchCategory:
            data = ResearchData(
                category=category,
                industry="Test",
                data={"test": "data"},
                confidence_score=0.8,
                sources=["test"],
                timestamp=time.time(),
                expiry_time=time.time() + 3600,
                version="1.0"
            )
            assert data.category == category
