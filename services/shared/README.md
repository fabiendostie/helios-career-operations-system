# Helios Shared Services

Shared utilities and components for the Helios Career Operations System.

## Overview

This module provides common functionality used across multiple services in the Helios system, including a resilient LLM client with advanced features for production use.

## LLM Client Features

The `ResilientLLMClient` provides a robust interface to Large Language Model services with:

- **Redis Caching**: Automatic caching of identical prompts to reduce API costs and latency
- **Automatic Retries**: Exponential backoff with jitter for transient failures
- **Provider Fallbacks**: Seamless fallback between multiple LLM providers (OpenAI, Anthropic, Azure OpenAI)
- **Circuit Breaker**: Prevents cascading failures by temporarily blocking calls to failing providers
- **Comprehensive Logging**: Detailed logging for monitoring and debugging

## Quick Start

### 1. Environment Setup

Set up your environment variables:

```bash
# Primary provider (OpenAI)
export OPENAI_API_KEY="your-openai-api-key"
export OPENAI_MODEL="gpt-4"

# Fallback provider (Anthropic)
export ANTHROPIC_API_KEY="your-anthropic-api-key"
export ANTHROPIC_MODEL="claude-3-sonnet-20240229"

# Redis for caching
export REDIS_URL="redis://localhost:6379"

# Optional: Circuit breaker and retry configuration
export CIRCUIT_BREAKER_FAILURE_THRESHOLD="5"
export LLM_MAX_RETRIES="3"
export LLM_CACHE_TTL="3600"
```

### 2. Basic Usage

```python
import asyncio
from services.shared.llm_client import ResilientLLMClient

async def main():
    # Initialize client with environment configuration
    async with ResilientLLMClient() as client:

        # Simple generation
        response = await client.generate("Explain quantum computing")
        print(response["content"])

        # With system prompt
        response = await client.generate(
            "Write a technical summary",
            system_prompt="You are a technical writer for developers"
        )
        print(response["content"])

asyncio.run(main())
```

### 3. Advanced Usage

```python
from services.shared.llm_client import ResilientLLMClient, LLMConfig, ProviderConfig

# Custom configuration
config = LLMConfig(
    providers=[
        ProviderConfig(
            name="openai",
            api_key="your-key",
            base_url="https://api.openai.com/v1",
            model="gpt-4"
        )
    ],
    primary_provider="openai"
)

async with ResilientLLMClient(config) as client:
    # Force specific provider
    response = await client.generate(
        "Analyze this data",
        provider_preference=["anthropic"]
    )

    # Disable caching for sensitive data
    response = await client.generate(
        "Process confidential info",
        use_cache=False
    )

    # Check client status
    status = client.get_status()
    print(f"Cache hits: {status['cache']['cached_keys']}")

    # Clear cache
    cleared = await client.clear_cache("gpt-4*")
    print(f"Cleared {cleared} cache entries")
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | - |
| `OPENAI_MODEL` | OpenAI model | `gpt-4` |
| `ANTHROPIC_API_KEY` | Anthropic API key | - |
| `ANTHROPIC_MODEL` | Anthropic model | `claude-3-sonnet-20240229` |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI key | - |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint | - |
| `LLM_PRIMARY_PROVIDER` | Primary provider | `openai` |
| `LLM_FALLBACK_PROVIDERS` | Comma-separated fallbacks | `anthropic` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379` |
| `LLM_CACHE_ENABLED` | Enable caching | `true` |
| `LLM_CACHE_TTL` | Cache TTL in seconds | `3600` |
| `LLM_MAX_RETRIES` | Maximum retry attempts | `3` |
| `LLM_BASE_DELAY` | Base retry delay (seconds) | `1.0` |
| `CIRCUIT_BREAKER_FAILURE_THRESHOLD` | Circuit breaker threshold | `5` |
| `CIRCUIT_BREAKER_RECOVERY_TIMEOUT` | Recovery timeout (seconds) | `60.0` |

### Programmatic Configuration

```python
from services.shared.llm_client.config import (
    LLMConfig, ProviderConfig, CacheConfig, RetryConfig, CircuitBreakerConfig
)

config = LLMConfig(
    providers=[
        ProviderConfig(
            name="openai",
            api_key="your-key",
            base_url="https://api.openai.com/v1",
            model="gpt-4",
            timeout=30.0,
            max_tokens=4000,
            temperature=0.7
        )
    ],
    primary_provider="openai",
    fallback_providers=["anthropic"],
    cache=CacheConfig(
        enabled=True,
        ttl=3600,
        redis_url="redis://localhost:6379"
    ),
    retry=RetryConfig(
        max_retries=3,
        base_delay=1.0,
        exponential_base=2.0,
        jitter=True
    ),
    circuit_breaker=CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=60.0
    )
)

client = ResilientLLMClient(config)
```

## Error Handling

The client provides comprehensive error handling:

```python
from services.shared.llm_client.exceptions import (
    LLMClientError,
    LLMProviderError,
    LLMTimeoutError,
    CircuitBreakerOpenError
)

try:
    response = await client.generate("Test prompt")
except CircuitBreakerOpenError as e:
    print(f"Circuit breaker open for {e.provider}")
    # Wait or try different provider
except LLMProviderError as e:
    print(f"Provider {e.provider} failed: {e}")
    # Log error, alert monitoring
except LLMTimeoutError as e:
    print(f"Request to {e.provider} timed out after {e.timeout}s")
    # Retry with different parameters
except LLMClientError as e:
    print(f"Client error: {e}")
    # General error handling
```

## Monitoring and Observability

