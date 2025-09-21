"""
Database Schema Definition for Dynamic Research Engine
Implements Medallion Architecture (Bronze, Silver, Gold layers)

This module defines the complete database schema for storing and organizing
research intelligence data in a structured, queryable format.

Bronze Layer: Raw, immutable source data
Silver Layer: Cleaned, parsed, structured data
Gold Layer: Aggregated, analysis-ready intelligence tables

Schema Design Philosophy:
- Immutable Bronze layer for audit trail and replayability
- Structured Silver layer for efficient processing
- Denormalized Gold layer optimized for fast analytics queries
- Comprehensive indexing for performance
- Foreign key constraints for data integrity
"""

from sqlalchemy import (
    create_engine, Column, Integer, String, Text, DateTime, Float,
    Boolean, JSON, ForeignKey, Index, CheckConstraint, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.dialects.postgresql import UUID, ARRAY
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
import structlog

logger = structlog.get_logger(__name__)

Base = declarative_base()

# ===================================================================
# BRONZE LAYER - Raw, Immutable Source Data
# ===================================================================

class BronzeRawContent(Base):
    """
    Stores raw, unprocessed content exactly as received from sources.
    Immutable for audit trail and pipeline replayability.
    """
    __tablename__ = 'bronze_raw_content'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_name = Column(String(255), nullable=False, index=True)
    source_url = Column(Text, nullable=False)
    source_category = Column(String(100), nullable=False, index=True)
    ingestion_method = Column(String(50), nullable=False)
    raw_content = Column(Text, nullable=False)  # Complete HTML/JSON
    content_hash = Column(String(64), nullable=False, unique=True)  # MD5 for deduplication
    ingestion_timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    content_length = Column(Integer, nullable=False)
    http_status = Column(Integer)
    response_headers = Column(JSON)

    # Relationships
    silver_entries = relationship("SilverProcessedContent", back_populates="bronze_source")

    __table_args__ = (
        Index('idx_bronze_source_timestamp', 'source_name', 'ingestion_timestamp'),
        Index('idx_bronze_category_timestamp', 'source_category', 'ingestion_timestamp'),
    )

# ===================================================================
# SILVER LAYER - Cleaned, Parsed, Structured Data
# ===================================================================

class SilverProcessedContent(Base):
    """
    Stores cleaned and NLP-processed content with extracted entities,
    classifications, and structured metadata.
    """
    __tablename__ = 'silver_processed_content'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bronze_source_id = Column(UUID(as_uuid=True), ForeignKey('bronze_raw_content.id'), nullable=False)

    # Extracted content
    title = Column(Text)
    clean_text = Column(Text, nullable=False)
    summary = Column(Text)  # NLP-generated summary
    word_count = Column(Integer, nullable=False)

    # NLP extractions (JSON fields)
    extracted_entities = Column(JSON)  # {"PERSON": [], "ORG": [], "TECH_SKILLS": []}
    content_classification = Column(JSON)  # {"category": score} pairs
    sentiment_analysis = Column(JSON)  # {"sentiment": "positive", "confidence": 0.85}
    trending_terms = Column(JSON)  # List of extracted trending terms
    technical_terms = Column(JSON)  # List of technical terminology

    # Processing metadata
    processing_timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    nlp_model_version = Column(String(50))
    processing_confidence = Column(Float)  # Overall confidence in extraction quality

    # Data quality indicators
    extraction_success = Column(Boolean, nullable=False, default=True)
    quality_score = Column(Float)  # 0.0 to 1.0 quality assessment

    # Relationships
    bronze_source = relationship("BronzeRawContent", back_populates="silver_entries")
    gold_entries = relationship("GoldIndustryTrends", back_populates="silver_source")

    __table_args__ = (
        Index('idx_silver_processing_time', 'processing_timestamp'),
        Index('idx_silver_confidence', 'processing_confidence'),
        CheckConstraint('processing_confidence >= 0.0 AND processing_confidence <= 1.0',
                       name='check_processing_confidence'),
        CheckConstraint('quality_score >= 0.0 AND quality_score <= 1.0',
                       name='check_quality_score'),
    )

# ===================================================================
# GOLD LAYER - Analysis-Ready Intelligence Tables
# ===================================================================

class GoldIndustryTrends(Base):
    """
    Aggregated industry trends and insights from authoritative sources.
    Optimized for fast analytical queries by ARCHITECT service.
    """
    __tablename__ = 'gold_industry_trends'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    silver_source_id = Column(UUID(as_uuid=True), ForeignKey('silver_processed_content.id'))

    # Core content
    publication_date = Column(DateTime, nullable=False, index=True)
    source_name = Column(String(100), nullable=False, index=True)
    article_title = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)

    # Categorization
    primary_category = Column(String(100), nullable=False, index=True)
    secondary_categories = Column(ARRAY(String(100)))  # PostgreSQL array
    industry_tags = Column(ARRAY(String(50)))  # ["technology", "healthcare", "finance"]

    # Extracted intelligence
    mentioned_orgs = Column(ARRAY(String(100)))  # Companies/organizations mentioned
    mentioned_people = Column(ARRAY(String(100)))  # Key people mentioned
    key_technologies = Column(ARRAY(String(50)))  # Tech mentioned
    market_predictions = Column(JSON)  # Structured predictions data

    # Metrics and scores
    confidence_score = Column(Float, nullable=False, index=True)
    impact_score = Column(Float)  # Estimated impact/importance (0-10)
    relevance_score = Column(Float)  # Relevance to career guidance (0-10)

    # Source metadata
    source_url = Column(Text, nullable=False, unique=True)  # Primary key candidate
    source_authority = Column(Float)  # Authority score of source (0-10)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    silver_source = relationship("SilverProcessedContent", back_populates="gold_entries")

    __table_args__ = (
        Index('idx_gold_trends_date_category', 'publication_date', 'primary_category'),
        Index('idx_gold_trends_confidence', 'confidence_score'),
        Index('idx_gold_trends_source_date', 'source_name', 'publication_date'),
        CheckConstraint('confidence_score >= 0.0 AND confidence_score <= 1.0',
                       name='check_trends_confidence'),
        CheckConstraint('impact_score >= 0.0 AND impact_score <= 10.0',
                       name='check_trends_impact'),
        CheckConstraint('relevance_score >= 0.0 AND relevance_score <= 10.0',
                       name='check_trends_relevance'),
    )

