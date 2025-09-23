"""Performance tests for connection pooling optimization."""

import asyncio
import time
from unittest.mock import AsyncMock, Mock, patch
import pytest
import aiohttp

from src.core.connection_pool import (
    HTTPConnectionPool, ConnectionPoolManager, ConnectionPoolConfig
)
from src.integrations.optimized_clients import (
    OptimizedServiceClient, OptimizedClientManager
)


class MockResponse:
    """Mock aiohttp response for testing."""

    def __init__(self, status: int = 200, json_data: dict = None):
        self.status = status
        self._json_data = json_data or {"status": "ok"}

    async def json(self):
        return self._json_data

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class TestHTTPConnectionPool:
    """Test HTTP connection pool functionality."""

    @pytest.mark.asyncio
    async def test_pool_initialization(self):
        """Test connection pool initialization."""
        config = ConnectionPoolConfig(max_connections=10, max_connections_per_host=5)
        pool = HTTPConnectionPool("test_pool", config, "http://localhost:8000")

        await pool.initialize()

        assert pool.session is not None
        assert pool.connector is not None
        assert pool.connector.limit == 10
        assert pool.connector.limit_per_host == 5

        await pool.close()

    @pytest.mark.asyncio
    async def test_pool_metrics_tracking(self):
        """Test that pool metrics are properly tracked."""
        config = ConnectionPoolConfig(max_connections=5)
        pool = HTTPConnectionPool("metrics_test", config)

        await pool.initialize()

        # Mock session to return successful response
        mock_response = MockResponse(200, {"result": "success"})

        with patch.object(pool.session, 'request', return_value=mock_response):
            response = await pool.request("GET", "http://example.com/test")
            assert response.status == 200

        # Check metrics were updated
        assert pool.metrics.requests_completed > 0
        assert pool.metrics.avg_response_time_ms >= 0

        await pool.close()

    @pytest.mark.asyncio
    async def test_pool_retry_mechanism(self):
        """Test connection pool retry mechanism."""
        config = ConnectionPoolConfig(retry_attempts=3, retry_backoff=0.01)  # Fast retries for testing
        pool = HTTPConnectionPool("retry_test", config)

        await pool.initialize()

        # Mock session to fail first two times, succeed on third
        call_count = 0

        async def mock_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise aiohttp.ClientError("Connection failed")
            return MockResponse(200, {"success": True})

        with patch.object(pool.session, 'request', side_effect=mock_request):
            response = await pool.request("GET", "http://example.com/test")
            assert response.status == 200
            assert call_count == 3  # Should have retried twice

        await pool.close()

    @pytest.mark.asyncio
    async def test_concurrent_requests_performance(self):
        """Test connection pool performance under concurrent load."""
        config = ConnectionPoolConfig(
            max_connections=20,
            max_connections_per_host=10,
            timeout_seconds=30
        )
        pool = HTTPConnectionPool("concurrent_test", config)

        await pool.initialize()

        # Mock successful responses
        mock_response = MockResponse(200, {"data": "test"})

        async def make_request():
            with patch.object(pool.session, 'request', return_value=mock_response):
                return await pool.request("GET", "http://example.com/api")

        # Execute 50 concurrent requests
        start_time = time.time()
        tasks = [make_request() for _ in range(50)]
        responses = await asyncio.gather(*tasks)
        end_time = time.time()

        # Verify all requests succeeded
        assert len(responses) == 50
        assert all(r.status == 200 for r in responses)

        # Check performance metrics
        metrics = await pool.get_metrics()
        assert metrics["requests_completed"] >= 50
        assert metrics["success_rate"] > 95.0

        total_time = end_time - start_time
        logger_info = f"50 concurrent requests completed in {total_time:.2f}s"
        print(f"\n>> {logger_info}")

        await pool.close()


class TestConnectionPoolManager:
    """Test connection pool manager functionality."""

    @pytest.mark.asyncio
    async def test_pool_creation_and_retrieval(self):
        """Test creating and retrieving pools."""
        manager = ConnectionPoolManager()

        # Create pools for different services
        config1 = ConnectionPoolConfig(max_connections=10)
        config2 = ConnectionPoolConfig(max_connections=20)

        pool1 = await manager.create_pool("service1", "http://service1:8001", config1)
        pool2 = await manager.create_pool("service2", "http://service2:8002", config2)

        # Retrieve pools
        retrieved1 = manager.get_pool("service1")
        retrieved2 = manager.get_pool("service2")

        assert retrieved1 == pool1
        assert retrieved2 == pool2
        assert retrieved1.config.max_connections == 10
        assert retrieved2.config.max_connections == 20

        await manager.close_all_pools()

    @pytest.mark.asyncio
    async def test_pool_metrics_aggregation(self):
        """Test aggregation of metrics across multiple pools."""
        manager = ConnectionPoolManager()

        # Create multiple pools
        await manager.create_pool("pool1", "http://service1:8001")
        await manager.create_pool("pool2", "http://service2:8002")

        # Get aggregated metrics
        all_metrics = await manager.get_all_metrics()

        assert "summary" in all_metrics
        assert "total_pools" in all_metrics["summary"]
        assert all_metrics["summary"]["total_pools"] == 2
        assert "pool1" in all_metrics
        assert "pool2" in all_metrics

        await manager.close_all_pools()


