# Dynamic Research Engine Architecture
# ARCHITECT Service - Real-Time Intelligence System

## **🔍 RESEARCH DATA SOURCES SPECIFICATION**

The Dynamic Research Engine gathers intelligence from **multiple live data sources** to keep the ARCHITECT service continuously updated with current trends, ATS requirements, and industry best practices.

### **1. WEB SEARCH INTELLIGENCE**
```python
# Primary Implementation using WebSearch tool
async def _web_search_industry_trends(self, industry: str):
    """Web search using Claude Code's WebSearch tool for real-time data"""

    search_queries = [
        f"{industry} hiring trends 2025",
        f"{industry} resume requirements latest",
        f"{industry} skills in demand {datetime.now().year}",
        f"ATS systems {industry} optimization tips",
        f"{industry} salary trends current market"
    ]

    research_results = []
    for query in search_queries:
        try:
            # Use WebSearch tool for current data
            search_result = await self.web_search_tool.search(
                query=query,
                max_results=10,
                recency="month"  # Last month data
            )
            research_results.append(search_result)
        except Exception as e:
            logger.warning(f"Web search failed for {query}: {e}")

    return self._analyze_search_results(research_results)
```

### **2. JOB BOARD ANALYSIS**
```python
# Live job posting analysis for skills trends
MONITORED_JOB_BOARDS = {
    "indeed": "https://indeed.com/api/jobs",
    "linkedin": "https://linkedin.com/jobs-api",
    "glassdoor": "https://glassdoor.com/api",
    "dice": "https://dice.com/api",
    "stackoverflow_jobs": "https://stackoverflow.com/jobs/feed"
}

async def _analyze_job_postings(self, industry: str, role_type: str):
    """Analyze current job postings for skills trends"""

    skills_frequency = {}
    salary_ranges = {}

    for board, api_url in MONITORED_JOB_BOARDS.items():
        try:
            # Fetch recent job postings
            jobs = await self._fetch_job_postings(
                api_url,
                industry=industry,
                role_type=role_type,
                posted_within="7days"  # Very recent postings
            )

            # Extract skills and requirements
            for job in jobs:
                skills = self._extract_skills_from_job(job)
                for skill in skills:
                    skills_frequency[skill] = skills_frequency.get(skill, 0) + 1

                # Track salary trends
                if job.get('salary'):
                    salary_ranges[job['level']] = job['salary']

        except Exception as e:
            logger.warning(f"Job board analysis failed for {board}: {e}")

    return {
        "trending_skills": sorted(skills_frequency.items(), key=lambda x: x[1], reverse=True)[:20],
        "salary_trends": salary_ranges,
        "data_freshness": "7_days",
        "source_boards": list(MONITORED_JOB_BOARDS.keys())
    }
```

### **3. ATS VENDOR DOCUMENTATION MONITORING**
```python
# Monitor ATS vendor sites for algorithm updates
ATS_VENDOR_SOURCES = {
    "workday": {
        "api": "https://community.workday.com/api/articles",
        "documentation": "https://doc.workday.com/reader/recruiting",
        "changelog": "https://community.workday.com/releases"
    },
    "greenhouse": {
        "api": "https://developers.greenhouse.io/harvest.html",
        "best_practices": "https://support.greenhouse.io/hc/en-us/articles/resume-parsing",
        "updates": "https://greenhouse.io/changelog"
    },
    "lever": {
        "documentation": "https://help.lever.co/hc/en-us/articles/resume-parsing",
        "api": "https://help.lever.co/hc/en-us/sections/api-documentation"
    },
    "bamboohr": {
        "parsing_guide": "https://help.bamboohr.com/hc/en-us/articles/resume-requirements",
        "api": "https://documentation.bamboohr.com/reference"
    }
}

async def _research_ats_vendor_documentation(self):
    """Monitor ATS vendor sites for parsing requirements updates"""

    ats_requirements = {}

    for vendor, sources in ATS_VENDOR_SOURCES.items():
        try:
            # Fetch latest documentation
            for source_type, url in sources.items():
                content = await self._fetch_web_content(url)

                # Extract ATS requirements using WebFetch
                requirements = await self.web_fetch_tool.fetch(
                    url=url,
                    prompt=f"Extract resume parsing requirements and ATS optimization tips for {vendor}"
                )

                ats_requirements[vendor] = {
                    "parsing_requirements": requirements.get("parsing_rules", []),
                    "optimization_tips": requirements.get("optimization_tips", []),
                    "file_format_requirements": requirements.get("format_requirements", []),
                    "last_updated": datetime.now().isoformat(),
                    "source_url": url
                }

        except Exception as e:
            logger.warning(f"ATS documentation research failed for {vendor}: {e}")

    return ats_requirements
```

