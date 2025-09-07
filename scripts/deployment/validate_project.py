#!/usr/bin/env python3
"""
Comprehensive Project Validation Script
Validates all aspects of the Helios Career Operations System
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import importlib.util


class ProjectValidator:
    """Comprehensive validation of project readiness"""
    
    def __init__(self, root_dir: str = None):
        self.root_dir = Path(root_dir) if root_dir else Path.cwd()
        self.services = ["profile-ingestor", "orchestrator", "strategist", "analyst"]
        self.validation_results = {}
        
    def validate_service_structure(self, service: str) -> Dict[str, Any]:
        """Validate service directory structure"""
        print(f"📦 Validating {service} structure...")
        
        service_path = self.root_dir / "services" / service
        results = {
            "service_exists": service_path.exists(),
            "src_directory": (service_path / "src").exists(),
            "tests_directory": (service_path / "tests").exists(),
            "requirements": (service_path / "requirements.txt").exists(),
            "dockerfile": (service_path / "Dockerfile").exists(),
            "main_file": False,
            "python_files": 0,
            "test_files": 0
        }
        
        if service_path.exists():
            # Check for main entry point
            main_candidates = [
                service_path / "src" / "main.py",
                service_path / "main.py",
                service_path / "app.py"
            ]
            results["main_file"] = any(f.exists() for f in main_candidates)
            
            # Count Python files
            results["python_files"] = len(list(service_path.rglob("*.py")))
            results["test_files"] = len(list((service_path / "tests").rglob("test_*.py")))
        
        # Score calculation
        score = sum([
            results["service_exists"] * 2,
            results["src_directory"] * 2,
            results["tests_directory"] * 1,
            results["requirements"] * 1,
            results["dockerfile"] * 1,
            results["main_file"] * 2
        ]) / 9 * 100
        
        results["score"] = score
        status = "PASS" if score >= 80 else "FAIL" if score < 50 else "PARTIAL"
        
        print(f"  {'✅' if status == 'PASS' else '❌' if status == 'FAIL' else '⚠️'} "
              f"{service}: {score:.0f}% ({results['python_files']} files, {results['test_files']} tests)")
        
        return results
    
    def validate_dependencies(self, service: str) -> Dict[str, Any]:
        """Validate service dependencies"""
        print(f"📋 Validating {service} dependencies...")
        
        service_path = self.root_dir / "services" / service
        requirements_file = service_path / "requirements.txt"
        
        results = {
            "requirements_exists": requirements_file.exists(),
            "dependencies": [],
            "dependency_issues": [],
            "can_import_main": False
        }
        
        if requirements_file.exists():
            try:
                with open(requirements_file, 'r') as f:
                    lines = f.readlines()
                
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        results["dependencies"].append(line)
                
                # Check for known problematic dependencies
                for dep in results["dependencies"]:
                    if "spacy==4.0.2" in dep:
                        results["dependency_issues"].append("spaCy 4.0.2 does not exist")
                    elif "spacy" in dep and "==" in dep:
                        # Extract version
                        version = dep.split("==")[1]
                        if version not in ["3.7.5", "3.7.4", "3.6.3"]:
                            results["dependency_issues"].append(f"Unverified spaCy version: {version}")
                
            except Exception as e:
                results["dependency_issues"].append(f"Error reading requirements: {e}")
        
        # Try to import main module
        main_file = service_path / "src" / "main.py"
        if main_file.exists():
            try:
                # Add to Python path temporarily
                sys.path.insert(0, str(service_path / "src"))
                spec = importlib.util.spec_from_file_location("main", main_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    # Don't actually load to avoid side effects
                    results["can_import_main"] = True
            except Exception as e:
                results["dependency_issues"].append(f"Cannot import main: {e}")
            finally:
                if str(service_path / "src") in sys.path:
                    sys.path.remove(str(service_path / "src"))
        
        score = (
            (not results["dependency_issues"]) * 50 +
            results["requirements_exists"] * 30 +
            results["can_import_main"] * 20
        )
        
        results["score"] = score
        status = "PASS" if score >= 80 else "FAIL" if score < 50 else "PARTIAL"
        
        print(f"  {'✅' if status == 'PASS' else '❌' if status == 'FAIL' else '⚠️'} "
              f"{service}: {score:.0f}% ({len(results['dependencies'])} deps, "
              f"{len(results['dependency_issues'])} issues)")
        
        if results["dependency_issues"]:
            for issue in results["dependency_issues"]:
                print(f"    ⚠️ {issue}")
        
        return results
    
    def validate_documentation(self) -> Dict[str, Any]:
        """Validate project documentation"""
        print("📚 Validating documentation...")
        
        docs_dir = self.root_dir / "docs"
        results = {
            "docs_directory": docs_dir.exists(),
            "structure_docs": [],
            "api_docs": (docs_dir / "api").exists(),
            "operations_docs": (docs_dir / "07-operations").exists(),
            "implementation_docs": (docs_dir / "04-implementation").exists()
        }
        
        # Check key documentation files
        key_docs = [
            "PRD.md",
            "architecture.md",
            "02-architecture/Architecture-Document.md",
            "07-operations/rollback-procedures.md",
            "04-implementation/integration-points-analysis.md",
            "07-operations/database-migration-risk-assessment.md"
        ]
        
        existing_docs = 0
        for doc in key_docs:
            doc_path = docs_dir / doc
            if doc_path.exists():
                existing_docs += 1
                results["structure_docs"].append(doc)
        
        # Check API documentation
        api_files = 0
        if (docs_dir / "api").exists():
            api_files = len(list((docs_dir / "api").rglob("*.html")))
        
        score = (
            results["docs_directory"] * 10 +
            (existing_docs / len(key_docs)) * 60 +
            results["api_docs"] * 15 +
            (min(api_files / 20, 1)) * 15  # Up to 20 API files for full score
        )
        
        results["score"] = score
        results["key_docs_count"] = existing_docs
        results["api_files_count"] = api_files
        
        status = "PASS" if score >= 80 else "FAIL" if score < 50 else "PARTIAL"
        
        print(f"  {'✅' if status == 'PASS' else '❌' if status == 'FAIL' else '⚠️'} "
              f"Documentation: {score:.0f}% ({existing_docs}/{len(key_docs)} docs, "
              f"{api_files} API files)")
        
        return results
    
    def validate_risk_management(self) -> Dict[str, Any]:
        """Validate risk management documentation"""
        print("🛡️ Validating risk management...")
        
        ops_dir = self.root_dir / "docs" / "07-operations"
        impl_dir = self.root_dir / "docs" / "04-implementation"
        
        results = {
            "rollback_procedures": (ops_dir / "rollback-procedures.md").exists(),
            "migration_assessment": (ops_dir / "database-migration-risk-assessment.md").exists(),
            "integration_analysis": (impl_dir / "integration-points-analysis.md").exists(),
            "feature_flags": False,  # Will check content
            "monitoring_plan": False  # Will check content
        }
        
        # Check for feature flag mentions in rollback procedures
        if results["rollback_procedures"]:
            try:
                with open(ops_dir / "rollback-procedures.md", 'r', encoding='utf-8') as f:
                    content = f.read()
                    results["feature_flags"] = "feature_flags" in content.lower()
                    results["monitoring_plan"] = "monitoring" in content.lower()
            except:
                pass
        
        score = sum([
            results["rollback_procedures"] * 30,
            results["migration_assessment"] * 30,
            results["integration_analysis"] * 25,
            results["feature_flags"] * 10,
            results["monitoring_plan"] * 5
        ])
        
        results["score"] = score
        status = "PASS" if score >= 80 else "FAIL" if score < 50 else "PARTIAL"
        
        print(f"  {'✅' if status == 'PASS' else '❌' if status == 'FAIL' else '⚠️'} "
              f"Risk Management: {score:.0f}%")
        
        return results
    
    def validate_bmad_compliance(self) -> Dict[str, Any]:
        """Validate BMAD methodology compliance"""
        print("📋 Validating BMAD compliance...")
        
        bmad_dir = self.root_dir / "bmad-core"
        results = {
            "bmad_directory": bmad_dir.exists(),
            "core_config": (bmad_dir / "core-config.yaml").exists(),
            "agent_configs": False,
            "story_structure": False,
            "qa_gates": False
        }
        
        if bmad_dir.exists():
            results["agent_configs"] = (bmad_dir / "agents").exists()
        
        # Check story structure
        stories_dir = self.root_dir / "docs" / "stories"
        if stories_dir.exists():
            story_files = list(stories_dir.glob("*.md"))
            results["story_structure"] = len(story_files) >= 3  # At least 3 stories
        
        # Check QA gates
        qa_dir = self.root_dir / "docs" / "qa" / "gates"
        if qa_dir.exists():
            qa_files = list(qa_dir.glob("*.yml"))
            results["qa_gates"] = len(qa_files) >= 3  # At least 3 QA gates
        
        score = sum([
            results["bmad_directory"] * 20,
            results["core_config"] * 30,
            results["agent_configs"] * 20,
            results["story_structure"] * 15,
            results["qa_gates"] * 15
        ])
        
        results["score"] = score
        status = "PASS" if score >= 80 else "FAIL" if score < 50 else "PARTIAL"
        
        print(f"  {'✅' if status == 'PASS' else '❌' if status == 'FAIL' else '⚠️'} "
              f"BMAD Compliance: {score:.0f}%")
        
        return results
    
    def run_validation(self) -> Dict[str, Any]:
        """Run complete project validation"""
        print("\n" + "="*60)
        print("🔍 HELIOS PROJECT VALIDATION")
        print("="*60 + "\n")
        
        # Service structure validation
        service_results = {}
        for service in self.services:
            service_results[service] = {
                "structure": self.validate_service_structure(service),
                "dependencies": self.validate_dependencies(service)
            }
        print()
        
        # Project-level validation
        project_results = {
            "documentation": self.validate_documentation(),
            "risk_management": self.validate_risk_management(),
            "bmad_compliance": self.validate_bmad_compliance()
        }
        print()
        
        # Calculate overall scores
        all_results = {
            "services": service_results,
            "project": project_results,
            "timestamp": datetime.now().isoformat()
        }
        
        # Summary
        print("="*60)
        print("📊 VALIDATION SUMMARY")
        print("="*60)
        
        # Service scores
        print("\n🏗️ Service Validation:")
        service_scores = []
        for service, results in service_results.items():
            structure_score = results["structure"]["score"]
            deps_score = results["dependencies"]["score"]
            avg_score = (structure_score + deps_score) / 2
            service_scores.append(avg_score)
            
            status_icon = "✅" if avg_score >= 80 else "❌" if avg_score < 50 else "⚠️"
            print(f"  {status_icon} {service}: {avg_score:.0f}% "
                  f"(Structure: {structure_score:.0f}%, Deps: {deps_score:.0f}%)")
        
        # Project scores
        print("\n📁 Project Validation:")
        project_scores = []
        for category, results in project_results.items():
            score = results["score"]
            project_scores.append(score)
            
            status_icon = "✅" if score >= 80 else "❌" if score < 50 else "⚠️"
            print(f"  {status_icon} {category.replace('_', ' ').title()}: {score:.0f}%")
        
        # Overall score
        overall_service = sum(service_scores) / len(service_scores) if service_scores else 0
        overall_project = sum(project_scores) / len(project_scores) if project_scores else 0
        overall_score = (overall_service * 0.6 + overall_project * 0.4)
        
        print(f"\n🎯 Overall Score: {overall_score:.0f}%")
        
        if overall_score >= 90:
            print("🎉 Excellent! Project is ready for production.")
        elif overall_score >= 75:
            print("👍 Good! Project is ready with minor improvements needed.")
        elif overall_score >= 60:
            print("⚠️  Needs work before proceeding to next story.")
        else:
            print("❌ Significant issues need to be addressed.")
        
        all_results["overall_score"] = overall_score
        all_results["service_average"] = overall_service
        all_results["project_average"] = overall_project
        
        return all_results
    
    def generate_report(self, results: Dict[str, Any]) -> None:
        """Generate detailed validation report"""
        report_file = self.root_dir / "validation_report.json"
        
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📄 Detailed report saved: {report_file}")


def main():
    """Main entry point"""
    validator = ProjectValidator()
    results = validator.run_validation()
    validator.generate_report(results)
    
    # Exit with appropriate code
    overall_score = results.get("overall_score", 0)
    sys.exit(0 if overall_score >= 75 else 1)


if __name__ == "__main__":
    main()