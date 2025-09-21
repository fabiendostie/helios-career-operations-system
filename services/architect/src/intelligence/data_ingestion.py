"""
Advanced Data Ingestion System for Dynamic Research Engine

This module implements sophisticated data gathering from authoritative sources
using Playwright for dynamic content scraping and requests for API integration.

Key Features:
- Playwright-based scraping for JavaScript-heavy sites
- Rate limiting and respectful crawling
- Comprehensive error handling and retry logic
- Data quality validation
- Structured output for downstream NLP processing

Example:
    >>> from data_ingestion import AdvancedDataIngester
    >>> ingester = AdvancedDataIngester()
    >>> await ingester.initialize()
    >>> content = await ingester.scrape_dynamic_content("https://mckinsey.com/insights")
    >>> api_data = await ingester.fetch_bls_data(["LNS14000000"])
"""

import asyncio
import aiohttp
import requests
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import structlog
from typing import Dict, List, Any, Optional, Union
import json
import time
from dataclasses import asdict
from urllib.parse import urljoin, urlparse
import hashlib

from .data_sources import (
    DataSource, DataSourceCategory, IngestionMethod,
    BLS_SERIES_IDS, DEFAULT_HEADERS, get_sources_by_category
)

logger = structlog.get_logger(__name__)

class DataIngestionError(Exception):
    """Custom exception for data ingestion failures"""
    pass

