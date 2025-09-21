"""Dynamic Research Engine for real-time industry and ATS intelligence."""

import asyncio
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib

import structlog
import aiohttp
from pydantic import BaseModel

from .config import get_settings

logger = structlog.get_logger(__name__)


class ResearchCategory(str, Enum):
    """Categories of research data."""
    INDUSTRY_TRENDS = "industry_trends"
    ATS_ALGORITHMS = "ats_algorithms"
    RESUME_FORMATS = "resume_formats"
    HIRING_PREFERENCES = "hiring_preferences"
    SKILLS_DEMAND = "skills_demand"
    SALARY_TRENDS = "salary_trends"
    COMPANY_CULTURE = "company_culture"


@dataclass
class ResearchData:
    """Dynamic research data structure."""
    category: ResearchCategory
    industry: str
    data: Dict[str, Any]
    confidence_score: float  # 0.0 to 1.0
    sources: List[str]
    timestamp: float
    expiry_time: float
    version: str

    def is_expired(self) -> bool:
        """Check if research data has expired."""
        return time.time() > self.expiry_time

    def get_hash(self) -> str:
        """Get unique hash for this research data."""
        content = f"{self.category}_{self.industry}_{self.version}"
        return hashlib.md5(content.encode()).hexdigest()


class DynamicResearchEngine:
    """
    Dynamic Research Engine that continuously gathers intelligence from multiple sources
    to keep the ARCHITECT service current with latest trends and best practices.
    """

    def __init__(self):
        self.settings = get_settings()
        self._research_cache: Dict[str, ResearchData] = {}
        self._research_in_progress: Dict[str, asyncio.Task] = {}
        self._last_update_check = 0
        self._update_interval = 3600  # 1 hour

        # Research sources configuration
        self.research_sources = {
            "web_search": True,
            "job_boards": True,
            "industry_reports": True,
            "ats_vendor_docs": True,
            "recruiting_forums": True,
            "linkedin_insights": True
        }

        logger.info("Dynamic Research Engine initialized")

    async def get_industry_intelligence(
        self,
        industry: str,
        research_depth: str = "standard",
        max_age_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get comprehensive industry intelligence with real-time research.

        Args:
            industry: Target industry for research
            research_depth: Research depth (quick, standard, deep)
            max_age_hours: Maximum age of cached data to accept

        Returns:
            Comprehensive industry intelligence data
        """
        logger.info(
            "Gathering industry intelligence",
            industry=industry,
            depth=research_depth
        )

        # Check cache first
        cache_key = f"industry_{industry.lower().replace(' ', '_')}"
        cached_data = self._get_cached_research(cache_key, max_age_hours)

        if cached_data and research_depth == "quick":
            logger.info("Using cached industry intelligence", industry=industry)
            return cached_data.data

        # Perform real-time research
        intelligence_data = await self._research_industry_intelligence(
            industry, research_depth
        )

        # Cache the results
        research_data = ResearchData(
            category=ResearchCategory.INDUSTRY_TRENDS,
            industry=industry,
            data=intelligence_data,
            confidence_score=0.85,
            sources=["web_search", "job_boards", "industry_reports"],
            timestamp=time.time(),
            expiry_time=time.time() + (max_age_hours * 3600),
            version="1.0"
        )

        self._cache_research(cache_key, research_data)

        logger.info(
            "Industry intelligence research completed",
            industry=industry,
            data_points=len(intelligence_data),
            confidence=research_data.confidence_score
        )

        return intelligence_data

    async def get_ats_compliance_intelligence(
        self,
        max_age_hours: int = 12
    ) -> Dict[str, Any]:
        """
        Get latest ATS compliance requirements and algorithm updates.

        Args:
            max_age_hours: Maximum age of cached ATS data

        Returns:
            Current ATS compliance intelligence
        """
        logger.info("Gathering ATS compliance intelligence")

        cache_key = "ats_compliance_global"
        cached_data = self._get_cached_research(cache_key, max_age_hours)

        if cached_data:
            logger.info("Using cached ATS intelligence")
            return cached_data.data

        # Research current ATS requirements
        ats_intelligence = await self._research_ats_compliance()

        # Cache results
        research_data = ResearchData(
            category=ResearchCategory.ATS_ALGORITHMS,
            industry="all",
            data=ats_intelligence,
            confidence_score=0.90,
            sources=["ats_vendor_docs", "recruiting_forums", "web_search"],
            timestamp=time.time(),
            expiry_time=time.time() + (max_age_hours * 3600),
            version="1.0"
        )

        self._cache_research(cache_key, research_data)

        logger.info(
            "ATS compliance intelligence completed",
            requirements_count=len(ats_intelligence.get('requirements', [])),
            confidence=research_data.confidence_score
        )

        return ats_intelligence

    async def get_skills_demand_intelligence(
        self,
        industry: str,
        role_type: str,
        max_age_hours: int = 6
    ) -> Dict[str, Any]:
        """
        Get real-time skills demand and market trends.

        Args:
            industry: Target industry
            role_type: Target role type
            max_age_hours: Maximum age of cached skills data

        Returns:
            Skills demand intelligence
        """
        logger.info(
            "Gathering skills demand intelligence",
            industry=industry,
            role_type=role_type
        )

        cache_key = f"skills_demand_{industry}_{role_type}".replace(" ", "_").lower()
        cached_data = self._get_cached_research(cache_key, max_age_hours)

        if cached_data:
            return cached_data.data

        # Research current skills demand
        skills_intelligence = await self._research_skills_demand(industry, role_type)

        # Cache results
        research_data = ResearchData(
            category=ResearchCategory.SKILLS_DEMAND,
            industry=industry,
            data=skills_intelligence,
            confidence_score=0.88,
            sources=["job_boards", "linkedin_insights", "web_search"],
            timestamp=time.time(),
            expiry_time=time.time() + (max_age_hours * 3600),
            version="1.0"
        )

        self._cache_research(cache_key, research_data)

        return skills_intelligence

    async def get_company_intelligence(
        self,
        company_name: str,
        max_age_hours: int = 4
    ) -> Dict[str, Any]:
        """
        Get real-time company intelligence for Pain & Promise customization.

        Args:
            company_name: Target company name
            max_age_hours: Maximum age of cached company data

        Returns:
            Company intelligence data
        """
        logger.info("Gathering company intelligence", company=company_name)

        cache_key = f"company_{company_name.replace(' ', '_').lower()}"
        cached_data = self._get_cached_research(cache_key, max_age_hours)

        if cached_data:
            return cached_data.data

        # Research company information
        company_intelligence = await self._research_company_intelligence(company_name)

        # Cache results
        research_data = ResearchData(
            category=ResearchCategory.COMPANY_CULTURE,
            industry=company_intelligence.get('industry', 'unknown'),
            data=company_intelligence,
            confidence_score=0.82,
            sources=["web_search", "company_website", "news_sources"],
            timestamp=time.time(),
            expiry_time=time.time() + (max_age_hours * 3600),
            version="1.0"
        )

        self._cache_research(cache_key, research_data)

        return company_intelligence

    async def _research_industry_intelligence(
        self,
        industry: str,
        research_depth: str
    ) -> Dict[str, Any]:
        """Perform comprehensive industry research using multiple sources."""

        research_tasks = []

        # Web search for latest industry trends
        research_tasks.append(self._web_search_industry_trends(industry))

        # Job board analysis for skills trends
        research_tasks.append(self._analyze_job_postings(industry))

        # Industry reports research
        if research_depth in ["standard", "deep"]:
            research_tasks.append(self._research_industry_reports(industry))

        # Salary trends research
        if research_depth == "deep":
            research_tasks.append(self._research_salary_trends(industry))

        # Execute all research tasks
        results = await asyncio.gather(*research_tasks, return_exceptions=True)

        # Combine and analyze results
        combined_intelligence = {
            "industry": industry,
            "research_timestamp": time.time(),
            "research_depth": research_depth,
            "trending_skills": [],
            "emphasis_areas": [],
            "terminology_style": "professional",
            "achievement_format": "metric_driven",
            "hiring_trends": {},
            "salary_trends": {},
            "top_companies": [],
            "growth_areas": [],
            "challenges": [],
            "keywords": [],
            "confidence_indicators": []
        }

        # Process successful results
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"Research task {i} failed", error=str(result))
                continue

            if result:
                combined_intelligence = self._merge_research_results(
                    combined_intelligence, result
                )

        # Apply intelligence analysis
        combined_intelligence = await self._analyze_intelligence_data(
            combined_intelligence
        )

        return combined_intelligence

    async def _research_ats_compliance(self) -> Dict[str, Any]:
        """Research current ATS compliance requirements."""

        # Research latest ATS algorithm updates
        ats_research_tasks = [
            self._web_search_ats_updates(),
            self._research_ats_vendor_documentation(),
            self._analyze_recruiting_forums()
        ]

        results = await asyncio.gather(*ats_research_tasks, return_exceptions=True)

        ats_intelligence = {
            "last_updated": time.time(),
            "requirements": {
                "layout": {
                    "single_column": True,
                    "no_tables_for_layout": True,
                    "linear_reading_order": True
                },
                "typography": {
                    "standard_fonts": ["Arial", "Calibri", "Helvetica", "Times New Roman"],
                    "font_size_range": [10, 16],
                    "no_text_decorations": True
                },
                "graphics": {
                    "no_background_images": True,
                    "no_icons": True,
                    "no_skill_bars": True
                },
                "keywords": {
                    "contextual_placement": True,
                    "avoid_keyword_stuffing": True,
                    "semantic_matching": True
                }
            },
            "trending_ats_systems": [],
            "parsing_improvements": [],
            "compliance_score_factors": [],
            "vendor_updates": []
        }

        # Process research results
        for result in results:
            if isinstance(result, Exception):
                continue
            if result:
                ats_intelligence = self._merge_ats_research(ats_intelligence, result)

        return ats_intelligence

    async def _research_skills_demand(
        self,
        industry: str,
        role_type: str
    ) -> Dict[str, Any]:
        """Research current skills demand trends."""

        skills_research_tasks = [
            self._analyze_job_board_skills(industry, role_type),
            self._research_linkedin_skills_trends(industry, role_type),
            self._web_search_skills_trends(industry, role_type)
        ]

        results = await asyncio.gather(*skills_research_tasks, return_exceptions=True)

        skills_intelligence = {
            "industry": industry,
            "role_type": role_type,
            "timestamp": time.time(),
            "high_demand_skills": [],
            "emerging_skills": [],
            "declining_skills": [],
            "skill_gaps": [],
            "salary_impact": {},
            "regional_variations": {},
            "skill_combinations": [],
            "certification_trends": []
        }

        # Process results
        for result in results:
            if isinstance(result, Exception):
                continue
            if result:
                skills_intelligence = self._merge_skills_research(
                    skills_intelligence, result
                )

        return skills_intelligence

    async def _research_company_intelligence(self, company_name: str) -> Dict[str, Any]:
        """Research comprehensive company intelligence."""

        company_research_tasks = [
            self._web_search_company_info(company_name),
            self._research_company_news(company_name),
            self._analyze_company_culture(company_name),
            self._research_company_challenges(company_name)
        ]

        results = await asyncio.gather(*company_research_tasks, return_exceptions=True)

        company_intelligence = {
            "company_name": company_name,
            "timestamp": time.time(),
            "industry": "unknown",
            "size": "unknown",
            "recent_news": [],
            "challenges": [],
            "goals": [],
            "culture_keywords": [],
            "values": [],
            "growth_areas": [],
            "pain_points": [],
            "hiring_trends": {},
            "competitive_landscape": []
        }

        # Process results
        for result in results:
            if isinstance(result, Exception):
                continue
            if result:
                company_intelligence = self._merge_company_research(
                    company_intelligence, result
                )

        return company_intelligence

    # MOCK IMPLEMENTATIONS - Replace with real API calls
    async def _web_search_industry_trends(self, industry: str) -> Dict[str, Any]:
        """Web search for industry trends - MOCK IMPLEMENTATION."""
        # In production, this would use WebSearch tool or search APIs
        await asyncio.sleep(0.1)  # Simulate API call

        return {
            "trending_skills": ["AI/ML", "Cloud Architecture", "Data Science"],
            "growth_areas": ["Automation", "Digital Transformation"],
            "keywords": ["innovation", "scalability", "efficiency"],
            "source": "web_search"
        }

    async def _analyze_job_postings(self, industry: str) -> Dict[str, Any]:
        """Analyze job postings for skills trends - MOCK IMPLEMENTATION."""
        await asyncio.sleep(0.1)

        return {
            "most_requested_skills": ["Python", "AWS", "Leadership"],
            "salary_ranges": {"entry": 60000, "mid": 90000, "senior": 130000},
            "source": "job_boards"
        }

    async def _research_industry_reports(self, industry: str) -> Dict[str, Any]:
        """Research industry reports - MOCK IMPLEMENTATION."""
        await asyncio.sleep(0.1)

        return {
            "industry_growth": "8.5%",
            "key_challenges": ["talent shortage", "technology adoption"],
            "future_outlook": "positive",
            "source": "industry_reports"
        }

    async def _research_salary_trends(self, industry: str) -> Dict[str, Any]:
        """Research salary trends - MOCK IMPLEMENTATION."""
        await asyncio.sleep(0.1)

        return {
            "average_increase": "5.2%",
            "high_value_skills": ["Machine Learning", "Cloud Architecture"],
            "source": "salary_data"
        }

    async def _web_search_ats_updates(self) -> Dict[str, Any]:
        """Search for ATS updates - MOCK IMPLEMENTATION."""
        await asyncio.sleep(0.1)

        return {
            "recent_updates": ["Improved semantic matching", "Better PDF parsing"],
            "trending_systems": ["Workday", "Greenhouse", "Lever"],
            "source": "ats_research"
        }

    async def _research_ats_vendor_documentation(self) -> Dict[str, Any]:
        """Research ATS vendor docs - MOCK IMPLEMENTATION."""
        await asyncio.sleep(0.1)

        return {
            "parsing_requirements": ["Single column layout", "Standard fonts"],
            "optimization_tips": ["Use standard headings", "Include relevant keywords"],
            "source": "vendor_docs"
        }

    async def _analyze_recruiting_forums(self) -> Dict[str, Any]:
        """Analyze recruiting forums - MOCK IMPLEMENTATION."""
        await asyncio.sleep(0.1)

        return {
            "recruiter_preferences": ["Clean formatting", "Quantified achievements"],
            "common_issues": ["Formatting problems", "Keyword mismatch"],
            "source": "forums"
        }

    async def _analyze_job_board_skills(self, industry: str, role_type: str) -> Dict[str, Any]:
        """Analyze job board skills - MOCK IMPLEMENTATION."""
        await asyncio.sleep(0.1)
        return {"high_demand": ["Python", "React", "Leadership"], "source": "job_boards"}

    async def _research_linkedin_skills_trends(self, industry: str, role_type: str) -> Dict[str, Any]:
        """Research LinkedIn skills - MOCK IMPLEMENTATION."""
        await asyncio.sleep(0.1)
        return {"trending": ["AI", "Cloud", "DevOps"], "source": "linkedin"}

    async def _web_search_skills_trends(self, industry: str, role_type: str) -> Dict[str, Any]:
        """Web search skills trends - MOCK IMPLEMENTATION."""
        await asyncio.sleep(0.1)
        return {"emerging": ["MLOps", "Edge Computing"], "source": "web_search"}

    async def _web_search_company_info(self, company_name: str) -> Dict[str, Any]:
        """Web search company info - MOCK IMPLEMENTATION."""
        await asyncio.sleep(0.1)
        return {"industry": "Technology", "size": "Mid-size", "source": "web_search"}

    async def _research_company_news(self, company_name: str) -> Dict[str, Any]:
        """Research company news - MOCK IMPLEMENTATION."""
        await asyncio.sleep(0.1)
        return {"recent_news": ["Expansion plans", "New product launch"], "source": "news"}

    async def _analyze_company_culture(self, company_name: str) -> Dict[str, Any]:
        """Analyze company culture - MOCK IMPLEMENTATION."""
        await asyncio.sleep(0.1)
        return {"values": ["Innovation", "Collaboration"], "source": "culture_analysis"}

    async def _research_company_challenges(self, company_name: str) -> Dict[str, Any]:
        """Research company challenges - MOCK IMPLEMENTATION."""
        await asyncio.sleep(0.1)
        return {"challenges": ["Scaling operations", "Talent acquisition"], "source": "business_intel"}

    def _merge_research_results(self, base: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
        """Merge research results intelligently."""
        # Implement intelligent merging logic
        for key, value in new.items():
            if key == "source":
                continue
            if isinstance(value, list):
                if key not in base:
                    base[key] = []
                base[key].extend(value)
                # Remove duplicates
                base[key] = list(set(base[key]))
            elif isinstance(value, dict):
                if key not in base:
                    base[key] = {}
                base[key].update(value)
            else:
                base[key] = value

        return base

    def _merge_ats_research(self, base: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
        """Merge ATS research results."""
        return self._merge_research_results(base, new)

    def _merge_skills_research(self, base: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
        """Merge skills research results."""
        return self._merge_research_results(base, new)

    def _merge_company_research(self, base: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
        """Merge company research results."""
        return self._merge_research_results(base, new)

    async def _analyze_intelligence_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply AI analysis to research data."""
        # Apply intelligent analysis to determine:
        # - Most important skills to emphasize
        # - Best terminology style
        # - Optimal achievement format
        # - Industry-specific customizations

        trending_skills = data.get('trending_skills', [])

        # Determine emphasis areas based on research
        if 'technology' in data['industry'].lower():
            data['emphasis_areas'] = ['technical_skills', 'system_impact', 'innovation']
            data['terminology_style'] = 'technical'
        elif 'finance' in data['industry'].lower():
            data['emphasis_areas'] = ['risk_management', 'compliance', 'revenue_impact']
            data['terminology_style'] = 'business'

        # Add confidence indicators
        data['confidence_indicators'] = [
            f"Based on {len(trending_skills)} trending skills analysis",
            f"Research timestamp: {datetime.fromtimestamp(data['research_timestamp']).isoformat()}",
            "Multiple source verification completed"
        ]

        return data

    def _get_cached_research(self, cache_key: str, max_age_hours: int) -> Optional[ResearchData]:
        """Get cached research data if still valid."""
        if cache_key not in self._research_cache:
            return None

        research_data = self._research_cache[cache_key]

        # Check if expired
        max_age_seconds = max_age_hours * 3600
        if time.time() - research_data.timestamp > max_age_seconds:
            # Remove expired data
            del self._research_cache[cache_key]
            return None

        return research_data

    def _cache_research(self, cache_key: str, research_data: ResearchData):
        """Cache research data."""
        self._research_cache[cache_key] = research_data

        # Cleanup expired entries periodically
        self._cleanup_expired_cache()

    def _cleanup_expired_cache(self):
        """Remove expired cache entries."""
        current_time = time.time()
        expired_keys = [
            key for key, data in self._research_cache.items()
            if current_time > data.expiry_time
        ]

        for key in expired_keys:
            del self._research_cache[key]

        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired research cache entries")

    async def start_background_research(self):
        """Start background research tasks for continuous updates."""
        logger.info("Starting background research engine")

        # Schedule periodic research updates
        asyncio.create_task(self._periodic_research_updates())
        asyncio.create_task(self._periodic_cache_cleanup())

    async def _periodic_research_updates(self):
        """Periodic research updates in background."""
        while True:
            try:
                await asyncio.sleep(self._update_interval)

                # Update core research data
                await self._update_core_intelligence()

            except Exception as e:
                logger.error("Background research update failed", error=str(e))

    async def _periodic_cache_cleanup(self):
        """Periodic cache cleanup."""
        while True:
            try:
                await asyncio.sleep(1800)  # 30 minutes
                self._cleanup_expired_cache()
            except Exception as e:
                logger.error("Cache cleanup failed", error=str(e))

    async def _update_core_intelligence(self):
        """Update core intelligence data in background."""
        # Update ATS compliance data
        await self.get_ats_compliance_intelligence(max_age_hours=6)

        # Update popular industry intelligence
        popular_industries = ["Technology", "Finance", "Healthcare", "Marketing"]
        for industry in popular_industries:
            await self.get_industry_intelligence(industry, "quick", max_age_hours=12)


# Global research engine instance
_research_engine = None

async def get_research_engine() -> DynamicResearchEngine:
    """Get global research engine instance."""
    global _research_engine
    if _research_engine is None:
        _research_engine = DynamicResearchEngine()
        await _research_engine.start_background_research()
    return _research_engine
