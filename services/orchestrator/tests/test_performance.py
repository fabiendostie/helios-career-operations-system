"""Performance testing for HELIOS Orchestrator under load."""

import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
import statistics

from fastapi.testclient import TestClient


class TestConcurrentPerformance:
    """Test performance under 100+ concurrent sessions as per AC3."""

    @pytest.mark.performance
    def test_100_concurrent_sessions_creation(self, client):
        """Test AC3: Handle 100+ concurrent user sessions with <2s response time."""

        def create_session_with_timing(session_id: int) -> Dict[str, Any]:
            """Create a session and measure response time."""
            start_time = time.time()

            try:
                response = client.post(
                    "/commands/start",
                    json={"user_id": f"perf-user-{session_id}"}
                )
                end_time = time.time()
                response_time = end_time - start_time

                return {
                    "session_id": session_id,
                    "success": response.status_code == 200,
                    "response_time": response_time,
                    "actual_session_id": response.json().get("result", {}).get("session_id") if response.status_code == 200 else None,
                    "error": None if response.status_code == 200 else response.text
                }
            except Exception as e:
                end_time = time.time()
                return {
                    "session_id": session_id,
                    "success": False,
                    "response_time": end_time - start_time,
                    "actual_session_id": None,
                    "error": str(e)
                }

        # Test with 150 concurrent sessions (exceeding AC requirement)
        session_count = 150
        max_workers = 30  # Limit concurrent threads to avoid overwhelming the test

        print(f"\nTesting {session_count} concurrent session creations...")

        overall_start_time = time.time()

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all session creation tasks
            futures = [
                executor.submit(create_session_with_timing, i)
                for i in range(session_count)
            ]

            # Collect results as they complete
            results = [future.result() for future in as_completed(futures)]

        overall_end_time = time.time()
        total_execution_time = overall_end_time - overall_start_time

        # Analyze results
        successful_sessions = [r for r in results if r["success"]]
        failed_sessions = [r for r in results if not r["success"]]

        response_times = [r["response_time"] for r in successful_sessions]

        # Calculate statistics
        success_rate = len(successful_sessions) / session_count * 100
        avg_response_time = statistics.mean(response_times) if response_times else 0
        median_response_time = statistics.median(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0
        min_response_time = min(response_times) if response_times else 0
        throughput = len(successful_sessions) / total_execution_time

        # Print detailed results
        print(f"Performance Test Results:")
        print(f"   Total execution time: {total_execution_time:.2f}s")
        print(f"   Successful sessions: {len(successful_sessions)}/{session_count} ({success_rate:.1f}%)")
        print(f"   Failed sessions: {len(failed_sessions)}")
        print(f"   Average response time: {avg_response_time:.3f}s")
        print(f"   Median response time: {median_response_time:.3f}s")
        print(f"   Min response time: {min_response_time:.3f}s")
        print(f"   Max response time: {max_response_time:.3f}s")
        print(f"   Throughput: {throughput:.2f} sessions/second")

        if failed_sessions:
            print(f"Failed session examples:")
            for failed in failed_sessions[:3]:  # Show first 3 failures
                print(f"   Session {failed['session_id']}: {failed['error']}")

        # AC3 Assertions: 100+ concurrent sessions with <2s response time
        assert len(successful_sessions) >= 100, f"Must handle at least 100 concurrent sessions, got {len(successful_sessions)}"
        assert success_rate >= 95.0, f"Success rate must be >=95%, got {success_rate:.1f}%"
        assert max_response_time < 2.0, f"Max response time must be <2s, got {max_response_time:.3f}s"
        assert avg_response_time < 1.0, f"Average response time should be <1s, got {avg_response_time:.3f}s"

        print("AC3 Requirements Met: 100+ concurrent sessions with <2s response time")

    @pytest.mark.performance
    def test_concurrent_mixed_operations(self, client):
        """Test mixed concurrent operations (create, read, update) under load."""

        # First, create base sessions
        print("\n🔧 Setting up base sessions for mixed operations test...")
        base_sessions = []
        for i in range(50):
            response = client.post("/commands/start", json={"user_id": f"mixed-ops-{i}"})
            if response.status_code == 200:
                base_sessions.append(response.json()["result"]["session_id"])

        print(f"Created {len(base_sessions)} base sessions")

        def mixed_operation_worker(worker_id: int) -> Dict[str, Any]:
            """Perform mixed operations and measure performance."""
            start_time = time.time()

            try:
                operation_type = worker_id % 4  # 4 types of operations

                if operation_type == 0:
                    # Create new session
                    response = client.post("/commands/start", json={"user_id": f"mixed-new-{worker_id}"})
                    operation = "create"
                elif operation_type == 1:
                    # Read session status
                    session_id = base_sessions[worker_id % len(base_sessions)]
                    response = client.get(f"/sessions/{session_id}")
                    operation = "read"
                elif operation_type == 2:
                    # Update session
                    session_id = base_sessions[worker_id % len(base_sessions)]
                    response = client.put(f"/sessions/{session_id}", json={"metadata": {"worker": worker_id}})
                    operation = "update"
                else:
                    # Status command
                    session_id = base_sessions[worker_id % len(base_sessions)]
                    response = client.get(f"/commands/status/{session_id}")
                    operation = "status"

                end_time = time.time()

                return {
                    "worker_id": worker_id,
                    "operation": operation,
                    "success": response.status_code == 200,
                    "response_time": end_time - start_time,
                    "status_code": response.status_code
                }
            except Exception as e:
                end_time = time.time()
                return {
                    "worker_id": worker_id,
                    "operation": "unknown",
                    "success": False,
                    "response_time": end_time - start_time,
                    "error": str(e)
                }

        # Run 200 mixed operations concurrently
        worker_count = 200
        max_workers = 40

        print(f"🚀 Running {worker_count} concurrent mixed operations...")

        start_time = time.time()

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(mixed_operation_worker, i) for i in range(worker_count)]
            results = [future.result() for future in as_completed(futures)]

        end_time = time.time()
        total_time = end_time - start_time

        # Analyze results by operation type
        operations_by_type = {}
        for result in results:
            op_type = result["operation"]
            if op_type not in operations_by_type:
                operations_by_type[op_type] = []
            operations_by_type[op_type].append(result)

        print(f"📊 Mixed Operations Performance Results:")
        print(f"   Total execution time: {total_time:.2f}s")
        print(f"   Total operations: {len(results)}")

        overall_success_rate = sum(1 for r in results if r["success"]) / len(results) * 100
        overall_avg_time = statistics.mean([r["response_time"] for r in results if r["success"]])

        for op_type, ops in operations_by_type.items():
            successful_ops = [op for op in ops if op["success"]]
            if successful_ops:
                avg_time = statistics.mean([op["response_time"] for op in successful_ops])
                max_time = max([op["response_time"] for op in successful_ops])
                success_rate = len(successful_ops) / len(ops) * 100

                print(f"   {op_type.upper():>8}: {len(successful_ops)}/{len(ops)} ({success_rate:.1f}%) - "
                      f"avg: {avg_time:.3f}s, max: {max_time:.3f}s")

        print(f"   OVERALL: {overall_success_rate:.1f}% success, avg: {overall_avg_time:.3f}s")

        # Performance assertions
        assert overall_success_rate >= 95.0, f"Overall success rate must be ≥95%, got {overall_success_rate:.1f}%"
        assert overall_avg_time < 2.0, f"Overall average response time must be <2s, got {overall_avg_time:.3f}s"

        print(" Mixed operations performance test passed")

    @pytest.mark.performance
    def test_session_cleanup_performance_under_load(self, client):
        """Test session cleanup performance with many sessions."""

        print("\n🧹 Testing session cleanup performance under load...")

        # Create many sessions
        session_count = 100
        session_ids = []

        print(f"Creating {session_count} sessions for cleanup test...")
        for i in range(session_count):
            response = client.post("/commands/start", json={"user_id": f"cleanup-perf-{i}"})
            if response.status_code == 200:
                session_ids.append(response.json()["result"]["session_id"])

        print(f"Created {len(session_ids)} sessions")

        # Test cleanup performance
        start_time = time.time()
        response = client.post("/sessions/cleanup")
        end_time = time.time()
        cleanup_time = end_time - start_time

        assert response.status_code == 200
        cleanup_result = response.json()

        print(f"📊 Cleanup Performance Results:")
        print(f"   Cleanup time: {cleanup_time:.3f}s")
        print(f"   Sessions cleaned: {cleanup_result.get('cleaned_up', 0)}")
        print(f"   Performance: {len(session_ids)/cleanup_time:.2f} sessions/second check rate")

        # Performance assertion - cleanup should be fast
        assert cleanup_time < 5.0, f"Cleanup should complete in <5s, took {cleanup_time:.3f}s"

        print(" Session cleanup performance test passed")

    @pytest.mark.performance
    def test_health_check_performance_under_load(self, client):
        """Test health check endpoints under concurrent load."""

        def health_check_worker(endpoint: str, worker_id: int) -> Dict[str, Any]:
            """Perform health check and measure response time."""
            start_time = time.time()

            try:
                response = client.get(endpoint)
                end_time = time.time()

                return {
                    "worker_id": worker_id,
                    "endpoint": endpoint,
                    "success": response.status_code == 200,
                    "response_time": end_time - start_time,
                    "status_code": response.status_code
                }
            except Exception as e:
                end_time = time.time()
                return {
                    "worker_id": worker_id,
                    "endpoint": endpoint,
                    "success": False,
                    "response_time": end_time - start_time,
                    "error": str(e)
                }

        # Test different health endpoints under load
        endpoints = ["/health/", "/health/detailed", "/health/ready", "/health/live"]
        requests_per_endpoint = 25  # 25 concurrent requests per endpoint

        print(f"\n Testing health endpoints under load ({requests_per_endpoint} concurrent per endpoint)...")

        start_time = time.time()

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = []

            for endpoint in endpoints:
                for i in range(requests_per_endpoint):
                    futures.append(executor.submit(health_check_worker, endpoint, i))

            results = [future.result() for future in as_completed(futures)]

        end_time = time.time()
        total_time = end_time - start_time

        # Analyze results by endpoint
        results_by_endpoint = {}
        for result in results:
            endpoint = result["endpoint"]
            if endpoint not in results_by_endpoint:
                results_by_endpoint[endpoint] = []
            results_by_endpoint[endpoint].append(result)

        print(f"📊 Health Endpoints Performance Results:")
        print(f"   Total execution time: {total_time:.2f}s")
        print(f"   Total requests: {len(results)}")

        for endpoint, endpoint_results in results_by_endpoint.items():
            successful = [r for r in endpoint_results if r["success"]]
            if successful:
                avg_time = statistics.mean([r["response_time"] for r in successful])
                max_time = max([r["response_time"] for r in successful])
                success_rate = len(successful) / len(endpoint_results) * 100

                print(f"   {endpoint:>16}: {len(successful)}/{len(endpoint_results)} ({success_rate:.1f}%) - "
                      f"avg: {avg_time:.3f}s, max: {max_time:.3f}s")

                # Health checks should be very fast
                assert avg_time < 0.5, f"{endpoint} average response time should be <0.5s, got {avg_time:.3f}s"
                assert max_time < 1.0, f"{endpoint} max response time should be <1.0s, got {max_time:.3f}s"

        overall_success_rate = sum(1 for r in results if r["success"]) / len(results) * 100
        assert overall_success_rate >= 99.0, f"Health endpoints should have ≥99% success rate, got {overall_success_rate:.1f}%"

        print(" Health endpoints performance test passed")


