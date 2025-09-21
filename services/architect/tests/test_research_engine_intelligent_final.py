"""Intelligent and meaningful Research Engine tests focused on real system behavior."""

import pytest
import time
import asyncio
from unittest.mock import patch

from src.core.research_engine import (
    DynamicResearchEngine, ResearchData, ResearchCategory, get_research_engine
)


class TestResearchEngineIntelligent:
    """Intelligent tests that validate Research Engine provides meaningful career intelligence."""

    @pytest.fixture
    def research_engine(self):
        """Create research engine instance."""
        return DynamicResearchEngine()

    def test_research_engine_intelligent_initialization(self, research_engine):
        """Test research engine initializes with proper career intelligence capabilities."""
        # Verify core intelligence gathering capabilities are configured
        assert hasattr(research_engine, '_research_cache'), "Engine should have caching for performance"
        assert hasattr(research_engine, 'research_sources'), "Engine should configure multiple intelligence sources"

        # Verify research sources are configured for comprehensive intelligence gathering
        sources = research_engine.research_sources
        critical_sources = ['web_search', 'job_boards', 'industry_reports', 'ats_vendor_docs']
        for source in critical_sources:
            assert sources.get(source) is True, f"Critical intelligence source '{source}' should be enabled"

        # Verify performance optimization settings
        assert research_engine._update_interval == 3600, "Cache should refresh hourly for current intelligence"

    def test_research_data_intelligence_and_expiration(self):
        """Test ResearchData intelligently manages career intelligence freshness."""
        # Create research data with career-relevant information
        current_skills_data = ResearchData(
            category=ResearchCategory.SKILLS_DEMAND,
            industry="Technology",
            data={
                "trending_skills": ["Python", "AI/ML", "Cloud Computing"],
                "high_demand_roles": ["Software Engineer", "Data Scientist"],
                "salary_growth": {"AI": "40%", "Cloud": "25%"}
            },
            confidence_score=0.92,  # High confidence in skills intelligence
            sources=["LinkedIn", "Indeed", "Stack Overflow Survey"],
            timestamp=time.time(),
            expiry_time=time.time() + 3600,  # 1 hour freshness for skills data
            version="2024.1"
        )

        # Verify intelligence quality metrics
        assert current_skills_data.confidence_score > 0.9, "Skills intelligence should have high confidence"
        assert len(current_skills_data.sources) >= 3, "Skills data should use multiple sources for reliability"
        assert not current_skills_data.is_expired(), "Fresh intelligence should not be expired"

        # Test hash generation for cache optimization
        hash1 = current_skills_data.get_hash()
        hash2 = current_skills_data.get_hash()
        assert hash1 == hash2, "Hash should be consistent for cache efficiency"
        assert len(hash1) == 32, "Should use MD5 hash for performance"

        # Test expiration logic for intelligence freshness
        stale_data = ResearchData(
            category=ResearchCategory.INDUSTRY_TRENDS,
            industry="Healthcare",
            data={"outdated": "information"},
            confidence_score=0.3,  # Low confidence due to staleness
            sources=["old_source"],
            timestamp=time.time() - 86400,  # 24 hours old
            expiry_time=time.time() - 7200,  # Expired 2 hours ago
            version="2023.1"
        )

        assert stale_data.is_expired(), "Stale intelligence should be marked as expired"
        assert stale_data.confidence_score < 0.5, "Stale data should have low confidence"

    @pytest.mark.asyncio
    async def test_industry_intelligence_provides_career_insights(self, research_engine):
        """Test industry intelligence provides actionable career optimization insights."""
        # Request intelligence for technology industry - a key career sector
        tech_intelligence = await research_engine.get_industry_intelligence("Technology", "standard")

        # Verify intelligent system provides comprehensive career insights
        assert isinstance(tech_intelligence, dict), "Intelligence should be structured data"

        # Test intelligence quality - system should provide confidence indicators
        assert "confidence_indicators" in tech_intelligence, "System should indicate intelligence confidence"
        confidence_indicators = tech_intelligence["confidence_indicators"]
        assert isinstance(confidence_indicators, list), "Confidence indicators should be detailed"
        assert len(confidence_indicators) > 0, "System should provide confidence metrics"

        # Verify career-relevant intelligence areas
        career_intelligence_fields = [
            "trending_skills", "emphasis_areas", "market_analysis",
            "achievement_format", "technical_skills", "growth_opportunities"
        ]

        found_intelligence = [field for field in career_intelligence_fields if field in tech_intelligence]
        assert len(found_intelligence) >= 3, f"Should provide comprehensive career intelligence: {found_intelligence}"

        # Test intelligence depth varies with research level
        quick_intelligence = await research_engine.get_industry_intelligence("Technology", "quick")
        assert isinstance(quick_intelligence, dict), "Quick research should still provide intelligence"
        # Quick research may have fewer data points but should still be meaningful

    @pytest.mark.asyncio
    async def test_ats_compliance_intelligence_for_resume_optimization(self, research_engine):
        """Test ATS compliance intelligence provides resume optimization guidance."""
        ats_intelligence = await research_engine.get_ats_compliance_intelligence()

        # Verify ATS intelligence provides actionable optimization guidance
        assert isinstance(ats_intelligence, dict), "ATS intelligence should be structured"

        # Critical ATS intelligence for resume optimization
        assert "optimization_tips" in ats_intelligence, "Should provide concrete optimization guidance"
        optimization_tips = ats_intelligence["optimization_tips"]
        assert isinstance(optimization_tips, list), "Tips should be actionable list"
        assert len(optimization_tips) > 0, "Should provide multiple optimization strategies"

        # Verify intelligence currency for ATS systems that change frequently
        assert "last_updated" in ats_intelligence, "ATS intelligence should track currency"
        last_updated = ats_intelligence["last_updated"]
        assert last_updated > time.time() - 3600, "ATS intelligence should be recent (within 1 hour)"

    @pytest.mark.asyncio
    async def test_skills_demand_intelligence_for_career_planning(self, research_engine):
        """Test skills demand intelligence provides career planning insights."""
        skills_intelligence = await research_engine.get_skills_demand_intelligence(
            industry="Technology",
            role_type="Software Engineer"
        )

        # Verify skills intelligence provides career planning data
        assert isinstance(skills_intelligence, dict), "Skills intelligence should be structured"

        # Verify the system provides meaningful skills intelligence with actual structure
        assert "industry" in skills_intelligence, "Should maintain industry context"
        assert "role_type" in skills_intelligence, "Should maintain role context"
        assert "timestamp" in skills_intelligence, "Should provide currency information"

        # Skills intelligence should have meaningful career data
        career_relevant_keys = list(skills_intelligence.keys())
        assert len(career_relevant_keys) >= 3, f"Should provide meaningful career intelligence: {career_relevant_keys}"

    @pytest.mark.asyncio
    async def test_company_intelligence_for_application_customization(self, research_engine):
        """Test company intelligence enables Pain & Promise application customization."""
        # Test with a well-known company for reliable intelligence
        company_intelligence = await research_engine.get_company_intelligence("Microsoft")

        # Verify company intelligence supports application customization
        assert isinstance(company_intelligence, dict), "Company intelligence should be structured"
        assert company_intelligence.get("company_name") == "Microsoft", "Should preserve company context"

        # Verify intelligence for Pain & Promise customization methodology
        customization_intelligence_fields = [
            "company_info", "recent_news", "culture_analysis", "challenges",
            "pain_points", "growth_opportunities", "strategic_priorities"
        ]

        found_customization_data = [field for field in customization_intelligence_fields if field in company_intelligence]
        assert len(found_customization_data) >= 2, f"Should provide application customization intelligence: {found_customization_data}"

    def test_intelligent_cache_management_for_performance_and_freshness(self, research_engine):
        """Test cache intelligently balances performance with intelligence freshness."""
        # Create high-confidence current intelligence
        current_intelligence = ResearchData(
            category=ResearchCategory.INDUSTRY_TRENDS,
            industry="Technology",
            data={
                "ai_adoption": "accelerating",
                "remote_work": "permanent_shift",
                "skill_shortages": ["cybersecurity", "machine_learning"]
            },
            confidence_score=0.95,
            sources=["McKinsey", "Gartner", "Harvard Business Review"],
            timestamp=time.time(),
            expiry_time=time.time() + 7200,  # 2 hours fresh
            version="2024.1"
        )

        # Test intelligent caching
        cache_key = "industry_technology_trends_2024"
        research_engine._cache_research(cache_key, current_intelligence)

        # Verify cache preserves intelligence integrity
        cached_intelligence = research_engine._get_cached_research(cache_key, max_age_hours=4)
        assert cached_intelligence is not None, "Fresh intelligence should be cached"
        assert cached_intelligence.confidence_score == 0.95, "Cache should preserve confidence scores"
        assert len(cached_intelligence.sources) == 3, "Cache should preserve source reliability"

        # Test intelligent expiration - old intelligence should be rejected
        expired_intelligence = ResearchData(
            category=ResearchCategory.SKILLS_DEMAND,
            industry="Technology",
            data={"outdated_skills": ["Flash", "Internet Explorer"]},
            confidence_score=0.2,  # Low confidence
            sources=["old_survey"],
            timestamp=time.time() - 172800,  # 48 hours old
            expiry_time=time.time() - 86400,  # Expired 24 hours ago
            version="2022.1"
        )

        research_engine._cache_research("expired_skills", expired_intelligence)
        retrieved_expired = research_engine._get_cached_research("expired_skills", max_age_hours=12)
        assert retrieved_expired is None, "Cache should reject expired intelligence for quality"

        # Test cache cleanup for system efficiency
        research_engine._cleanup_expired_cache()
        assert "expired_skills" not in research_engine._research_cache, "Cleanup should remove expired intelligence"
        assert cache_key in research_engine._research_cache, "Cleanup should preserve fresh intelligence"

    def test_research_data_merging_intelligence(self, research_engine):
        """Test research merging provides comprehensive intelligence from multiple sources."""
        # Test general research merging logic
        base_intelligence = {
            "market_trends": ["AI growth", "Remote work"],
            "skill_demands": {"Python": "high", "JavaScript": "very_high"},
            "salary_data": {"median": 120000}
        }

        new_intelligence = {
            "market_trends": ["Cloud adoption", "Automation"],  # Additional trends
            "skill_demands": {"Python": "very_high", "TypeScript": "high"},  # Updated demands
            "salary_data": {"median": 125000, "growth": "8%"},  # Enhanced salary data
            "job_outlook": "positive"  # New intelligence area
        }

        merged = research_engine._merge_research_results(base_intelligence, new_intelligence)

        # Verify merging enhances intelligence comprehensiveness
        assert "job_outlook" in merged, "Merging should add new intelligence areas"
        assert merged["skill_demands"]["Python"] == "very_high", "Should use latest skill intelligence"
        assert merged["skill_demands"]["JavaScript"] == "very_high", "Should preserve existing intelligence"
        assert merged["salary_data"]["growth"] == "8%", "Should enhance salary intelligence"
        assert len(merged["market_trends"]) == 4, "Should combine trend intelligence"

        # Test specialized ATS merging
        ats_base = {"vendors": ["Workday"], "compliance_rules": ["format_check"]}
        ats_new = {"vendors": ["Greenhouse"], "compliance_rules": ["keyword_analysis"], "updates": ["2024_changes"]}
        ats_merged = research_engine._merge_ats_research(ats_base, ats_new)
        assert isinstance(ats_merged, dict), "ATS merging should produce structured intelligence"

        # Test specialized skills merging
        skills_base = {"trending": ["Python"], "growth_areas": {"AI": "40%"}}
        skills_new = {"trending": ["Rust"], "growth_areas": {"Cloud": "30%"}, "certifications": ["AWS"]}
        skills_merged = research_engine._merge_skills_research(skills_base, skills_new)
        assert isinstance(skills_merged, dict), "Skills merging should combine market intelligence"

    @pytest.mark.asyncio
    async def test_research_methods_provide_targeted_intelligence(self, research_engine):
        """Test individual research methods provide targeted, meaningful intelligence."""

        # Test industry research provides comprehensive market intelligence
        industry_data = await research_engine._research_industry_intelligence("Technology", "standard")
        assert isinstance(industry_data, dict), "Industry research should provide structured intelligence"
        assert industry_data["industry"] == "Technology", "Should maintain industry context"
        assert industry_data["research_depth"] == "standard", "Should provide appropriate research depth"

        # Test ATS research provides current compliance intelligence
        ats_data = await research_engine._research_ats_compliance()
        assert isinstance(ats_data, dict), "ATS research should provide structured compliance data"
        assert "last_updated" in ats_data, "ATS research should have timestamp"
        assert "optimization_tips" in ats_data, "Should provide optimization guidance"

        # Test skills research provides market demand intelligence
        skills_data = await research_engine._research_skills_demand("Technology", "Data Scientist")
        assert isinstance(skills_data, dict), "Skills research should provide market intelligence"
        assert skills_data["industry"] == "Technology", "Should maintain industry context"
        assert skills_data["role_type"] == "Data Scientist", "Should maintain role context"
        assert "timestamp" in skills_data, "Should have timing information"

        # Test company research provides customization intelligence
        company_data = await research_engine._research_company_intelligence("Google")
        assert isinstance(company_data, dict), "Company research should provide customization data"
        assert company_data["company_name"] == "Google", "Should maintain company context"
        assert "timestamp" in company_data, "Should have timing information"

    @pytest.mark.asyncio
    async def test_intelligence_analysis_provides_insights(self, research_engine):
        """Test intelligence analysis enhances raw data with insights."""
        raw_career_data = {
            "industry": "Technology",  # Required field for analysis
            "job_postings": ["Senior Python Developer", "ML Engineer", "DevOps Engineer"],
            "skill_frequencies": {"Python": 85, "AWS": 70, "Docker": 65, "ML": 45},
            "salary_ranges": {"min": 90000, "max": 180000, "median": 135000},
            "company_sizes": {"startup": 30, "mid_size": 45, "enterprise": 25},
            "trending_skills": ["Python", "AI", "Cloud Computing"],
            "research_timestamp": time.time()  # Required for confidence indicators
        }

        analyzed_intelligence = await research_engine._analyze_intelligence_data(raw_career_data)

        # Verify analysis enhances data with career insights
        assert isinstance(analyzed_intelligence, dict), "Analysis should provide structured insights"

        # Verify intelligence analysis enhances data with meaningful insights
        analysis_fields = ["emphasis_areas", "terminology_style", "confidence_indicators"]
        found_fields = [field for field in analysis_fields if field in analyzed_intelligence]
        assert len(found_fields) >= 2, f"Analysis should enhance data with intelligence: {found_fields}"

        # Verify specific intelligent enhancements
        if "emphasis_areas" in analyzed_intelligence:
            assert isinstance(analyzed_intelligence["emphasis_areas"], list), "Should provide emphasis guidance"
        if "confidence_indicators" in analyzed_intelligence:
            assert isinstance(analyzed_intelligence["confidence_indicators"], list), "Should provide confidence metrics"

        # If confidence_score exists, verify it's meaningful
        if "confidence_score" in analyzed_intelligence:
            confidence = analyzed_intelligence["confidence_score"]
            assert isinstance(confidence, (int, float)), "Confidence should be numeric"
            assert 0 <= confidence <= 1, "Confidence should be normalized percentage"

    @pytest.mark.asyncio
    async def test_factory_function_provides_configured_engine(self):
        """Test factory function provides properly configured research engine."""
        engine = await get_research_engine()

        # Verify factory produces fully configured intelligence engine
        assert isinstance(engine, DynamicResearchEngine), "Factory should create proper engine type"
        assert hasattr(engine, '_research_cache'), "Should configure caching for performance"
        assert hasattr(engine, 'research_sources'), "Should configure intelligence sources"

        # Verify research sources are properly configured
        sources = engine.research_sources
        assert sources['web_search'] is True, "Web search should be enabled for intelligence gathering"
        assert sources['job_boards'] is True, "Job boards should be enabled for market intelligence"
        assert sources['ats_vendor_docs'] is True, "ATS docs should be enabled for compliance intelligence"

    def test_research_categories_support_comprehensive_intelligence(self):
        """Test research categories cover comprehensive career intelligence needs."""
        # Verify all critical career intelligence categories exist
        expected_categories = [
            ResearchCategory.INDUSTRY_TRENDS,    # Market intelligence
            ResearchCategory.ATS_ALGORITHMS,     # Resume optimization
            ResearchCategory.SKILLS_DEMAND,      # Career planning
            ResearchCategory.HIRING_PREFERENCES, # Application strategy
            ResearchCategory.SALARY_TRENDS,      # Compensation intelligence
            ResearchCategory.COMPANY_CULTURE,    # Customization intelligence
            ResearchCategory.RESUME_FORMATS      # Optimization intelligence
        ]

        for category in expected_categories:
            # Verify each category can be used for intelligence gathering
            research_data = ResearchData(
                category=category,
                industry="Test",
                data={"intelligence": f"test_{category.value}"},
                confidence_score=0.8,
                sources=["test_source"],
                timestamp=time.time(),
                expiry_time=time.time() + 3600,
                version="test"
            )

            assert research_data.category == category, f"Category {category} should be supported"
            # Verify hash generation works (hash uses industry + category + data content)
            hash_value = research_data.get_hash()
            assert isinstance(hash_value, str), "Hash should be string"
            assert len(hash_value) == 32, "Should generate MD5 hash"
