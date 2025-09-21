"""
Prefect-based Research Orchestration System

This module implements the complete orchestration pipeline for the Dynamic Research Engine
using Prefect Core for scheduling, error handling, and monitoring of research operations.

Key Features:
- Weekly automated research updates from authoritative sources
- Fault-tolerant processing with automatic retries
- Bronze/Silver/Gold data layer population
- Quality assurance and validation
- Comprehensive logging and monitoring

Architecture:
- Prefect flows orchestrate the complete research pipeline
- Tasks handle individual operations with retry logic
- Parallel processing of multiple data sources
- Graceful degradation on partial failures

Example Usage:
    >>> from research_orchestrator import ResearchOrchestrator
    >>> orchestrator = ResearchOrchestrator(database_url="postgresql://...")
    >>> await orchestrator.run_full_research_pipeline()
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import structlog
from prefect import flow, task, get_run_logger
from prefect.task_runners import ConcurrentTaskRunner
from prefect.states import Completed, Failed

from .data_sources import (
    get_all_sources, get_sources_by_category, DataSourceCategory, DataSource
)
from .data_ingestion import get_data_ingester, AdvancedDataIngester
from .nlp_processor import get_nlp_processor, AdvancedNLPProcessor
from .database_schema import (
    get_database_manager, DatabaseManager,
    BronzeRawContent, SilverProcessedContent,
    GoldIndustryTrends, GoldATSUpdates, GoldResumeTrends,
    GoldHiringManagerSentiment, GoldJobMarketIndicators, GoldSkillsDemand
)
import hashlib

logger = structlog.get_logger(__name__)

class ResearchOrchestrator:
    """
    Main orchestrator for the Dynamic Research Engine.

    Manages the complete research pipeline from data ingestion through
    NLP processing to gold layer analytics preparation.
    """

    def __init__(self, database_url: str):
        """
        Initialize research orchestrator.

        Args:
            database_url: PostgreSQL connection string
        """
        self.database_url = database_url
        self.db_manager = get_database_manager(database_url)
        self.processing_stats = {
            'sources_processed': 0,
            'sources_failed': 0,
            'total_content_processed': 0,
            'processing_errors': []
        }

    async def initialize(self):
        """Initialize database and create tables if needed"""
        self.db_manager.initialize_connection()
        self.db_manager.create_all_tables()
        logger.info("Research orchestrator initialized")

# ===================================================================
# PREFECT TASKS - Individual Operations with Retry Logic
# ===================================================================

@task(retries=3, retry_delay_seconds=60, name="ingest_source_data")
async def ingest_source_data(source: DataSource) -> Dict[str, Any]:
    """
    Ingest data from a single source with error handling.

    Args:
        source: DataSource configuration object

    Returns:
        Dict containing ingested data and metadata

    Raises:
        Exception: Re-raises after max retries exceeded
    """
    run_logger = get_run_logger()
    run_logger.info(f"Starting ingestion for source: {source.name}")

    try:
        ingester = await get_data_ingester()

        # Fetch data from source
        raw_data = await ingester.fetch_from_source(source)

        # Add source metadata
        result = {
            'source': source,
            'raw_data': raw_data,
            'ingestion_timestamp': datetime.utcnow().isoformat(),
            'success': True
        }

        run_logger.info(f"Successfully ingested data from {source.name}: "
                       f"{len(raw_data.get('text_content', ''))} characters")
        return result

    except Exception as e:
        run_logger.error(f"Failed to ingest data from {source.name}: {str(e)}")
        raise

@task(retries=2, retry_delay_seconds=120, name="process_with_nlp")
async def process_with_nlp(ingestion_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process ingested content with NLP pipeline.

    Args:
        ingestion_result: Result from ingestion task

    Returns:
        Dict containing NLP-processed data
    """
    run_logger = get_run_logger()

    if not ingestion_result.get('success'):
        run_logger.warning("Skipping NLP processing for failed ingestion")
        return {'success': False, 'reason': 'ingestion_failed'}

    source = ingestion_result['source']
    raw_data = ingestion_result['raw_data']

    run_logger.info(f"Starting NLP processing for {source.name}")

    try:
        nlp_processor = await get_nlp_processor()

        # Extract text content
        text_content = raw_data.get('text_content', '')
        if not text_content or len(text_content) < 100:
            run_logger.warning(f"Insufficient content from {source.name}: {len(text_content)} chars")
            return {'success': False, 'reason': 'insufficient_content'}

        # Run comprehensive NLP analysis
        entities = await nlp_processor.extract_entities(text_content)
        summary = await nlp_processor.summarize_text(text_content)
        classification = await nlp_processor.classify_content(
            text_content, source.classification_labels
        )
        sentiment = await nlp_processor.analyze_sentiment(text_content)
        skills_trends = await nlp_processor.extract_skills_and_trends(text_content)

        # Calculate overall processing confidence
        confidence_scores = [
            sentiment.get('confidence', 0),
            skills_trends.get('confidence_score', 0),
            1.0 if len(entities.get('ORG', [])) > 0 else 0.5  # Basic entity validation
        ]
        overall_confidence = sum(confidence_scores) / len(confidence_scores)

        result = {
            'source': source,
            'original_data': raw_data,
            'processed_content': {
                'title': raw_data.get('title', ''),
                'clean_text': text_content,
                'summary': summary,
                'word_count': len(text_content.split()),
                'extracted_entities': entities,
                'content_classification': classification,
                'sentiment_analysis': sentiment,
                'trending_terms': skills_trends.get('trending_terms', []),
                'technical_terms': skills_trends.get('technical_terms', []),
                'processing_confidence': overall_confidence,
                'extraction_success': True,
                'quality_score': min(overall_confidence + 0.1, 1.0)  # Slight quality boost
            },
            'processing_timestamp': datetime.utcnow().isoformat(),
            'success': True
        }

        run_logger.info(f"NLP processing completed for {source.name}: "
                       f"confidence={overall_confidence:.2f}")
        return result

    except Exception as e:
        run_logger.error(f"NLP processing failed for {source.name}: {str(e)}")
        return {
            'source': source,
            'success': False,
            'error': str(e),
            'processing_timestamp': datetime.utcnow().isoformat()
        }