class GoldATSUpdates(Base):
    """
    ATS vendor updates and algorithm changes affecting resume optimization.
    """
    __tablename__ = 'gold_ats_updates'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    silver_source_id = Column(UUID(as_uuid=True), ForeignKey('silver_processed_content.id'))

    # Core update information
    announcement_date = Column(DateTime, nullable=False, index=True)
    vendor_name = Column(String(100), nullable=False, index=True)
    feature_name = Column(String(255), nullable=False)
    update_summary = Column(Text, nullable=False)

    # Categorization
    update_category = Column(String(100), nullable=False, index=True)
    # e.g., "parsing_algorithm", "ai_features", "ui_changes", "integrations"

    # Technical details
    affected_features = Column(ARRAY(String(100)))  # Features affected
    technical_details = Column(JSON)  # Structured technical information
    implementation_timeline = Column(String(100))  # "immediate", "Q2 2024", etc.

    # Impact assessment
    impact_on_resumes = Column(Text)  # How this affects resume optimization
    recommended_actions = Column(JSON)  # List of recommended actions for users
    confidence_score = Column(Float, nullable=False)

    # Source metadata
    source_url = Column(Text, nullable=False, unique=True)
    vendor_authority_score = Column(Float)  # Vendor reliability score

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_gold_ats_vendor_date', 'vendor_name', 'announcement_date'),
        Index('idx_gold_ats_category', 'update_category'),
        CheckConstraint('confidence_score >= 0.0 AND confidence_score <= 1.0',
                       name='check_ats_confidence'),
    )

class GoldResumeTrends(Base):
    """
    Current resume formatting and content trends from expert sources.
    """
    __tablename__ = 'gold_resume_trends'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    silver_source_id = Column(UUID(as_uuid=True), ForeignKey('silver_processed_content.id'))

    # Trend information
    trend_id = Column(String(100), unique=True)  # Unique identifier for trend
    publication_date = Column(DateTime, nullable=False, index=True)
    source_name = Column(String(100), nullable=False, index=True)
    trend_title = Column(String(255), nullable=False)
    trend_summary = Column(Text, nullable=False)

    # Categorization
    trend_category = Column(String(100), nullable=False, index=True)
    # e.g., "formatting", "content_structure", "ats_optimization", "design"

    # Specific guidance
    actionable_advice = Column(JSON)  # List of specific actions
    examples = Column(JSON)  # Before/after examples, templates, etc.
    tools_recommended = Column(ARRAY(String(100)))  # Recommended tools/software

    # Applicability
    is_ats_focused = Column(Boolean, nullable=False, default=False, index=True)
    target_industries = Column(ARRAY(String(50)))  # Industries this applies to
    experience_levels = Column(ARRAY(String(50)))  # ["entry", "mid", "senior", "executive"]

    # Quality metrics
    evidence_strength = Column(Float)  # How well-evidenced is this trend (0-10)
    adoption_rate = Column(Float)  # Estimated adoption rate (0-1)
    confidence_score = Column(Float, nullable=False)

    # Source metadata
    source_url = Column(Text, nullable=False)
    expert_credibility = Column(Float)  # Credibility of source expert (0-10)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_gold_resume_trends_category_date', 'trend_category', 'publication_date'),
        Index('idx_gold_resume_trends_ats', 'is_ats_focused'),
        CheckConstraint('confidence_score >= 0.0 AND confidence_score <= 1.0',
                       name='check_resume_trends_confidence'),
        CheckConstraint('evidence_strength >= 0.0 AND evidence_strength <= 10.0',
                       name='check_evidence_strength'),
        CheckConstraint('adoption_rate >= 0.0 AND adoption_rate <= 1.0',
                       name='check_adoption_rate'),
    )

