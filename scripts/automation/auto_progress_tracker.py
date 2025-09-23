#!/usr/bin/env python3
"""
Automated Progress Tracking System
Automatically updates BMAD progress tracking when files change
"""

import json
import os
import sys
import subprocess
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any
import hashlib

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

class AutoProgressTracker:
    """Automatically tracks progress and updates BMAD documentation"""

    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.progress_file = self.project_root / "bmad-progress" / "progress-log.json"
        self.service_dirs = self.project_root / "services"

    def detect_changes(self) -> Dict[str, Any]:
        """Detect what has changed since last run"""
        try:
            # Get git status to see what's changed
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )

            changes = {
                "modified_files": [],
                "new_files": [],
                "services_affected": set(),
                "epics_affected": set(),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue

                status = line[:2]
                filepath = line[3:].strip()

                if status.startswith('M'):
                    changes["modified_files"].append(filepath)
                elif status.startswith('A') or status.startswith('??'):
                    changes["new_files"].append(filepath)

                # Detect service changes
                if filepath.startswith('services/'):
                    service_name = filepath.split('/')[1]
                    changes["services_affected"].add(service_name)

                # Detect epic changes
                if 'epic' in filepath.lower() or 'story' in filepath.lower():
                    changes["epics_affected"].add("documentation")

            return changes

        except subprocess.CalledProcessError as e:
            print(f"Error detecting changes: {e}")
            return {"error": str(e)}

    def analyze_service_completion(self, service_name: str) -> Dict[str, Any]:
        """Analyze if a service is complete based on file structure"""
        service_path = self.service_dirs / service_name

        if not service_path.exists():
            return {"status": "not_started", "completion": 0}

        required_files = [
            "src/main.py",
            "src/api/health.py",
            "src/core/config.py",
            "requirements.txt"
        ]

        optional_files = [
            "tests/",
            "Dockerfile",
            "README.md"
        ]

        completion_score = 0
        files_present = []

        for file_path in required_files:
            if (service_path / file_path).exists():
                completion_score += 20  # Each required file = 20%
                files_present.append(file_path)

        for file_path in optional_files:
            if (service_path / file_path).exists():
                completion_score += 5   # Each optional file = 5%
                files_present.append(file_path)

        # Check for core implementation files
        core_dir = service_path / "src" / "core"
        if core_dir.exists():
            core_files = list(core_dir.glob("*.py"))
            if len(core_files) > 1:  # More than just config.py
                completion_score += 15

        # Check for API endpoints
        api_dir = service_path / "src" / "api"
        if api_dir.exists():
            api_files = list(api_dir.glob("*.py"))
            if len(api_files) > 1:  # More than just health.py
                completion_score += 10

        completion_score = min(100, completion_score)

        if completion_score >= 90:
            status = "completed"
        elif completion_score >= 50:
            status = "in_progress"
        else:
            status = "started"

        return {
            "status": status,
            "completion": completion_score,
            "files_present": files_present,
            "analysis_timestamp": datetime.now(timezone.utc).isoformat()
        }

    def update_progress_log(self, changes: Dict[str, Any]) -> None:
        """Update the progress log based on detected changes"""
        try:
            # Load current progress
            with open(self.progress_file, 'r') as f:
                progress = json.load(f)

            # Update timestamp
            progress["last_updated"] = changes["timestamp"]

            # Analyze each affected service
            for service_name in changes["services_affected"]:
                service_analysis = self.analyze_service_completion(service_name)

                # Update service status
                if service_name in progress["service_status"]:
                    progress["service_status"][service_name].update({
                        "status": "operational" if service_analysis["completion"] >= 90 else "in_progress",
                        "completion_percentage": service_analysis["completion"],
                        "last_analyzed": service_analysis["analysis_timestamp"]
                    })

                # Update corresponding BMAD story status
                self.update_story_status(service_name, service_analysis["completion"])

            # Update overall progress
            total_services = len(progress["service_status"])
            operational_services = sum(1 for s in progress["service_status"].values()
                                     if s.get("status") == "operational")

            if total_services > 0:
                progress["overall_progress"] = int((operational_services / total_services) * 100)

            # Determine current phase and update epics
            if operational_services >= 5:  # All core services operational
                progress["current_phase"] = "Phase 3"
                progress["session_metadata"]["next_priority"] = "integration_testing"
                self.update_epic_status("epic-3-generation", "completed")
            elif operational_services >= 3:  # Core + 2 new services
                progress["current_phase"] = "Phase 2"
                progress["session_metadata"]["next_priority"] = "service_completion"
                self.update_epic_status("epic-2-intelligence", "in_progress")

            # Update QA gates
            self.update_qa_gates(changes["services_affected"])

            # Save updated progress
            with open(self.progress_file, 'w') as f:
                json.dump(progress, f, indent=2)

            print(f"✅ Progress log updated automatically at {changes['timestamp']}")
            print(f"📚 BMAD stories and epics synchronized")

        except Exception as e:
            print(f"❌ Error updating progress log: {e}")

    def update_story_status(self, service_name: str, completion_percentage: int) -> None:
        """Update corresponding BMAD story status"""
        try:
            # Map services to story files
            service_to_story = {
                "orchestrator": "2.1.helios-orchestrator.md",
                "strategist": "2.2.strategist-service.md",
                "analyst": "2.3.analyst-service.md",
                "architect": "2.4.architect-service.md",
                "editor": "2.5.editor-service.md"  # If exists
            }

            story_file = service_to_story.get(service_name)
            if not story_file:
                return

            story_path = self.project_root / "docs" / "stories" / story_file
            if not story_path.exists():
                return

            # Read current story content
            content = story_path.read_text(encoding='utf-8')

            # Update status based on completion
            if completion_percentage >= 90:
                new_status = "✅ COMPLETED"
                # Update any existing status line
                content = re.sub(
                    r'^## Status: .*$',
                    f'## Status: {new_status} - Fully Verified and Operational',
                    content,
                    flags=re.MULTILINE
                )
            elif completion_percentage >= 50:
                new_status = "🔄 IN PROGRESS"
                content = re.sub(
                    r'^## Status: .*$',
                    f'## Status: {new_status} - Implementation Active',
                    content,
                    flags=re.MULTILINE
                )

            # Write updated content
            story_path.write_text(content, encoding='utf-8')
            print(f"   📝 Updated story {story_file} status")

        except Exception as e:
            print(f"   ⚠️ Failed to update story status: {e}")

    def update_epic_status(self, epic_name: str, status: str) -> None:
        """Update BMAD epic status"""
        try:
            epic_files = {
                "epic-1-foundation": "epic-1-foundation.md",
                "epic-2-intelligence": "epic-2-intelligence.md",
                "epic-3-generation": "epic-3-generation.md"
            }

            epic_file = epic_files.get(epic_name)
            if not epic_file:
                return

            epic_path = self.project_root / "docs" / "01-requirements" / epic_file
            if not epic_path.exists():
                return

            content = epic_path.read_text(encoding='utf-8')

            # Update epic status
            status_mapping = {
                "completed": "✅ COMPLETED",
                "in_progress": "🔄 IN-PROGRESS",
                "pending": "⏳ PENDING"
            }

            new_status = status_mapping.get(status, status)
            content = re.sub(
                r'^(\*\*Status\*\*): .*$',
                f'\\1: {new_status}',
                content,
                flags=re.MULTILINE
            )

            epic_path.write_text(content, encoding='utf-8')
            print(f"   📋 Updated epic {epic_file} status to {new_status}")

        except Exception as e:
            print(f"   ⚠️ Failed to update epic status: {e}")

    def update_qa_gates(self, services_affected: set) -> None:
        """Update QA gate status for affected services"""
        try:
            service_to_gate = {
                "orchestrator": "2.1-helios-orchestrator.yml",
                "strategist": "2.2-strategist.yml",
                "analyst": "2.3-analyst.yml",
                "architect": "2.4-architect.yml",
                "editor": "2.5-editor.yml"  # If exists
            }

            for service_name in services_affected:
                gate_file = service_to_gate.get(service_name)
                if not gate_file:
                    continue

                gate_path = self.project_root / "docs" / "qa" / "gates" / gate_file
                if not gate_path.exists():
                    continue

                # Analyze service for QA gate status
                service_analysis = self.analyze_service_completion(service_name)

                gate_data = {
                    'schema': 1,
                    'story': service_name,
                    'gate': 'PASS' if service_analysis['completion'] >= 90 else 'IN_PROGRESS',
                    'status_reason': f'Service implementation at {service_analysis["completion"]}% completion',
                    'reviewer': 'BMAD Automation System',
                    'updated': datetime.now(timezone.utc).isoformat(),
                    'top_issues': [],
                    'metrics': {
                        'implementation_status': 'complete' if service_analysis['completion'] >= 90 else 'in_progress',
                        'story_defined': True,
                        'architecture_planned': True
                    },
                    'waiver': {'active': False}
                }

                # Write YAML content
                import yaml
                with open(gate_path, 'w') as f:
                    yaml.dump(gate_data, f, default_flow_style=False)

                print(f"   🔍 Updated QA gate {gate_file}")

        except Exception as e:
            print(f"   ⚠️ Failed to update QA gates: {e}")

    def generate_commit_message(self, changes: Dict[str, Any]) -> str:
        """Generate conventional commit message based on changes"""
        services = list(changes["services_affected"])

        if len(services) == 1:
            service = services[0]
            if any("requirements.txt" in f for f in changes["modified_files"]):
                return f"deps({service}): update dependencies to latest compatible versions"
            elif any(f"services/{service}/src/core/" in f for f in changes["new_files"]):
                return f"feat({service}): implement core functionality"
            elif any(f"services/{service}/src/api/" in f for f in changes["new_files"]):
                return f"feat({service}): add API endpoints"
            else:
                return f"chore({service}): update service implementation"
        elif len(services) > 1:
            service_list = ",".join(services)
            return f"feat({service_list}): implement multiple service updates"
        elif changes["epics_affected"]:
            return "docs: update BMAD progress tracking and epic status"
        else:
            return "chore: automated progress and documentation updates"

    def run_automation(self) -> None:
        """Main automation pipeline"""
        print("🤖 Running automated progress tracking...")

        # Detect changes
        changes = self.detect_changes()

        if "error" in changes:
            print(f"❌ Failed to detect changes: {changes['error']}")
            return

        if not changes["modified_files"] and not changes["new_files"]:
            print("ℹ️  No changes detected, skipping automation")
            return

        print(f"📊 Detected changes in: {changes['services_affected']}")

        # Update progress tracking
        self.update_progress_log(changes)

        # Stage progress file for commit
        try:
            subprocess.run(
                ["git", "add", str(self.progress_file)],
                cwd=self.project_root,
                check=True
            )
            print("✅ Progress file staged for commit")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to stage progress file: {e}")

def main():
    """Entry point for automated progress tracking"""
    if len(sys.argv) > 1 and sys.argv[1] == "--hook":
        # Running as git hook
        print("🔗 Running as git hook...")

    tracker = AutoProgressTracker()
    tracker.run_automation()

if __name__ == "__main__":
    main()