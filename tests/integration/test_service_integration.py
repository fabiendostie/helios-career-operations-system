#!/usr/bin/env python3
"""
Integration Tests for Helios Career Operations System
Tests inter-service communication and end-to-end workflows
"""

import asyncio
import json
import os
import sys
from pathlib import Path
import pytest
import aiohttp
from typing import Dict, Any, Optional
import time
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

class ServiceHealthChecker:
    """Check health status of all services"""

    SERVICES = {
        "orchestrator": "http://localhost:8000/health",
        "profile-ingestor": "http://localhost:8001/health",
        "strategist": "http://localhost:8002/health",
        "analyst": "http://localhost:8003/health"
    }

    @classmethod
    async def check_all_services(cls) -> Dict[str, bool]:
        """Check health of all services"""
        results = {}
        async with aiohttp.ClientSession() as session:
            for service, url in cls.SERVICES.items():
                try:
                    async with session.get(url, timeout=5) as response:
                        results[service] = response.status == 200
                except:
                    results[service] = False
        return results

    @classmethod
    async def wait_for_services(cls, timeout: int = 60) -> bool:
        """Wait for all services to be healthy"""
        start = time.time()
        while time.time() - start < timeout:
            health = await cls.check_all_services()
            if all(health.values()):
                return True
            await asyncio.sleep(2)
        return False


