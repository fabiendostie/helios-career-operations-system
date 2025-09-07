#!/usr/bin/env python3
"""
Simple Project Validation Script - ASCII only
"""

import os
import sys
from pathlib import Path
from datetime import datetime


def validate_service(service_name, root_dir):
    """Validate a single service"""
    print(f"Validating {service_name}...")
    
    service_path = root_dir / "services" / service_name
    
    # Check basic structure
    checks = {
        "service_exists": service_path.exists(),
        "src_directory": (service_path / "src").exists(),
        "requirements": (service_path / "requirements.txt").exists(),
        "dockerfile": (service_path / "Dockerfile").exists(),
        "tests": (service_path / "tests").exists()
    }
    
    # Count files
    py_files = len(list(service_path.rglob("*.py"))) if service_path.exists() else 0
    test_files = len(list((service_path / "tests").rglob("test_*.py"))) if (service_path / "tests").exists() else 0
    
    # Calculate score
    score = sum(checks.values()) / len(checks) * 100
    
    print(f"  Score: {score:.0f}% ({py_files} Python files, {test_files} tests)")
    
    if score >= 80:
        print("  Status: PASS")
    elif score >= 50:
        print("  Status: PARTIAL")
    else:
        print("  Status: FAIL")
    
    return score, checks, py_files, test_files


def validate_documentation(root_dir):
    """Validate documentation"""
    print("Validating documentation...")
    
    docs_dir = root_dir / "docs"
    
    # Key documentation files
    key_docs = [
        "PRD.md",
        "architecture.md", 
        "02-architecture/Architecture-Document.md",
        "07-operations/rollback-procedures.md",
        "04-implementation/integration-points-analysis.md",
        "07-operations/database-migration-risk-assessment.md"
    ]
    
    existing = 0
    for doc in key_docs:
        if (docs_dir / doc).exists():
            existing += 1
            print(f"  Found: {doc}")
    
    score = (existing / len(key_docs)) * 100
    print(f"  Score: {score:.0f}% ({existing}/{len(key_docs)} key docs)")
    
    return score


def validate_bmad(root_dir):
    """Validate BMAD compliance"""
    print("Validating BMAD compliance...")
    
    bmad_dir = root_dir / "bmad-core"
    
    checks = {
        "bmad_core_exists": bmad_dir.exists(),
        "core_config": (bmad_dir / "core-config.yaml").exists(),
        "agents_dir": (bmad_dir / "agents").exists()
    }
    
    # Check stories
    stories_dir = root_dir / "docs" / "stories"
    story_count = len(list(stories_dir.glob("*.md"))) if stories_dir.exists() else 0
    
    # Check QA gates
    qa_dir = root_dir / "docs" / "qa" / "gates"
    qa_count = len(list(qa_dir.glob("*.yml"))) if qa_dir.exists() else 0
    
    base_score = sum(checks.values()) / len(checks) * 70
    story_score = min(story_count / 3, 1) * 15  # 3+ stories for full points
    qa_score = min(qa_count / 3, 1) * 15      # 3+ QA gates for full points
    
    score = base_score + story_score + qa_score
    
    print(f"  Score: {score:.0f}% ({story_count} stories, {qa_count} QA gates)")
    
    return score


def main():
    """Main validation"""
    root_dir = Path.cwd()
    
    print("=" * 50)
    print("HELIOS PROJECT VALIDATION")
    print("=" * 50)
    print()
    
    # Validate services
    services = ["profile-ingestor", "orchestrator", "strategist", "analyst"]
    service_scores = []
    
    print("SERVICE VALIDATION:")
    for service in services:
        score, checks, py_files, test_files = validate_service(service, root_dir)
        service_scores.append(score)
        print()
    
    # Validate documentation
    print("DOCUMENTATION VALIDATION:")
    doc_score = validate_documentation(root_dir)
    print()
    
    # Validate BMAD
    print("BMAD VALIDATION:")
    bmad_score = validate_bmad(root_dir)
    print()
    
    # Overall score
    avg_service = sum(service_scores) / len(service_scores) if service_scores else 0
    overall = (avg_service * 0.5 + doc_score * 0.3 + bmad_score * 0.2)
    
    print("=" * 50)
    print("SUMMARY:")
    print(f"Services Average: {avg_service:.0f}%")
    print(f"Documentation: {doc_score:.0f}%")
    print(f"BMAD Compliance: {bmad_score:.0f}%")
    print(f"Overall Score: {overall:.0f}%")
    
    if overall >= 80:
        print("Status: READY FOR NEXT STORY")
    elif overall >= 60:
        print("Status: NEEDS MINOR FIXES")
    else:
        print("Status: NEEDS MAJOR WORK")
    
    print("=" * 50)
    
    # Save results
    with open("validation_results.txt", "w") as f:
        f.write(f"Validation Results - {datetime.now()}\n")
        f.write(f"Overall Score: {overall:.0f}%\n")
        f.write(f"Services: {avg_service:.0f}%\n")
        f.write(f"Documentation: {doc_score:.0f}%\n")
        f.write(f"BMAD: {bmad_score:.0f}%\n")
    
    return overall


if __name__ == "__main__":
    score = main()
    sys.exit(0 if score >= 75 else 1)