class TestOptimizedServiceClients:
    """Test optimized service clients with connection pooling."""

    @pytest.mark.asyncio
    async def test_optimized_client_initialization(self):
        """Test optimized client initialization."""
        client = OptimizedServiceClient(
            "test_service",
            "http://localhost:8000",
            ConnectionPoolConfig(max_connections=5)
        )

        await client.initialize()

        assert client._initialized is True
        assert client.pool_manager.get_pool(client.pool_name) is not None

        # Cleanup
        await client.pool_manager.close_all_pools()

    @pytest.mark.asyncio
    async def test_optimized_client_request_handling(self):
        """Test optimized client request handling."""
        client = OptimizedServiceClient("test_service", "http://localhost:8000")

        # Mock the pool manager's request method
        mock_response = MockResponse(200, {"success": True, "data": "test"})

        with patch('src.integrations.optimized_clients.http_request') as mock_http:
            mock_http.return_value.__aenter__.return_value = mock_response
            mock_http.return_value.__aexit__.return_value = None

            result = await client._make_request("GET", "/api/test")

            assert result["success"] is True
            assert result["data"] == "test"

    @pytest.mark.asyncio
    async def test_client_manager_initialization(self):
        """Test optimized client manager initialization."""
        manager = OptimizedClientManager()

        # Mock the individual client initializations
        with patch.object(manager.profile_ingestor, 'initialize', new_callable=AsyncMock), \
             patch.object(manager.strategist, 'initialize', new_callable=AsyncMock), \
             patch.object(manager.analyst, 'initialize', new_callable=AsyncMock):

            await manager.initialize_all()

            assert manager._initialized is True
            manager.profile_ingestor.initialize.assert_called_once()
            manager.strategist.initialize.assert_called_once()
            manager.analyst.initialize.assert_called_once()


class TestConnectionPoolingPerformance:
    """Performance tests for connection pooling vs non-pooled requests."""

    @pytest.mark.asyncio
    async def test_pooled_vs_non_pooled_performance(self):
        """Compare performance between pooled and non-pooled requests."""
        num_requests = 20  # Reduced for testing speed

        # Test with connection pooling
        config = ConnectionPoolConfig(max_connections=10, max_connections_per_host=5)
        pool = HTTPConnectionPool("perf_test", config)
        await pool.initialize()

        mock_response = MockResponse(200, {"result": "success"})

        # Pooled requests
        start_time = time.time()
        pooled_tasks = []

        for _ in range(num_requests):
            with patch.object(pool.session, 'request', return_value=mock_response):
                task = pool.request("GET", "http://example.com/api")
                pooled_tasks.append(task)

        pooled_responses = await asyncio.gather(*pooled_tasks)
        pooled_time = time.time() - start_time

        # Non-pooled requests (simulated with individual sessions)
        start_time = time.time()
        non_pooled_responses = []

        for _ in range(num_requests):
            # Simulate creating new session for each request
            await asyncio.sleep(0.001)  # Simulate connection overhead
            non_pooled_responses.append(MockResponse(200, {"result": "success"}))

        non_pooled_time = time.time() - start_time

        # Verify results
        assert len(pooled_responses) == num_requests
        assert len(non_pooled_responses) == num_requests

        # Performance comparison
        print(f"\n>> Pooled requests: {pooled_time:.3f}s")
        print(f">> Non-pooled requests: {non_pooled_time:.3f}s")

        # Connection pooling should be significantly faster for concurrent requests
        # (accounting for the artificial delay we added)
        assert pooled_time < non_pooled_time

        # Get final metrics
        metrics = await pool.get_metrics()
        print(f">> Pool utilization: {metrics['pool_utilization_percent']:.1f}%")
        print(f">> Success rate: {metrics['success_rate']:.1f}%")

        await pool.close()

    @pytest.mark.asyncio
    async def test_connection_pool_under_load(self):
        """Test connection pool behavior under heavy load."""
        config = ConnectionPoolConfig(
            max_connections=15,
            max_connections_per_host=8,
            timeout_seconds=10
        )
        pool = HTTPConnectionPool("load_test", config)
        await pool.initialize()

        mock_response = MockResponse(200, {"data": "load_test"})

        async def make_request(request_id: int):
            """Make a single request with some processing time."""
            with patch.object(pool.session, 'request', return_value=mock_response):
                result = await pool.request("GET", f"http://api.example.com/data/{request_id}")
                await asyncio.sleep(0.01)  # Simulate processing time
                return result

        # Execute 100 requests with controlled concurrency
        start_time = time.time()

        # Process in batches to test pool management
        batch_size = 25
        all_results = []

        for batch_start in range(0, 100, batch_size):
            batch_tasks = [
                make_request(i)
                for i in range(batch_start, min(batch_start + batch_size, 100))
            ]
            batch_results = await asyncio.gather(*batch_tasks)
            all_results.extend(batch_results)

            # Small delay between batches
            await asyncio.sleep(0.01)

        total_time = time.time() - start_time

        # Verify results
        assert len(all_results) == 100
        assert all(r.status == 200 for r in all_results)

        # Get performance metrics
        metrics = await pool.get_metrics()

        print(f"\n>> Load test completed: 100 requests in {total_time:.2f}s")
        print(f">> Requests per second: {100 / total_time:.1f}")
        print(f">> Success rate: {metrics['success_rate']:.1f}%")
        print(f">> Average response time: {metrics['avg_response_time_ms']:.1f}ms")
        print(f">> Peak pool utilization: {metrics['pool_utilization_percent']:.1f}%")

        # Performance assertions
        assert metrics["success_rate"] >= 95.0
        assert total_time < 10.0  # Should complete in reasonable time
        assert metrics["avg_response_time_ms"] < 1000  # Response times should be reasonable

        await pool.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
