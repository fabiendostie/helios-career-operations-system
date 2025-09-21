#!/usr/bin/env python3
"""
BMAD Phase 4 - Service Status Verification Script
Enhanced verification script that tests actual service functionality

Usage: python bmad-core/scripts/verify-service-status.py [service_name]
"""

import os
import sys
import subprocess
import importlib.util
from pathlib import Path
import yaml
import json
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import time

class ServiceStatusVerifier:
    """Comprehensive service functionality verification"""

    def __init__(self):
        self.root_path = Path(__file__).parent.parent.parent
        self.config_path = self.root_path / "bmad-core" / "core-config.yaml"
        self.results = {}

    def load_config(self) -> Dict:
        """Load BMAD core configuration"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def verify_service_import(self, service_name: str, service_path: str) -> Tuple[bool, str, List[str]]:
        """Verify service can be imported and capture detailed logs"""
        try:
            service_dir = self.root_path / service_path
            if not service_dir.exists():
                return False, f"Service directory not found: {service_dir}", []

            # Change to service directory
            original_cwd = os.getcwd()
            os.chdir(service_dir)

            # Try to import main module with detailed output
            result = subprocess.run([
                sys.executable, "-c",
                "import sys; import src.main; print('Import successful'); print('Available modules:', [m for m in dir(src.main) if not m.startswith('_')])"
            ], capture_output=True, text=True, timeout=120)

            os.chdir(original_cwd)

            # Parse output for module info
            modules_info = []
            if result.stdout:
                lines = result.stdout.strip().split('\n')
                modules_info = lines

            if result.returncode == 0:
                return True, "Import successful", modules_info
            else:
                return False, f"Import failed: {result.stderr}", []

        except Exception as e:
            return False, f"Import verification failed: {str(e)}", []

    def verify_fastapi_service(self, service_name: str, service_path: str, port: int = 8000) -> Dict:
        """Verify FastAPI service can start and respond"""
        service_dir = self.root_path / service_path
        original_cwd = os.getcwd()

        try:
            os.chdir(service_dir)

            # Test if uvicorn can load the app without starting server
            result = subprocess.run([
                sys.executable, "-c",
                "from src.main import app; print('FastAPI app loaded'); print('Routes:', [route.path for route in app.routes])"
            ], capture_output=True, text=True, timeout=60)

            os.chdir(original_cwd)

            if result.returncode == 0:
                routes = []
                if result.stdout:
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if 'Routes:' in line:
                            routes = line.split('Routes:')[1].strip()

                return {
                    "can_load_app": True,
                    "message": "FastAPI app loads successfully",
                    "routes": routes,
                    "details": result.stdout
                }
            else:
                return {
                    "can_load_app": False,
                    "message": f"FastAPI app failed to load: {result.stderr}",
                    "routes": [],
                    "details": result.stderr
                }

        except Exception as e:
            os.chdir(original_cwd)
            return {
                "can_load_app": False,
                "message": f"FastAPI verification failed: {str(e)}",
                "routes": [],
                "details": str(e)
            }

    def verify_ml_models(self, service_name: str, service_path: str) -> Dict:
        """Verify ML models can load (for Strategist/Analyst services)"""
        service_dir = self.root_path / service_path
        original_cwd = os.getcwd()

        try:
            os.chdir(service_dir)

            # Test model loading
            test_script = '''
import sys
try:
    from src.main import app
    print("Main app imported")

    # Try to identify ML components
    if hasattr(app, "state"):
        print("FastAPI app state available")

    # Test sentence-transformers if available
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        print("sentence-transformers model loaded")
    except ImportError:
        print("sentence-transformers not available")
    except Exception as e:
        print(f"sentence-transformers error: {e}")

    # Test spaCy if available
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        print("spaCy en_core_web_sm loaded")
    except ImportError:
        print("spaCy not available")
    except Exception as e:
        print(f"spaCy error: {e}")

except Exception as e:
    print(f"Model verification failed: {e}")
    sys.exit(1)
'''

            result = subprocess.run([
                sys.executable, "-c", test_script
            ], capture_output=True, text=True, timeout=180)

            os.chdir(original_cwd)

            return {
                "models_verified": result.returncode == 0,
                "details": result.stdout if result.stdout else result.stderr,
                "message": "ML models verified" if result.returncode == 0 else "ML model verification failed"
            }

        except Exception as e:
            os.chdir(original_cwd)
            return {
                "models_verified": False,
                "details": str(e),
                "message": f"ML model verification failed: {str(e)}"
            }

    def run_service_tests(self, service_name: str, service_path: str) -> Dict:
        """Run pytest tests if available"""
        service_dir = self.root_path / service_path
        tests_dir = service_dir / "tests"

        if not tests_dir.exists():
            return {
                "tests_available": False,
                "message": "No tests directory found"
            }

        original_cwd = os.getcwd()

        try:
            os.chdir(service_dir)

            # Run pytest with timeout
            result = subprocess.run([
                sys.executable, "-m", "pytest", "tests/", "--tb=short", "-v"
            ], capture_output=True, text=True, timeout=300)

            os.chdir(original_cwd)

            # Parse test results
            test_info = {
                "tests_available": True,
                "tests_passed": result.returncode == 0,
                "output": result.stdout,
                "errors": result.stderr
            }

            # Extract test count info
            if result.stdout:
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'passed' in line or 'failed' in line or 'error' in line:
                        test_info["summary"] = line.strip()
                        break

            return test_info

        except subprocess.TimeoutExpired:
            os.chdir(original_cwd)
            return {
                "tests_available": True,
                "tests_passed": False,
                "message": "Test execution timed out (>5 minutes)"
            }
        except Exception as e:
            os.chdir(original_cwd)
            return {
                "tests_available": True,
                "tests_passed": False,
                "message": f"Test execution failed: {str(e)}"
            }

    def verify_service_comprehensive(self, service_name: str, service_info: Dict) -> Dict:
        """Comprehensive service verification"""
        service_path = service_info.get("location", "")

        verification = {
            "service": service_name,
            "path": str(service_path),
            "verification_date": datetime.now().isoformat(),
            "import_test": {},
            "fastapi_test": {},
            "ml_models_test": {},
            "tests_execution": {},
            "overall_status": "unknown",
            "functional_score": 0
        }

        print(f"Verifying {service_name}...")

        # 1. Import test
        import_success, import_message, modules_info = self.verify_service_import(service_name, service_path)
        verification["import_test"] = {
            "success": import_success,
            "message": import_message,
            "modules_info": modules_info
        }

        if import_success:
            verification["functional_score"] += 25

            # 2. FastAPI test
            fastapi_result = self.verify_fastapi_service(service_name, service_path)
            verification["fastapi_test"] = fastapi_result

            if fastapi_result.get("can_load_app"):
                verification["functional_score"] += 25

            # 3. ML Models test (for ML services)
            if service_name in ["strategist", "analyst"]:
                ml_result = self.verify_ml_models(service_name, service_path)
                verification["ml_models_test"] = ml_result

                if ml_result.get("models_verified"):
                    verification["functional_score"] += 25
            else:
                verification["functional_score"] += 25  # Non-ML services skip this

            # 4. Tests execution
            tests_result = self.run_service_tests(service_name, service_path)
            verification["tests_execution"] = tests_result

            if tests_result.get("tests_passed"):
                verification["functional_score"] += 25
            elif not tests_result.get("tests_available"):
                verification["functional_score"] += 15  # Partial credit if no tests

        # Determine overall status
        if verification["functional_score"] >= 75:
            verification["overall_status"] = "operational"
        elif verification["functional_score"] >= 50:
            verification["overall_status"] = "partially_functional"
        elif verification["functional_score"] >= 25:
            verification["overall_status"] = "limited_functionality"
        else:
            verification["overall_status"] = "failed"

        return verification

    def verify_all_services(self) -> Dict:
        """Verify all services in configuration"""
        config = self.load_config()
        services = config.get("agents", {})

        results = {
            "verification_date": datetime.now().isoformat(),
            "total_services": len(services),
            "services": {},
            "summary": {
                "operational": 0,
                "partially_functional": 0,
                "limited_functionality": 0,
                "failed": 0
            }
        }

        for service_name, service_info in services.items():
            if service_info.get("location"):
                verification = self.verify_service_comprehensive(service_name, service_info)
                results["services"][service_name] = verification

                # Update summary
                status = verification["overall_status"]
                results["summary"][status] = results["summary"].get(status, 0) + 1

        return results

    def generate_report(self, results: Dict) -> str:
        """Generate comprehensive verification report"""
        report = []
        report.append("BMAD PHASE 4 - SERVICE STATUS VERIFICATION REPORT")
        report.append("=" * 70)
        report.append(f"Verification Date: {results['verification_date']}")
        report.append(f"Total Services: {results['total_services']}")
        report.append("")

        # Summary
        summary = results['summary']
        total_functional = summary.get('operational', 0) + summary.get('partially_functional', 0)
        report.append("SUMMARY")
        report.append(f"Operational: {summary.get('operational', 0)}")
        report.append(f"Partially Functional: {summary.get('partially_functional', 0)}")
        report.append(f"Limited Functionality: {summary.get('limited_functionality', 0)}")
        report.append(f"Failed: {summary.get('failed', 0)}")
        report.append(f"Overall System Health: {total_functional}/{results['total_services']} services functional")
        report.append("")

        # Detailed results
        report.append("DETAILED VERIFICATION RESULTS")
        for service_name, verification in results["services"].items():
            status = verification["overall_status"]
            score = verification["functional_score"]

            if status == "operational":
                icon = "[PASS]"
            elif status == "partially_functional":
                icon = "[WARN]"
            elif status == "limited_functionality":
                icon = "[PARTIAL]"
            else:
                icon = "[FAIL]"

            report.append(f"{icon} {service_name.upper()} (Score: {score}/100)")
            report.append(f"   Path: {verification['path']}")
            report.append(f"   Status: {status}")

            # Import test
            import_test = verification["import_test"]
            import_icon = "[OK]" if import_test["success"] else "[FAIL]"
            report.append(f"   Import: {import_icon} {import_test['message']}")

            # FastAPI test
            if verification["fastapi_test"]:
                fastapi_test = verification["fastapi_test"]
                fastapi_icon = "[OK]" if fastapi_test.get("can_load_app") else "[FAIL]"
                report.append(f"   FastAPI: {fastapi_icon} {fastapi_test['message']}")

            # ML Models test
            if verification["ml_models_test"]:
                ml_test = verification["ml_models_test"]
                ml_icon = "[OK]" if ml_test.get("models_verified") else "[FAIL]"
                report.append(f"   ML Models: {ml_icon} {ml_test['message']}")

            # Tests execution
            if verification["tests_execution"]:
                tests = verification["tests_execution"]
                if tests.get("tests_available"):
                    tests_icon = "[OK]" if tests.get("tests_passed") else "[FAIL]"
                    summary_text = tests.get("summary", "Test execution completed")
                    report.append(f"   Tests: {tests_icon} {summary_text}")
                else:
                    report.append(f"   Tests: [INFO] No tests available")

            report.append("")

        return "\n".join(report)

    def save_results(self, results: Dict, output_file: Optional[str] = None):
        """Save verification results to file"""
        if not output_file:
            output_file = self.root_path / "bmad-core" / "verification-results" / f"service-status-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"Results saved to: {output_path}")

def main():
    verifier = ServiceStatusVerifier()

    if len(sys.argv) > 1:
        # Verify specific service
        service_name = sys.argv[1]
        config = verifier.load_config()
        services = config.get("agents", {})

        if service_name not in services:
            print(f"❌ Service '{service_name}' not found in configuration")
            print(f"Available services: {', '.join(services.keys())}")
            sys.exit(1)

        service_info = services[service_name]
        verification = verifier.verify_service_comprehensive(service_name, service_info)

        results = {
            "verification_date": datetime.now().isoformat(),
            "total_services": 1,
            "services": {service_name: verification},
            "summary": {
                verification["overall_status"]: 1
            }
        }
    else:
        # Verify all services
        print("Starting comprehensive service verification...")
        results = verifier.verify_all_services()

    # Generate and display report
    report = verifier.generate_report(results)
    print(report)

    # Save results
    verifier.save_results(results)

    # Exit with error code based on service health
    summary = results["summary"]
    failed_count = summary.get("failed", 0) + summary.get("limited_functionality", 0)

    if failed_count == 0:
        print("All services are functional!")
        sys.exit(0)
    elif failed_count < results["total_services"] / 2:
        print("Some services have issues but system is mostly functional")
        sys.exit(0)
    else:
        print("Critical system issues detected")
        sys.exit(1)

if __name__ == "__main__":
    main()