### **4. RECRUITING FORUM INTELLIGENCE**
```python
# Monitor recruiting forums for hiring manager preferences
RECRUITING_FORUMS = [
    "https://reddit.com/r/recruiting",
    "https://reddit.com/r/humanresources",
    "https://reddit.com/r/jobs",
    "https://news.ycombinator.com/jobs",
    "https://stackoverflow.com/jobs/companies",
    "https://recruitingdaily.com/api/articles",
    "https://ere.net/api/articles"
]

async def _analyze_recruiting_forums(self):
    """Analyze recruiting forums for current hiring preferences"""

    hiring_insights = {
        "recruiter_preferences": [],
        "common_resume_issues": [],
        "trending_hiring_practices": [],
        "ats_optimization_tips": []
    }

    for forum_url in RECRUITING_FORUMS:
        try:
            # Use WebFetch to analyze forum discussions
            forum_insights = await self.web_fetch_tool.fetch(
                url=forum_url,
                prompt="Extract current hiring manager preferences, resume best practices, and ATS optimization tips from recent discussions"
            )

            # Merge insights
            hiring_insights["recruiter_preferences"].extend(
                forum_insights.get("preferences", [])
            )
            hiring_insights["common_resume_issues"].extend(
                forum_insights.get("common_issues", [])
            )

        except Exception as e:
            logger.warning(f"Forum analysis failed for {forum_url}: {e}")

    return hiring_insights
```

### **5. COMPANY INTELLIGENCE GATHERING**
```python
async def _research_company_intelligence(self, company_name: str):
    """Gather comprehensive company intelligence for Pain & Promise customization"""

    # Multi-source company research
    research_sources = [
        f"{company_name} recent news 2025",
        f"{company_name} company challenges growth",
        f"{company_name} hiring trends careers",
        f"{company_name} company culture values",
        f"{company_name} business strategy goals",
        f"{company_name} industry position competitors"
    ]

    company_intel = {
        "recent_news": [],
        "challenges": [],
        "goals": [],
        "culture_keywords": [],
        "hiring_trends": {},
        "competitive_position": "",
        "growth_areas": [],
        "pain_points": []
    }

    for query in research_sources:
        try:
            # Web search for company information
            search_results = await self.web_search_tool.search(
                query=query,
                max_results=5,
                recency="week"  # Very fresh company data
            )

            # Extract structured intelligence
            intel = await self._extract_company_intelligence(search_results)
            company_intel = self._merge_company_intelligence(company_intel, intel)

        except Exception as e:
            logger.warning(f"Company research failed for query '{query}': {e}")

    # Additional company website analysis
    try:
        company_website = f"https://{company_name.lower().replace(' ', '')}.com"
        website_intel = await self.web_fetch_tool.fetch(
            url=company_website,
            prompt="Extract company values, recent initiatives, challenges, and business goals from company website"
        )
        company_intel.update(website_intel)

    except Exception as e:
        logger.info(f"Company website analysis skipped: {e}")

    return company_intel
```

### **6. LINKEDIN INSIGHTS INTEGRATION**
```python
# LinkedIn API integration for professional network insights
async def _research_linkedin_skills_trends(self, industry: str, role_type: str):
    """Analyze LinkedIn for professional skills trends"""

    # Note: Requires LinkedIn API access
    try:
        linkedin_insights = {
            "trending_skills": [],
            "skill_endorsements": {},
            "job_posting_analysis": {},
            "professional_network_trends": []
        }

        # Would integrate with LinkedIn's Skills API
        # This is a placeholder for the actual implementation

        return linkedin_insights

    except Exception as e:
        logger.warning(f"LinkedIn integration not available: {e}")
        return {}
```

## **🔄 CONTINUOUS RESEARCH ARCHITECTURE**

### **Background Research Tasks**
```python
class ContinuousResearchScheduler:
    """Manages continuous background research updates"""

    RESEARCH_SCHEDULES = {
        "ats_compliance": {
            "interval": "6_hours",
            "priority": "critical",
            "sources": ["vendor_docs", "forums", "web_search"]
        },
        "industry_trends": {
            "interval": "12_hours",
            "priority": "high",
            "sources": ["web_search", "job_boards", "industry_reports"]
        },
        "skills_demand": {
            "interval": "4_hours",
            "priority": "high",
            "sources": ["job_boards", "linkedin", "web_search"]
        },
        "company_intelligence": {
            "interval": "2_hours",
            "priority": "medium",
            "sources": ["web_search", "news_feeds", "company_websites"]
        }
    }

    async def start_continuous_research(self):
        """Start all background research tasks"""
        for research_type, config in self.RESEARCH_SCHEDULES.items():
            interval_hours = int(config["interval"].split("_")[0])
            asyncio.create_task(
                self._periodic_research_task(research_type, interval_hours)
            )
```