class IntegrationTestSuite:
    """Comprehensive integration tests for all services"""

    def __init__(self):
        self.orchestrator_url = "http://localhost:8000"
        self.session_id = None
        self.test_data = self._load_test_data()

    def _load_test_data(self) -> Dict[str, Any]:
        """Load test data for integration testing"""
        return {
            "resume_path": "tests/sample_resumes/english/resume_1.txt",
            "profile_data": {
                "personal_info": {
                    "name": "Test User",
                    "email": "test@example.com",
                    "phone": "+1-555-0100"
                },
                "work_experience": [
                    {
                        "title": "Senior Software Engineer",
                        "company": "Tech Corp",
                        "duration": "2020-2023",
                        "responsibilities": [
                            "Led team of 5 engineers",
                            "Architected microservices platform",
                            "Reduced deployment time by 60%"
                        ]
                    }
                ],
                "skills": [
                    "Python", "FastAPI", "PostgreSQL",
                    "Docker", "Kubernetes", "AWS"
                ]
            }
        }

    async def test_orchestrator_session_management(self) -> bool:
        """Test 1: Orchestrator session creation and management"""
        print("🧪 Test 1: Orchestrator Session Management")

        async with aiohttp.ClientSession() as session:
            # Create new session
            async with session.post(f"{self.orchestrator_url}/sessions/start") as response:
                if response.status != 200:
                    print(f"  ❌ Failed to create session: {response.status}")
                    return False

                data = await response.json()
                self.session_id = data.get("session_id")
                print(f"  ✅ Session created: {self.session_id}")

            # Check session status
            async with session.get(f"{self.orchestrator_url}/sessions/{self.session_id}/status") as response:
                if response.status != 200:
                    print(f"  ❌ Failed to get session status: {response.status}")
                    return False

                data = await response.json()
                print(f"  ✅ Session status: {data.get('state')}")

        return True

    async def test_profile_ingestor_integration(self) -> bool:
        """Test 2: Profile Ingestor integration with Orchestrator"""
        print("🧪 Test 2: Profile Ingestor Integration")

        if not self.session_id:
            print("  ❌ No session ID available")
            return False

        async with aiohttp.ClientSession() as session:
            # Send ingest command
            command_data = {
                "session_id": self.session_id,
                "command": "ingest",
                "data": self.test_data["profile_data"]
            }

            async with session.post(
                f"{self.orchestrator_url}/commands/execute",
                json=command_data
            ) as response:
                if response.status != 200:
                    print(f"  ❌ Failed to execute ingest: {response.status}")
                    return False

                data = await response.json()
                print(f"  ✅ Profile ingested: {data.get('status')}")

        return True

    async def test_strategist_career_generation(self) -> bool:
        """Test 3: Strategist career path generation"""
        print("🧪 Test 3: Strategist Career Generation")

        if not self.session_id:
            print("  ❌ No session ID available")
            return False

        async with aiohttp.ClientSession() as session:
            # Send discover command
            command_data = {
                "session_id": self.session_id,
                "command": "discover"
            }

            async with session.post(
                f"{self.orchestrator_url}/commands/execute",
                json=command_data
            ) as response:
                if response.status != 200:
                    print(f"  ❌ Failed to execute discover: {response.status}")
                    return False

                data = await response.json()
                career_paths = data.get("career_paths", [])

                if not career_paths:
                    print("  ❌ No career paths generated")
                    return False

                print(f"  ✅ Generated {len(career_paths)} career paths")
                for i, path in enumerate(career_paths[:3], 1):
                    print(f"     {i}. {path.get('title', 'Unknown')}")

        return True

    async def test_analyst_market_analysis(self) -> bool:
        """Test 4: Analyst market analysis pipeline"""
        print("🧪 Test 4: Analyst Market Analysis")

        if not self.session_id:
            print("  ❌ No session ID available")
            return False

        async with aiohttp.ClientSession() as session:
            # Send analyze command
            command_data = {
                "session_id": self.session_id,
                "command": "analyze",
                "target_role": "Senior Software Engineer"
            }

            async with session.post(
                f"{self.orchestrator_url}/commands/execute",
                json=command_data
            ) as response:
                if response.status != 200:
                    print(f"  ❌ Failed to execute analyze: {response.status}")
                    return False

                data = await response.json()

                # Check for analysis results
                if "ats_score" not in data:
                    print("  ❌ No ATS score in analysis")
                    return False

                print(f"  ✅ Analysis complete:")
                print(f"     - ATS Score: {data.get('ats_score', 0)}/100")
                print(f"     - Market Match: {data.get('market_match', 0)}%")
                print(f"     - Skills Gap: {len(data.get('skill_gaps', []))} identified")

        return True

    async def test_end_to_end_workflow(self) -> bool:
        """Test 5: Complete end-to-end workflow"""
        print("🧪 Test 5: End-to-End Workflow")

        async with aiohttp.ClientSession() as session:
            # Step 1: Start new session
            async with session.post(f"{self.orchestrator_url}/sessions/start") as response:
                if response.status != 200:
                    print("  ❌ Failed to start session")
                    return False
                data = await response.json()
                workflow_session = data.get("session_id")
                print(f"  ✅ Step 1: Session started ({workflow_session})")

            # Step 2: Ingest profile
            ingest_data = {
                "session_id": workflow_session,
                "command": "ingest",
                "data": self.test_data["profile_data"]
            }

            async with session.post(
                f"{self.orchestrator_url}/commands/execute",
                json=ingest_data
            ) as response:
                if response.status != 200:
                    print("  ❌ Failed to ingest profile")
                    return False
                print("  ✅ Step 2: Profile ingested")

            # Step 3: Generate career paths
            discover_data = {
                "session_id": workflow_session,
                "command": "discover"
            }

            async with session.post(
                f"{self.orchestrator_url}/commands/execute",
                json=discover_data
            ) as response:
                if response.status != 200:
                    print("  ❌ Failed to discover paths")
                    return False
                data = await response.json()
                career_paths = data.get("career_paths", [])
                print(f"  ✅ Step 3: {len(career_paths)} paths discovered")

            # Step 4: Analyze first career path
            if career_paths:
                analyze_data = {
                    "session_id": workflow_session,
                    "command": "analyze",
                    "career_path_id": career_paths[0].get("id")
                }

                async with session.post(
                    f"{self.orchestrator_url}/commands/execute",
                    json=analyze_data
                ) as response:
                    if response.status != 200:
                        print("  ❌ Failed to analyze path")
                        return False
                    print("  ✅ Step 4: Career path analyzed")

            # Step 5: Check final session state
            async with session.get(f"{self.orchestrator_url}/sessions/{workflow_session}/status") as response:
                if response.status != 200:
                    print("  ❌ Failed to get final status")
                    return False
                data = await response.json()
                print(f"  ✅ Step 5: Workflow complete (state: {data.get('state')})")

        return True

    async def test_error_handling(self) -> bool:
        """Test 6: Error handling and recovery"""
        print("🧪 Test 6: Error Handling & Recovery")

        async with aiohttp.ClientSession() as session:
            # Test invalid session
            invalid_data = {
                "session_id": "invalid-session-id",
                "command": "ingest"
            }

            async with session.post(
                f"{self.orchestrator_url}/commands/execute",
                json=invalid_data
            ) as response:
                if response.status == 404:
                    print("  ✅ Invalid session handled correctly")
                else:
                    print(f"  ❌ Unexpected response: {response.status}")
                    return False

            # Test invalid command
            if self.session_id:
                invalid_command = {
                    "session_id": self.session_id,
                    "command": "invalid_command"
                }

                async with session.post(
                    f"{self.orchestrator_url}/commands/execute",
                    json=invalid_command
                ) as response:
                    if response.status == 400:
                        print("  ✅ Invalid command handled correctly")
                    else:
                        print(f"  ❌ Unexpected response: {response.status}")
                        return False

        return True

    async def test_performance_metrics(self) -> bool:
        """Test 7: Performance metrics and response times"""
        print("🧪 Test 7: Performance Metrics")

        metrics = {
            "session_creation": [],
            "profile_ingestion": [],
            "career_generation": [],
            "market_analysis": []
        }

        async with aiohttp.ClientSession() as session:
            # Run 5 iterations to get average
            for i in range(5):
                # Measure session creation
                start = time.time()
                async with session.post(f"{self.orchestrator_url}/sessions/start") as response:
                    if response.status == 200:
                        metrics["session_creation"].append(time.time() - start)
                        data = await response.json()
                        test_session = data.get("session_id")

                # Measure profile ingestion
                if test_session:
                    start = time.time()
                    ingest_data = {
                        "session_id": test_session,
                        "command": "ingest",
                        "data": self.test_data["profile_data"]
                    }
                    async with session.post(
                        f"{self.orchestrator_url}/commands/execute",
                        json=ingest_data
                    ) as response:
                        if response.status == 200:
                            metrics["profile_ingestion"].append(time.time() - start)

        # Calculate averages
        for metric, times in metrics.items():
            if times:
                avg = sum(times) / len(times)
                print(f"  📊 {metric}: {avg:.3f}s average")

                # Check against SLA
                if metric == "session_creation" and avg > 0.2:
                    print(f"     ⚠️ Above SLA target (0.2s)")
                elif metric == "profile_ingestion" and avg > 5:
                    print(f"     ⚠️ Above SLA target (5s)")

        return True

    async def run_all_tests(self) -> Dict[str, bool]:
        """Run all integration tests"""
        print("\n" + "="*60)
        print("🚀 HELIOS INTEGRATION TEST SUITE")
        print("="*60 + "\n")

        # Check services are running
        print("⏳ Checking service health...")
        services_ready = await ServiceHealthChecker.wait_for_services(timeout=30)

        if not services_ready:
            health = await ServiceHealthChecker.check_all_services()
            print("\n❌ Services not ready:")
            for service, status in health.items():
                icon = "✅" if status else "❌"
                print(f"  {icon} {service}: {'Online' if status else 'Offline'}")
            print("\n⚠️  Please start all services before running tests")
            return {"services_check": False}

        print("✅ All services online\n")

        # Run tests
        results = {}
        tests = [
            ("orchestrator_session", self.test_orchestrator_session_management),
            ("profile_ingestor", self.test_profile_ingestor_integration),
            ("strategist", self.test_strategist_career_generation),
            ("analyst", self.test_analyst_market_analysis),
            ("end_to_end", self.test_end_to_end_workflow),
            ("error_handling", self.test_error_handling),
            ("performance", self.test_performance_metrics)
        ]

        for test_name, test_func in tests:
            try:
                results[test_name] = await test_func()
                print()  # Add spacing between tests
            except Exception as e:
                print(f"  ❌ Test failed with exception: {e}")
                results[test_name] = False
                print()

        # Summary
        print("="*60)
        print("📊 TEST SUMMARY")
        print("="*60)

        passed = sum(1 for r in results.values() if r)
        total = len(results)

        for test_name, result in results.items():
            icon = "✅" if result else "❌"
            print(f"{icon} {test_name}: {'PASSED' if result else 'FAILED'}")

        print(f"\n🎯 Overall: {passed}/{total} tests passed ({passed*100//total}%)")

        if passed == total:
            print("🎉 All integration tests passed!")
        else:
            print("⚠️  Some tests failed. Please review the output above.")

        return results


async def main():
    """Main entry point for integration tests"""
    tester = IntegrationTestSuite()
    results = await tester.run_all_tests()

    # Exit with appropriate code
    sys.exit(0 if all(results.values()) else 1)


if __name__ == "__main__":
    asyncio.run(main())
