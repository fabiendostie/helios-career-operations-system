#!/usr/bin/env python3
"""
BMAD Dependency Verification Script
Checks all dependencies for an agent and provides installation commands
"""

import sys
import subprocess
import yaml
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

class DependencyVerifier:
    """Verifies and reports on agent dependencies"""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.project_root = Path(__file__).parent.parent.parent
        self.agent_config = self.load_agent_config()
        self.results = {
            'agent_id': agent_id,
            'verification_date': datetime.now().strftime('%Y-%m-%d'),
            'dependency_status': {},
            'missing_packages': [],
            'missing_models': [],
            'installation_commands': [],
            'all_dependencies_satisfied': False
        }
    
    def load_agent_config(self) -> Dict:
        """Load agent configuration"""
        # Try different naming conventions
        possible_names = [
            self.agent_id.lower(),
            self.agent_id.lower().replace('_', '-'),
            'profile-ingestor' if self.agent_id.upper() == 'PROFILE_INGESTOR' else self.agent_id.lower()
        ]
        
        for name in possible_names:
            agent_config_path = self.project_root / "bmad-core" / "agents" / f"{name}.yaml"
            if agent_config_path.exists():
                with open(agent_config_path, 'r') as f:
                    return yaml.safe_load(f)
        
        raise FileNotFoundError(f"Agent config not found for {self.agent_id}. Tried: {possible_names}")
    
    def run_command(self, command: str) -> Tuple[bool, str, str]:
        """Run shell command and return success, stdout, stderr"""
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True,
                timeout=30
            )
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)
    
    def check_python_packages(self):
        """Check if all required Python packages are installed"""
        if 'dependencies' not in self.agent_config or 'packages' not in self.agent_config['dependencies']:
            return
        
        for package_spec in self.agent_config['dependencies']['packages']:
            package_name = package_spec.split('>=')[0].split('==')[0]
            
            # Test import
            success, stdout, stderr = self.run_command(f'python -c "import {package_name}"')
            
            self.results['dependency_status'][package_name] = {
                'type': 'python_package',
                'spec': package_spec,
                'installed': success,
                'error': stderr if not success else None
            }
            
            if not success:
                self.results['missing_packages'].append(package_spec)
    
    def check_spacy_models(self):
        """Check if required spaCy models are available"""
        if 'dependencies' not in self.agent_config or 'models' not in self.agent_config['dependencies']:
            return
            
        for model in self.agent_config['dependencies']['models']:
            success, stdout, stderr = self.run_command(f'python -c "import spacy; spacy.load(\'{model}\')"')
            
            self.results['dependency_status'][model] = {
                'type': 'spacy_model',
                'installed': success,
                'error': stderr if not success else None
            }
            
            if not success:
                self.results['missing_models'].append(model)
    
    def generate_installation_commands(self):
        """Generate commands to install missing dependencies"""
        commands = []
        
        # Python packages
        if self.results['missing_packages']:
            pip_packages = ' '.join(f'"{pkg}"' for pkg in self.results['missing_packages'])
            commands.append(f"pip install {pip_packages}")
        
        # spaCy models
        for model in self.results['missing_models']:
            commands.append(f"python -m spacy download {model}")
        
        self.results['installation_commands'] = commands
    
    def verify_all_dependencies(self) -> Dict:
        """Run complete dependency verification"""
        print(f"Checking dependencies for: {self.agent_id}")
        
        self.check_python_packages()
        self.check_spacy_models()
        self.generate_installation_commands()
        
        # Check if all dependencies are satisfied
        self.results['all_dependencies_satisfied'] = (
            len(self.results['missing_packages']) == 0 and 
            len(self.results['missing_models']) == 0
        )
        
        self.print_dependency_report()
        return self.results
    
    def print_dependency_report(self):
        """Print comprehensive dependency report"""
        print(f"\n{'='*60}")
        print(f"DEPENDENCY VERIFICATION: {self.agent_id}")
        print(f"{'='*60}")
        
        if self.results['all_dependencies_satisfied']:
            print("SUCCESS: ALL DEPENDENCIES SATISFIED")
        else:
            print("FAILED: MISSING DEPENDENCIES DETECTED")
        
        # Missing packages
        if self.results['missing_packages']:
            print(f"\nMISSING PYTHON PACKAGES ({len(self.results['missing_packages'])}):")
            for pkg in self.results['missing_packages']:
                print(f"   - {pkg}")
        
        # Missing models  
        if self.results['missing_models']:
            print(f"\nMISSING SPACY MODELS ({len(self.results['missing_models'])}):")
            for model in self.results['missing_models']:
                print(f"   - {model}")
        
        # Installation commands
        if self.results['installation_commands']:
            print(f"\nINSTALLATION COMMANDS:")
            for i, cmd in enumerate(self.results['installation_commands'], 1):
                print(f"   {i}. {cmd}")
        
        # Detailed status
        if self.results['dependency_status']:
            print(f"\nDETAILED STATUS:")
            for dep, info in self.results['dependency_status'].items():
                status = "PASS" if info['installed'] else "FAIL"
                dep_type = info['type'].replace('_', ' ').title()
                print(f"   {status}: {dep} ({dep_type})")
                if info.get('error'):
                    print(f"      Error: {info['error'][:100]}...")
        
        print(f"{'='*60}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python verify-dependencies.py <agent_id>")
        sys.exit(1)
    
    agent_id = sys.argv[1]
    
    try:
        verifier = DependencyVerifier(agent_id)
        results = verifier.verify_all_dependencies()
        
        # Save results
        results_dir = Path(__file__).parent.parent / "verification-results"
        results_dir.mkdir(exist_ok=True)
        
        results_file = results_dir / f"{agent_id}-dependencies-{datetime.now().strftime('%Y-%m-%d')}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📄 Results saved to: {results_file}")
        
        # Exit with error code if dependencies missing
        sys.exit(0 if results['all_dependencies_satisfied'] else 1)
        
    except Exception as e:
        print(f"ERROR: Dependency verification failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()