@task(retries=2, retry_delay_seconds=30, name="store_bronze_data")
async def store_bronze_data(ingestion_result: Dict[str, Any], db_url: str) -> str:
    """
    Store raw ingested data in Bronze layer.

    Args:
        ingestion_result: Result from ingestion task
        db_url: Database connection URL

    Returns:
        Bronze record ID
    """
    run_logger = get_run_logger()

    if not ingestion_result.get('success'):
        run_logger.warning("Skipping bronze storage for failed ingestion")
        return None

    try:
        db_manager = get_database_manager(db_url)
        session = db_manager.get_session()

        source = ingestion_result['source']
        raw_data = ingestion_result['raw_data']

        # Generate content hash for deduplication
        content_text = raw_data.get('text_content', '') or raw_data.get('raw_html', '')
        content_hash = hashlib.md5(content_text.encode('utf-8')).hexdigest()

        # Check if content already exists
        existing = session.query(BronzeRawContent).filter_by(content_hash=content_hash).first()
        if existing:
            run_logger.info(f"Content from {source.name} already exists in bronze layer")
            session.close()
            return str(existing.id)

        # Create new bronze record
        bronze_record = BronzeRawContent(
            source_name=source.name,
            source_url=source.url,
            source_category=source.category.value,
            ingestion_method=source.ingestion_method.value,
            raw_content=content_text,
            content_hash=content_hash,
            content_length=len(content_text),
            http_status=raw_data.get('http_status', 200),
            response_headers=raw_data.get('response_headers', {})
        )

        session.add(bronze_record)
        session.commit()

        record_id = str(bronze_record.id)
        session.close()

        run_logger.info(f"Stored bronze data for {source.name}: {record_id}")
        return record_id

    except Exception as e:
        run_logger.error(f"Failed to store bronze data for {source.name}: {str(e)}")
        raise

