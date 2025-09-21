"""Profile Ingestor service integration client."""

import asyncio
import json
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

import aiohttp
from aiohttp import ClientTimeout, ClientSession
from pydantic import BaseModel, Field

from ..core.config import settings
from ..utils.logging_config import get_logger


logger = get_logger("profile_ingestor")


class IngestionRequest(BaseModel):
    """Profile Ingestor ingestion request model."""

    session_id: str = Field(..., description="Session identifier")
    file_paths: List[str] = Field(default_factory=list, description="Local file paths to process")
    text_content: Optional[str] = Field(None, description="Direct text content to process")
    user_context: Dict[str, Any] = Field(default_factory=dict, description="User context information")
    processing_options: Dict[str, Any] = Field(default_factory=dict, description="Processing options")


class IngestionResponse(BaseModel):
    """Profile Ingestor ingestion response model."""

    success: bool = Field(..., description="Whether ingestion was successful")
    session_id: str = Field(..., description="Session identifier")
    master_career_database: Dict[str, Any] = Field(..., description="Extracted career data")
    processing_summary: Dict[str, Any] = Field(..., description="Processing summary and metrics")
    errors: List[str] = Field(default_factory=list, description="Any processing errors")
    warnings: List[str] = Field(default_factory=list, description="Processing warnings")


class IngestionProgress(BaseModel):
    """Profile Ingestor progress tracking model."""

    session_id: str
    status: str  # "processing", "completed", "failed"
    progress_percent: float
    current_step: str
    estimated_completion: Optional[str] = None
    errors: List[str] = Field(default_factory=list)


