#!/usr/bin/env python3
"""
BMAD Status Script for Helios Career Operations System
Displays current project status, agent states, and development progress
"""

import os
import sys
import yaml
import json
from pathlib import Path
from typing import Dict, List
from datetime import datetime

class BMadStatus:
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
            return None
        except yaml.YAMLError as e:
            print(f"❌ Invalid YAML in configuration: {e}")
            return None
            
    def get_service_info(self, service_path: str) -> Dict:
        """Get information about a service"""
        full_path = self.project_root / service_path
        
        info = {
            'exists': full_path.exists(),
            'files': 0,
            'tests': 0,
            'coverage': 'unknown',
            'last_modified': None
        }
        
        if info['exists']:
            # Count files
            for root, dirs, files in os.walk(full_path):
                info['files'] += len([f for f in files if f.endswith(('.py', '.js', '.ts'))])
                
            # Count tests
            tests_path = full_path / "tests"
            if tests_path.exists():
                for root, dirs, files in os.walk(tests_path):
                    info['tests'] += len([f for f in files if f.startswith('test_')])
                    
            # Get last modification time
            try:
                timestamps = []
                for root, dirs, files in os.walk(full_path):
                    for file in files:
                        file_path = Path(root) / file
                        timestamps.append(file_path.stat().st_mtime)
                if timestamps:
                    info['last_modified'] = datetime.fromtimestamp(max(timestamps))
            except:
                pass
                
        return info
        
    def display_header(self):
        """Display header information"""
        print("\n" + "="*80)
        print("HELIOS CAREER OPERATIONS SYSTEM - STATUS REPORT")
        print("="*80)
        
        if self.config:
            project_info = self.config.get('project', {})
            print(f"[*] Project: {project_info.get('name', 'Unknown')}")
            print(f"[*] Version: {project_info.get('version', 'Unknown')}")
            print(f"[*] Methodology: {project_info.get('methodology', 'Unknown')}")
            print(f"[*] Description: {project_info.get('description', 'No description')}")
            
        print(f"[*] Root Directory: {self.project_root}")
        print(f"[*] Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    def display_agents_status(self):
        """Display agent status information"""
        if not self.config or 'agents' not in self.config:
            return
            
        print("\n[AGENT STATUS]")
        print("-" * 80)
        
        agents = self.config['agents']
        completed_count = 0
        in_progress_count = 0
        pending_count = 0
        
        for agent_name, agent_config in agents.items():
            status = agent_config.get('status', 'unknown')
            name = agent_config.get('name', agent_name)
            role = agent_config.get('role', 'No role defined')
            location = agent_config.get('location', 'No location')
            
            # Status icon and counter
            if status == 'completed':
                status_icon = "✅"
                completed_count += 1
            elif status == 'in_progress':
                status_icon = "🔄"
                in_progress_count += 1
            elif status == 'pending':
                status_icon = "⏳"
                pending_count += 1
            else:
                status_icon = "❓"
                
            print(f"{status_icon} {name:<20} {status:<12} {role}")
            
            # Get service information
            if location:
                service_info = self.get_service_info(location)
                if service_info['exists']:
                    print(f"   📁 Location: {location}")
                    print(f"   📄 Files: {service_info['files']}, Tests: {service_info['tests']}")
                    if service_info['last_modified']:
                        print(f"   🕐 Last Modified: {service_info['last_modified'].strftime('%Y-%m-%d %H:%M')}")
                else:
                    print(f"   ❌ Service directory not found: {location}")
            print()
            
        # Summary
        total_agents = len(agents)
        print(f"📊 SUMMARY: {total_agents} total agents")
        print(f"   ✅ Completed: {completed_count}")
        print(f"   🔄 In Progress: {in_progress_count}")
        print(f"   ⏳ Pending: {pending_count}")
        
    def display_stories_status(self):
        """Display story status information"""
        if not self.config or 'stories' not in self.config:
            return
            
        print("\n📚 STORY STATUS")
        print("-" * 80)
        
        stories = self.config['stories']
        completed = stories.get('completed', [])
        pending = stories.get('pending', [])
        
        print("✅ COMPLETED STORIES:")
        for story in completed:
            print(f"   ✅ {story}")
            
        print("\n⏳ PENDING STORIES:")
        for story in pending:
            print(f"   ⏳ {story}")
            
        completion_rate = len(completed) / (len(completed) + len(pending)) * 100 if (completed or pending) else 0
        print(f"\n📈 Completion Rate: {completion_rate:.1f}% ({len(completed)}/{len(completed) + len(pending)})")
        
    def display_infrastructure_status(self):
        """Display infrastructure and tooling status"""
        print("\n🏗️ INFRASTRUCTURE STATUS")
        print("-" * 80)
        
        # Check key directories
        key_dirs = [
            ("bmad-core", "BMAD Core"),
            ("docs", "Documentation"),
            ("knowledge-base", "Knowledge Base"),
            ("services", "Services"),
            ("infrastructure", "Infrastructure"),
            ("scripts", "Scripts")
        ]
        
        for dir_name, display_name in key_dirs:
            dir_path = self.project_root / dir_name
            if dir_path.exists():
                file_count = len(list(dir_path.rglob("*.*")))
                print(f"✅ {display_name:<20} {file_count} files")
            else:
                print(f"❌ {display_name:<20} Missing")
                
        # Check key files
        key_files = [
            ("package.json", "NPM Configuration"),
            ("requirements.txt", "Python Requirements"),
            ("CLAUDE.md", "Claude Code Configuration"),
            (".gitignore", "Git Configuration")
        ]
        
        print("\n📄 Key Files:")
        for file_name, description in key_files:
            file_path = self.project_root / file_name
            if file_path.exists():
                print(f"✅ {description}")
            else:
                print(f"❌ {description} - Missing {file_name}")
                
    def display_next_actions(self):
        """Display recommended next actions"""
        print("\n🎯 RECOMMENDED NEXT ACTIONS")
        print("-" * 80)
        
        if not self.config:
            print("1. ❌ Fix BMAD configuration issues")
            return
            
        # Check for pending agents
        agents = self.config.get('agents', {})
        pending_agents = [name for name, config in agents.items() if config.get('status') == 'pending']
        in_progress_agents = [name for name, config in agents.items() if config.get('status') == 'in_progress']
        
        if in_progress_agents:
            print(f"1. 🔄 Complete in-progress agents: {', '.join(in_progress_agents)}")
        elif pending_agents:
            next_agent = pending_agents[0]
            agent_config = agents[next_agent]
            print(f"1. 🚀 Start next agent: {agent_config.get('name', next_agent)}")
            print(f"   📝 Role: {agent_config.get('role', 'Not specified')}")
            print(f"   📁 Location: {agent_config.get('location', 'Not specified')}")
        else:
            print("1. ✅ All agents completed - Ready for integration testing!")
            
        # Check dependencies
        venv_path = self.project_root / "venv"
        if not venv_path.exists():
            print("2. 📦 Set up development environment: npm run setup:env")
        else:
            print("2. ✅ Development environment ready")
            
        # Check models
        profile_ingestor_path = self.project_root / "services" / "profile-ingestor"
        if profile_ingestor_path.exists():
            print("3. 🧠 Download NLP models: npm run setup:models")
        else:
            print("3. ⏳ NLP models setup pending (Story 1.1 location)")
            
        print("4. 📚 Review agent documentation: knowledge-base/agent-knowledge/")
        print("5. 🧪 Run tests: npm run test:all")
        
    def run(self):
        """Run status report"""
        self.load_config()
        
        self.display_header()
        self.display_agents_status()
        self.display_stories_status()
        self.display_infrastructure_status()
        self.display_next_actions()
        
        print("\n" + "="*80)
        print("📋 Status report complete. Use 'npm run bmad:init' to validate setup.")
        print("="*80)

if __name__ == "__main__":
    status_checker = BMadStatus()
    status_checker.run()