### Status Monitoring

```python
status = client.get_status()
print(f"Active providers: {list(status['providers'].keys())}")
print(f"Cache enabled: {status['cache']['enabled']}")
print(f"Cached entries: {status['cache']['cached_keys']}")

for name, provider_status in status['providers'].items():
    cb_stats = provider_status['circuit_breaker']
    print(f"{name}: {cb_stats['state']} ({cb_stats['failure_count']} failures)")
```

### Circuit Breaker Management

```python
# Reset specific circuit breaker
client.reset_circuit_breakers("openai")

# Reset all circuit breakers
client.reset_circuit_breakers()

# Get detailed circuit breaker stats
for name, cb in client.circuit_breakers.items():
    stats = cb.get_stats()
    print(f"{name}: {stats}")
```

### Cache Management

```python
# Get cache statistics
cache_stats = client.cache.get_stats()
print(f"Memory used: {cache_stats['redis_memory_used']}")

# Clear specific patterns
await client.clear_cache("gpt-4*")

# Clear all cache
await client.clear_cache()
```

## Integration with Existing Services

### Strategist Service

```python
# services/strategist/src/llm_service.py
from services.shared.llm_client import ResilientLLMClient

class CareerStrategistLLM:
    def __init__(self):
        self.llm_client = ResilientLLMClient()

    async def generate_career_path(self, profile_data: dict) -> str:
        prompt = f\"\"\"
        Generate a career path for a professional with this profile:
        {profile_data}

        Provide specific recommendations for:
        1. Next role targets
        2. Skill development priorities
        3. Timeline for advancement
        \"\"\"

        response = await self.llm_client.generate(
            prompt,
            system_prompt="You are a career development expert"
        )

        return response["content"]

    async def close(self):
        await self.llm_client.close()
```

### Analyst Service

```python
# services/analyst/src/market_analyzer.py
from services.shared.llm_client import ResilientLLMClient

class MarketAnalyzer:
    def __init__(self):
        self.llm_client = ResilientLLMClient()

    async def analyze_job_market(self, skills: list, location: str) -> dict:
        prompt = f\"\"\"
        Analyze the job market for someone with these skills: {skills}
        Location: {location}

        Provide analysis on:
        1. Market demand
        2. Salary ranges
        3. Growth opportunities
        4. Skill gaps
        \"\"\"

        response = await self.llm_client.generate(
            prompt,
            system_prompt="You are a labor market analyst",
            # Use specific provider for market data
            provider_preference=["anthropic"]
        )

        return {
            "analysis": response["content"],
            "model_used": response["model"],
            "provider": response["provider"]
        }
```

## Testing

Run the test suite:

```bash
cd services/shared
pip install -r requirements.txt
pytest tests/ -v --cov=llm_client
```

### Test Coverage

The test suite includes:

- **Configuration Tests**: Environment variable loading, validation
- **Cache Tests**: Redis operations, key generation, TTL handling
- **Circuit Breaker Tests**: State transitions, failure thresholds, recovery
- **Retry Tests**: Exponential backoff, jitter, timeout handling
- **Provider Tests**: API interactions, error handling, timeout management
- **Client Integration Tests**: End-to-end workflows, fallback logic

### Mock Testing

For testing services that use the LLM client:

```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_service_with_llm():
    with patch('services.shared.llm_client.ResilientLLMClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client.generate.return_value = {
            "content": "Test response",
            "model": "gpt-4",
            "provider": "openai",
            "cached": False,
            "attempts": 1
        }
        mock_client_class.return_value = mock_client

        # Test your service
        service = YourService()
        result = await service.process_with_llm("test input")

        assert "Test response" in result
        mock_client.generate.assert_called_once()
```

## Performance Considerations

### Caching Strategy

- Cache keys include prompt, model, and relevant parameters
- TTL defaults to 1 hour but can be customized per request
- Consider cache warming for frequently used prompts
- Monitor cache hit rates and adjust TTL accordingly

### Provider Selection

- OpenAI: Generally faster, good for shorter responses
- Anthropic: Better for longer, more nuanced responses
- Azure OpenAI: Better for enterprise compliance requirements

### Circuit Breaker Tuning

- Adjust `failure_threshold` based on provider reliability
- Set `recovery_timeout` based on typical service recovery times
- Monitor circuit breaker state transitions

## Troubleshooting

### Common Issues

**Cache Connection Errors**
```
Failed to initialize Redis cache: Connection refused
```
- Check Redis is running: `redis-cli ping`
- Verify REDIS_URL environment variable
- Check network connectivity and firewall rules

**Provider Authentication**
```
Provider openai failed: API error: Invalid API key
```
- Verify API keys are set correctly
- Check API key permissions and quotas
- Ensure API keys are not expired

**Circuit Breaker Open**
```
Circuit breaker open for openai after 5 failures
```
- Check provider status and API limits
- Review error logs for root cause
- Reset circuit breaker: `client.reset_circuit_breakers("openai")`

**High Latency**
```
Request to anthropic timed out after 30.0s
```
- Increase timeout: `ANTHROPIC_TIMEOUT=60`
- Check network connectivity
- Consider using faster models for time-sensitive requests

### Debug Logging

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or configure specific loggers
logging.getLogger('services.shared.llm_client').setLevel(logging.DEBUG)
```

## Contributing

When extending the LLM client:

1. Add comprehensive tests for new features
2. Update configuration documentation
3. Consider backward compatibility
4. Add appropriate error handling
5. Update this README with usage examples

## License

Part of the Helios Career Operations System. See project root for license information.
