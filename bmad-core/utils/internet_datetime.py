"""
Internet-based Date and Time Utilities for Helios Career Operations System

This module provides centralized date/time functionality that fetches the actual
current date from internet sources to ensure accuracy across all system components.

Usage:
    from bmad_core.utils import get_current_datetime, get_current_date
    
    # Get current datetime with internet verification
    current_dt = get_current_datetime()
    
    # Get current date string
    current_date = get_current_date()
"""

import asyncio
import logging
import re
from datetime import datetime, timezone
from typing import Optional, Union
import aiohttp
import json

logger = logging.getLogger(__name__)


class InternetDateTimeService:
    """Service for fetching accurate current date/time from internet sources."""
    
    # Multiple reliable time sources for redundancy
    TIME_SOURCES = [
        {
            "name": "WorldTimeAPI Montreal",
            "url": "http://worldtimeapi.org/api/timezone/America/Montreal",
            "parser": "_parse_worldtime_api"
        },
        {
            "name": "WorldTimeAPI UTC",
            "url": "http://worldtimeapi.org/api/timezone/UTC", 
            "parser": "_parse_worldtime_api"
        },
        {
            "name": "TimeAPI Montreal",
            "url": "http://timeapi.io/api/Time/current/zone?timeZone=America/Montreal",
            "parser": "_parse_timeapi"
        },
        {
            "name": "HTTP Date Header",
            "url": "http://www.google.com",
            "parser": "_parse_http_date_header"
        }
    ]
    
    def __init__(self, timeout: int = 5):
        """Initialize the service with timeout settings."""
        self.timeout = timeout
        self._fallback_offset = None  # Offset from local time when internet fails
        
    async def get_current_datetime(self) -> datetime:
        """
        Get current UTC datetime from internet sources.
        
        Returns:
            datetime: Current UTC datetime
            
        Raises:
            Exception: If all internet sources fail and no fallback available
        """
        # Try each source until one succeeds
        for source in self.TIME_SOURCES:
            try:
                logger.debug(f"Attempting to fetch time from {source['name']}")
                dt = await self._fetch_from_source(source)
                if dt:
                    logger.info(f"Successfully fetched time from {source['name']}: {dt}")
                    self._update_fallback_offset(dt)
                    return dt
            except Exception as e:
                logger.warning(f"Failed to fetch time from {source['name']}: {e}")
                continue
                
        # If all internet sources fail, use fallback with stored offset
        if self._fallback_offset is not None:
            fallback_dt = datetime.now(timezone.utc) + self._fallback_offset
            logger.warning(f"Using fallback time calculation: {fallback_dt}")
            return fallback_dt
            
        # Last resort: use system time with warning
        system_dt = datetime.now(timezone.utc)
        logger.error(f"All time sources failed, using system time: {system_dt}")
        return system_dt
        
    async def _fetch_from_source(self, source: dict) -> Optional[datetime]:
        """Fetch datetime from a specific source."""
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
            async with session.get(source["url"]) as response:
                if response.status == 200:
                    parser_method = getattr(self, source["parser"])
                    return await parser_method(response)
        return None
        
    async def _parse_worldtime_api(self, response) -> Optional[datetime]:
        """Parse WorldTimeAPI response."""
        data = await response.json()
        datetime_str = data.get("utc_datetime")
        if datetime_str:
            # Parse ISO format: 2025-09-07T22:30:45.123456+00:00
            return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        return None
        
    async def _parse_timeapi(self, response) -> Optional[datetime]:
        """Parse TimeAPI response.""" 
        data = await response.json()
        datetime_str = data.get("dateTime")
        if datetime_str:
            return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        return None
        
    async def _parse_http_date_header(self, response) -> Optional[datetime]:
        """Parse HTTP Date header from any web server."""
        date_header = response.headers.get('Date')
        if date_header:
            # Parse HTTP date format: "Sat, 07 Sep 2025 22:30:45 GMT"
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(date_header)
        return None
        
    def _update_fallback_offset(self, internet_time: datetime):
        """Update the fallback offset based on successful internet fetch."""
        local_time = datetime.now(timezone.utc) 
        self._fallback_offset = internet_time - local_time
        logger.debug(f"Updated fallback offset: {self._fallback_offset}")


# Global service instance
_service = InternetDateTimeService()


async def get_current_datetime() -> datetime:
    """
    Get the current UTC datetime from internet sources.
    
    This function ensures all system components use the accurate current date
    by fetching from reliable internet time sources.
    
    Returns:
        datetime: Current UTC datetime
    """
    return await _service.get_current_datetime()


def get_current_datetime_sync() -> datetime:
    """
    Synchronous version of get_current_datetime.
    
    Returns:
        datetime: Current UTC datetime
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're in an async context, create a new event loop in a thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _service.get_current_datetime())
                return future.result(timeout=10)
        else:
            return loop.run_until_complete(_service.get_current_datetime())
    except Exception as e:
        logger.error(f"Failed to get internet time synchronously: {e}")
        return datetime.now(timezone.utc)


async def get_current_date(format_str: str = "%Y-%m-%d") -> str:
    """
    Get the current date as a formatted string.
    
    Args:
        format_str: Date format string (default: YYYY-MM-DD)
        
    Returns:
        str: Formatted current date
    """
    dt = await get_current_datetime()
    return dt.strftime(format_str)


def get_current_date_sync(format_str: str = "%Y-%m-%d") -> str:
    """
    Synchronous version of get_current_date.
    
    Args:
        format_str: Date format string (default: YYYY-MM-DD)
        
    Returns:
        str: Formatted current date
    """
    dt = get_current_datetime_sync()
    return dt.strftime(format_str)


async def format_date_for_filename() -> str:
    """
    Get current date formatted for safe filename usage.
    
    Returns:
        str: Date in YYYYMMDD_HHMMSS format
    """
    dt = await get_current_datetime()
    return dt.strftime("%Y%m%d_%H%M%S")


def format_date_for_filename_sync() -> str:
    """
    Synchronous version of format_date_for_filename.
    
    Returns:
        str: Date in YYYYMMDD_HHMMSS format
    """
    dt = get_current_datetime_sync()
    return dt.strftime("%Y%m%d_%H%M%S")


# Convenience aliases for backward compatibility
get_current_date = get_current_date_sync
format_date_for_filename = format_date_for_filename_sync