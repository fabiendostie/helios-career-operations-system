#!/usr/bin/env python3
"""
Pre-commit hook for automatic documentation generation.
Runs before each commit to ensure documentation is up-to-date.
"""

import os
import sys
import subprocess
import time
from pathlib import Path


def has_python_changes(modified_files):
    """Check if any Python files were modified."""
    for file_path in modified_files:
        if file_path.endswith('.py') and 'services/' in file_path:
            return True
    return False


def get_modified_files():
    """Get list of modified files in the staging area."""
    try:
        result = subprocess.run(
            ['git', 'diff', '--cached', '--name-only'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip().split('\n') if result.stdout.strip() else []
    except subprocess.CalledProcessError:
        return []


def is_docs_current():
    """Check if documentation is current compared to source files."""
    project_root = Path(__file__).parent.parent
    docs_index = project_root / "docs" / "api" / "index.html"

    if not docs_index.exists():
        return False

    docs_mtime = docs_index.stat().st_mtime

    # Check if any Python file in services is newer than docs
    services_dir = project_root / "services"
    if not services_dir.exists():
        return True

    for py_file in services_dir.rglob("*.py"):
        if py_file.stat().st_mtime > docs_mtime:
            return False

    return True


def generate_documentation():
    """Generate documentation using the main script."""
    project_root = Path(__file__).parent.parent
    generate_script = project_root / "scripts" / "generate_docs.py"

    if not generate_script.exists():
        print("⚠️  Documentation generation script not found")
        return False

    try:
        print("📚 Generating documentation...")
        start_time = time.time()

        result = subprocess.run(
            [sys.executable, str(generate_script)],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=60
        )

        elapsed = time.time() - start_time

        if result.returncode == 0:
            print(f"✅ Documentation generated successfully in {elapsed:.1f}s")
            return True
        else:
            print(f"❌ Documentation generation failed:")
            print(result.stderr)
            return False

    except subprocess.TimeoutExpired:
        print("❌ Documentation generation timed out")
        return False
    except Exception as e:
        print(f"❌ Error generating documentation: {e}")
        return False


def stage_documentation_changes():
    """Stage any documentation changes."""
    project_root = Path(__file__).parent.parent
    docs_dir = project_root / "docs" / "api"

    if not docs_dir.exists():
        return False

    try:
        # Stage all documentation files
        subprocess.run(
            ['git', 'add', str(docs_dir)],
            cwd=project_root,
            check=True
        )

        # Check if anything was actually staged
        result = subprocess.run(
            ['git', 'diff', '--cached', '--name-only', '--', str(docs_dir)],
            capture_output=True,
            text=True,
            check=True
        )

        staged_files = result.stdout.strip().split('\n') if result.stdout.strip() else []

        if staged_files:
            print(f"📄 Staged {len(staged_files)} documentation files")
            return True
        else:
            print("ℹ️  No documentation changes to stage")
            return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to stage documentation: {e}")
        return False


def main():
    """Main pre-commit hook execution."""
    print("🔍 HELIOS Documentation Pre-commit Hook")
    print("=" * 45)

    # Get modified files
    modified_files = get_modified_files()

    if not modified_files:
        print("ℹ️  No files modified, skipping documentation check")
        return 0

    # Check if Python files were modified
    if not has_python_changes(modified_files):
        print("ℹ️  No Python service files modified, skipping documentation generation")
        return 0

    print(f"📝 Python files modified in services/:")
    for file_path in modified_files:
        if file_path.endswith('.py') and 'services/' in file_path:
            print(f"   • {file_path}")

    # Check if documentation is current
    if is_docs_current():
        print("✅ Documentation is already up-to-date")
        return 0

    print("\n🔄 Documentation needs updating...")

    # Generate documentation
    if not generate_documentation():
        print("\n❌ Pre-commit hook failed: Could not generate documentation")
        print("💡 You can bypass this check with: git commit --no-verify")
        return 1

    # Stage documentation changes
    if not stage_documentation_changes():
        print("\n❌ Pre-commit hook failed: Could not stage documentation")
        return 1

    print("\n✅ Pre-commit hook completed successfully")
    print("📚 Documentation has been updated and staged")
    return 0


if __name__ == "__main__":
    sys.exit(main())
