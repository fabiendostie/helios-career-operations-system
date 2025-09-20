"""
Advanced Data Source Configuration and Management
Defines authoritative sources for research intelligence gathering
"""

from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum

class IngestionMethod(Enum):
    WEB_SCRAPING = "web_scraping_playwright"
    API_REQUEST = "api_requests"
    HYBRID = "hybrid"

class DataSourceCategory(Enum):
    INDUSTRY_TRENDS = "industry_trends"
    ATS_UPDATES = "ats_updates"  
    RESUME_TRENDS = "resume_trends"
    HIRING_SENTIMENT = "hiring_sentiment"
    JOB_MARKET = "job_market"
    SKILLS_DEMAND = "skills_demand"

@dataclass
class DataSource:
    name: str
    url: str
    category: DataSourceCategory
    ingestion_method: IngestionMethod
    update_frequency: str  # e.g., "weekly", "monthly"
    priority: int  # 1-10, higher is more important
    classification_labels: List[str]
    extraction_focus: str
    rate_limit_delay: float = 1.0  # seconds between requests

# ===================================================================
# AUTHORITATIVE DATA SOURCES CONFIGURATION
# ===================================================================

RESEARCH_DATA_SOURCES = {
    
    # INDUSTRY TRENDS - Tier 1 Consulting and Tech Giants
    DataSourceCategory.INDUSTRY_TRENDS: [
        DataSource(
            name="McKinsey Digital",
            url="https://www.mckinsey.com/capabilities/mckinsey-digital/our-insights",
            category=DataSourceCategory.INDUSTRY_TRENDS,
            ingestion_method=IngestionMethod.WEB_SCRAPING,
            update_frequency="weekly",
            priority=10,
            classification_labels=[
                "digital_transformation", "ai_adoption", "future_of_work", 
                "technology_trends", "business_strategy", "automation"
            ],
            extraction_focus="Extract key findings, strategic recommendations, and data-driven predictions from reports and articles",
            rate_limit_delay=3.0
        ),
        DataSource(
            name="Gartner HR Insights", 
            url="https://www.gartner.com/en/human-resources/insights",
            category=DataSourceCategory.INDUSTRY_TRENDS,
            ingestion_method=IngestionMethod.WEB_SCRAPING,
            update_frequency="weekly",
            priority=9,
            classification_labels=[
                "hr_technology", "talent_management", "employee_experience",
                "workforce_analytics", "recruitment_trends"
            ],
            extraction_focus="Focus on HR technology trends, workforce predictions, and talent acquisition insights"
        ),
        DataSource(
            name="Google AI Research",
            url="https://ai.google/research/",
            category=DataSourceCategory.INDUSTRY_TRENDS,
            ingestion_method=IngestionMethod.WEB_SCRAPING,
            update_frequency="weekly", 
            priority=8,
            classification_labels=[
                "machine_learning", "artificial_intelligence", "research_breakthroughs",
                "technical_innovation", "ai_applications"
            ],
            extraction_focus="Extract latest AI research developments and their potential industry applications"
        ),
        DataSource(
            name="Meta AI Research",
            url="https://ai.meta.com/",
            category=DataSourceCategory.INDUSTRY_TRENDS,
            ingestion_method=IngestionMethod.WEB_SCRAPING,
            update_frequency="weekly",
            priority=7,
            classification_labels=[
                "ai_research", "computer_vision", "nlp_advances", 
                "social_technology", "metaverse"
            ],
            extraction_focus="Focus on AI research with practical applications and emerging tech trends"
        )
    ],
    
    # ATS ALGORITHM UPDATES - Direct from Vendor Sources
    DataSourceCategory.ATS_UPDATES: [
        DataSource(
            name="Greenhouse Blog",
            url="https://www.greenhouse.com/blog",
            category=DataSourceCategory.ATS_UPDATES,
            ingestion_method=IngestionMethod.WEB_SCRAPING,
            update_frequency="weekly",
            priority=9,
            classification_labels=[
                "ats_features", "hiring_automation", "candidate_screening",
                "recruitment_technology", "product_updates"
            ],
            extraction_focus="Detail new functionality, impact on hiring process, and mentioned technologies like AI and semantic search"
        ),
        DataSource(
            name="Lever Blog",
            url="https://www.lever.co/blog",
            category=DataSourceCategory.ATS_UPDATES,
            ingestion_method=IngestionMethod.WEB_SCRAPING,
            update_frequency="weekly",
            priority=8,
            classification_labels=[
                "talent_acquisition", "recruiting_software", "hiring_insights",
                "candidate_experience", "ats_optimization"
            ],
            extraction_focus="Extract feature announcements, algorithmic improvements, and resume parsing updates"
        ),
        DataSource(
            name="iCIMS Newsroom",
            url="https://www.icims.com/company/corporate-newsroom/",
            category=DataSourceCategory.ATS_UPDATES,
            ingestion_method=IngestionMethod.WEB_SCRAPING,
            update_frequency="monthly",
            priority=7,
            classification_labels=[
                "talent_cloud", "ai_recruiting", "hiring_platform",
                "workforce_solutions"
            ],
            extraction_focus="Focus on platform updates and AI-powered recruiting enhancements"
        ),
        DataSource(
            name="Bullhorn Blog",
            url="https://www.bullhorn.com/blog/",
            category=DataSourceCategory.ATS_UPDATES,
            ingestion_method=IngestionMethod.WEB_SCRAPING,
            update_frequency="weekly",
            priority=6,
            classification_labels=[
                "staffing_technology", "recruiting_automation", "crm_integration"
            ],
            extraction_focus="Extract staffing industry updates and technology integrations"
        )
    ],
    
    # RESUME TRENDS - Expert Resume Guidance Sources
    DataSourceCategory.RESUME_TRENDS: [
        DataSource(
            name="Jobscan Blog",
            url="https://www.jobscan.co/blog/",
            category=DataSourceCategory.RESUME_TRENDS,
            ingestion_method=IngestionMethod.WEB_SCRAPING,
            update_frequency="weekly",
            priority=10,
            classification_labels=[
                "ats_optimization", "resume_keywords", "application_tracking",
                "resume_formatting", "job_matching"
            ],
            extraction_focus="Extract ATS optimization techniques, keyword strategies, and resume formatting best practices"
        ),
        DataSource(
            name="Novoresume Blog",
            url="https://novoresume.com/career-blog/",
            category=DataSourceCategory.RESUME_TRENDS,
            ingestion_method=IngestionMethod.WEB_SCRAPING,
            update_frequency="weekly",
            priority=8,
            classification_labels=[
                "resume_design", "career_advice", "job_search_strategy",
                "professional_branding"
            ],
            extraction_focus="Focus on modern resume design trends and career development strategies"
        ),
        DataSource(
            name="ResumeBuilder Career Center",
            url="https://www.resumebuilder.com/career-center/",
            category=DataSourceCategory.RESUME_TRENDS,
            ingestion_method=IngestionMethod.WEB_SCRAPING,
            update_frequency="bi-weekly",
            priority=7,
            classification_labels=[
                "resume_writing", "career_tips", "industry_guidance"
            ],
            extraction_focus="Extract resume structure advice and industry-specific guidance"
        )
    ],
    
    # HIRING MANAGER SENTIMENT - Ground Truth from Forums
    DataSourceCategory.HIRING_SENTIMENT: [
        DataSource(
            name="Reddit r/recruiting",
            url="https://www.reddit.com/r/recruiting/",
            category=DataSourceCategory.HIRING_SENTIMENT,
            ingestion_method=IngestionMethod.WEB_SCRAPING,
            update_frequency="daily",
            priority=8,
            classification_labels=[
                "recruiter_insights", "hiring_challenges", "candidate_quality",
                "recruitment_tools", "industry_discussions"
            ],
            extraction_focus="Analyze recruiter sentiment on resume trends, hiring challenges, and candidate preferences",
            rate_limit_delay=2.0
        ),
        DataSource(
            name="Reddit r/recruitinghell",
            url="https://www.reddit.com/r/recruitinghell/",
            category=DataSourceCategory.HIRING_SENTIMENT,
            ingestion_method=IngestionMethod.WEB_SCRAPING,
            update_frequency="daily",
            priority=6,
            classification_labels=[
                "candidate_frustration", "hiring_process_issues", "ats_problems"
            ],
            extraction_focus="Extract candidate perspectives on hiring process pain points and ATS issues"
        )
    ],
    
    # JOB MARKET INDICATORS - Government Economic Data
    DataSourceCategory.JOB_MARKET: [
        DataSource(
            name="U.S. Bureau of Labor Statistics API",
            url="https://api.bls.gov/publicAPI/v2/timeseries/data/",
            category=DataSourceCategory.JOB_MARKET,
            ingestion_method=IngestionMethod.API_REQUEST,
            update_frequency="monthly",
            priority=10,
            classification_labels=[],  # No classification needed for time series
            extraction_focus="Process unemployment rate, job openings, and employment statistics",
            rate_limit_delay=1.0
        )
    ],
    
    # SKILLS DEMAND - Educational and Professional Platform Data
    DataSourceCategory.SKILLS_DEMAND: [
        DataSource(
            name="Coursera Course Trends",
            url="https://www.coursera.org/browse",
            category=DataSourceCategory.SKILLS_DEMAND,
            ingestion_method=IngestionMethod.WEB_SCRAPING,
            update_frequency="monthly",
            priority=7,
            classification_labels=[
                "online_learning", "skill_development", "career_advancement",
                "technology_education"
            ],
            extraction_focus="Extract trending course categories and skill development patterns"
        ),
        DataSource(
            name="Udemy Business Insights",
            url="https://business.udemy.com/resources/",
            category=DataSourceCategory.SKILLS_DEMAND,
            ingestion_method=IngestionMethod.WEB_SCRAPING,
            update_frequency="monthly",
            priority=6,
            classification_labels=[
                "business_skills", "technical_training", "workforce_development"
            ],
            extraction_focus="Focus on enterprise skill development trends and workforce training insights"
        )
    ]
}

# BLS API Series IDs for Job Market Data
BLS_SERIES_IDS = {
    "unemployment_rate": "LNS14000000",
    "job_openings": "JTS00000000JOL",  
    "labor_force_participation": "LNS11300000",
    "employment_level": "LNS12000000"
}

# Rate limiting and request headers
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
}

def get_sources_by_category(category: DataSourceCategory) -> List[DataSource]:
    """Get all data sources for a specific category"""
    return RESEARCH_DATA_SOURCES.get(category, [])

def get_high_priority_sources() -> List[DataSource]:
    """Get all sources with priority >= 8"""
    high_priority = []
    for sources in RESEARCH_DATA_SOURCES.values():
        high_priority.extend([s for s in sources if s.priority >= 8])
    return sorted(high_priority, key=lambda x: x.priority, reverse=True)

def get_all_sources() -> List[DataSource]:
    """Get all configured data sources"""
    all_sources = []
    for sources in RESEARCH_DATA_SOURCES.values():
        all_sources.extend(sources)
    return sorted(all_sources, key=lambda x: x.priority, reverse=True)