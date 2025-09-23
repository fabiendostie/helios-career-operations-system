#!/usr/bin/env python3
"""
Automated Documentation Generation System
Automatically generates and updates documentation, README, and changelogs
"""

import json
import os
import sys
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any
import re

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

class AutoDocumentationGenerator:
    """Automatically generates and updates project documentation"""

    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.progress_file = self.project_root / "bmad-progress" / "progress-log.json"
        self.readme_file = self.project_root / "README.md"
        self.changelog_file = self.project_root / "CHANGELOG.md"

    def load_progress_data(self) -> Dict[str, Any]:
        """Load current progress data"""
        try:
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def get_service_overview(self) -> Dict[str, Any]:
        """Generate service overview from current state"""
        progress = self.load_progress_data()
        services = progress.get("service_status", {})

        overview = {
            "total_services": len(services),
            "operational": 0,
            "in_progress": 0,
            "not_started": 0,
            "services": {}
        }

        for name, data in services.items():
            status = data.get("status", "not_started")
            overview["services"][name] = {
                "status": status,
                "port": data.get("port"),
                "coverage": data.get("test_coverage", "TBD"),
                "notes": data.get("notes", "")
            }

            if status == "operational":
                overview["operational"] += 1
            elif status == "in_progress":
                overview["in_progress"] += 1
            else:
                overview["not_started"] += 1

        return overview

    def generate_readme(self) -> str:
        """Generate comprehensive README.md"""
        progress = self.load_progress_data()
        service_overview = self.get_service_overview()

        readme_content = f"""# Helios Career Operations System

🚀 **AI-powered career intelligence platform built using BMAD methodology**

[![Overall Progress](https://img.shields.io/badge/Progress-{progress.get('overall_progress', 0)}%25-blue)](./bmad-progress/progress-log.json)
[![Phase](https://img.shields.io/badge/Phase-{progress.get('current_phase', 'N/A')}-green)](./docs/mvp-backlog-report.md)
[![Services](https://img.shields.io/badge/Services-{service_overview['operational']}/{service_overview['total_services']}_Operational-brightgreen)](./services/)
[![Methodology](https://img.shields.io/badge/Methodology-BMAD-orange)](https://github.com/bmad-code-org/BMAD-METHOD)

## 📊 Current Status

**Last Updated**: {progress.get('last_updated', 'Unknown')}

### 🏗️ Service Architecture

| Service | Status | Port | Coverage | Notes |
|---------|--------|------|----------|-------|"""

        for name, data in service_overview["services"].items():
            status_emoji = {
                "operational": "✅",
                "in_progress": "🔄",
                "not_started": "📋"
            }.get(data["status"], "❓")

            readme_content += f"""
| {name.title()} | {status_emoji} {data['status'].title()} | {data['port'] or 'TBD'} | {data['coverage']} | {data['notes']} |"""

        readme_content += f"""

### 📈 Progress Overview

- **Total Services**: {service_overview['total_services']}
- **Operational**: {service_overview['operational']} ✅
- **In Progress**: {service_overview['in_progress']} 🔄
- **Not Started**: {service_overview['not_started']} 📋
- **Overall Progress**: {progress.get('overall_progress', 0)}%

## 🚀 Quick Start

### Prerequisites

- Python 3.13.1+
- Docker & Docker Compose
- Git

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd helios-career-operations-system

# Set up virtual environment
python -m venv venv
# Windows:
venv\\Scripts\\activate
# Unix/Mac:
source venv/bin/activate

# Install dependencies for specific service
cd services/profile-ingestor
pip install -r requirements.txt
```

### Running Services

```bash
# Run individual service (example: profile-ingestor)
cd services/profile-ingestor
python -m src.main

# Or using Docker
docker-compose up profile-ingestor
```

## 🎯 User Journey

1. **Upload Resume** → Profile Ingestor extracts structured data
2. **Career Analysis** → Strategist generates career paths, Analyst provides market insights
3. **Document Generation** → Architect creates ATS-compliant resumes, Editor optimizes text
4. **Optimization** → Continuous improvement based on market feedback

## 📋 Service Details

### Core Services

#### Profile Ingestor (Port 8002) ✅
- **Status**: Fully Operational
- **Function**: Multi-format resume processing (PDF, DOCX, MD, TXT, YAML, JSON)
- **Features**: Bilingual NLP (EN/FR), skill mapping, conflict resolution
- **Test Coverage**: 99% (208/208 tests passing)

#### Orchestrator (Port 8001) 🔄
- **Status**: In Progress
- **Function**: Session management and service coordination
- **Features**: Command routing, state persistence, error recovery

#### Strategist (Port 8003) 🔄
- **Status**: In Progress
- **Function**: Career path generation and fit scoring
- **Features**: Skill adjacency modeling, ML-driven recommendations

#### Analyst (Port 8004) ✅
- **Status**: Enhanced (Phase 2)
- **Function**: Market analysis and resume optimization
- **Features**: Real-time market data, ATS compliance scoring, skill gap analysis

#### Architect (Port 8005) ✅
- **Status**: Completed (Phase 2)
- **Function**: ATS-compliant document generation
- **Features**: 2025 ATS standards, 91% parsing success, multi-format output

#### Editor (Port 8006) ✅
- **Status**: Completed (Phase 2)
- **Function**: Advanced text optimization
- **Features**: VMO transformation, weak word elimination, AI skills integration

## 🔧 Development

### BMAD Methodology

This project follows [BMAD (Behavioral Model Analysis and Design)](https://github.com/bmad-code-org/BMAD-METHOD) methodology:

- **Documentation**: Structured in `docs/` following BMAD standards
- **Progress Tracking**: Automated via `bmad-progress/` system
- **Agent Knowledge**: Centralized in `knowledge-base/agent-knowledge/`
- **Quality Gates**: 95%+ test coverage, comprehensive error handling

### Development Commands

```bash
# Run tests
pytest

# Check code quality
ruff check .
black .

# Update progress tracking
python bmad-progress/update_coverage.py

# Review lessons learned
python bmad-progress/lessons_learned.py
```

### Automated Systems

- **🤖 Progress Tracking**: Auto-updates on file changes
- **📝 Documentation**: Auto-generates README and changelogs
- **🔄 Git Commits**: Conventional commits with automation
- **🧪 Testing**: Pre-commit hooks ensure quality

## 📚 Documentation

- **[Architecture Document](./docs/02-architecture/Architecture-Document.md)**: System design and patterns
- **[MVP Backlog](./docs/mvp-backlog-report.md)**: Current status and next steps
- **[Epic Breakdown](./docs/01-requirements/)**: Detailed requirements and stories
- **[Progress Tracking](./bmad-progress/progress-log.json)**: Real-time project status

## 🔐 Security

- Container hardening implemented
- Input validation across all services
- Secure API endpoints with proper error handling
- Regular dependency updates

## 📊 Performance Targets

- **Response Time**: <2 seconds for standard operations
- **Document Generation**: <30 seconds
- **ATS Compliance**: >85% for generated resumes
- **Test Coverage**: >95% across all services

## 🤝 Contributing

1. Follow BMAD methodology guidelines
2. Maintain 95%+ test coverage
3. Use conventional commit format
4. Update documentation automatically via hooks
5. Review `CLAUDE.md` for specific guidance

## 📄 License

[License information here]

## 🔗 Links

- [BMAD Methodology](https://github.com/bmad-code-org/BMAD-METHOD)
- [Project Documentation](./docs/)
- [Progress Tracking](./bmad-progress/)

---

*This README is automatically generated and updated. Last update: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}*
"""

        return readme_content

    def generate_changelog_entry(self, commit_data: Dict[str, Any]) -> str:
        """Generate changelog entry from commit data"""
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d')

        entry = f"""
## [{timestamp}] - Phase {commit_data.get('phase', 'Unknown')}

### Added
"""

        for item in commit_data.get('added', []):
            entry += f"- {item}\n"

        entry += "\n### Enhanced\n"
        for item in commit_data.get('enhanced', []):
            entry += f"- {item}\n"

        entry += "\n### Fixed\n"
        for item in commit_data.get('fixed', []):
            entry += f"- {item}\n"

        return entry

    def update_changelog(self) -> None:
        """Update CHANGELOG.md with recent changes"""
        progress = self.load_progress_data()

        # Extract recent changes from progress log
        commit_data = {
            'phase': progress.get('current_phase', 'Unknown'),
            'added': [],
            'enhanced': [],
            'fixed': []
        }

        # Analyze completed phase 2 tasks
        phase_2 = progress.get('phases', {}).get('phase_2', {})
        if phase_2.get('status') == 'completed':
            for task_name, task_data in phase_2.get('tasks', {}).items():
                if task_data.get('status') == 'completed':
                    for detail in task_data.get('details', []):
                        commit_data['added'].append(detail)

        new_entry = self.generate_changelog_entry(commit_data)

        # Read existing changelog or create new
        if self.changelog_file.exists():
            with open(self.changelog_file, 'r') as f:
                existing_content = f.read()
        else:
            existing_content = "# Changelog\n\nAll notable changes to this project will be documented in this file.\n"

        # Insert new entry at the top
        lines = existing_content.split('\n')
        title_index = 0
        for i, line in enumerate(lines):
            if line.startswith('# Changelog'):
                title_index = i + 2
                break

        lines.insert(title_index, new_entry)
        updated_content = '\n'.join(lines)

        with open(self.changelog_file, 'w') as f:
            f.write(updated_content)

    def run_generation(self) -> None:
        """Main documentation generation pipeline"""
        print("📝 Running automated documentation generation...")

        try:
            # Generate and update README
            readme_content = self.generate_readme()
            with open(self.readme_file, 'w') as f:
                f.write(readme_content)
            print("✅ README.md generated")

            # Update changelog
            self.update_changelog()
            print("✅ CHANGELOG.md updated")

            # Stage documentation files for commit
            subprocess.run(
                ["git", "add", str(self.readme_file), str(self.changelog_file)],
                cwd=self.project_root,
                check=True
            )
            print("✅ Documentation files staged for commit")

        except Exception as e:
            print(f"❌ Error generating documentation: {e}")

def main():
    """Entry point for automated documentation generation"""
    generator = AutoDocumentationGenerator()
    generator.run_generation()

if __name__ == "__main__":
    main()