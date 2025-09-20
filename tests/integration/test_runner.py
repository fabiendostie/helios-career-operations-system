#!/usr/bin/env python3
"""
Integration test runner for Helios Career Operations System.

This script provides a convenient way to run integration tests with
Docker Compose environment management and reporting.
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path


class HeliosTestRunner:
    """Test runner for Helios integration tests."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.compose_file = project_root / "docker-compose.test.yml"
        self.reports_dir = project_root / "tests" / "integration" / "reports"

    def setup_environment(self):
        """Set up test environment."""
        print("Setting up test environment...")

        # Create reports directory
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        # Set environment variables
        os.environ["PYTHONPATH"] = str(self.project_root)
        os.environ["PYTEST_CURRENT_TEST"] = "integration"

        print("✓ Environment setup complete")

    def start_services(self, services: list[str] | None = None):
        """Start Docker Compose services for testing."""
        print("Starting test services...")

        cmd = ["docker-compose", "-f", str(self.compose_file), "up", "-d"]
        if services:
            cmd.extend(services)

        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print("✓ Services started successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to start services: {e.stderr}")
            return False

    def wait_for_services(self, timeout: int = 300):
        """Wait for all services to become healthy."""
        print("Waiting for services to become healthy...")

        start_time = time.time()
        services = [
            "postgres-test",
            "redis-test",
            "orchestrator-test",
            "profile-ingestor-test",
            "strategist-test",
            "analyst-test",
        ]

        while time.time() - start_time < timeout:
            all_healthy = True

            for service in services:
                cmd = [
                    "docker-compose",
                    "-f",
                    str(self.compose_file),
                    "ps",
                    "-q",
                    service,
                ]
                result = subprocess.run(cmd, capture_output=True, text=True)

                if not result.stdout.strip():
                    all_healthy = False
                    break

                # Check health status
                container_id = result.stdout.strip()
                health_cmd = [
                    "docker",
                    "inspect",
                    "--format",
                    "{{.State.Health.Status}}",
                    container_id,
                ]
                health_result = subprocess.run(
                    health_cmd, capture_output=True, text=True
                )

                if health_result.returncode == 0:
                    health_status = health_result.stdout.strip()
                    if health_status != "healthy":
                        all_healthy = False
                        break
                else:
                    # Service might not have health check, check if running
                    status_cmd = [
                        "docker",
                        "inspect",
                        "--format",
                        "{{.State.Status}}",
                        container_id,
                    ]
                    status_result = subprocess.run(
                        status_cmd, capture_output=True, text=True
                    )
                    if status_result.stdout.strip() != "running":
                        all_healthy = False
                        break

            if all_healthy:
                print("✓ All services are healthy")
                return True

            print("⏳ Waiting for services to become healthy...")
            time.sleep(5)

        print("✗ Timeout waiting for services to become healthy")
        return False

    def run_tests(
        self, test_type: str = "all", markers: list[str] | None = None
    ) -> bool:
        """Run integration tests."""
        print(f"Running {test_type} tests...")

        # Base pytest command
        cmd = [
            "python",
            "-m",
            "pytest",
            "tests/integration/",
            "--verbose",
            "--tb=short",
            f"--junit-xml={self.reports_dir}/test-results.xml",
            f"--html={self.reports_dir}/test-report.html",
            "--self-contained-html",
            "--cov=services",
            f"--cov-report=html:{self.reports_dir}/coverage",
            "--cov-report=term",
            "--durations=10",
        ]

        # Add test type specific options
        if test_type == "smoke":
            cmd.extend(["-m", "smoke"])
        elif test_type == "performance":
            cmd.extend(["-m", "performance", "--timeout=600"])
        elif test_type == "error_handling":
            cmd.extend(["-m", "error_handling"])
        elif test_type == "data_validation":
            cmd.extend(["-m", "data_validation"])
        elif test_type == "fast":
            cmd.extend(["-m", "fast"])
        elif test_type == "integration":
            cmd.extend(["-m", "integration"])

        # Add custom markers
        if markers:
            for marker in markers:
                cmd.extend(["-m", marker])

        # Run tests
        try:
            result = subprocess.run(
                cmd, cwd=self.project_root, timeout=1800
            )  # 30 minute timeout
            success = result.returncode == 0

            if success:
                print("✓ Tests completed successfully")
            else:
                print("✗ Some tests failed")

            return success

        except subprocess.TimeoutExpired:
            print("✗ Tests timed out")
            return False
        except Exception as e:
            print(f"✗ Error running tests: {e}")
            return False

    def stop_services(self):
        """Stop and clean up Docker Compose services."""
        print("Stopping test services...")

        cmd = ["docker-compose", "-f", str(self.compose_file), "down", "-v"]
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            print("✓ Services stopped and cleaned up")
        except subprocess.CalledProcessError as e:
            print(f"✗ Error stopping services: {e.stderr}")

    def cleanup(self):
        """Clean up test artifacts."""
        print("Cleaning up test artifacts...")

        # Remove test containers and volumes
        subprocess.run(["docker", "system", "prune", "-f"], capture_output=True)

        print("✓ Cleanup complete")

    def generate_report(self):
        """Generate comprehensive test report."""
        print("Generating test report...")

        report_file = self.reports_dir / "integration-test-summary.md"

        with open(report_file, "w") as f:
            f.write("# Helios Integration Test Report\n\n")
            f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            # Test results summary
            if (self.reports_dir / "test-results.xml").exists():
                f.write("## Test Results\n\n")
                f.write("- JUnit XML: [test-results.xml](test-results.xml)\n")
                f.write("- HTML Report: [test-report.html](test-report.html)\n\n")

            # Coverage summary
            if (self.reports_dir / "coverage").exists():
                f.write("## Coverage Report\n\n")
                f.write(
                    "- Coverage HTML: [coverage/index.html](coverage/index.html)\n\n"
                )

            # Service status
            f.write("## Service Status\n\n")
            f.write("All services were tested in isolated Docker environment.\n\n")

            f.write("## Test Categories\n\n")
            f.write("- **Integration**: End-to-end workflow tests\n")
            f.write("- **Performance**: Load and performance tests\n")
            f.write("- **Error Handling**: Error scenarios and resilience\n")
            f.write("- **Data Validation**: Data integrity and validation\n\n")

        print(f"✓ Report generated: {report_file}")


