# Helios Integration Test Suite

Comprehensive integration tests for the Helios Career Operations System, testing end-to-end workflows across all microservices.

## Overview

This integration test suite validates the complete Helios workflow from initial session creation through profile ingestion, career path generation, and market analysis. The tests run in an isolated Docker environment that mirrors the production setup.

## Test Categories

### 🔄 Integration Tests (`integration`)
- End-to-end workflow validation
- Service communication testing
- Data flow verification
- Session management

### ⚡ Performance Tests (`performance`)
- Load testing with concurrent users
- Response time validation
- Throughput measurement
- Resource utilization

### 🛡️ Error Handling Tests (`error_handling`)
- Service failure scenarios
- Invalid data handling
- Timeout management
- Recovery testing

### 📊 Data Validation Tests (`data_validation`)
- Schema validation
- Data integrity checks
- Transformation verification
- Consistency across services

### 🚀 Smoke Tests (`smoke`)
- Basic health checks
- Core functionality validation
- Quick deployment verification

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.13.1+
- Git

### Running Tests

1. **Run all integration tests:**
   ```bash
   python tests/integration/test_runner.py --type all
   ```

2. **Run specific test categories:**
   ```bash
   # Smoke tests (fastest)
   python tests/integration/test_runner.py --type smoke

   # Performance tests
   python tests/integration/test_runner.py --type performance

   # Error handling tests
   python tests/integration/test_runner.py --type error_handling

   # Data validation tests
   python tests/integration/test_runner.py --type data_validation
   ```

3. **Run with pytest directly:**
   ```bash
   # Start services first
   docker-compose -f docker-compose.test.yml up -d

   # Run specific markers
   pytest tests/integration/ -m "integration and not performance"
   pytest tests/integration/ -m "smoke"
   pytest tests/integration/ -m "data_validation"
   ```

### Using Docker Compose

```bash
# Start test environment
docker-compose -f docker-compose.test.yml up -d

# Run tests in container
docker-compose -f docker-compose.test.yml run test-runner

# Run performance tests
docker-compose -f docker-compose.test.yml run performance-test-runner

# Stop and cleanup
docker-compose -f docker-compose.test.yml down -v
```

## Test Environment

### Services

The test environment includes:

- **PostgreSQL Test Database** (port 5433)
- **Redis Test Cache** (port 6380)
- **Orchestrator Service** (port 8100)
- **Profile Ingestor Service** (port 8101)
- **Strategist Service** (port 8102)
- **Analyst Service** (port 8103)

### Configuration

Tests run with isolated test configuration:
- Separate database and cache instances
- Mock external dependencies
- Reduced timeouts for faster feedback
- Enhanced logging for debugging

## Test Structure

```
tests/integration/
├── conftest.py                 # Pytest fixtures and configuration
├── test_end_to_end_workflow.py # Complete workflow tests
├── test_service_interactions.py # Service communication tests
├── test_data_validation.py     # Data integrity tests
├── fixtures/
│   ├── test_resumes.py         # Sample resume data
│   ├── mock_responses.py       # Mock API responses
│   └── sql/                    # Database fixtures
├── reports/                    # Test reports and coverage
├── requirements-test.txt       # Test dependencies
├── pytest.ini                 # Pytest configuration
├── Dockerfile.test             # Test runner container
└── test_runner.py             # Standalone test runner
```

## Writing Tests

### Test Naming Convention

- File: `test_<functionality>.py`
- Class: `Test<Component>`
- Method: `test_<specific_behavior>`

### Markers

Use pytest markers to categorize tests:

```python
@pytest.mark.integration
@pytest.mark.performance
async def test_concurrent_users_performance(self, ...):
    """Test performance with multiple concurrent users."""
```

### Fixtures

Common fixtures available:

- `http_session`: Async HTTP client
- `postgres_client`: Database connection
- `redis_client`: Cache connection
- `sample_resume_data`: Test resume data
- `clean_database`: Database cleanup
- `clean_redis`: Cache cleanup

### Example Test

```python
@pytest.mark.asyncio
@pytest.mark.integration
async def test_complete_workflow(
    self,
    http_session: aiohttp.ClientSession,
    sample_resume_data: Dict[str, Any],
    clean_database,
    clean_redis
):
    """Test complete workflow from session to analysis."""
    # Start session
    session_response = await http_session.post(
        "http://localhost:8100/api/v1/session/start",
        json={"user_id": "test-user"}
    )
    assert session_response.status == 200

    # Continue with workflow steps...
```

## Reports and Coverage

Test results are generated in `tests/integration/reports/`:

- `test-results.xml`: JUnit XML results
- `test-report.html`: HTML test report
- `coverage/`: HTML coverage report
- `integration-test-summary.md`: Summary report

## CI/CD Integration

Tests run automatically on:

- **Push/PR**: Smoke and integration tests
- **Nightly**: Full test suite including performance
- **Manual**: Performance and security tests

### GitHub Actions

- `.github/workflows/integration-tests.yml`: Main CI pipeline
- Parallel test execution
- Artifact upload for reports
- Docker layer caching

## Debugging

### Local Debugging

1. **Start services only:**
   ```bash
   python tests/integration/test_runner.py --services-only
   ```

2. **Keep services running after tests:**
   ```bash
   python tests/integration/test_runner.py --no-cleanup
   ```

3. **Check service logs:**
   ```bash
   docker-compose -f docker-compose.test.yml logs orchestrator-test
   docker-compose -f docker-compose.test.yml logs profile-ingestor-test
   ```

### Test Debugging

- Use `--capture=no` to see print statements
- Add `pytest.set_trace()` for breakpoints
- Use `--lf` to run only last failed tests
- Use `--tb=long` for detailed tracebacks

## Performance Baselines

### Expected Performance

- **Session Creation**: < 5 seconds
- **Profile Processing**: < 30 seconds
- **Career Path Generation**: < 10 seconds
- **Market Analysis**: < 15 seconds
- **Complete Workflow**: < 60 seconds

### Load Testing

- **Concurrent Users**: 10
- **Requests per User**: 5
- **Target Throughput**: > 1 request/second

## Troubleshooting

### Common Issues

1. **Services not starting:**
   - Check Docker daemon is running
   - Verify ports are not in use
   - Check Docker Compose logs

2. **Tests timing out:**
   - Increase timeout values
   - Check service health status
   - Verify network connectivity

3. **Database connection errors:**
   - Ensure PostgreSQL container is healthy
   - Check connection parameters
   - Verify test database exists

4. **Redis connection errors:**
   - Ensure Redis container is running
   - Check Redis port availability
   - Verify Redis configuration

### Getting Help

- Check service logs for error details
- Review test reports for failure patterns
- Use verbose pytest output: `-v -s`
- Check GitHub Actions logs for CI failures

## Contributing

1. Add new tests following existing patterns
2. Use appropriate markers for categorization
3. Include fixtures for test data
4. Update documentation for new features
5. Ensure tests pass in CI environment

## Maintenance

- **Weekly**: Review test performance metrics
- **Monthly**: Update test data and scenarios
- **Quarterly**: Review and optimize test suite
- **As needed**: Update dependencies and configurations
