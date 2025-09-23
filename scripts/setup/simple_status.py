#!/usr/bin/env python3
"""
Simple Status Script for Helios Career Operations System
ASCII-only version for Windows compatibility
"""

import os
import sys
import yaml
from pathlib import Path
from datetime import datetime

def load_config(project_root):
    """Load BMAD core configuration"""
    config_path = project_root / "bmad-core" / "core-config.yaml"
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"ERROR: BMAD configuration not found: {config_path}")
        return None
    except yaml.YAMLError as e:
        print(f"ERROR: Invalid YAML in configuration: {e}")
        return None

def main():
    project_root = Path.cwd()
    config = load_config(project_root)

    print("\n" + "="*60)
    print("HELIOS CAREER OPERATIONS SYSTEM - STATUS")
    print("="*60)

    if config:
        project_info = config.get('project', {})
        print(f"Project: {project_info.get('name', 'Unknown')}")
        print(f"Version: {project_info.get('version', 'Unknown')}")
        print(f"Status: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Agent Status
        print(f"\nAGENT STATUS:")
        agents = config.get('agents', {})
        for agent_name, agent_config in agents.items():
            status = agent_config.get('status', 'unknown')
            name = agent_config.get('name', agent_name)
            print(f"  {name}: {status.upper()}")

        # Story Status
        stories = config.get('stories', {})
        completed = stories.get('completed', [])
        pending = stories.get('pending', [])
        print(f"\nSTORY STATUS:")
        print(f"  Completed: {len(completed)}")
        print(f"  Pending: {len(pending)}")

        print(f"\nNEXT STEPS:")
        print(f"  1. Run: npm run install:bmad")
        print(f"  2. Run: python scripts/setup/bmad_init.py")
        print(f"  3. Check: knowledge-base/agent-knowledge/")
    else:
        print("ERROR: Could not load configuration")

    print("="*60)

if __name__ == "__main__":
    main()