class GoldHiringManagerSentiment(Base):
    """
    Aggregated hiring manager sentiment and preferences from forum discussions.
    """
    __tablename__ = 'gold_hiring_manager_sentiment'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Topic and time period
    topic = Column(String(255), nullable=False, index=True)
    # e.g., "ats_systems", "resume_length", "remote_work", "skill_requirements"
    analysis_month = Column(DateTime, nullable=False, index=True)  # Month being analyzed

    # Sentiment metrics
    avg_sentiment_score = Column(Float, nullable=False)  # -1.0 to 1.0
    sentiment_distribution = Column(JSON)  # {"positive": 0.4, "neutral": 0.3, "negative": 0.3}
    discussion_volume = Column(Integer, nullable=False)  # Number of posts/comments analyzed

    # Content analysis
    key_themes = Column(JSON)  # List of key themes/subtopics
    representative_quotes = Column(JSON)  # List of representative quotes
    pain_points = Column(JSON)  # List of identified pain points
    positive_feedback = Column(JSON)  # List of positive aspects

    # Quality metrics
    analysis_confidence = Column(Float, nullable=False)  # Confidence in sentiment analysis
    sample_size = Column(Integer, nullable=False)  # Number of discussions analyzed
    data_quality_score = Column(Float)  # Quality of source discussions (0-1)

    # Source metadata
    source_platforms = Column(ARRAY(String(50)))  # ["reddit_recruiting", "linkedin", etc.]
    analysis_methodology = Column(String(100))  # Method used for analysis

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_gold_sentiment_topic_month', 'topic', 'analysis_month'),
        Index('idx_gold_sentiment_score', 'avg_sentiment_score'),
        CheckConstraint('avg_sentiment_score >= -1.0 AND avg_sentiment_score <= 1.0',
                       name='check_sentiment_range'),
        CheckConstraint('analysis_confidence >= 0.0 AND analysis_confidence <= 1.0',
                       name='check_sentiment_confidence'),
        CheckConstraint('data_quality_score >= 0.0 AND data_quality_score <= 1.0',
                       name='check_sentiment_quality'),
        UniqueConstraint('topic', 'analysis_month', name='unique_topic_month'),
    )

class GoldJobMarketIndicators(Base):
    """
    Economic indicators and job market statistics from government sources.
    """
    __tablename__ = 'gold_job_market_indicators'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Indicator identification
    indicator_name = Column(String(255), nullable=False, index=True)
    series_id = Column(String(50), nullable=False, index=True)  # BLS series ID
    period = Column(DateTime, nullable=False, index=True)  # Time period for this data point

    # Values
    value = Column(Float, nullable=False)
    previous_period_value = Column(Float)  # For change calculation
    year_over_year_value = Column(Float)  # Same period previous year

    # Calculated changes
    period_change = Column(Float)  # Change from previous period
    period_change_percent = Column(Float)  # Percentage change from previous period
    year_over_year_change = Column(Float)  # Change from same period last year
    year_over_year_change_percent = Column(Float)  # YoY percentage change

    # Context and interpretation
    interpretation = Column(String(500))  # Brief interpretation of the value
    trend_direction = Column(String(20))  # "improving", "declining", "stable"
    economic_context = Column(Text)  # Broader economic context

    # Data quality
    is_preliminary = Column(Boolean, default=False)  # Is this preliminary data?
    revision_status = Column(String(50))  # "original", "revised", "final"
    data_source_quality = Column(Float, default=1.0)  # Source reliability (0-1)

    # Timestamps
    data_release_date = Column(DateTime, nullable=False)  # When BLS released this data
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_gold_indicators_name_period', 'indicator_name', 'period'),
        Index('idx_gold_indicators_series_period', 'series_id', 'period'),
        Index('idx_gold_indicators_release_date', 'data_release_date'),
        UniqueConstraint('series_id', 'period', name='unique_series_period'),
    )

