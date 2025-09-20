#!/usr/bin/env python3
"""
Basic usage examples for the ResilientLLMClient.

This script demonstrates common usage patterns for the Helios LLM client
including basic generation, caching, error handling, and monitoring.
"""

import asyncio
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Add parent directory to path for imports
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.shared.llm_client import ResilientLLMClient
from services.shared.llm_client.exceptions import (
    CircuitBreakerOpenError,
    LLMClientError,
    LLMProviderError,
)


async def basic_generation_example():
    """Demonstrate basic LLM generation."""
    print("\n=== Basic Generation Example ===")

    async with ResilientLLMClient() as client:
        try:
            response = await client.generate(
                "Explain the concept of microservices architecture in 2 sentences."
            )

            print(f"Response: {response['content']}")
            print(f"Model: {response['model']}")
            print(f"Provider: {response['provider']}")
            print(f"Cached: {response['cached']}")
            print(f"Attempts: {response['attempts']}")

        except Exception as e:
            print(f"Error: {e}")


async def system_prompt_example():
    """Demonstrate usage with system prompts."""
    print("\n=== System Prompt Example ===")

    async with ResilientLLMClient() as client:
        try:
            response = await client.generate(
                "How should I structure a career transition from software engineering to product management?",
                system_prompt="You are a senior career counselor with 15 years of experience helping tech professionals advance their careers. Provide practical, actionable advice.",
            )

            print(f"Career Advice: {response['content']}")

        except Exception as e:
            print(f"Error: {e}")


async def caching_demonstration():
    """Demonstrate caching behavior."""
    print("\n=== Caching Demonstration ===")

    async with ResilientLLMClient() as client:
        prompt = "What are the key benefits of using Redis for caching?"

        # First call - should hit the API
        print("First call (API):")
        response1 = await client.generate(prompt)
        print(f"Cached: {response1['cached']}")
        print(f"Attempts: {response1['attempts']}")

        # Second call - should hit cache
        print("\nSecond call (Cache):")
        response2 = await client.generate(prompt)
        print(f"Cached: {response2['cached']}")
        print(f"Attempts: {response2['attempts']}")

        # Verify same content
        print(f"Same content: {response1['content'] == response2['content']}")


async def provider_preference_example():
    """Demonstrate provider preference selection."""
    print("\n=== Provider Preference Example ===")

    async with ResilientLLMClient() as client:
        try:
            # Try to use Anthropic first
            response = await client.generate(
                "Compare Python and JavaScript for backend development",
                provider_preference=["anthropic", "openai"],
            )

            print(f"Used provider: {response['provider']}")
            print(f"Response: {response['content'][:200]}...")

        except Exception as e:
            print(f"Error: {e}")


async def error_handling_example():
    """Demonstrate comprehensive error handling."""
    print("\n=== Error Handling Example ===")

    async with ResilientLLMClient() as client:
        try:
            # This might fail if no providers are configured
            response = await client.generate(
                "Test prompt for error handling",
                provider_preference=["nonexistent_provider"],
            )
            print(f"Unexpected success: {response['provider']}")

        except CircuitBreakerOpenError as e:
            print(f"Circuit breaker open for {e.provider}: {e}")
        except LLMProviderError as e:
            print(f"Provider {e.provider} failed: {e}")
        except LLMClientError as e:
            print(f"Client error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")


async def monitoring_example():
    """Demonstrate monitoring and status checking."""
    print("\n=== Monitoring Example ===")

    async with ResilientLLMClient() as client:
        # Get overall status
        status = client.get_status()

        print("=== Client Status ===")
        print(f"Primary provider: {status['config']['primary_provider']}")
        print(f"Fallback providers: {status['config']['fallback_providers']}")

        print("\n=== Provider Status ===")
        for name, provider_status in status["providers"].items():
            cb_stats = provider_status["circuit_breaker"]
            print(f"Provider: {name}")
            print(f"  Circuit Breaker: {cb_stats['state']}")
            print(f"  Failures: {cb_stats['failure_count']}")
            print(f"  Successes: {cb_stats['success_count']}")

        print("\n=== Cache Status ===")
        cache_stats = status["cache"]
        print(f"Cache enabled: {cache_stats.get('enabled', False)}")
        print(f"Redis connected: {cache_stats.get('redis_connected', False)}")
        if cache_stats.get("redis_connected"):
            print(f"Cached keys: {cache_stats.get('cached_keys', 0)}")
            print(f"Memory used: {cache_stats.get('redis_memory_used', 'N/A')}")


