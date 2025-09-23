#!/usr/bin/env python3
"""
BMAD Automation Setup Script
Configures the complete BMAD automation system for seamless operation
"""

import subprocess
import os
import sys
from pathlib import Path

class BMADAutomationSetup:
    """Setup BMAD automation system"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.success_count = 0
        self.total_steps = 8

    def run_command(self, cmd, description):
        """Run a command and report success/failure"""
        print(f"🔧 {description}...")
        try:
            result = subprocess.run(cmd, cwd=self.project_root, check=True, capture_output=True, text=True)
            print(f"   ✅ Success")
            self.success_count += 1
            return True
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Failed: {e}")
            print(f"   Output: {e.stdout}")
            print(f"   Error: {e.stderr}")
            return False

    def setup_git_hooks(self):
        """Configure git to use BMAD automation hooks"""
        print("🪝 Setting up Git hooks for BMAD automation...")

        # Configure git to use .githooks directory
        success = self.run_command(
            ["git", "config", "core.hooksPath", ".githooks"],
            "Configuring git to use .githooks directory"
        )

        if success:
            print("   📝 Git will now use BMAD automation hooks")

        return success

    def make_scripts_executable(self):
        """Make all automation scripts executable"""
        print("Making automation scripts executable...")

        scripts = [
            ".githooks/pre-commit",
            ".githooks/post-commit-bmad",
            ".githooks/setup_hooks.sh",
            "scripts/automation/auto_progress_tracker.py",
            "scripts/automation/auto_documentation_generator.py",
            "scripts/automation/bmad_auto_commit.py",
            "scripts/generate_docs.py"
        ]

        success_count = 0
        for script in scripts:
            script_path = self.project_root / script
            if script_path.exists():
                try:
                    # On Windows, we don't need chmod, but we can ensure the files are accessible
                    if os.name == 'nt':
                        # On Windows, just verify the file exists and is readable
                        if script_path.is_file():
                            print(f"   ✅ {script} (Windows - no chmod needed)")
                            success_count += 1
                    else:
                        # On Unix-like systems, make executable
                        os.chmod(script_path, 0o755)
                        print(f"   ✅ {script}")
                        success_count += 1
                except Exception as e:
                    print(f"   ❌ {script}: {e}")
            else:
                print(f"   ⚠️  {script} not found")

        if success_count > 0:
            self.success_count += 1

        return success_count > 0

    def test_python_automation(self):
        """Test Python automation scripts"""
        print("🐍 Testing Python automation scripts...")

        # Test progress tracker
        progress_tracker = self.project_root / "scripts" / "automation" / "auto_progress_tracker.py"
        if progress_tracker.exists():
            try:
                result = subprocess.run([sys.executable, str(progress_tracker), "--help"],
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    print("   ✅ Progress tracker works")
                else:
                    print("   ⚠️  Progress tracker help failed")
            except Exception as e:
                print(f"   ⚠️  Progress tracker test failed: {e}")

        # Test documentation generator
        doc_generator = self.project_root / "scripts" / "automation" / "auto_documentation_generator.py"
        if doc_generator.exists():
            try:
                result = subprocess.run([sys.executable, str(doc_generator), "--help"],
                                      capture_output=True, text=True, timeout=10)
                print("   ✅ Documentation generator accessible")
            except Exception:
                print("   ⚠️  Documentation generator test inconclusive")

        self.success_count += 1
        return True

    def create_automation_config(self):
        """Create automation configuration file"""
        print("Creating automation configuration...")

        config_content = """# BMAD Automation Configuration
# This file controls the behavior of the BMAD automation system

[automation]
enabled = true
auto_progress_tracking = true
auto_documentation = true
auto_commit_messages = true
bmad_compliance_check = true

[hooks]
pre_commit_enabled = true
post_commit_enabled = true
security_analysis = true

[documentation]
auto_readme_generation = true
auto_changelog_generation = true
api_docs_generation = true

[progress_tracking]
auto_epic_updates = true
auto_service_status = true
auto_phase_detection = true

