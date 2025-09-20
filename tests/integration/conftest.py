"""
Integration test configuration and fixtures for Helios Career Operations System.

This module provides pytest fixtures and configuration for integration testing
of the complete HELIOS workflow across all microservices.
"""

import asyncio
import time
from pathlib import Path

import aiohttp
import asyncpg
import pytest
import redis.asyncio as redis
from testcontainers.compose import DockerCompose


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def docker_services():
    """Start Docker Compose services for integration testing."""
    compose_file = Path(__file__).parent.parent.parent / "docker-compose.yml"

    with DockerCompose(
        filepath=str(compose_file.parent),
        compose_file_name="docker-compose.yml",
        pull=True,
    ) as compose:
        # Wait for services to be healthy
        await _wait_for_services_healthy(compose)
        yield compose


@pytest.fixture(scope="session")
async def postgres_client(docker_services):
    """PostgreSQL client for integration tests."""
    conn = await asyncpg.connect(
        host="localhost",
        port=5432,
        user="helios_dev",
        password="helios_dev_password",
        database="helios_dev",
    )
    yield conn
    await conn.close()


@pytest.fixture(scope="session")
async def redis_client(docker_services):
    """Redis client for integration tests."""
    client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
    yield client
    await client.close()


@pytest.fixture(scope="session")
async def http_session(docker_services):
    """HTTP session for API calls."""
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        yield session


@pytest.fixture
async def clean_database(postgres_client):
    """Clean database before each test."""
    # Clean up any existing data
    await postgres_client.execute("TRUNCATE TABLE sessions CASCADE")
    await postgres_client.execute("TRUNCATE TABLE profiles CASCADE")
    await postgres_client.execute("TRUNCATE TABLE career_paths CASCADE")
    await postgres_client.execute("TRUNCATE TABLE market_analysis CASCADE")
    yield
    # Clean up after test
    await postgres_client.execute("TRUNCATE TABLE sessions CASCADE")
    await postgres_client.execute("TRUNCATE TABLE profiles CASCADE")
    await postgres_client.execute("TRUNCATE TABLE career_paths CASCADE")
    await postgres_client.execute("TRUNCATE TABLE market_analysis CASCADE")


@pytest.fixture
async def clean_redis(redis_client):
    """Clean Redis cache before each test."""
    await redis_client.flushdb()
    yield
    await redis_client.flushdb()


@pytest.fixture
def sample_resume_data():
    """Sample resume data for testing."""
    return {
        "personal_info": {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "+1-555-0123",
            "location": "San Francisco, CA",
        },
        "work_experience": [
            {
                "company": "TechCorp Inc",
                "position": "Senior Software Engineer",
                "start_date": "2020-01-15",
                "end_date": "2023-08-30",
                "accomplishments": [
                    "Led development of microservices architecture serving 1M+ users",
                    "Reduced system latency by 40% through performance optimization",
                    "Mentored 5 junior developers and improved team productivity by 25%",
                ],
                "technologies": [
                    "Python",
                    "Django",
                    "PostgreSQL",
                    "Docker",
                    "Kubernetes",
                ],
            },
            {
                "company": "StartupXYZ",
                "position": "Full Stack Developer",
                "start_date": "2018-06-01",
                "end_date": "2019-12-31",
                "accomplishments": [
                    "Built MVP product from scratch using React and Node.js",
                    "Implemented CI/CD pipeline reducing deployment time by 60%",
                    "Designed and built RESTful APIs handling 10K+ requests/hour",
                ],
                "technologies": ["JavaScript", "React", "Node.js", "MongoDB", "AWS"],
            },
        ],
        "projects": [
            {
                "name": "Open Source ML Library",
                "description": "Contributed to scikit-learn with focus on algorithm optimization",
                "technologies": ["Python", "Machine Learning", "NumPy", "Pandas"],
                "impact": "Improved algorithm performance by 15% for linear regression models",
            }
        ],
        "skills_inventory": {
            "programming_languages": ["Python", "JavaScript", "Java", "Go"],
            "frameworks": ["Django", "React", "Node.js", "FastAPI"],
            "databases": ["PostgreSQL", "MongoDB", "Redis"],
            "cloud_platforms": ["AWS", "Docker", "Kubernetes"],
            "methodologies": ["Agile", "TDD", "CI/CD", "Microservices"],
        },
        "education": [
            {
                "institution": "University of California, Berkeley",
                "degree": "Bachelor of Science in Computer Science",
                "graduation_year": "2018",
                "gpa": "3.8",
            }
        ],
    }