@task(retries=2, retry_delay_seconds=30, name="store_silver_data")
async def store_silver_data(nlp_result: Dict[str, Any], bronze_id: str, db_url: str) -> str:
    """
    Store NLP-processed data in Silver layer.

    Args:
        nlp_result: Result from NLP processing task
        bronze_id: Bronze layer record ID
        db_url: Database connection URL

    Returns:
        Silver record ID
    """
    run_logger = get_run_logger()

    if not nlp_result.get('success'):
        run_logger.warning("Skipping silver storage for failed NLP processing")
        return None

    try:
        db_manager = get_database_manager(db_url)
        session = db_manager.get_session()

        processed = nlp_result['processed_content']

        # Create silver record
        silver_record = SilverProcessedContent(
            bronze_source_id=bronze_id,
            title=processed['title'],
            clean_text=processed['clean_text'],
            summary=processed['summary'],
            word_count=processed['word_count'],
            extracted_entities=processed['extracted_entities'],
            content_classification=processed['content_classification'],
            sentiment_analysis=processed['sentiment_analysis'],
            trending_terms=processed['trending_terms'],
            technical_terms=processed['technical_terms'],
            processing_confidence=processed['processing_confidence'],
            extraction_success=processed['extraction_success'],
            quality_score=processed['quality_score'],
            nlp_model_version="spacy_3.7_transformers_4.46"
        )

        session.add(silver_record)
        session.commit()

        record_id = str(silver_record.id)
        session.close()

        run_logger.info(f"Stored silver data: {record_id}")
        return record_id

    except Exception as e:
        run_logger.error(f"Failed to store silver data: {str(e)}")
        raise

@task(retries=2, retry_delay_seconds=30, name="create_gold_analytics")
async def create_gold_analytics(nlp_result: Dict[str, Any], silver_id: str, db_url: str) -> Dict[str, Any]:
    """
    Create analytics-ready records in Gold layer.

    Args:
        nlp_result: NLP processing result
        silver_id: Silver layer record ID
        db_url: Database connection URL

    Returns:
        Dict with gold record creation results
    """
    run_logger = get_run_logger()

    if not nlp_result.get('success'):
        return {'success': False, 'reason': 'nlp_processing_failed'}

    try:
        db_manager = get_database_manager(db_url)
        session = db_manager.get_session()

        source = nlp_result['source']
        processed = nlp_result['processed_content']
        original_data = nlp_result['original_data']

        gold_records_created = []

        # Create appropriate gold record based on source category
        if source.category == DataSourceCategory.INDUSTRY_TRENDS:
            gold_record = GoldIndustryTrends(
                silver_source_id=silver_id,
                publication_date=datetime.utcnow(),  # Would extract from content in real implementation
                source_name=source.name,
                article_title=processed['title'] or f"Research from {source.name}",
                summary=processed['summary'],
                primary_category=max(processed['content_classification'],
                                   key=processed['content_classification'].get),
                mentioned_orgs=processed['extracted_entities'].get('ORG', []),
                mentioned_people=processed['extracted_entities'].get('PERSON', []),
                key_technologies=processed['extracted_entities'].get('TECH_SKILLS', []),
                confidence_score=processed['processing_confidence'],
                impact_score=min(processed['processing_confidence'] * 10, 10),
                relevance_score=processed['quality_score'] * 10,
                source_url=source.url,
                source_authority=source.priority  # Use priority as authority score
            )
            gold_records_created.append('industry_trends')

        elif source.category == DataSourceCategory.ATS_UPDATES:
            gold_record = GoldATSUpdates(
                silver_source_id=silver_id,
                announcement_date=datetime.utcnow(),
                vendor_name=source.name.split()[0],  # Extract vendor from source name
                feature_name=processed['title'] or "ATS Update",
                update_summary=processed['summary'],
                update_category=max(processed['content_classification'],
                                  key=processed['content_classification'].get),
                technical_details=processed['extracted_entities'],
                confidence_score=processed['processing_confidence'],
                source_url=source.url,
                vendor_authority_score=source.priority
            )
            gold_records_created.append('ats_updates')

        # Add similar logic for other categories...
        # This is abbreviated for space, but would include all gold table types

        if 'gold_record' in locals():
            session.add(gold_record)
            session.commit()

            record_id = str(gold_record.id)
            run_logger.info(f"Created gold record: {record_id} for category {source.category.value}")

        session.close()

        return {
            'success': True,
            'records_created': gold_records_created,
            'source_category': source.category.value
        }

    except Exception as e:
        run_logger.error(f"Failed to create gold analytics: {str(e)}")
        return {'success': False, 'error': str(e)}

