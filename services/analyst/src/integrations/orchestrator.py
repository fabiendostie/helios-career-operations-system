"""Orchestrator service integration client for the Analyst service."""

import logging
import asyncio
from typing import Dict, Any, Optional
import uuid

import aiohttp
from aiohttp import ClientSession, ClientTimeout, ClientError

from src.core.config import settings


logger = logging.getLogger(__name__)


class OrchestratorError(Exception):
    """Custom exception for orchestrator communication errors."""

    pass


class OrchestratorClient:
    """HTTP client for communication with the Orchestrator service."""

    def __init__(self, base_url: Optional[str] = None):
        """Initialize orchestrator client.

        Args:
            base_url: Orchestrator service base URL. Defaults to config setting.
        """
        self.base_url = base_url or settings.ORCHESTRATOR_URL
        self.timeout = ClientTimeout(total=30)
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
            self._session = aiohttp.ClientSession(
                timeout=self.timeout,
                headers={"User-Agent": "Helios-Analyst-Service/1.0"},
            )

    async def close(self):
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def _make_request(
        self, method: str, endpoint: str, correlation_id: Optional[str] = None, **kwargs
    ) -> Dict[str, Any]:
        """Make HTTP request to orchestrator.

        Args:
            method: HTTP method
            endpoint: API endpoint
            correlation_id: Request correlation ID
            **kwargs: Additional request parameters

        Returns:
            Response JSON data

        Raises:
            OrchestratorError: If request fails
        """
        await self._ensure_session()

        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"

        # Add correlation ID header
        headers = kwargs.get("headers", {})
        if correlation_id:
            headers["X-Correlation-ID"] = correlation_id
        kwargs["headers"] = headers

        try:
            async with self._session.request(method, url, **kwargs) as response:
                response_data = await response.json()

                if response.status >= 400:
                    error_msg = f"Orchestrator request failed: {response.status} - {response_data.get('detail', 'Unknown error')}"
                    logger.error(error_msg)
                    raise OrchestratorError(error_msg)

                return response_data

        except ClientError as e:
            error_msg = f"Failed to communicate with orchestrator: {str(e)}"
            logger.error(error_msg)
            raise OrchestratorError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error communicating with orchestrator: {str(e)}"
            logger.error(error_msg)
            raise OrchestratorError(error_msg)

    async def register_analysis_request(
        self,
        user_id: str,
        master_career_data: Dict[str, Any],
        correlation_id: Optional[str] = None,
    ) -> str:
        """Register analysis request with orchestrator.

        Args:
            user_id: User identifier
            master_career_data: Career data from profile ingestor
            correlation_id: Request correlation ID

        Returns:
            Analysis request ID
        """
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        payload = {
            "user_id": user_id,
            "service": "analyst",
            "operation": "analyze_career",
            "data": master_career_data,
            "correlation_id": correlation_id,
        }

        response = await self._make_request(
            "POST",
            "/sessions/register_operation",
            correlation_id=correlation_id,
            json=payload,
        )

        logger.info(
            f"Registered analysis request for user {user_id}, correlation_id: {correlation_id}"
        )
        return response.get("operation_id", correlation_id)

    async def update_analysis_progress(
        self,
        operation_id: str,
        progress: Dict[str, Any],
        correlation_id: Optional[str] = None,
    ) -> None:
        """Update analysis progress with orchestrator.

        Args:
            operation_id: Operation identifier
            progress: Progress update data
            correlation_id: Request correlation ID
        """
        payload = {
            "operation_id": operation_id,
            "service": "analyst",
            "progress": progress,
        }

        await self._make_request(
            "PUT",
            f"/sessions/operations/{operation_id}/progress",
            correlation_id=correlation_id,
            json=payload,
        )

        logger.info(f"Updated progress for operation {operation_id}")

    async def complete_analysis(
        self,
        operation_id: str,
        analysis_result: Dict[str, Any],
        correlation_id: Optional[str] = None,
    ) -> None:
        """Mark analysis as complete and send results.

        Args:
            operation_id: Operation identifier
            analysis_result: Complete analysis results
            correlation_id: Request correlation ID
        """
        payload = {
            "operation_id": operation_id,
            "service": "analyst",
            "status": "completed",
            "result": analysis_result,
        }

        await self._make_request(
            "PUT",
            f"/sessions/operations/{operation_id}/complete",
            correlation_id=correlation_id,
            json=payload,
        )

        logger.info(f"Completed analysis for operation {operation_id}")

    async def report_analysis_error(
        self,
        operation_id: str,
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> None:
        """Report analysis error to orchestrator.

        Args:
            operation_id: Operation identifier
            error_message: Error description
            error_details: Additional error details
            correlation_id: Request correlation ID
        """
        payload = {
            "operation_id": operation_id,
            "service": "analyst",
            "status": "failed",
            "error": {"message": error_message, "details": error_details or {}},
        }

        await self._make_request(
            "PUT",
            f"/sessions/operations/{operation_id}/error",
            correlation_id=correlation_id,
            json=payload,
        )

        logger.error(f"Reported error for operation {operation_id}: {error_message}")

    async def get_session_context(
        self, user_id: str, correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get session context for user.

        Args:
            user_id: User identifier
            correlation_id: Request correlation ID

        Returns:
            Session context data
        """
        response = await self._make_request(
            "GET", f"/sessions/users/{user_id}/context", correlation_id=correlation_id
        )

        return response.get("context", {})

    async def health_check(self) -> Dict[str, Any]:
        """Check orchestrator service health.

        Returns:
            Health check response
        """
        try:
            response = await self._make_request("GET", "/health")
            return response
        except OrchestratorError as e:
            logger.warning(f"Orchestrator health check failed: {str(e)}")
            return {"status": "unhealthy", "error": str(e)}


class AsyncOrchestratorIntegration:
    """Async orchestrator integration with error handling and retry logic."""

    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        """Initialize integration.

        Args:
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._client: Optional[OrchestratorClient] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self._client = OrchestratorClient()
        await self._client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.__aexit__(exc_type, exc_val, exc_tb)

    async def _retry_operation(self, operation, *args, **kwargs):
        """Retry operation with exponential backoff.

        Args:
            operation: Function to retry
            *args: Operation arguments
            **kwargs: Operation keyword arguments

        Returns:
            Operation result
        """
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                return await operation(*args, **kwargs)

            except OrchestratorError as e:
                last_error = e
                if attempt < self.max_retries:
                    delay = self.retry_delay * (2**attempt)  # Exponential backoff
                    logger.warning(
                        f"Operation failed (attempt {attempt + 1}/{self.max_retries + 1}), retrying in {delay}s: {str(e)}"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"Operation failed after {self.max_retries + 1} attempts: {str(e)}"
                    )
                    break

        raise last_error

    async def execute_analysis_with_orchestrator(
        self,
        user_id: str,
        master_career_data: Dict[str, Any],
        analysis_function,
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute analysis with full orchestrator integration.

        Args:
            user_id: User identifier
            master_career_data: Career data from profile ingestor
            analysis_function: Analysis function to execute
            correlation_id: Request correlation ID

        Returns:
            Analysis results
        """
        if not self._client:
            raise RuntimeError(
                "Integration not initialized. Use async context manager."
            )

        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        operation_id = None

        try:
            # Register analysis request
            operation_id = await self._retry_operation(
                self._client.register_analysis_request,
                user_id,
                master_career_data,
                correlation_id,
            )

            # Update progress: Starting analysis
            await self._retry_operation(
                self._client.update_analysis_progress,
                operation_id,
                {
                    "stage": "initializing",
                    "progress_percentage": 0,
                    "message": "Starting career analysis",
                },
                correlation_id,
            )

            # Execute analysis with progress updates
            result = await self._execute_analysis_with_progress(
                analysis_function, master_career_data, operation_id, correlation_id
            )

            # Report completion
            await self._retry_operation(
                self._client.complete_analysis, operation_id, result, correlation_id
            )

            return result

        except Exception as e:
            # Report error if we have an operation ID
            if operation_id:
                try:
                    await self._client.report_analysis_error(
                        operation_id,
                        str(e),
                        {"error_type": type(e).__name__},
                        correlation_id,
                    )
                except Exception as report_error:
                    logger.error(
                        f"Failed to report error to orchestrator: {str(report_error)}"
                    )

            raise

    async def _execute_analysis_with_progress(
        self,
        analysis_function,
        master_career_data: Dict[str, Any],
        operation_id: str,
        correlation_id: str,
    ) -> Dict[str, Any]:
        """Execute analysis function with progress reporting.

        Args:
            analysis_function: Analysis function to execute
            master_career_data: Career data input
            operation_id: Operation identifier
            correlation_id: Request correlation ID

        Returns:
            Analysis results
        """
        progress_stages = [
            (
                10,
                "resume_deconstruction",
                "Analyzing resume structure and extracting entities",
            ),
            (30, "market_analysis", "Analyzing market opportunities and job matches"),
            (50, "ats_simulation", "Simulating ATS scoring and optimization"),
            (70, "skill_recalibration", "Performing skill gap analysis"),
            (90, "career_inference", "Generating career path recommendations"),
            (100, "report_generation", "Finalizing analysis report"),
        ]

        try:
            # Simulate progress updates (in real implementation, these would be called from within analysis components)
            for progress, stage, message in progress_stages[
                :-1
            ]:  # Exclude final stage for now
                await self._retry_operation(
                    self._client.update_analysis_progress,
                    operation_id,
                    {
                        "stage": stage,
                        "progress_percentage": progress,
                        "message": message,
                    },
                    correlation_id,
                )

                # Small delay to simulate processing time
                await asyncio.sleep(0.1)

            # Execute actual analysis
            result = await analysis_function(master_career_data)

            # Final progress update
            final_progress, final_stage, final_message = progress_stages[-1]
            await self._retry_operation(
                self._client.update_analysis_progress,
                operation_id,
                {
                    "stage": final_stage,
                    "progress_percentage": final_progress,
                    "message": final_message,
                },
                correlation_id,
            )

            return result

        except Exception as e:
            logger.error(f"Analysis execution failed: {str(e)}")
            raise

    async def check_orchestrator_connectivity(self) -> bool:
        """Check if orchestrator is accessible.

        Returns:
            True if orchestrator is healthy, False otherwise
        """
        if not self._client:
            return False

        try:
            health_response = await self._client.health_check()
            return health_response.get("status") == "healthy"
        except Exception as e:
            logger.warning(f"Orchestrator connectivity check failed: {str(e)}")
            return False