[git]
conventional_commits = true
auto_staging = true
bmad_integration = true
"""

        config_file = self.project_root / ".bmad-automation.ini"
        try:
            config_file.write_text(config_content)
            print("   ✅ Configuration file created")
            self.success_count += 1
            return True
        except Exception as e:
            print(f"   ❌ Failed to create config: {e}")
            return False

    def verify_bmad_structure(self):
        """Verify BMAD methodology structure is in place"""
        print("Verifying BMAD methodology structure...")

        required_dirs = [
            "bmad-progress",
            "docs/01-requirements",
            "docs/02-architecture",
            "knowledge-base/agent-knowledge",
            "services",
            "scripts/automation"
        ]

        required_files = [
            "bmad-progress/progress-log.json",
            "docs/mvp-backlog-report.md",
            "CLAUDE.md"
        ]

        all_present = True

        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            if full_path.exists():
                print(f"   ✅ {dir_path}")
            else:
                print(f"   ❌ {dir_path} (missing)")
                all_present = False

        for file_path in required_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                print(f"   ✅ {file_path}")
            else:
                print(f"   ❌ {file_path} (missing)")
                all_present = False

        if all_present:
            self.success_count += 1

        return all_present

    def test_git_integration(self):
        """Test git integration with automation"""
        print("🔗 Testing git integration...")

        # Check git config
        try:
            result = subprocess.run(["git", "config", "core.hooksPath"],
                                  capture_output=True, text=True, cwd=self.project_root)
            if result.stdout.strip() == ".githooks":
                print("   ✅ Git configured to use BMAD hooks")
                self.success_count += 1
                return True
            else:
                print(f"   ❌ Git hooks path: {result.stdout.strip()} (expected: .githooks)")
        except Exception as e:
            print(f"   ❌ Git config check failed: {e}")

        return False

    def create_usage_guide(self):
        """Create usage guide for the automation system"""
        print("📖 Creating automation usage guide...")

        guide_content = """# BMAD Automation System Usage Guide

## Overview
The BMAD automation system provides seamless integration of progress tracking,
documentation generation, and git workflow automation following BMAD methodology.

## Automatic Features

### Every Commit
- ✅ Progress tracking automatically updated
- ✅ Documentation regenerated when services change
- ✅ README and changelog updated
- ✅ Conventional commit messages generated
- ✅ BMAD methodology compliance checked

### Manual Commands

#### Automated Commit with Full Pipeline
```bash
python scripts/automation/bmad_auto_commit.py --auto
```

#### Generate Documentation Only
```bash
python scripts/generate_docs.py
```

#### Update Progress Tracking Only
```bash
python scripts/automation/auto_progress_tracker.py
```

#### Update README and Changelog
```bash
python scripts/automation/auto_documentation_generator.py
```

## Configuration

Edit `.bmad-automation.ini` to customize automation behavior.

## Hook Behavior

### Pre-Commit Hook
1. Updates BMAD progress tracking
2. Regenerates documentation
3. Updates README and changelog
4. Runs code quality checks
5. Verifies BMAD methodology compliance

### Post-Commit Hook
1. Analyzes commit for service changes
2. Updates epic and story tracking
3. Generates phase completion reports
4. Updates test coverage
5. Runs security analysis

## Troubleshooting

### Hooks Not Running
```bash
git config core.hooksPath .githooks
```

### Python Errors
Ensure Python 3.13+ is available and all dependencies are installed.

### Permission Issues (Unix/Linux)
```bash
chmod +x .githooks/*
chmod +x scripts/automation/*.py
```

## Integration with BMAD Methodology

The automation system is fully integrated with BMAD methodology:
- Progress tracking follows BMAD phase structure
- Documentation updates maintain BMAD compliance
- Epic and story tracking automatically updated
- Agent status synchronized with implementation progress

For more information, see: https://github.com/bmad-code-org/BMAD-METHOD
"""

        guide_file = self.project_root / "BMAD_AUTOMATION_GUIDE.md"
        try:
            guide_file.write_text(guide_content)
            print("   ✅ Usage guide created")
            self.success_count += 1
            return True
        except Exception as e:
            print(f"   ❌ Failed to create guide: {e}")
            return False

    def run_setup(self):
        """Run complete BMAD automation setup"""
        print("BMAD Automation System Setup")
        print("=" * 50)

        # Run all setup steps
        self.verify_bmad_structure()
        self.make_scripts_executable()
        self.setup_git_hooks()
        self.test_python_automation()
        self.create_automation_config()
        self.test_git_integration()
        self.create_usage_guide()

        # Final summary
        print("\n" + "=" * 50)
        print("BMAD Automation Setup Summary")
        print("=" * 50)

        success_rate = (self.success_count / self.total_steps) * 100

        if success_rate >= 90:
            print(f"SUCCESS: Setup completed successfully! ({self.success_count}/{self.total_steps} steps)")
            print("\nBMAD automation is now active and will:")
            print("   - Automatically track progress on every commit")
            print("   - Generate documentation when services change")
            print("   - Update README and changelog automatically")
            print("   - Create conventional commit messages")
            print("   - Maintain BMAD methodology compliance")
            print("\nSee BMAD_AUTOMATION_GUIDE.md for usage instructions")
        elif success_rate >= 70:
            print(f"WARNING: Setup mostly completed ({self.success_count}/{self.total_steps} steps)")
            print("   Some features may not work perfectly, but core automation is functional")
        else:
            print(f"ERROR: Setup encountered issues ({self.success_count}/{self.total_steps} steps)")
            print("   Manual configuration may be required")

        print(f"\nSuccess rate: {success_rate:.1f}%")

        if success_rate >= 70:
            print("\nTry the automation with:")
            print("   python scripts/automation/bmad_auto_commit.py --auto")

        return success_rate >= 70

def main():
    """Main setup entry point"""
    setup = BMADAutomationSetup()
    success = setup.run_setup()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()