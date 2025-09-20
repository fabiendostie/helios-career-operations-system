#!/usr/bin/env python3
"""
Enhanced Verification Protocols for Helios Career Operations System
Prevents documentation drift and ensures truth over aspiration
"""

import json
import yaml
import subprocess
import sys
import importlib
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

class HeliosVerificationEngine:
    """Comprehensive verification system to prevent documentation drift"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.verification_date = datetime.now().strftime("%Y-%m-%d")
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'services': {},
            'tests': {},
            'documentation': {},
            'overall_status': 'UNKNOWN'
        }
        
    def verify_service_imports(self, service_name: str, service_path: str) -> Dict:
        """Verify that a service can actually be imported and initialized"""
        print(f"🔍 Verifying {service_name} service imports...")
        
        try:
            # Change to service directory
            old_cwd = os.getcwd()
            service_dir = self.project_root / service_path
            os.chdir(service_dir)
            
            # Try to import the main module
            result = subprocess.run(
                [sys.executable, '-c', 'import src.main; print("✅ Import successful")'],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            os.chdir(old_cwd)
            
            if result.returncode == 0:
                return {
                    'status': 'OPERATIONAL',
                    'import_test': 'PASS',
                    'error': None,
                    'output': result.stdout.strip()
                }
            else:
                return {
                    'status': 'FAILED',
                    'import_test': 'FAIL',
                    'error': result.stderr.strip(),
                    'output': result.stdout.strip()
                }
                
        except Exception as e:
            return {
                'status': 'ERROR',
                'import_test': 'ERROR',
                'error': str(e),
                'output': None
            }
    
    def verify_test_suites(self, service_name: str, service_path: str) -> Dict:
        """Verify test suites can run and get actual pass rates"""
        print(f"🧪 Verifying {service_name} test suite...")
        
        try:
            old_cwd = os.getcwd()
            service_dir = self.project_root / service_path
            os.chdir(service_dir)
            
            # Run pytest with JSON output
            result = subprocess.run([
                sys.executable, '-m', 'pytest', 
                '--tb=no', '-q', '--json-report', 
                '--json-report-file=/tmp/pytest_report.json'
            ], capture_output=True, text=True, timeout=300)
            
            os.chdir(old_cwd)
            
            # Parse results
            try:
                with open('/tmp/pytest_report.json', 'r') as f:
                    report = json.load(f)
                    
                return {
                    'status': 'COMPLETED',
                    'total_tests': report.get('summary', {}).get('total', 0),
                    'passed': report.get('summary', {}).get('passed', 0),
                    'failed': report.get('summary', {}).get('failed', 0),
                    'errors': report.get('summary', {}).get('error', 0),
                    'pass_rate': round((report.get('summary', {}).get('passed', 0) / 
                                     max(1, report.get('summary', {}).get('total', 1))) * 100, 1),
                    'execution_time': report.get('duration', 0)
                }
            except FileNotFoundError:
                # Fallback parsing from stdout
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'failed' in line and 'passed' in line:
                        # Parse pytest summary line
                        parts = line.split()
                        passed = failed = 0
                        for i, part in enumerate(parts):
                            if part == 'passed':
                                passed = int(parts[i-1])
                            elif part == 'failed':
                                failed = int(parts[i-1])
                        
                        total = passed + failed
                        return {
                            'status': 'COMPLETED',
                            'total_tests': total,
                            'passed': passed,
                            'failed': failed,
                            'pass_rate': round((passed / max(1, total)) * 100, 1),
                            'raw_output': result.stdout
                        }
                
                return {
                    'status': 'PARSING_FAILED',
                    'raw_output': result.stdout,
                    'raw_error': result.stderr
                }
                
        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e)
            }
    
    def verify_dependencies(self, service_name: str, service_path: str) -> Dict:
        """Verify all dependencies are installed and accessible"""
        print(f"📦 Verifying {service_name} dependencies...")
        
        try:
            old_cwd = os.getcwd()
            service_dir = self.project_root / service_path
            os.chdir(service_dir)
            
            # Check requirements.txt exists
            req_file = service_dir / 'requirements.txt'
            if not req_file.exists():
                return {'status': 'NO_REQUIREMENTS_FILE'}
            
            # Try to install in dry-run mode to check availability
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'check'
            ], capture_output=True, text=True)
            
            os.chdir(old_cwd)
            
            if result.returncode == 0:
                return {
                    'status': 'SATISFIED',
                    'pip_check': 'PASS',
                    'output': result.stdout
                }
            else:
                return {
                    'status': 'CONFLICTS',
                    'pip_check': 'FAIL', 
                    'conflicts': result.stdout
                }
                
        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e)
            }
    
    def verify_ml_models(self, service_name: str, service_path: str) -> Dict:
        """Verify ML models can load for ML-enabled services"""
        if service_name not in ['strategist', 'analyst']:
            return {'status': 'N/A', 'reason': 'Not an ML service'}
            
        print(f"🤖 Verifying {service_name} ML models...")
        
        try:
            old_cwd = os.getcwd()
            service_dir = self.project_root / service_path
            os.chdir(service_dir)
            
            if service_name == 'strategist':
                # Test sentence-transformers loading
                test_code = '''
import sentence_transformers
model = sentence_transformers.SentenceTransformer("all-MiniLM-L6-v2")
print("✅ Strategist ML models loaded successfully")
'''
            elif service_name == 'analyst':
                # Test spaCy + sentence-transformers loading
                test_code = '''
import spacy
import sentence_transformers
nlp = spacy.load("en_core_web_sm")
model = sentence_transformers.SentenceTransformer("all-MiniLM-L6-v2")
print("✅ Analyst NLP models loaded successfully")
'''
            
            result = subprocess.run([
                sys.executable, '-c', test_code
            ], capture_output=True, text=True, timeout=120)
            
            os.chdir(old_cwd)
            
            if result.returncode == 0:
                return {
                    'status': 'LOADED',
                    'models_test': 'PASS',
                    'output': result.stdout.strip()
                }
            else:
                return {
                    'status': 'FAILED',
                    'models_test': 'FAIL',
                    'error': result.stderr.strip()
                }
                
        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e)
            }
    
    def verify_core_config_accuracy(self) -> Dict:
        """Verify core-config.yaml reflects actual system status"""
        print("📋 Verifying core-config.yaml accuracy...")
        
        try:
            config_path = self.project_root / 'bmad-core' / 'core-config.yaml'
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            documented_agents = config.get('agents', {})
            verification_results = {}
            
            for agent_name, agent_info in documented_agents.items():
                service_path = agent_info.get('location', '')
                if not service_path:
                    continue
                    
                # Verify actual status vs documented
                actual_verification = self.verify_service_imports(agent_name, service_path)
                documented_status = agent_info.get('status', 'unknown')
                
                matches = (
                    (documented_status == 'operational' and actual_verification['status'] == 'OPERATIONAL') or
                    (documented_status == 'completed' and actual_verification['status'] == 'OPERATIONAL')
                )
                
                verification_results[agent_name] = {
                    'documented_status': documented_status,
                    'actual_status': actual_verification['status'],
                    'accuracy': 'ACCURATE' if matches else 'INACCURATE',
                    'needs_update': not matches
                }
            
            return {
                'status': 'VERIFIED',
                'agents': verification_results,
                'overall_accuracy': all(r['accuracy'] == 'ACCURATE' for r in verification_results.values())
            }
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e)
            }
    
    def run_comprehensive_verification(self) -> Dict:
        """Run complete verification across all services"""
        print("🔍 Starting Comprehensive Helios Verification...")
        print("=" * 60)
        
        services = {
            'profile-ingestor': 'services/profile-ingestor',
            'orchestrator': 'services/orchestrator', 
            'strategist': 'services/strategist',
            'analyst': 'services/analyst'
        }
        
        for service_name, service_path in services.items():
            print(f"\n🔧 Verifying {service_name.upper()}...")
            
            # Service-level verification
            import_result = self.verify_service_imports(service_name, service_path)
            deps_result = self.verify_dependencies(service_name, service_path)
            test_result = self.verify_test_suites(service_name, service_path)
            ml_result = self.verify_ml_models(service_name, service_path)
            
            self.results['services'][service_name] = {
                'imports': import_result,
                'dependencies': deps_result,
                'tests': test_result,
                'ml_models': ml_result,
                'overall_status': self._determine_service_status(
                    import_result, deps_result, test_result, ml_result
                )
            }
        
        # Documentation verification
        config_result = self.verify_core_config_accuracy()
        self.results['documentation']['core_config'] = config_result
        
        # Overall system status
        self.results['overall_status'] = self._determine_overall_status()
        
        return self.results
    
    def _determine_service_status(self, imports, deps, tests, ml_models) -> str:
        """Determine overall service status from individual checks"""
        if imports['status'] != 'OPERATIONAL':
            return 'NON_FUNCTIONAL'
        if deps['status'] not in ['SATISFIED']:
            return 'DEPENDENCY_ISSUES'
        if ml_models['status'] == 'FAILED':
            return 'ML_ISSUES'
        if tests.get('pass_rate', 0) < 80:
            return 'TEST_ISSUES'
        return 'OPERATIONAL'
    
    def _determine_overall_status(self) -> str:
        """Determine overall system status"""
        operational_services = sum(1 for s in self.results['services'].values() 
                                 if s['overall_status'] == 'OPERATIONAL')
        total_services = len(self.results['services'])
        
        if operational_services == total_services:
            return 'FULLY_OPERATIONAL'
        elif operational_services >= total_services * 0.75:
            return 'MOSTLY_OPERATIONAL'
        elif operational_services >= total_services * 0.5:
            return 'PARTIALLY_OPERATIONAL'
        else:
            return 'SYSTEM_ISSUES'
    
    def generate_report(self) -> str:
        """Generate comprehensive verification report"""
        report = [
            "# HELIOS VERIFICATION REPORT",
            f"**Date**: {self.verification_date}",
            f"**Overall Status**: {self.results['overall_status']}",
            "",
            "## SERVICE VERIFICATION RESULTS",
            ""
        ]
        
        for service_name, service_data in self.results['services'].items():
            status_icon = "✅" if service_data['overall_status'] == 'OPERATIONAL' else "❌"
            report.extend([
                f"### {status_icon} {service_name.upper()}",
                f"- **Overall Status**: {service_data['overall_status']}",
                f"- **Import Test**: {service_data['imports']['status']}",
                f"- **Dependencies**: {service_data['dependencies']['status']}",
            ])
            
            if 'tests' in service_data and service_data['tests'].get('status') == 'COMPLETED':
                tests = service_data['tests']
                report.append(f"- **Tests**: {tests['passed']}/{tests['total_tests']} passing ({tests['pass_rate']}%)")
            
            if service_data['ml_models']['status'] != 'N/A':
                report.append(f"- **ML Models**: {service_data['ml_models']['status']}")
            
            report.append("")
        
        # Documentation accuracy
        if 'core_config' in self.results['documentation']:
            config_result = self.results['documentation']['core_config']
            accuracy_icon = "✅" if config_result.get('overall_accuracy') else "⚠️"
            report.extend([
                f"## {accuracy_icon} DOCUMENTATION ACCURACY",
                f"- **Core Config Accuracy**: {'ACCURATE' if config_result.get('overall_accuracy') else 'NEEDS_UPDATE'}",
                ""
            ])
        
        # Summary recommendations
        report.extend([
            "## RECOMMENDATIONS",
            ""
        ])
        
        non_operational = [name for name, data in self.results['services'].items() 
                          if data['overall_status'] != 'OPERATIONAL']
        
        if not non_operational:
            report.append("✅ All services operational - system ready for production")
        else:
            report.append("❌ Services requiring attention:")
            for service in non_operational:
                report.append(f"  - {service}: {self.results['services'][service]['overall_status']}")
        
        return "\n".join(report)
    
    def save_results(self, output_path: Optional[str] = None):
        """Save verification results to JSON and markdown"""
        if not output_path:
            output_path = self.project_root / 'bmad-core' / 'verification-results'
        
        output_dir = Path(output_path)
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save JSON results
        json_file = output_dir / f"verification_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        # Save markdown report
        report = self.generate_report()
        md_file = output_dir / f"verification_report_{timestamp}.md"
        with open(md_file, 'w') as f:
            f.write(report)
        
        print(f"📊 Results saved:")
        print(f"  - JSON: {json_file}")
        print(f"  - Report: {md_file}")

def main():
    """Run comprehensive Helios verification"""
    verifier = HeliosVerificationEngine()
    
    try:
        results = verifier.run_comprehensive_verification()
        
        print("\n" + "=" * 60)
        print("📊 VERIFICATION COMPLETE")
        print("=" * 60)
        print(verifier.generate_report())
        
        # Save results
        verifier.save_results()
        
        # Exit with appropriate code
        if results['overall_status'] in ['FULLY_OPERATIONAL', 'MOSTLY_OPERATIONAL']:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        sys.exit(2)

if __name__ == '__main__':
    main()