def main():
    """Main test runner entry point."""
    parser = argparse.ArgumentParser(description="Helios Integration Test Runner")

    parser.add_argument(
        "--type",
        choices=[
            "all",
            "smoke",
            "performance",
            "error_handling",
            "data_validation",
            "fast",
            "integration",
        ],
        default="all",
        help="Type of tests to run",
    )

    parser.add_argument(
        "--markers", nargs="*", help="Additional pytest markers to apply"
    )

    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Skip cleanup after tests (useful for debugging)",
    )

    parser.add_argument(
        "--services-only",
        action="store_true",
        help="Only start services, don't run tests",
    )

    parser.add_argument("--stop-only", action="store_true", help="Only stop services")

    args = parser.parse_args()

    # Determine project root
    current_dir = Path(__file__).parent
    project_root = current_dir.parent.parent

    runner = HeliosTestRunner(project_root)

    if args.stop_only:
        runner.stop_services()
        return

    try:
        # Setup
        runner.setup_environment()

        # Start services
        if not runner.start_services():
            print("Failed to start services")
            sys.exit(1)

        # Wait for services
        if not runner.wait_for_services():
            print("Services failed to become healthy")
            sys.exit(1)

        if args.services_only:
            print("Services are running. Press Ctrl+C to stop.")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
        else:
            # Run tests
            success = runner.run_tests(args.type, args.markers)

            # Generate report
            runner.generate_report()

            if not success:
                sys.exit(1)

    except KeyboardInterrupt:
        print("\nTest run interrupted")
        sys.exit(1)

    finally:
        if not args.no_cleanup:
            runner.stop_services()
            runner.cleanup()


if __name__ == "__main__":
    main()
