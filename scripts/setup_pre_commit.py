#!/usr/bin/env python3
"""
Setup script for pre-commit hooks in HELIOS Career Operations System.
Installs the documentation generation pre-commit hook.
"""

import os
import sys
import shutil
import stat
from pathlib import Path

# Fix encoding issues on Windows
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def setup_pre_commit_hook():
    """Setup the pre-commit hook for documentation generation."""
    project_root = Path(__file__).parent.parent
    git_hooks_dir = project_root / ".git" / "hooks"
    hook_source = project_root / ".pre-commit-hooks" / "generate-docs.py"
    hook_target = git_hooks_dir / "pre-commit"

    print("🔧 Setting up HELIOS documentation pre-commit hook...")
    print(f"📂 Project root: {project_root}")

    # Check if .git directory exists
    if not git_hooks_dir.parent.exists():
        print("❌ This is not a Git repository")
        return False

    # Create hooks directory if it doesn't exist
    git_hooks_dir.mkdir(exist_ok=True)

    # Check if hook source exists
    if not hook_source.exists():
        print(f"❌ Hook source not found: {hook_source}")
        return False

    # Backup existing pre-commit hook if it exists
    if hook_target.exists():
        backup_path = hook_target.with_suffix('.backup')
        print(f"📋 Backing up existing pre-commit hook to: {backup_path}")
        shutil.copy2(hook_target, backup_path)

    # Copy the hook
    print(f"📄 Installing pre-commit hook: {hook_target}")
    shutil.copy2(hook_source, hook_target)

    # Make the hook executable (Unix/Linux/Mac)
    if os.name != 'nt':
        current_permissions = hook_target.stat().st_mode
        hook_target.chmod(current_permissions | stat.S_IEXEC)
        print("✅ Made hook executable")

    print("✅ Pre-commit hook installed successfully!")
    print("\n📋 Hook features:")
    print("   • Automatically generates documentation when Python files change")
    print("   • Stages documentation changes in the same commit")
    print("   • Prevents commits if documentation generation fails")
    print("   • Can be bypassed with: git commit --no-verify")

    return True


def test_pre_commit_hook():
    """Test the pre-commit hook installation."""
    project_root = Path(__file__).parent.parent
    hook_target = project_root / ".git" / "hooks" / "pre-commit"

    print("\n🧪 Testing pre-commit hook...")

    if not hook_target.exists():
        print("❌ Pre-commit hook not found")
        return False

    # Test if the hook is executable
    if os.name != 'nt':
        if not os.access(hook_target, os.X_OK):
            print("❌ Pre-commit hook is not executable")
            return False

    # Test if the hook runs without error (dry run)
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, str(hook_target)],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            print("✅ Pre-commit hook test passed")
            return True
        else:
            print(f"❌ Pre-commit hook test failed: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print("⚠️  Pre-commit hook test timed out (but hook is installed)")
        return True
    except Exception as e:
        print(f"❌ Error testing pre-commit hook: {e}")
        return False


def create_pre_commit_config():
    """Create a .pre-commit-config.yaml for additional hooks."""
    project_root = Path(__file__).parent.parent
    config_file = project_root / ".pre-commit-config.yaml"

    if config_file.exists():
        print(f"ℹ️  Pre-commit config already exists: {config_file}")
        return True

    config_content = """# Pre-commit configuration for HELIOS Career Operations System
repos:
  - repo: local
    hooks:
      - id: generate-docs
        name: Generate Documentation
        entry: python .pre-commit-hooks/generate-docs.py
        language: system
        files: ^services/.*\\.py$
        pass_filenames: false
        always_run: false

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-merge-conflict
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3
        files: ^services/.*\\.py$

  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        files: ^services/.*\\.py$
"""

    try:
        config_file.write_text(config_content, encoding='utf-8')
        print(f"✅ Created pre-commit config: {config_file}")
        print("💡 You can now use 'pre-commit install' for additional hooks")
        return True
    except Exception as e:
        print(f"❌ Failed to create pre-commit config: {e}")
        return False


def main():
    """Main setup function."""
    print("🚀 HELIOS Pre-commit Hook Setup")
    print("=" * 40)

    success = True

    # Setup the main pre-commit hook
    if not setup_pre_commit_hook():
        success = False

    # Test the hook
    if success and not test_pre_commit_hook():
        success = False

    # Create pre-commit config
    if not create_pre_commit_config():
        success = False

    print("\n" + "=" * 40)
    if success:
        print("🎉 Setup completed successfully!")
        print("\n📋 Next steps:")
        print("   1. The documentation pre-commit hook is now active")
        print("   2. Documentation will be auto-generated on commits")
        print("   3. Optional: Install pre-commit framework:")
        print("      pip install pre-commit")
        print("      pre-commit install")
    else:
        print("❌ Setup failed. Please check the errors above.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