class TestScalabilityLimits:
    """Test scalability limits and resource usage."""

    @pytest.mark.performance
    @pytest.mark.slow
    def test_maximum_concurrent_sessions_limit(self, client):
        """Test system behavior at scalability limits."""

        print("\n🔥 Testing maximum concurrent sessions (stress test)...")

        def stress_test_worker(batch_start: int, batch_size: int) -> List[Dict[str, Any]]:
            """Create a batch of sessions and return results."""
            results = []

            for i in range(batch_size):
                session_id = batch_start + i
                start_time = time.time()

                try:
                    response = client.post("/commands/start", json={"user_id": f"stress-{session_id}"})
                    end_time = time.time()

                    results.append({
                        "session_id": session_id,
                        "success": response.status_code == 200,
                        "response_time": end_time - start_time,
                        "status_code": response.status_code
                    })
                except Exception as e:
                    end_time = time.time()
                    results.append({
                        "session_id": session_id,
                        "success": False,
                        "response_time": end_time - start_time,
                        "error": str(e)
                    })

            return results

        # Stress test with 500 sessions in batches
        total_sessions = 500
        batch_size = 50
        batches = total_sessions // batch_size

        print(f"Creating {total_sessions} sessions in {batches} batches of {batch_size}...")

        all_results = []
        overall_start = time.time()

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []

            for batch in range(batches):
                batch_start = batch * batch_size
                futures.append(executor.submit(stress_test_worker, batch_start, batch_size))

            # Collect all results
            for future in as_completed(futures):
                batch_results = future.result()
                all_results.extend(batch_results)

        overall_end = time.time()
        total_time = overall_end - overall_start

        # Analyze stress test results
        successful_sessions = [r for r in all_results if r["success"]]
        failed_sessions = [r for r in all_results if not r["success"]]

        if successful_sessions:
            response_times = [r["response_time"] for r in successful_sessions]
            avg_response_time = statistics.mean(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)
            p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
        else:
            avg_response_time = max_response_time = min_response_time = p95_response_time = 0

        success_rate = len(successful_sessions) / len(all_results) * 100
        throughput = len(successful_sessions) / total_time

        print(f"📊 Stress Test Results ({total_sessions} sessions):")
        print(f"   Total execution time: {total_time:.2f}s")
        print(f"   Successful sessions: {len(successful_sessions)}/{total_sessions} ({success_rate:.1f}%)")
        print(f"   Failed sessions: {len(failed_sessions)}")
        print(f"   Throughput: {throughput:.2f} sessions/second")
        print(f"   Response times:")
        print(f"     Average: {avg_response_time:.3f}s")
        print(f"     Min: {min_response_time:.3f}s")
        print(f"     Max: {max_response_time:.3f}s")
        print(f"     95th percentile: {p95_response_time:.3f}s")

        # Scalability assertions (more relaxed for stress test)
        assert success_rate >= 80.0, f"Even under stress, success rate should be ≥80%, got {success_rate:.1f}%"
        assert max_response_time < 10.0, f"Even under stress, max response should be <10s, got {max_response_time:.3f}s"
        assert p95_response_time < 5.0, f"95th percentile response time should be <5s, got {p95_response_time:.3f}s"

        print(" Stress test completed - system maintained reasonable performance under load")


if __name__ == "__main__":
    # For manual performance testing
    print("Manual Performance Test Runner")
    print("Run with: pytest tests/test_performance.py -v -m performance")
    print("For stress tests: pytest tests/test_performance.py -v -m 'performance and slow'")