class ProfileIngestorClient:
    """HTTP client for Profile Ingestor service communication."""

    def __init__(self, base_url: str = None, timeout_seconds: int = None):
        """Initialize Profile Ingestor client.

        Args:
            base_url: Profile Ingestor service base URL
            timeout_seconds: Request timeout in seconds
        """
        self.base_url = (base_url or settings.profile_ingestor_url).rstrip('/')
        self.timeout = ClientTimeout(total=timeout_seconds or settings.http_timeout_seconds)
        self._session: Optional[ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def _ensure_session(self):
        """Ensure HTTP session is created."""
        if not self._session or self._session.closed:
            connector = aiohttp.TCPConnector(
                limit=100,
                limit_per_host=30,
                keepalive_timeout=60
            )

            self._session = ClientSession(
                connector=connector,
                timeout=self.timeout,
                headers={
                    "User-Agent": f"{settings.app_name}/{settings.app_version}",
                    "Content-Type": "application/json"
                }
            )

    async def close(self):
        """Close HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def health_check(self) -> Dict[str, Any]:
        """Check Profile Ingestor service health.

        Returns:
            Health status information

        Raises:
            aiohttp.ClientError: If request fails
        """
        await self._ensure_session()

        try:
            url = f"{self.base_url}/health"

            async with self._session.get(url) as response:
                response.raise_for_status()
                return await response.json()

        except Exception as e:
            logger.error(f"Profile Ingestor health check failed: {str(e)}")
            raise

    async def ingest_files(
        self,
        session_id: str,
        file_paths: List[Union[str, Path]],
        user_context: Dict[str, Any] = None,
        processing_options: Dict[str, Any] = None
    ) -> IngestionResponse:
        """Ingest files through Profile Ingestor service.

        Args:
            session_id: Session identifier
            file_paths: List of file paths to process
            user_context: Additional user context
            processing_options: Processing configuration options

        Returns:
            Ingestion response with extracted data

        Raises:
            aiohttp.ClientError: If request fails
        """
        await self._ensure_session()

        try:
            request = IngestionRequest(
                session_id=session_id,
                file_paths=[str(path) for path in file_paths],
                user_context=user_context or {},
                processing_options=processing_options or {}
            )

            url = f"{self.base_url}/api/ingest"
            payload = request.model_dump()

            logger.info(f"Starting file ingestion for session {session_id}")
            logger.debug(f"Ingesting files: {file_paths}")

            async with self._session.post(url, json=payload) as response:
                response.raise_for_status()
                result = await response.json()

                logger.info(f"File ingestion completed for session {session_id}")
                return IngestionResponse(**result)

        except aiohttp.ClientError as e:
            logger.error(f"Profile Ingestor request failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during ingestion: {str(e)}")
            raise

    async def ingest_text(
        self,
        session_id: str,
        text_content: str,
        user_context: Dict[str, Any] = None,
        processing_options: Dict[str, Any] = None
    ) -> IngestionResponse:
        """Ingest text content through Profile Ingestor service.

        Args:
            session_id: Session identifier
            text_content: Text content to process
            user_context: Additional user context
            processing_options: Processing configuration options

        Returns:
            Ingestion response with extracted data

        Raises:
            aiohttp.ClientError: If request fails
        """
        await self._ensure_session()

        try:
            request = IngestionRequest(
                session_id=session_id,
                text_content=text_content,
                user_context=user_context or {},
                processing_options=processing_options or {}
            )

            url = f"{self.base_url}/api/ingest"
            payload = request.model_dump()

            logger.info(f"Starting text ingestion for session {session_id}")

            async with self._session.post(url, json=payload) as response:
                response.raise_for_status()
                result = await response.json()

                logger.info(f"Text ingestion completed for session {session_id}")
                return IngestionResponse(**result)

        except aiohttp.ClientError as e:
            logger.error(f"Profile Ingestor request failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during text ingestion: {str(e)}")
            raise

    async def get_progress(self, session_id: str) -> IngestionProgress:
        """Get ingestion progress for a session.

        Args:
            session_id: Session identifier

        Returns:
            Current ingestion progress

        Raises:
            aiohttp.ClientError: If request fails
        """
        await self._ensure_session()

        try:
            url = f"{self.base_url}/api/progress/{session_id}"

            async with self._session.get(url) as response:
                if response.status == 404:
                    # Session not found in Profile Ingestor
                    logger.warning(f"Ingestion progress not found for session {session_id}")
                    return IngestionProgress(
                        session_id=session_id,
                        status="not_found",
                        progress_percent=0,
                        current_step="unknown"
                    )

                response.raise_for_status()
                result = await response.json()

                return IngestionProgress(**result)

        except aiohttp.ClientError as e:
            logger.error(f"Failed to get ingestion progress: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting progress: {str(e)}")
            raise

    async def cancel_ingestion(self, session_id: str) -> Dict[str, Any]:
        """Cancel ongoing ingestion for a session.

        Args:
            session_id: Session identifier

        Returns:
            Cancellation result

        Raises:
            aiohttp.ClientError: If request fails
        """
        await self._ensure_session()

        try:
            url = f"{self.base_url}/api/cancel/{session_id}"

            async with self._session.post(url) as response:
                response.raise_for_status()
                result = await response.json()

                logger.info(f"Ingestion cancelled for session {session_id}")
                return result

        except aiohttp.ClientError as e:
            logger.error(f"Failed to cancel ingestion: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error cancelling ingestion: {str(e)}")
            raise

    async def wait_for_completion(
        self,
        session_id: str,
        check_interval: float = 5.0,
        max_wait_time: float = 300.0
    ) -> IngestionProgress:
        """Wait for ingestion to complete with polling.

        Args:
            session_id: Session identifier
            check_interval: Seconds between progress checks
            max_wait_time: Maximum time to wait in seconds

        Returns:
            Final ingestion progress

        Raises:
            asyncio.TimeoutError: If ingestion doesn't complete in time
        """
        start_time = asyncio.get_event_loop().time()

        while True:
            progress = await self.get_progress(session_id)

            if progress.status in ["completed", "failed"]:
                logger.info(f"Ingestion {progress.status} for session {session_id}")
                return progress

            # Check timeout
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed >= max_wait_time:
                logger.error(f"Ingestion timeout after {elapsed:.1f}s for session {session_id}")
                raise asyncio.TimeoutError(f"Ingestion timeout after {max_wait_time}s")

            # Wait before next check
            await asyncio.sleep(check_interval)


# Global client instance
_client_instance: Optional[ProfileIngestorClient] = None


async def get_profile_ingestor_client() -> ProfileIngestorClient:
    """Get global Profile Ingestor client instance.

    Returns:
        ProfileIngestorClient instance
    """
    global _client_instance

    if not _client_instance:
        _client_instance = ProfileIngestorClient()

    await _client_instance._ensure_session()
    return _client_instance


async def close_profile_ingestor_client():
    """Close global Profile Ingestor client instance."""
    global _client_instance

    if _client_instance:
        await _client_instance.close()
        _client_instance = None
