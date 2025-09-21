#!/usr/bin/env python3
"""
BMAD Initialization Script for Helios Career Operations System
Initializes the development environment and validates BMAD structure
"""

import os
import sys
import yaml
import json
from pathlib import Path
from typing import Dict, List

class BMadInitializer:
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.bmad_core_path = self.project_root / "bmad-core"
        self.config_path = self.bmad_core_path / "core-config.yaml"
        self.config = None

    def load_config(self) -> Dict:
        """Load BMAD core configuration"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            return self.config
        except FileNotFoundError:
            print(f"❌ BMAD configuration not found: {self.config_path}")
            sys.exit(1)
        except yaml.YAMLError as e:
            print(f"❌ Invalid YAML in configuration: {e}")
            sys.exit(1)

    def validate_structure(self) -> bool:
        """Validate BMAD project structure"""
        print("🔍 Validating BMAD project structure...")

        required_dirs = [
            "bmad-core",
            "bmad-core/agents",
            "bmad-core/templates",
            "bmad-core/workflows",
            "docs",
            "docs/01-requirements",
            "docs/02-architecture",
            "knowledge-base",
            "knowledge-base/agent-knowledge",
            "services"
        ]

        missing_dirs = []
        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            if not full_path.exists():
                missing_dirs.append(dir_path)

        if missing_dirs:
            print("❌ Missing required directories:")
            for dir_path in missing_dirs:
                print(f"   - {dir_path}")
            return False

        print("✅ Project structure validation passed")
        return True

    def validate_agents(self) -> bool:
        """Validate agent configurations"""
        print("🤖 Validating agent configurations...")

        if not self.config or 'agents' not in self.config:
            print("❌ No agents defined in configuration")
            return False

        agents = self.config['agents']
        for agent_name, agent_config in agents.items():
            # Check required fields
            required_fields = ['name', 'role', 'location', 'status']
            for field in required_fields:
                if field not in agent_config:
                    print(f"❌ Agent {agent_name} missing required field: {field}")
                    return False

            # Check if service location exists for completed agents
            if agent_config['status'] == 'completed':
                service_path = self.project_root / agent_config['location']
                if not service_path.exists():
                    print(f"❌ Service location not found for {agent_name}: {service_path}")
                    return False

        print("✅ Agent configuration validation passed")
        return True

    def check_dependencies(self) -> bool:
        """Check for required dependencies"""
        print("📦 Checking dependencies...")

        # Check Python version
        python_version = sys.version_info
        if python_version.major < 3 or python_version.minor < 11:
            print(f"❌ Python 3.11+ required, found {python_version.major}.{python_version.minor}")
            return False

        # Check for Node.js (for package.json scripts)
        if os.system("node --version") != 0:
            print("⚠️  Node.js not found - some scripts may not work")

        # Check for virtual environment
        venv_path = self.project_root / "venv"
        if not venv_path.exists():
            print("⚠️  Virtual environment not found - run 'npm run setup:env' to create")

        print("✅ Dependency check completed")
        return True

    def initialize_ai_debug(self) -> bool:
        """Initialize AI debug directory"""
        print("🤖 Setting up AI debug environment...")

        ai_dir = self.project_root / ".ai"
        ai_dir.mkdir(exist_ok=True)

        debug_log = ai_dir / "debug-log.md"
        if not debug_log.exists():
            with open(debug_log, 'w', encoding='utf-8') as f:
                f.write("# Helios AI Debug Log\n\n")
                f.write("## Session Logs\n\n")
                f.write("This file tracks AI agent interactions and debugging information.\n\n")

        print("✅ AI debug environment initialized")
        return True

    def display_status(self):
        """Display current project status"""
        if not self.config:
            return

        print("\n" + "="*60)
        print("🚀 HELIOS CAREER OPERATIONS SYSTEM")
        print("="*60)
        print(f"Project: {self.config['project']['name']}")
        print(f"Version: {self.config['project']['version']}")
        print(f"Methodology: {self.config['project']['methodology']}")

        print("\n📊 Agent Status:")
        agents = self.config['agents']
        for agent_name, agent_config in agents.items():
            status_icon = "✅" if agent_config['status'] == 'completed' else "🔄" if agent_config['status'] == 'in_progress' else "⏳"
            print(f"   {status_icon} {agent_config['name']} ({agent_config['status']})")

        print(f"\n📁 Stories:")
        if 'stories' in self.config:
            completed = self.config['stories'].get('completed', [])
            pending = self.config['stories'].get('pending', [])
            print(f"   ✅ Completed: {len(completed)}")
            print(f"   ⏳ Pending: {len(pending)}")

        print("\n🎯 Next Steps:")
        print("   1. Run 'npm run install:bmad' to install dependencies")
        print("   2. Run 'npm run setup:models' to download NLP models")
        print("   3. Check agent documentation in knowledge-base/agent-knowledge/")
        print("   4. Begin development with Story 2.1 (HELIOS Orchestrator)")
        print("="*60)

    def run(self) -> bool:
        """Run complete BMAD initialization"""
        print("🚀 Initializing BMAD environment for Helios Career Operations System...")

        success = True
        success &= self.load_config() is not None
        success &= self.validate_structure()
        success &= self.validate_agents()
        success &= self.check_dependencies()
        success &= self.initialize_ai_debug()

        if success:
            print("\n✅ BMAD initialization completed successfully!")
            self.display_status()
        else:
            print("\n❌ BMAD initialization failed. Please fix the issues above.")

        return success

if __name__ == "__main__":
    initializer = BMadInitializer()
    success = initializer.run()
    sys.exit(0 if success else 1)