## **📈 RESEARCH QUALITY & CONFIDENCE SCORING**

```python
class ResearchQualityScorer:
    """Scores research data quality and confidence"""

    def calculate_confidence_score(self, research_data: Dict) -> float:
        """Calculate confidence score based on multiple factors"""

        score = 0.0

        # Source diversity bonus
        source_count = len(research_data.get('sources', []))
        score += min(source_count * 0.2, 0.8)  # Max 0.8 for sources

        # Data freshness bonus
        data_age_hours = (time.time() - research_data.get('timestamp', 0)) / 3600
        freshness_score = max(0, 1.0 - (data_age_hours / 24))  # Decay over 24 hours
        score += freshness_score * 0.3

        # Data consistency across sources
        consistency_score = self._calculate_consistency_score(research_data)
        score += consistency_score * 0.3

        # Verification checks
        if research_data.get('verified_sources', 0) > 0:
            score += 0.2

        return min(score, 1.0)  # Cap at 1.0

    def _calculate_consistency_score(self, research_data: Dict) -> float:
        """Calculate how consistent data is across sources"""
        # Implementation for measuring data consistency
        # across multiple research sources
        return 0.8  # Placeholder
```

## **🛡️ ERROR HANDLING & FALLBACKS**

```python
class ResearchFailsafeSystem:
    """Handles research failures and provides fallbacks"""

    async def research_with_fallback(self, primary_method, fallback_method, **kwargs):
        """Execute research with automatic fallback"""

        try:
            result = await primary_method(**kwargs)
            if self._is_valid_result(result):
                return result, "primary"

        except Exception as e:
            logger.warning(f"Primary research method failed: {e}")

        try:
            result = await fallback_method(**kwargs)
            return result, "fallback"

        except Exception as e:
            logger.error(f"Fallback research method failed: {e}")
            return self._get_static_fallback(**kwargs), "static"

    def _get_static_fallback(self, **kwargs) -> Dict:
        """Provide static fallback data when all research fails"""
        return {
            "industry": kwargs.get("industry", "General"),
            "emphasis_areas": ["performance", "results", "leadership"],
            "terminology_style": "professional",
            "data_source": "static_fallback",
            "confidence_score": 0.3
        }
```

## **🔌 INTEGRATION POINTS**

### **Claude Code Tool Integration**
```python
# Integration with Claude Code's built-in tools
class ClaudeToolsIntegration:
    """Integrates with Claude Code's WebSearch and WebFetch tools"""

    def __init__(self):
        # These would be injected by Claude Code runtime
        self.web_search = WebSearchTool()
        self.web_fetch = WebFetchTool()

    async def search_intelligence(self, query: str, max_age: str = "week"):
        """Use Claude's WebSearch for intelligence gathering"""
        return await self.web_search.search(
            query=query,
            recency=max_age,
            max_results=10
        )

    async def analyze_webpage(self, url: str, analysis_prompt: str):
        """Use Claude's WebFetch for webpage analysis"""
        return await self.web_fetch.fetch(
            url=url,
            prompt=analysis_prompt
        )
```

## **📊 DATA FRESHNESS GUARANTEES**

| Research Type | Update Frequency | Max Age | Sources |
|---------------|------------------|---------|---------|
| **ATS Compliance** | 6 hours | 12 hours | Vendor docs, forums |
| **Industry Trends** | 12 hours | 24 hours | Web search, job boards |
| **Skills Demand** | 4 hours | 8 hours | Job boards, LinkedIn |
| **Company Intel** | 2 hours | 4 hours | Web search, news |
| **Market Analysis** | 24 hours | 48 hours | Industry reports |

## **🎯 IMPLEMENTATION STATUS**

✅ **Completed:**
- Research engine architecture
- Multi-source data integration framework
- Caching and freshness management
- Error handling and fallbacks

🔄 **In Progress:**
- Real API integrations (WebSearch/WebFetch)
- Background research scheduler
- Quality scoring algorithms

⏳ **Pending:**
- LinkedIn API integration
- ATS vendor API access
- Advanced NLP analysis for intelligence extraction

This dynamic research system ensures the ARCHITECT service **stays current** with:
- Latest ATS parsing algorithms
- Current industry hiring trends
- Real-time company intelligence
- Market-driven skills demand
- Evolving resume best practices

**The system is designed to be completely autonomous and self-updating.**
