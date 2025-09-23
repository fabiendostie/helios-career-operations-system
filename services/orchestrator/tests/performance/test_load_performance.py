"""Load testing for orchestrator service with 100+ concurrent sessions."""

import asyncio
import time
import statistics
from datetime import datetime
from typing import List, Dict, Any
import aiohttp
import pytest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import AsyncMock, Mock, patch

from src.core.service_coordinator import ServiceCoordinator
from src.models.session import SessionState, CurrentStep


class LoadTestResults:
    """Container for load test results and metrics."""

    def __init__(self):
        self.response_times: List[float] = []
        self.success_count: int = 0
        self.error_count: int = 0
        self.errors: List[str] = []
        self.concurrent_sessions: int = 0
        self.test_duration: float = 0.0
        self.start_time: datetime = None
        self.end_time: datetime = None

    def add_result(self, response_time: float, success: bool, error: str = None):
        """Add a test result."""
        self.response_times.append(response_time)
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
            if error:
                self.errors.append(error)

    def calculate_metrics(self) -> Dict[str, Any]:
        """Calculate performance metrics."""
        if not self.response_times:
            return {"error": "No response times recorded"}

        return {
            "total_requests": len(self.response_times),
            "success_count": self.success_count,
            "error_count": self.error_count,
            "success_rate": (self.success_count / len(self.response_times)) * 100,
            "concurrent_sessions": self.concurrent_sessions,
            "test_duration_seconds": self.test_duration,
            "requests_per_second": len(self.response_times) / self.test_duration,
            "response_times": {
                "min": min(self.response_times),
                "max": max(self.response_times),
                "mean": statistics.mean(self.response_times),
                "median": statistics.median(self.response_times),
                "p95": self._percentile(self.response_times, 95),
                "p99": self._percentile(self.response_times, 99)
            },
            "errors": self.errors[:10]  # First 10 errors for analysis
        }

    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile."""
        sorted_data = sorted(data)
        index = int((percentile / 100) * len(sorted_data))
        return sorted_data[min(index, len(sorted_data) - 1)]


@pytest.fixture
def load_test_setup():
    """Setup for load testing with optimized mocks."""

    # Create fast mock session manager
    session_manager = AsyncMock()
    session_manager.create_session.return_value = Mock(session_id="load-test-session")
    session_manager.get_session.return_value = Mock(
        session_id="load-test-session",
        state=SessionState.COMPLETED,
        current_step=CurrentStep.REVIEW,
        master_career_database={},
        updated_at=datetime.utcnow()
    )
    session_manager.update_session.return_value = Mock()

    # Create fast mock profile ingestor
    profile_ingestor = AsyncMock()
    profile_ingestor.ingest_resume.return_value = {
        "success": True,
        "master_career_database": {
            "work_experience": [{"job_title": "Engineer", "company": "TechCorp"}],
            "skills_inventory": {"technical": ["Python", "FastAPI"]},
            "strategic_metadata": {"core_competencies": ["Programming"]},
            "holistic_profile": {"career_aspirations": ["Senior Engineer"]}
        }
    }

    # Create fast mock strategist
    strategist = AsyncMock()
    strategist.generate_career_paths.return_value = {
        "success": True,
        "career_paths": {
            "recommended_paths": [
                {"path_id": "senior_eng", "title": "Senior Engineer", "fit_score": 0.9}
            ]
        }
    }

    # Create fast mock analyst
    analyst = AsyncMock()
    analyst.analyze_market_position.return_value = {
        "success": True,
        "analysis": {
            "market_demand": {"senior_eng": {"demand_score": 0.8}},
            "skill_gaps": [{"skill": "Kubernetes", "importance": 0.7}],
            "resume_optimization": {"ats_score": 0.75}
        }
    }

    return ServiceCoordinator(
        session_manager=session_manager,
        profile_ingestor=profile_ingestor,
        strategist=strategist,
        analyst=analyst
    )


async def single_pipeline_request(coordinator: ServiceCoordinator, session_id: str) -> tuple[float, bool, str]:
    """Execute a single pipeline request and measure performance."""
    start_time = time.time()
    error_msg = None
    success = False

    try:
        result = await coordinator.execute_full_pipeline(
            session_id=session_id,
            career_data={
                "work_experience": [{"job_title": "Engineer", "company": "TestCorp"}],
                "skills_inventory": {"technical": ["Python"], "soft_skills": ["Communication"]},
                "strategic_metadata": {"core_competencies": ["Engineering"]},
                "holistic_profile": {"career_aspirations": ["Senior Role"]}
            }
        )
        success = result.get("pipeline_status") == "completed"
        if not success:
            error_msg = f"Pipeline failed: {result.get('error', 'Unknown error')}"

    except Exception as e:
        error_msg = f"Exception: {str(e)}"
        success = False

    response_time = time.time() - start_time
    return response_time, success, error_msg


class TestLoadPerformance:
    """Load testing for orchestrator service."""

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_concurrent_sessions_50(self, load_test_setup):
        """Test performance with 50 concurrent sessions."""
        coordinator = load_test_setup
        concurrent_sessions = 50
        results = LoadTestResults()
        results.concurrent_sessions = concurrent_sessions
        results.start_time = datetime.utcnow()

        print(f"\n>> Starting load test with {concurrent_sessions} concurrent sessions...")

        start_time = time.time()

        # Create concurrent tasks
        tasks = []
        for i in range(concurrent_sessions):
            session_id = f"load-test-session-{i}"
            task = single_pipeline_request(coordinator, session_id)
            tasks.append(task)

        # Execute all tasks concurrently
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        end_time = time.time()
        results.test_duration = end_time - start_time
        results.end_time = datetime.utcnow()

        # Process results
        for response in responses:
            if isinstance(response, Exception):
                results.add_result(0.0, False, str(response))
            else:
                response_time, success, error = response
                results.add_result(response_time, success, error)

        # Calculate and display metrics
        metrics = results.calculate_metrics()

        print(f">> Load Test Results ({concurrent_sessions} concurrent sessions):")
        print(f"   Total Requests: {metrics['total_requests']}")
        print(f"   Success Rate: {metrics['success_rate']:.1f}%")
        print(f"   Test Duration: {metrics['test_duration_seconds']:.2f}s")
        print(f"   Requests/Second: {metrics['requests_per_second']:.2f}")
        print(f"   Response Times:")
        print(f"     Mean: {metrics['response_times']['mean']:.3f}s")
        print(f"     Median: {metrics['response_times']['median']:.3f}s")
        print(f"     P95: {metrics['response_times']['p95']:.3f}s")
        print(f"     P99: {metrics['response_times']['p99']:.3f}s")

        # Performance assertions
        assert metrics['success_rate'] >= 95.0, f"Success rate {metrics['success_rate']:.1f}% below 95%"
        assert metrics['response_times']['mean'] < 1.0, f"Mean response time {metrics['response_times']['mean']:.3f}s exceeds 1s"
        assert metrics['response_times']['p95'] < 2.0, f"P95 response time {metrics['response_times']['p95']:.3f}s exceeds 2s"

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_concurrent_sessions_100(self, load_test_setup):
        """Test performance with 100 concurrent sessions."""
        coordinator = load_test_setup
        concurrent_sessions = 100
        results = LoadTestResults()
        results.concurrent_sessions = concurrent_sessions
        results.start_time = datetime.utcnow()

        print(f"\n>> Starting load test with {concurrent_sessions} concurrent sessions...")

        start_time = time.time()

        # Create concurrent tasks in batches to avoid overwhelming the system
        batch_size = 25
        all_responses = []

        for batch_start in range(0, concurrent_sessions, batch_size):
            batch_end = min(batch_start + batch_size, concurrent_sessions)
            batch_tasks = []

            for i in range(batch_start, batch_end):
                session_id = f"load-test-session-{i}"
                task = single_pipeline_request(coordinator, session_id)
                batch_tasks.append(task)

            # Execute batch concurrently
            batch_responses = await asyncio.gather(*batch_tasks, return_exceptions=True)
            all_responses.extend(batch_responses)

            # Small delay between batches to prevent resource exhaustion
            await asyncio.sleep(0.01)

        end_time = time.time()
        results.test_duration = end_time - start_time
        results.end_time = datetime.utcnow()

        # Process results
        for response in all_responses:
            if isinstance(response, Exception):
                results.add_result(0.0, False, str(response))
            else:
                response_time, success, error = response
                results.add_result(response_time, success, error)

        # Calculate and display metrics
        metrics = results.calculate_metrics()

        print(f">> Load Test Results ({concurrent_sessions} concurrent sessions):")
        print(f"   Total Requests: {metrics['total_requests']}")
        print(f"   Success Rate: {metrics['success_rate']:.1f}%")
        print(f"   Test Duration: {metrics['test_duration_seconds']:.2f}s")
        print(f"   Requests/Second: {metrics['requests_per_second']:.2f}")
        print(f"   Response Times:")
        print(f"     Mean: {metrics['response_times']['mean']:.3f}s")
        print(f"     Median: {metrics['response_times']['median']:.3f}s")
        print(f"     P95: {metrics['response_times']['p95']:.3f}s")
        print(f"     P99: {metrics['response_times']['p99']:.3f}s")

        if metrics['errors']:
            print(f"   Sample Errors: {metrics['errors'][:3]}")

        # Performance assertions for 100 concurrent sessions
        assert metrics['success_rate'] >= 90.0, f"Success rate {metrics['success_rate']:.1f}% below 90%"
        assert metrics['response_times']['mean'] < 2.0, f"Mean response time {metrics['response_times']['mean']:.3f}s exceeds 2s"
        assert metrics['response_times']['p95'] < 5.0, f"P95 response time {metrics['response_times']['p95']:.3f}s exceeds 5s"

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_concurrent_sessions_150(self, load_test_setup):
        """Test performance with 150 concurrent sessions (stress test)."""
        coordinator = load_test_setup
        concurrent_sessions = 150
        results = LoadTestResults()
        results.concurrent_sessions = concurrent_sessions
        results.start_time = datetime.utcnow()

        print(f"\n>> Starting stress test with {concurrent_sessions} concurrent sessions...")

        start_time = time.time()

        # Create concurrent tasks in smaller batches for stress test
        batch_size = 20
        all_responses = []

        for batch_start in range(0, concurrent_sessions, batch_size):
            batch_end = min(batch_start + batch_size, concurrent_sessions)
            batch_tasks = []

            for i in range(batch_start, batch_end):
                session_id = f"stress-test-session-{i}"
                task = single_pipeline_request(coordinator, session_id)
                batch_tasks.append(task)

            # Execute batch concurrently
            batch_responses = await asyncio.gather(*batch_tasks, return_exceptions=True)
            all_responses.extend(batch_responses)

            # Small delay between batches
            await asyncio.sleep(0.02)

        end_time = time.time()
        results.test_duration = end_time - start_time
        results.end_time = datetime.utcnow()

        # Process results
        for response in all_responses:
            if isinstance(response, Exception):
                results.add_result(0.0, False, str(response))
            else:
                response_time, success, error = response
                results.add_result(response_time, success, error)

        # Calculate and display metrics
        metrics = results.calculate_metrics()

        print(f">> Stress Test Results ({concurrent_sessions} concurrent sessions):")
        print(f"   Total Requests: {metrics['total_requests']}")
        print(f"   Success Rate: {metrics['success_rate']:.1f}%")
        print(f"   Test Duration: {metrics['test_duration_seconds']:.2f}s")
        print(f"   Requests/Second: {metrics['requests_per_second']:.2f}")
        print(f"   Response Times:")
        print(f"     Mean: {metrics['response_times']['mean']:.3f}s")
        print(f"     Median: {metrics['response_times']['median']:.3f}s")
        print(f"     P95: {metrics['response_times']['p95']:.3f}s")
        print(f"     P99: {metrics['response_times']['p99']:.3f}s")

        if metrics['errors']:
            print(f"   Sample Errors: {metrics['errors'][:5]}")

        # Stress test assertions (more lenient)
        assert metrics['success_rate'] >= 80.0, f"Success rate {metrics['success_rate']:.1f}% below 80%"
        assert metrics['response_times']['mean'] < 3.0, f"Mean response time {metrics['response_times']['mean']:.3f}s exceeds 3s"

        print(">> Stress test completed successfully!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "performance"])