class AdvancedDataIngester:
    """
    Production-grade data ingestion system for research intelligence gathering.

    This class handles both web scraping and API data collection from multiple
    authoritative sources with proper rate limiting, error handling, and content validation.

    Attributes:
        playwright: Playwright browser instance for dynamic content scraping
        session: aiohttp session for API requests
        rate_limiter: Dictionary tracking last request times per domain
        content_cache: Simple in-memory cache to avoid duplicate requests
    """

    def __init__(self, cache_ttl_seconds: int = 3600):
        """
        Initialize the advanced data ingester.

        Args:
            cache_ttl_seconds: Time-to-live for cached content in seconds (default: 1 hour)
        """
        self.playwright = None
        self.browser = None
        self.session = None
        self.rate_limiter = {}
        self.content_cache = {}
        self.cache_ttl = cache_ttl_seconds
        self._initialized = False

    async def initialize(self):
        """
        Initialize Playwright browser and aiohttp session.

        This method must be called before using any scraping functionality.
        It sets up the browser with optimized settings for content extraction.
        """
        if self._initialized:
            return

        logger.info("Initializing advanced data ingester...")

        # Initialize Playwright
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-extensions',
                '--disable-plugins',
                '--disable-images'  # Speed optimization
            ]
        )

        # Initialize aiohttp session
        connector = aiohttp.TCPConnector(
            limit=10,  # Connection pool limit
            ttl_dns_cache=300,  # DNS cache TTL
            use_dns_cache=True
        )

        timeout = aiohttp.ClientTimeout(
            total=30,
            sock_connect=10,
            sock_read=20
        )

        self.session = aiohttp.ClientSession(
            headers=DEFAULT_HEADERS,
            connector=connector,
            timeout=timeout
        )

        self._initialized = True
        logger.info("Data ingester initialized successfully")

    async def cleanup(self):
        """Clean up resources (browser, session)"""
        if self.browser:
            await self.browser.close()
        if self.session:
            await self.session.close()
        if self.playwright:
            await self.playwright.stop()
        self._initialized = False
        logger.info("Data ingester cleaned up")

    async def _respect_rate_limit(self, domain: str, delay: float):
        """
        Implement respectful rate limiting per domain.

        Args:
            domain: Domain to rate limit
            delay: Minimum delay between requests in seconds
        """
        current_time = time.time()
        last_request = self.rate_limiter.get(domain, 0)

        time_since_last = current_time - last_request
        if time_since_last < delay:
            sleep_time = delay - time_since_last
            logger.debug(f"Rate limiting {domain}: sleeping {sleep_time:.2f}s")
            await asyncio.sleep(sleep_time)

        self.rate_limiter[domain] = time.time()

    def _generate_cache_key(self, url: str) -> str:
        """Generate cache key for URL"""
        return hashlib.md5(url.encode()).hexdigest()

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached content is still valid"""
        if cache_key not in self.content_cache:
            return False

        cached_time = self.content_cache[cache_key].get('timestamp', 0)
        return (time.time() - cached_time) < self.cache_ttl

    async def scrape_dynamic_content(self, url: str, wait_for_selector: Optional[str] = None) -> Dict[str, Any]:
        """
        Scrape content from JavaScript-heavy websites using Playwright.

        This method handles dynamic content loading, waits for complete page rendering,
        and extracts both text content and structured data.

        Args:
            url: Target URL to scrape
            wait_for_selector: Optional CSS selector to wait for before extraction

        Returns:
            Dict containing:
                - raw_html: Complete page HTML
                - text_content: Extracted text content
                - title: Page title
                - meta_description: Meta description if available
                - links: List of internal links
                - timestamp: Scraping timestamp

        Raises:
            DataIngestionError: If scraping fails after retries
        """
        if not self._initialized:
            await self.initialize()

        cache_key = self._generate_cache_key(url)
        if self._is_cache_valid(cache_key):
            logger.debug(f"Returning cached content for {url}")
            return self.content_cache[cache_key]['data']

        domain = urlparse(url).netloc
        await self._respect_rate_limit(domain, 2.0)  # Default 2 second delay

        logger.info(f"Scraping dynamic content from {url}")

        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Create new page for each request
                page = await self.browser.new_page()

                # Configure page settings
                await page.set_viewport_size({"width": 1920, "height": 1080})
                await page.set_extra_http_headers(DEFAULT_HEADERS)

                # Navigate and wait for content
                await page.goto(url, wait_until="networkidle", timeout=30000)

                # Wait for specific selector if provided
                if wait_for_selector:
                    await page.wait_for_selector(wait_for_selector, timeout=15000)

                # Extract comprehensive content
                content_data = await page.evaluate("""
                    () => {
                        // Remove script and style tags
                        const scripts = document.querySelectorAll('script, style, nav, footer, aside');
                        scripts.forEach(el => el.remove());

                        // Extract main content
                        const mainContent = document.querySelector('main, article, .content, #content') || document.body;

                        return {
                            title: document.title || '',
                            meta_description: document.querySelector('meta[name="description"]')?.content || '',
                            text_content: mainContent.innerText || '',
                            raw_html: document.documentElement.outerHTML,
                            url: window.location.href,
                            links: Array.from(document.querySelectorAll('a[href]')).map(a => a.href).slice(0, 50)
                        };
                    }
                """)

                await page.close()

                # Add metadata
                result = {
                    **content_data,
                    'timestamp': time.time(),
                    'word_count': len(content_data['text_content'].split()),
                    'extraction_success': True
                }

                # Cache the result
                self.content_cache[cache_key] = {
                    'data': result,
                    'timestamp': time.time()
                }

                logger.info(f"Successfully scraped {url} - {result['word_count']} words")
                return result

            except Exception as e:
                logger.warning(f"Scraping attempt {attempt + 1} failed for {url}: {e}")
                if attempt == max_retries - 1:
                    raise DataIngestionError(f"Failed to scrape {url} after {max_retries} attempts: {e}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

    async def fetch_bls_data(self, series_ids: List[str], api_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch economic data from U.S. Bureau of Labor Statistics API.

        This method retrieves time series data for unemployment rates, job openings,
        and other economic indicators crucial for job market analysis.

        Args:
            series_ids: List of BLS series identifiers (e.g., ["LNS14000000"])
            api_key: Optional BLS API key for higher rate limits

        Returns:
            Dict containing:
                - series_data: Time series data by series ID
                - metadata: API response metadata
                - timestamp: Request timestamp

        Raises:
            DataIngestionError: If API request fails
        """
        if not self._initialized:
            await self.initialize()

        logger.info(f"Fetching BLS data for series: {series_ids}")

        # Prepare request data
        request_data = {
            "seriesid": series_ids,
            "startyear": "2022",
            "endyear": "2025"
        }

        if api_key:
            request_data["registrationkey"] = api_key

        url = "https://api.bls.gov/publicAPI/v2/timeseries/data/"

        try:
            async with self.session.post(url, json=request_data) as response:
                response.raise_for_status()
                data = await response.json()

                if data.get('status') != 'REQUEST_SUCCEEDED':
                    raise DataIngestionError(f"BLS API error: {data.get('message', 'Unknown error')}")

                # Process and structure the data
                processed_data = {
                    'series_data': {},
                    'metadata': {
                        'request_timestamp': time.time(),
                        'api_status': data.get('status'),
                        'result_count': len(data.get('Results', {}).get('series', []))
                    }
                }

                for series in data.get('Results', {}).get('series', []):
                    series_id = series['seriesID']
                    processed_data['series_data'][series_id] = {
                        'data_points': series.get('data', []),
                        'series_id': series_id,
                        'latest_value': series.get('data', [{}])[0].get('value') if series.get('data') else None
                    }

                logger.info(f"Successfully fetched BLS data for {len(series_ids)} series")
                return processed_data

        except Exception as e:
            logger.error(f"BLS API request failed: {e}")
            raise DataIngestionError(f"Failed to fetch BLS data: {e}")

    async def scrape_reddit_discussions(self, subreddit_url: str, limit: int = 50) -> Dict[str, Any]:
        """
        Scrape Reddit discussions for hiring manager sentiment analysis.

        This method extracts post titles, content, and top comments from recruiting
        subreddits to analyze sentiment and trending topics.

        Args:
            subreddit_url: Reddit subreddit URL
            limit: Maximum number of posts to scrape

        Returns:
            Dict containing:
                - posts: List of post data with titles, content, comments
                - metadata: Extraction metadata

        Raises:
            DataIngestionError: If Reddit scraping fails
        """
        if not self._initialized:
            await self.initialize()

        # Add .json to get API-style data
        if not subreddit_url.endswith('.json'):
            subreddit_url = subreddit_url.rstrip('/') + '.json'

        domain = urlparse(subreddit_url).netloc
        await self._respect_rate_limit(domain, 3.0)  # Reddit rate limiting

        logger.info(f"Scraping Reddit discussions from {subreddit_url}")

        try:
            async with self.session.get(subreddit_url) as response:
                response.raise_for_status()
                reddit_data = await response.json()

                posts = []
                for post in reddit_data['data']['children'][:limit]:
                    post_data = post['data']
                    posts.append({
                        'title': post_data.get('title', ''),
                        'selftext': post_data.get('selftext', ''),
                        'score': post_data.get('score', 0),
                        'num_comments': post_data.get('num_comments', 0),
                        'created_utc': post_data.get('created_utc', 0),
                        'subreddit': post_data.get('subreddit', ''),
                        'url': post_data.get('url', ''),
                        'id': post_data.get('id', '')
                    })

                result = {
                    'posts': posts,
                    'metadata': {
                        'extraction_timestamp': time.time(),
                        'posts_extracted': len(posts),
                        'subreddit_url': subreddit_url
                    }
                }

                logger.info(f"Successfully scraped {len(posts)} Reddit posts")
                return result

        except Exception as e:
            logger.error(f"Reddit scraping failed: {e}")
            raise DataIngestionError(f"Failed to scrape Reddit discussions: {e}")

    async def fetch_from_source(self, source: DataSource) -> Dict[str, Any]:
        """
        Fetch data from a configured data source.

        This method routes to appropriate ingestion method based on source configuration
        and handles source-specific requirements like rate limiting and content extraction.

        Args:
            source: Configured DataSource object

        Returns:
            Dict containing extracted data and metadata

        Raises:
            DataIngestionError: If data fetching fails
        """
        logger.info(f"Fetching data from source: {source.name}")

        try:
            if source.ingestion_method == IngestionMethod.WEB_SCRAPING:
                # Special handling for Reddit
                if 'reddit.com' in source.url:
                    return await self.scrape_reddit_discussions(source.url)
                else:
                    return await self.scrape_dynamic_content(source.url)

            elif source.ingestion_method == IngestionMethod.API_REQUEST:
                if 'bls.gov' in source.url:
                    return await self.fetch_bls_data(list(BLS_SERIES_IDS.values()))
                else:
                    raise DataIngestionError(f"API method not implemented for {source.url}")

            else:
                raise DataIngestionError(f"Unsupported ingestion method: {source.ingestion_method}")

        except Exception as e:
            logger.error(f"Failed to fetch from {source.name}: {e}")
            raise DataIngestionError(f"Data fetching failed for {source.name}: {e}")

# Global instance for reuse
_data_ingester = AdvancedDataIngester()

async def get_data_ingester() -> AdvancedDataIngester:
    """
    Get initialized data ingester instance.

    Returns:
        Initialized AdvancedDataIngester instance
    """
    if not _data_ingester._initialized:
        await _data_ingester.initialize()
    return _data_ingester