class GoldSkillsDemand(Base):
    """
    Skills demand trends from educational platforms and job market analysis.
    """
    __tablename__ = 'gold_skills_demand'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Skill identification
    skill_name = Column(String(255), nullable=False, index=True)
    skill_category = Column(String(100), nullable=False, index=True)
    # e.g., "programming", "data_analysis", "leadership", "design"

    # Time and context
    analysis_month = Column(DateTime, nullable=False, index=True)
    geographic_scope = Column(String(100), default="US")  # Geographic scope of analysis

    # Demand metrics
    demand_score = Column(Float, nullable=False)  # Normalized demand score (0-100)
    demand_growth_rate = Column(Float)  # Monthly growth rate
    job_posting_mentions = Column(Integer)  # Number of job postings mentioning skill
    course_enrollment_trend = Column(Float)  # Course enrollment growth rate

    # Market context
    industry_breakdown = Column(JSON)  # Demand by industry {"tech": 40, "finance": 25, ...}
    experience_level_breakdown = Column(JSON)  # Demand by experience level
    geographic_demand = Column(JSON)  # Demand by geographic region
    salary_impact = Column(JSON)  # Salary premium data {"median_premium": 15000, ...}

    # Related skills and pathways
    related_skills = Column(ARRAY(String(100)))  # Skills commonly learned together
    prerequisite_skills = Column(ARRAY(String(100)))  # Skills typically needed first
    career_paths = Column(JSON)  # Career paths this skill enables

    # Data sources and quality
    source_platforms = Column(ARRAY(String(50)))  # ["coursera", "linkedin", "indeed"]
    confidence_score = Column(Float, nullable=False)  # Overall confidence (0-1)
    sample_size = Column(Integer)  # Number of data points analyzed

    # Future outlook
    projected_demand_6m = Column(Float)  # Projected demand in 6 months
    projected_demand_12m = Column(Float)  # Projected demand in 12 months
    trend_classification = Column(String(50))  # "emerging", "growing", "stable", "declining"

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_gold_skills_name_month', 'skill_name', 'analysis_month'),
        Index('idx_gold_skills_category_month', 'skill_category', 'analysis_month'),
        Index('idx_gold_skills_demand_score', 'demand_score'),
        CheckConstraint('demand_score >= 0.0 AND demand_score <= 100.0',
                       name='check_demand_score_range'),
        CheckConstraint('confidence_score >= 0.0 AND confidence_score <= 1.0',
                       name='check_skills_confidence'),
        UniqueConstraint('skill_name', 'analysis_month', 'geographic_scope',
                        name='unique_skill_month_geo'),
    )

# ===================================================================
# DATABASE MANAGEMENT UTILITIES
# ===================================================================

class DatabaseManager:
    """
    Manages database connections, schema creation, and maintenance operations.
    """

    def __init__(self, database_url: str):
        """
        Initialize database manager with connection URL.

        Args:
            database_url: PostgreSQL connection string
                Example: "postgresql://user:pass@localhost:5432/research_db"
        """
        self.database_url = database_url
        self.engine = None
        self.SessionLocal = None

    def initialize_connection(self):
        """Initialize database engine and session factory"""
        self.engine = create_engine(
            self.database_url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,  # Verify connections before use
            echo=False  # Set to True for SQL debugging
        )

        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

        logger.info("Database connection initialized")

    def create_all_tables(self):
        """Create all tables if they don't exist"""
        if not self.engine:
            self.initialize_connection()

        Base.metadata.create_all(bind=self.engine)
        logger.info("All database tables created successfully")

    def drop_all_tables(self):
        """Drop all tables (use with caution!)"""
        if not self.engine:
            self.initialize_connection()

        Base.metadata.drop_all(bind=self.engine)
        logger.info("All database tables dropped")

    def get_session(self):
        """Get a database session"""
        if not self.SessionLocal:
            self.initialize_connection()
        return self.SessionLocal()

    def get_table_counts(self) -> Dict[str, int]:
        """Get row counts for all tables"""
        session = self.get_session()
        try:
            counts = {}
            for table_class in [BronzeRawContent, SilverProcessedContent,
                              GoldIndustryTrends, GoldATSUpdates, GoldResumeTrends,
                              GoldHiringManagerSentiment, GoldJobMarketIndicators,
                              GoldSkillsDemand]:
                count = session.query(table_class).count()
                counts[table_class.__tablename__] = count
            return counts
        finally:
            session.close()

# Global database manager instance
db_manager = None

def get_database_manager(database_url: str = None) -> DatabaseManager:
    """
    Get global database manager instance.

    Args:
        database_url: Database connection URL (required on first call)

    Returns:
        DatabaseManager instance
    """
    global db_manager
    if db_manager is None:
        if database_url is None:
            raise ValueError("database_url is required on first call")
        db_manager = DatabaseManager(database_url)
    return db_manager
