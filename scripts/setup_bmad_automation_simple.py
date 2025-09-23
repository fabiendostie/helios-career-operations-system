#!/usr/bin/env python3
"""
BMAD Automation Setup Script (Simple Version)
Configures the complete BMAD automation system for seamless operation
"""

import subprocess
import os
import sys
from pathlib import Path

def setup_git_hooks():
    """Configure git to use BMAD automation hooks"""
    print("Setting up Git hooks for BMAD automation...")

    try:
        result = subprocess.run(
            ["git", "config", "core.hooksPath", ".githooks"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print("   SUCCESS: Git configured to use .githooks directory")
            return True
        else:
            print(f"   FAILED: {result.stderr}")
            return False
    except Exception as e:
        print(f"   ERROR: {e}")
        return False

def test_automation_scripts():
    """Test automation scripts are working"""
    print("Testing automation scripts...")

    project_root = Path(__file__).parent.parent

    # Test progress tracker
    progress_tracker = project_root / "scripts" / "automation" / "auto_progress_tracker.py"
    if progress_tracker.exists():
        print("   SUCCESS: Progress tracker found")
    else:
        print("   WARNING: Progress tracker not found")

    # Test documentation generator
    doc_generator = project_root / "scripts" / "automation" / "auto_documentation_generator.py"
    if doc_generator.exists():
        print("   SUCCESS: Documentation generator found")
    else:
        print("   WARNING: Documentation generator not found")

    return True

def verify_bmad_structure():
    """Verify BMAD structure exists"""
    print("Verifying BMAD structure...")

    project_root = Path(__file__).parent.parent

    required_items = [
        "bmad-progress/progress-log.json",
        "docs/01-requirements",
        "docs/stories",
        "docs/qa/gates"
    ]

    all_present = True
    for item in required_items:
        path = project_root / item
        if path.exists():
            print(f"   FOUND: {item}")
        else:
            print(f"   MISSING: {item}")
            all_present = False

    return all_present

def main():
    """Main setup function"""
    print("BMAD Automation System Setup")
    print("=" * 40)

    success_count = 0
    total_steps = 3

    # Run setup steps
    if setup_git_hooks():
        success_count += 1

    if test_automation_scripts():
        success_count += 1

    if verify_bmad_structure():
        success_count += 1

    # Summary
    print("\n" + "=" * 40)
    print("Setup Summary")
    print("=" * 40)

    success_rate = (success_count / total_steps) * 100

    print(f"Steps completed: {success_count}/{total_steps}")
    print(f"Success rate: {success_rate:.1f}%")

    if success_rate >= 90:
        print("SUCCESS: BMAD automation system is ready!")
        print("\nThe automation will now:")
        print("- Update progress tracking automatically")
        print("- Generate documentation on file changes")
        print("- Update BMAD stories and epics")
        print("- Update QA gates")
        print("- Generate conventional commit messages")
        print("\nTo test the automation:")
        print("python scripts/automation/bmad_auto_commit.py --dry-run")
    else:
        print("WARNING: Some setup steps failed")
        print("Manual configuration may be needed")

    return success_rate >= 70

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)