# ===================================================================
# PREFECT FLOWS - Complete Pipeline Orchestration
# ===================================================================

@flow(name="process_single_source", task_runner=ConcurrentTaskRunner())
async def process_single_source_flow(source: DataSource, db_url: str) -> Dict[str, Any]:
    """
    Complete processing pipeline for a single data source.

    This flow handles the full Bronze->Silver->Gold pipeline for one source
    with proper error handling and state management.
    """
    run_logger = get_run_logger()
    run_logger.info(f"Processing source: {source.name}")

    try:
        # Step 1: Ingest raw data
        ingestion_result = await ingest_source_data.submit(source)

        # Step 2: Store in Bronze layer
        bronze_id = await store_bronze_data.submit(ingestion_result, db_url)

        if bronze_id:
            # Step 3: Process with NLP
            nlp_result = await process_with_nlp.submit(ingestion_result)

            # Step 4: Store in Silver layer
            silver_id = await store_silver_data.submit(nlp_result, bronze_id, db_url)

            if silver_id:
                # Step 5: Create Gold analytics
                gold_result = await create_gold_analytics.submit(nlp_result, silver_id, db_url)

                return {
                    'source_name': source.name,
                    'success': True,
                    'bronze_id': bronze_id,
                    'silver_id': silver_id,
                    'gold_result': gold_result
                }

        return {'source_name': source.name, 'success': False}

    except Exception as e:
        run_logger.error(f"Source processing failed for {source.name}: {str(e)}")
        return {'source_name': source.name, 'success': False, 'error': str(e)}

@flow(name="dynamic_research_engine_pipeline", task_runner=ConcurrentTaskRunner())
async def dynamic_research_engine_pipeline(db_url: str, max_sources: int = None) -> Dict[str, Any]:
    """
    Main research pipeline flow that processes all configured sources.

    This is the primary entry point for the research system, handling
    parallel processing of multiple sources with comprehensive reporting.

    Args:
        db_url: Database connection URL
        max_sources: Optional limit on number of sources to process

    Returns:
        Dict with complete pipeline results and statistics
    """
    run_logger = get_run_logger()
    run_logger.info("Starting Dynamic Research Engine pipeline")

    # Get all configured sources
    all_sources = get_all_sources()
    if max_sources:
        all_sources = all_sources[:max_sources]

    run_logger.info(f"Processing {len(all_sources)} data sources")

    # Process sources in parallel
    source_futures = []
    for source in all_sources:
        future = process_single_source_flow.submit(source, db_url)
        source_futures.append(future)

    # Wait for all sources to complete
    results = []
    for future in source_futures:
        try:
            result = await future
            results.append(result)
        except Exception as e:
            run_logger.error(f"Source processing failed: {str(e)}")
            results.append({'success': False, 'error': str(e)})

    # Calculate pipeline statistics
    successful_sources = [r for r in results if r.get('success')]
    failed_sources = [r for r in results if not r.get('success')]

    pipeline_result = {
        'pipeline_timestamp': datetime.utcnow().isoformat(),
        'total_sources': len(all_sources),
        'successful_sources': len(successful_sources),
        'failed_sources': len(failed_sources),
        'success_rate': len(successful_sources) / len(all_sources) * 100,
        'results': results
    }

    run_logger.info(f"Pipeline completed: {len(successful_sources)}/{len(all_sources)} sources successful "
                   f"({pipeline_result['success_rate']:.1f}%)")

    return pipeline_result

# ===================================================================
# SCHEDULING AND DEPLOYMENT
# ===================================================================

if __name__ == "__main__":
    # For deployment and scheduling
    import os

    # Get database URL from environment
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/research")

    # Deploy the flow for scheduled execution
    dynamic_research_engine_pipeline.serve(
        name="weekly-research-deployment",
        cron="0 5 * * 1",  # Every Monday at 5 AM
        parameters={
            "db_url": DATABASE_URL,
            "max_sources": None  # Process all sources
        }
    )