@pytest.fixture
def sample_career_goals():
    """Sample career goals for testing."""
    return {
        "target_roles": [
            "Staff Software Engineer",
            "Technical Lead",
            "Engineering Manager",
        ],
        "target_companies": ["Google", "Microsoft", "Amazon", "Meta"],
        "preferred_technologies": ["Python", "Go", "Kubernetes", "Machine Learning"],
        "salary_expectations": {"min": 180000, "max": 250000, "currency": "USD"},
        "location_preferences": ["San Francisco", "Seattle", "Remote"],
        "timeline": "6 months",
    }


@pytest.fixture
def orchestrator_commands():
    """Sample orchestrator commands for testing."""
    return {
        "start_session": {
            "command": "START",
            "user_id": "test-user-123",
            "session_config": {"timeout_minutes": 60, "language": "en"},
        },
        "status_check": {"command": "STATUS", "session_id": "test-session-456"},
        "help_request": {"command": "HELP", "topic": "career_analysis"},
    }


@pytest.fixture
def mock_api_responses():
    """Mock API responses for service testing."""
    return {
        "profile_ingestor": {
            "success": {
                "status": "success",
                "profile_id": "profile-789",
                "processing_time": 2.5,
                "data": {
                    "skills_count": 25,
                    "experience_years": 5.5,
                    "education_level": "bachelor",
                },
            },
            "error": {
                "status": "error",
                "error_code": "PARSING_FAILED",
                "message": "Unable to extract meaningful data from resume",
            },
        },
        "strategist": {
            "success": {
                "status": "success",
                "career_paths": [
                    {
                        "path_id": "path-001",
                        "title": "Senior to Staff Engineer Track",
                        "probability": 0.85,
                        "timeline_months": 18,
                        "required_skills": ["System Design", "Leadership", "Go"],
                        "salary_range": {"min": 200000, "max": 280000},
                    }
                ],
                "processing_time": 1.2,
            },
            "error": {
                "status": "error",
                "error_code": "INSUFFICIENT_DATA",
                "message": "Profile lacks sufficient experience data for path generation",
            },
        },
        "analyst": {
            "success": {
                "status": "success",
                "market_analysis": {
                    "demand_score": 0.92,
                    "competition_level": "moderate",
                    "salary_trends": "increasing",
                    "recommended_skills": [
                        "Kubernetes",
                        "Machine Learning",
                        "System Design",
                    ],
                },
                "resume_optimization": {
                    "ats_score": 78,
                    "keyword_density": 0.15,
                    "suggested_improvements": [
                        "Add quantified metrics",
                        "Include more technical keywords",
                    ],
                },
                "processing_time": 3.1,
            },
            "error": {
                "status": "error",
                "error_code": "MARKET_DATA_UNAVAILABLE",
                "message": "Market analysis temporarily unavailable",
            },
        },
    }


async def _wait_for_services_healthy(compose, timeout=300):
    """Wait for all services to be healthy."""
    start_time = time.time()
    services = [
        "orchestrator",
        "profile-ingestor",
        "strategist",
        "analyst",
        "postgres",
        "redis",
    ]

    while time.time() - start_time < timeout:
        healthy_count = 0
        for service in services:
            try:
                # Check service health endpoints
                if service == "postgres":
                    # Check PostgreSQL connection
                    conn = await asyncpg.connect(
                        host="localhost",
                        port=5432,
                        user="helios_dev",
                        password="helios_dev_password",
                        database="helios_dev",
                    )
                    await conn.close()
                    healthy_count += 1
                elif service == "redis":
                    # Check Redis connection
                    client = redis.Redis(host="localhost", port=6379, db=0)
                    await client.ping()
                    await client.close()
                    healthy_count += 1
                else:
                    # Check HTTP health endpoints
                    port_map = {
                        "orchestrator": 8000,
                        "profile-ingestor": 8001,
                        "strategist": 8002,
                        "analyst": 8003,
                    }
                    async with aiohttp.ClientSession() as session:
                        async with session.get(
                            f"http://localhost:{port_map[service]}/health"
                        ) as resp:
                            if resp.status == 200:
                                healthy_count += 1
            except Exception:
                pass

        if healthy_count == len(services):
            return

        await asyncio.sleep(5)

    raise RuntimeError(f"Services did not become healthy within {timeout} seconds")


# Performance test fixtures
@pytest.fixture
def performance_thresholds():
    """Performance thresholds for integration tests."""
    return {
        "orchestrator_response_time": 5.0,  # seconds
        "profile_processing_time": 30.0,  # seconds
        "career_path_generation_time": 10.0,  # seconds
        "market_analysis_time": 15.0,  # seconds
        "end_to_end_workflow_time": 60.0,  # seconds
    }


@pytest.fixture
def load_test_config():
    """Configuration for load testing."""
    return {
        "concurrent_users": 10,
        "requests_per_user": 5,
        "ramp_up_time": 30,  # seconds
        "test_duration": 120,  # seconds
    }