async def custom_parameters_example():
    """Demonstrate using custom parameters."""
    print("\n=== Custom Parameters Example ===")

    async with ResilientLLMClient() as client:
        try:
            response = await client.generate(
                "Write a creative story about a robot learning to paint",
                temperature=0.9,  # Higher creativity
                max_tokens=500,  # Longer response
                top_p=0.95,  # More diverse word choices
            )

            print(f"Creative story: {response['content']}")
            print(f"Token usage: {response.get('usage', {})}")

        except Exception as e:
            print(f"Error: {e}")


async def cache_management_example():
    """Demonstrate cache management operations."""
    print("\n=== Cache Management Example ===")

    async with ResilientLLMClient() as client:
        # Generate some cached responses
        await client.generate("What is machine learning?")
        await client.generate("What is deep learning?")
        await client.generate("What is artificial intelligence?")

        # Check cache stats
        cache_stats = client.cache.get_stats()
        if cache_stats.get("redis_connected"):
            print(f"Cached entries before clear: {cache_stats.get('cached_keys', 0)}")

            # Clear cache with pattern
            cleared = await client.clear_cache("*learning*")
            print(f"Cleared {cleared} entries matching '*learning*'")

            # Check cache stats again
            cache_stats = client.cache.get_stats()
            print(f"Cached entries after clear: {cache_stats.get('cached_keys', 0)}")
        else:
            print("Cache not available for management example")


async def batch_processing_example():
    """Demonstrate processing multiple prompts efficiently."""
    print("\n=== Batch Processing Example ===")

    prompts = [
        "Summarize the benefits of cloud computing",
        "Explain RESTful API design principles",
        "What are the advantages of containerization?",
        "Describe the microservices architecture pattern",
    ]

    async with ResilientLLMClient() as client:
        tasks = []
        for i, prompt in enumerate(prompts):
            task = client.generate(f"[Question {i+1}] {prompt}")
            tasks.append(task)

        # Process all prompts concurrently
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                print(f"Prompt {i+1} failed: {response}")
            else:
                print(
                    f"Prompt {i+1} ({response['provider']}): {response['content'][:100]}..."
                )


async def circuit_breaker_demo():
    """Demonstrate circuit breaker behavior (requires failing provider)."""
    print("\n=== Circuit Breaker Demo ===")

    async with ResilientLLMClient() as client:
        # Check initial circuit breaker states
        print("Initial circuit breaker states:")
        for name, cb in client.circuit_breakers.items():
            stats = cb.get_stats()
            print(f"  {name}: {stats['state']} ({stats['failure_count']} failures)")

        # You can manually test circuit breaker by:
        # 1. Setting invalid API keys in environment
        # 2. Or using a test configuration with bad endpoints

        print(
            "\nNote: To test circuit breaker behavior, configure invalid API credentials"
        )
        print("and run several requests to trigger failures.")


async def main():
    """Run all examples."""
    print("=== ResilientLLMClient Usage Examples ===")
    print("Make sure you have set up your environment variables:")
    print("- OPENAI_API_KEY or ANTHROPIC_API_KEY")
    print("- REDIS_URL (optional, for caching)")
    print()

    examples = [
        basic_generation_example,
        system_prompt_example,
        caching_demonstration,
        provider_preference_example,
        error_handling_example,
        monitoring_example,
        custom_parameters_example,
        cache_management_example,
        batch_processing_example,
        circuit_breaker_demo,
    ]

    for example in examples:
        try:
            await example()
        except Exception as e:
            print(f"Example {example.__name__} failed: {e}")

        print("-" * 60)


if __name__ == "__main__":
    # Run examples
    asyncio.run(main())
