#!/usr/bin/env python3
"""
BMAD Phase 4 - Automated Health Check Script
Tests all service health endpoints and validates system readiness

Usage: python bmad-core/scripts/health-check-all.py [--port-range 8000-8010]
"""

import asyncio
import aiohttp
import sys
import yaml
import json
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import argparse

class ServiceHealthChecker:
    """Automated health checking for all BMAD services"""

    def __init__(self, port_range: str = "8000-8010"):
        self.root_path = Path(__file__).parent.parent.parent
        self.config_path = self.root_path / "bmad-core" / "core-config.yaml"
        self.port_start, self.port_end = self._parse_port_range(port_range)
        self.service_processes = {}
        self.health_results = {}

    def _parse_port_range(self, port_range: str) -> Tuple[int, int]:
        """Parse port range string like '8000-8010'"""
        try:
            start, end = port_range.split('-')
            return int(start), int(end)
        except ValueError:
            return 8000, 8010

    def load_config(self) -> Dict:
        """Load BMAD core configuration"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def get_service_port(self, service_name: str) -> int:
        """Get designated port for service"""
        port_mapping = {
            "orchestrator": 8000,
            "profile_ingestor": 8001,
            "strategist": 8002,
            "analyst": 8003,
            "architect": 8004,
            "editor": 8005
        }
        return port_mapping.get(service_name, 8000)

    def start_service(self, service_name: str, service_path: str) -> Dict:
        """Start a service in background"""
        service_dir = self.root_path / service_path
        port = self.get_service_port(service_name)

        if not service_dir.exists():
            return {
                "started": False,
                "error": f"Service directory not found: {service_dir}"
            }

        try:
            # Start uvicorn server
            cmd = [
                sys.executable, "-m", "uvicorn", "src.main:app",
                "--host", "0.0.0.0",
                "--port", str(port),
                "--log-level", "error"  # Reduce noise
            ]

            process = subprocess.Popen(
                cmd,
                cwd=service_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
            )

            self.service_processes[service_name] = {
                "process": process,
                "port": port,
                "start_time": time.time()
            }

            # Give service time to start
            time.sleep(3)

            return {
                "started": True,
                "port": port,
                "pid": process.pid
            }

        except Exception as e:
            return {
                "started": False,
                "error": f"Failed to start service: {str(e)}"
            }

    async def check_health_endpoint(self, service_name: str, port: int, timeout: int = 10) -> Dict:
        """Check service health endpoint"""
        health_url = f"http://localhost:{port}/health"

        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                async with session.get(health_url) as response:
                    if response.status == 200:
                        try:
                            data = await response.json()
                            return {
                                "healthy": True,
                                "status_code": response.status,
                                "response": data,
                                "response_time": timeout - session._timeout.total if hasattr(session, '_timeout') else "unknown"
                            }
                        except:
                            text = await response.text()
                            return {
                                "healthy": True,
                                "status_code": response.status,
                                "response": text,
                                "response_time": "unknown"
                            }
                    else:
                        return {
                            "healthy": False,
                            "status_code": response.status,
                            "error": f"HTTP {response.status}"
                        }

        except asyncio.TimeoutError:
            return {
                "healthy": False,
                "error": "Request timeout"
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }

    def stop_service(self, service_name: str):
        """Stop a running service"""
        if service_name in self.service_processes:
            process_info = self.service_processes[service_name]
            process = process_info["process"]

            try:
                process.terminate()
                process.wait(timeout=10)
            except:
                try:
                    process.kill()
                    process.wait(timeout=5)
                except:
                    pass

            del self.service_processes[service_name]

    def stop_all_services(self):
        """Stop all running services"""
        for service_name in list(self.service_processes.keys()):
            self.stop_service(service_name)

    async def run_comprehensive_health_check(self) -> Dict:
        """Run health checks on all services"""
        config = self.load_config()
        services = config.get("agents", {})

        results = {
            "check_date": datetime.now().isoformat(),
            "total_services": len(services),
            "services": {},
            "summary": {
                "healthy": 0,
                "unhealthy": 0,
                "failed_to_start": 0
            }
        }

        print("Starting comprehensive health check...")

        # Start all services
        for service_name, service_info in services.items():
            if service_info.get("location") and service_info.get("status") not in ["pending"]:
                print(f"Starting {service_name}...")
                start_result = self.start_service(service_name, service_info["location"])

                service_result = {
                    "service": service_name,
                    "path": service_info["location"],
                    "start_result": start_result,
                    "health_check": None,
                    "overall_status": "unknown"
                }

                if start_result["started"]:
                    port = start_result["port"]
                    print(f"Checking health endpoint for {service_name} on port {port}...")

                    # Wait a bit more for service to be ready
                    await asyncio.sleep(2)

                    health_result = await self.check_health_endpoint(service_name, port)
                    service_result["health_check"] = health_result

                    if health_result["healthy"]:
                        service_result["overall_status"] = "healthy"
                        results["summary"]["healthy"] += 1
                    else:
                        service_result["overall_status"] = "unhealthy"
                        results["summary"]["unhealthy"] += 1
                else:
                    service_result["overall_status"] = "failed_to_start"
                    results["summary"]["failed_to_start"] += 1

                results["services"][service_name] = service_result

        return results

    def generate_health_report(self, results: Dict) -> str:
        """Generate comprehensive health check report"""
        report = []
        report.append("BMAD AUTOMATED HEALTH CHECK REPORT")
        report.append("=" * 50)
        report.append(f"Check Date: {results['check_date']}")
        report.append(f"Total Services: {results['total_services']}")
        report.append("")

        # Summary
        summary = results['summary']
        report.append("SUMMARY")
        report.append(f"Healthy: {summary['healthy']}")
        report.append(f"Unhealthy: {summary['unhealthy']}")
        report.append(f"Failed to Start: {summary['failed_to_start']}")

        system_health = (summary['healthy'] / results['total_services']) * 100 if results['total_services'] > 0 else 0
        report.append(f"System Health: {system_health:.1f}%")
        report.append("")

        # Detailed results
        report.append("DETAILED RESULTS")
        for service_name, service_result in results["services"].items():
            status = service_result["overall_status"]

            if status == "healthy":
                icon = "[HEALTHY]"
            elif status == "unhealthy":
                icon = "[UNHEALTHY]"
            else:
                icon = "[FAILED]"

            report.append(f"{icon} {service_name.upper()}")

            # Start result
            start_result = service_result["start_result"]
            if start_result["started"]:
                report.append(f"   Started: OK (Port {start_result['port']}, PID {start_result['pid']})")
            else:
                report.append(f"   Started: FAILED - {start_result['error']}")

            # Health check result
            health_check = service_result.get("health_check")
            if health_check:
                if health_check["healthy"]:
                    response = health_check.get("response", "OK")
                    report.append(f"   Health: OK (HTTP {health_check['status_code']}) - {response}")
                else:
                    error = health_check.get("error", "Unknown error")
                    status_code = health_check.get("status_code", "N/A")
                    report.append(f"   Health: FAILED (HTTP {status_code}) - {error}")
            else:
                report.append(f"   Health: Not checked (service failed to start)")

            report.append("")

        return "\n".join(report)

    def save_results(self, results: Dict, output_file: Optional[str] = None):
        """Save health check results"""
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            output_file = self.root_path / "bmad-core" / "verification-results" / f"health-check-{timestamp}.json"

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"Results saved to: {output_path}")

async def main():
    parser = argparse.ArgumentParser(description='BMAD Automated Health Check')
    parser.add_argument('--port-range', default='8000-8010',
                       help='Port range for services (default: 8000-8010)')
    parser.add_argument('--timeout', type=int, default=30,
                       help='Timeout for health checks in seconds (default: 30)')

    args = parser.parse_args()

    checker = ServiceHealthChecker(port_range=args.port_range)

    try:
        # Run comprehensive health check
        results = await checker.run_comprehensive_health_check()

        # Generate and display report
        report = checker.generate_health_report(results)
        print("\n" + report)

        # Save results
        checker.save_results(results)

        # Determine exit code
        summary = results["summary"]
        if summary["healthy"] == results["total_services"]:
            print("\nAll services are healthy!")
            exit_code = 0
        elif summary["healthy"] > 0:
            print("\nSome services are unhealthy but system is partially functional")
            exit_code = 1
        else:
            print("\nCritical: No services are healthy")
            exit_code = 2

    except KeyboardInterrupt:
        print("\nHealth check interrupted by user")
        exit_code = 130
    except Exception as e:
        print(f"\nHealth check failed: {str(e)}")
        exit_code = 1
    finally:
        # Clean up - stop all services
        print("\nStopping services...")
        checker.stop_all_services()

    sys.exit(exit_code)

if __name__ == "__main__":
    asyncio.run(main())
