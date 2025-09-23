#!/usr/bin/env python3
"""
BMAD Automated Commit System
Automatically generates conventional commits with BMAD progress tracking integration
"""

import subprocess
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

class BMADAutoCommit:
    """Automated commit system integrated with BMAD methodology"""

    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.progress_file = self.project_root / "bmad-progress" / "progress-log.json"

    def get_git_status(self) -> Dict[str, List[str]]:
        """Get current git status"""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )

            changes = {
                "modified": [],
                "added": [],
                "deleted": [],
                "renamed": [],
                "untracked": []
            }

            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue

                status = line[:2]
                filepath = line[3:].strip()

                if status.startswith('M'):
                    changes["modified"].append(filepath)
                elif status.startswith('A'):
                    changes["added"].append(filepath)
                elif status.startswith('D'):
                    changes["deleted"].append(filepath)
                elif status.startswith('R'):
                    changes["renamed"].append(filepath)
                elif status.startswith('??'):
                    changes["untracked"].append(filepath)

            return changes

        except subprocess.CalledProcessError as e:
            print(f"Error getting git status: {e}")
            return {}

    def analyze_changes(self, changes: Dict[str, List[str]]) -> Dict[str, Any]:
        """Analyze changes to determine commit type and scope"""
        analysis = {
            "type": "chore",
            "scope": None,
            "breaking": False,
            "services_affected": set(),
            "epics_affected": set(),
            "bmad_files_affected": set(),
            "description": "update project files"
        }

        all_files = []
        for file_list in changes.values():
            all_files.extend(file_list)

        # Analyze affected services
        for filepath in all_files:
            if filepath.startswith('services/'):
                parts = filepath.split('/')
                if len(parts) > 1:
                    service_name = parts[1]
                    analysis["services_affected"].add(service_name)

            # Check for epic/story changes
            if any(keyword in filepath.lower() for keyword in ['epic', 'story', 'backlog']):
                analysis["epics_affected"].add("documentation")

            # Check for BMAD methodology files
            if any(keyword in filepath.lower() for keyword in ['bmad', 'progress', 'agent']):
                analysis["bmad_files_affected"].add("methodology")

        # Determine commit type based on changes
        if analysis["services_affected"]:
            # Check if it's a new service implementation
            new_services = []
            enhanced_services = []

            for service in analysis["services_affected"]:
                service_files = [f for f in all_files if f.startswith(f'services/{service}/')]

                # Check for new core files
                new_core_files = [f for f in service_files if f.endswith('.py') and 'core' in f and f in changes.get('added', [])]
                new_api_files = [f for f in service_files if f.endswith('.py') and 'api' in f and f in changes.get('added', [])]

                if new_core_files or new_api_files:
                    new_services.append(service)
                else:
                    enhanced_services.append(service)

            if new_services:
                analysis["type"] = "feat"
                analysis["description"] = f"implement {', '.join(new_services)} service{'s' if len(new_services) > 1 else ''}"
                if len(new_services) == 1:
                    analysis["scope"] = new_services[0]
                else:
                    analysis["scope"] = f"{','.join(new_services)}"
            elif enhanced_services:
                analysis["type"] = "feat"
                analysis["description"] = f"enhance {', '.join(enhanced_services)} service{'s' if len(enhanced_services) > 1 else ''}"
                if len(enhanced_services) == 1:
                    analysis["scope"] = enhanced_services[0]

        # Check for dependency updates
        if any('requirements.txt' in f for f in all_files):
            if analysis["type"] == "chore":
                analysis["type"] = "deps"
                analysis["description"] = "update dependencies to latest compatible versions"

        # Check for documentation updates
        if analysis["epics_affected"] or any('docs/' in f for f in all_files):
            if analysis["type"] == "chore":
                analysis["type"] = "docs"
                analysis["description"] = "update BMAD progress tracking and documentation"

        # Check for test updates
        if any('test' in f.lower() for f in all_files):
            if analysis["type"] == "chore":
                analysis["type"] = "test"
                analysis["description"] = "update test coverage and validation"

        return analysis

    def load_progress_data(self) -> Dict[str, Any]:
        """Load current BMAD progress data"""
        try:
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def determine_phase_completion(self, analysis: Dict[str, Any]) -> bool:
        """Check if this commit completes a phase"""
        progress_data = self.load_progress_data()

        # Check if all services in current phase are completed
        current_phase = progress_data.get("current_phase", "")

        if current_phase == "Phase 2":
            # Check if ARCHITECT and EDITOR services are both operational
            service_status = progress_data.get("service_status", {})
            architect_status = service_status.get("architect", {}).get("status", "")
            editor_status = service_status.get("editor", {}).get("status", "")

            return architect_status == "operational" and editor_status == "operational"

        return False

    def generate_commit_message(self, analysis: Dict[str, Any]) -> str:
        """Generate conventional commit message"""
        # Determine if this is a phase completion
        phase_completion = self.determine_phase_completion(analysis)

        # Build commit type and scope
        commit_type = analysis["type"]
        scope = analysis["scope"]
        breaking = "!" if analysis["breaking"] else ""

        if scope:
            header = f"{commit_type}({scope}){breaking}: {analysis['description']}"
        else:
            header = f"{commit_type}{breaking}: {analysis['description']}"

        # Build commit body
        body_parts = []

        # Add technical details
        if analysis["services_affected"]:
            services_list = ", ".join(sorted(analysis["services_affected"]))
            body_parts.append(f"Services updated: {services_list}")

        # Add BMAD methodology notes
        if analysis["bmad_files_affected"]:
            body_parts.append("BMAD methodology tracking updated automatically")

        # Add phase completion note
        if phase_completion:
            body_parts.append("Phase 2 implementation completed!")
            body_parts.append("All core services now operational with 2025 standards")

        # Build footer
        footer_parts = [
            "Generated with [Claude Code](https://claude.ai/code)",
            "",
            "Co-Authored-By: Claude <noreply@anthropic.com>"
        ]

        # Combine all parts
        message_parts = [header]

        if body_parts:
            message_parts.append("")
            message_parts.extend(body_parts)

        message_parts.append("")
        message_parts.extend(footer_parts)

        return "\n".join(message_parts)

    def create_automated_commit(self, message: Optional[str] = None) -> bool:
        """Create an automated commit with generated message"""
        try:
            # Get current changes
            changes = self.get_git_status()

            if not any(changes.values()):
                print("No changes to commit")
                return False

            # Add all changes
            subprocess.run(
                ["git", "add", "."],
                cwd=self.project_root,
                check=True
            )

            # Generate commit message if not provided
            if not message:
                analysis = self.analyze_changes(changes)
                message = self.generate_commit_message(analysis)

            # Create commit
            subprocess.run(
                ["git", "commit", "-m", message],
                cwd=self.project_root,
                check=True
            )

            print(f"✅ Automated commit created successfully")
            print(f"📝 Commit message:\n{message}")

            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Error creating commit: {e}")
            return False

    def run_pre_commit_automation(self) -> bool:
        """Run the full pre-commit automation pipeline"""
        print("🤖 Running BMAD automated commit pipeline...")

        # Update progress tracking
        progress_tracker = self.project_root / "scripts" / "automation" / "auto_progress_tracker.py"
        if progress_tracker.exists():
            try:
                subprocess.run(
                    [sys.executable, str(progress_tracker), "--auto"],
                    cwd=self.project_root,
                    check=True
                )
                print("✅ Progress tracking updated")
            except subprocess.CalledProcessError:
                print("⚠️ Progress tracking update failed, continuing...")

        # Generate documentation
        doc_generator = self.project_root / "scripts" / "automation" / "auto_documentation_generator.py"
        if doc_generator.exists():
            try:
                subprocess.run(
                    [sys.executable, str(doc_generator)],
                    cwd=self.project_root,
                    check=True
                )
                print("✅ Documentation updated")
            except subprocess.CalledProcessError:
                print("⚠️ Documentation update failed, continuing...")

        return True

def main():
    """Main entry point for automated commit system"""
    import argparse

    parser = argparse.ArgumentParser(description="BMAD Automated Commit System")
    parser.add_argument("--message", "-m", help="Custom commit message")
    parser.add_argument("--auto", action="store_true", help="Run full automation pipeline")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be committed")

    args = parser.parse_args()

    auto_commit = BMADAutoCommit()

    if args.dry_run:
        changes = auto_commit.get_git_status()
        analysis = auto_commit.analyze_changes(changes)
        message = auto_commit.generate_commit_message(analysis)

        print("Dry run - would create commit with message:")
        print("=" * 60)
        print(message)
        print("=" * 60)
        return

    if args.auto:
        auto_commit.run_pre_commit_automation()

    success = auto_commit.create_automated_commit(args.message)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()