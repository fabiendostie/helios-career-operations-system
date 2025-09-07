#!/usr/bin/env python3
"""
Comprehensive Documentation Generator for Helios Career Operations System
Generates pydoc documentation for all Python modules across all services
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Optional
import argparse
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DocGenerator:
    """
    Comprehensive documentation generator using pydoc and Sphinx
    
    This class handles the generation of HTML documentation for all Python
    modules in the Helios Career Operations System, including:
    - Service modules (orchestrator, profile-ingestor, strategist, analyst)
    - API documentation
    - Core business logic
    - Integration layers
    - Test documentation
    """
    
    def __init__(self, root_dir: str = None):
        """
        Initialize the documentation generator
        
        Args:
            root_dir: Root directory of the project (defaults to current working directory)
        """
        self.root_dir = Path(root_dir) if root_dir else Path.cwd()
        self.docs_output = self.root_dir / "docs" / "api"
        self.services = ["profile-ingestor", "orchestrator", "strategist", "analyst"]
        self.generated_files: List[str] = []
        
    def setup_environment(self) -> None:
        """
        Set up the documentation generation environment
        
        Creates necessary directories and ensures all dependencies are available
        """
        logger.info("Setting up documentation environment...")
        
        # Create output directory
        self.docs_output.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for each service
        for service in self.services:
            service_docs = self.docs_output / service
            service_docs.mkdir(exist_ok=True)
            
        logger.info(f"Documentation will be generated in: {self.docs_output}")
        
    def generate_service_docs(self, service: str) -> List[str]:
        """
        Generate documentation for a specific service
        
        Args:
            service: Name of the service to document
            
        Returns:
            List of generated documentation file paths
        """
        logger.info(f"Generating documentation for {service}...")
        
        service_path = self.root_dir / "services" / service
        if not service_path.exists():
            logger.warning(f"Service path not found: {service_path}")
            return []
        
        generated = []
        
        # Add service src to Python path
        src_path = service_path / "src"
        if src_path.exists():
            sys.path.insert(0, str(src_path))
        
        # Find all Python modules
        for py_file in service_path.rglob("*.py"):
            # Skip __pycache__, venv, and test files for main docs
            if any(skip in str(py_file) for skip in ["__pycache__", "venv", ".pyc"]):
                continue
                
            # Generate module path
            relative_path = py_file.relative_to(service_path)
            module_name = str(relative_path.with_suffix("")).replace(os.sep, ".")
            
            # Skip setup.py
            if module_name == "setup":
                continue
            
            # Generate HTML documentation
            output_file = self.docs_output / service / f"{module_name}.html"
            
            try:
                # Use pydoc to generate HTML
                result = subprocess.run(
                    [sys.executable, "-m", "pydoc", "-w", module_name],
                    cwd=str(service_path),
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    # Move generated file to docs directory
                    generated_file = service_path / f"{module_name}.html"
                    if generated_file.exists():
                        generated_file.rename(output_file)
                        generated.append(str(output_file))
                        logger.debug(f"Generated: {output_file}")
                else:
                    logger.error(f"Failed to generate docs for {module_name}: {result.stderr}")
                    
            except Exception as e:
                logger.error(f"Error generating docs for {module_name}: {e}")
        
        # Remove src from path
        if src_path.exists() and str(src_path) in sys.path:
            sys.path.remove(str(src_path))
            
        logger.info(f"Generated {len(generated)} documentation files for {service}")
        return generated
    
    def generate_index(self) -> None:
        """
        Generate main index.html file with links to all documentation
        
        Creates a comprehensive index page that organizes all generated
        documentation by service and module type
        """
        logger.info("Generating documentation index...")
        
        index_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Helios Career Operations System - API Documentation</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }
        h2 {
            color: #34495e;
            margin-top: 30px;
            border-bottom: 1px solid #bdc3c7;
            padding-bottom: 5px;
        }
        h3 {
            color: #7f8c8d;
            margin-top: 20px;
        }
        .service-section {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .module-list {
            list-style: none;
            padding: 0;
        }
        .module-list li {
            padding: 8px;
            margin: 5px 0;
            background: #ecf0f1;
            border-radius: 4px;
            transition: background 0.3s;
        }
        .module-list li:hover {
            background: #d5dbdd;
        }
        .module-list a {
            color: #2980b9;
            text-decoration: none;
            display: block;
        }
        .module-list a:hover {
            color: #1abc9c;
        }
        .stats {
            background: #3498db;
            color: white;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }
        .category {
            margin: 15px 0;
        }
        .category-title {
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 1.1em;
        }
        .breadcrumb {
            background: white;
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 20px;
        }
        .timestamp {
            color: #95a5a6;
            font-size: 0.9em;
            text-align: right;
            margin-top: 30px;
        }
    </style>
</head>
<body>
    <div class="breadcrumb">
        <a href="../index.html">Documentation</a> / API Documentation
    </div>
    
    <h1>🚀 Helios Career Operations System - API Documentation</h1>
    
    <div class="stats">
        <strong>Documentation Coverage:</strong> Complete Python API documentation for all services<br>
        <strong>Generated:</strong> {timestamp}<br>
        <strong>Total Modules:</strong> {total_modules}
    </div>
    
    <p>
        Comprehensive API documentation for the Helios Career Operations System, 
        an AI-powered career intelligence platform built using BMAD methodology.
    </p>
"""
        
        # Organize documentation by service
        for service in self.services:
            service_docs = self.docs_output / service
            if not service_docs.exists():
                continue
                
            modules = list(service_docs.glob("*.html"))
            if not modules:
                continue
            
            # Categorize modules
            api_modules = []
            core_modules = []
            model_modules = []
            integration_modules = []
            test_modules = []
            other_modules = []
            
            for module in modules:
                module_name = module.stem
                if "api" in module_name:
                    api_modules.append(module)
                elif "core" in module_name:
                    core_modules.append(module)
                elif "model" in module_name:
                    model_modules.append(module)
                elif "integration" in module_name:
                    integration_modules.append(module)
                elif "test" in module_name:
                    test_modules.append(module)
                else:
                    other_modules.append(module)
            
            index_content += f"""
    <div class="service-section">
        <h2>📦 {service.replace('-', ' ').title()}</h2>
        <p>Documentation for the {service} microservice.</p>
"""
            
            # Add categories
            categories = [
                ("🔌 API Endpoints", api_modules),
                ("⚙️ Core Business Logic", core_modules),
                ("📊 Data Models", model_modules),
                ("🔗 Integrations", integration_modules),
                ("🧪 Tests", test_modules),
                ("📁 Other Modules", other_modules)
            ]
            
            for category_name, modules in categories:
                if modules:
                    index_content += f"""
        <div class="category">
            <div class="category-title">{category_name}</div>
            <ul class="module-list">
"""
                    for module in sorted(modules):
                        module_name = module.stem
                        relative_path = module.relative_to(self.docs_output)
                        index_content += f"""                <li><a href="{relative_path}">{module_name}</a></li>
"""
                    index_content += """            </ul>
        </div>
"""
            
            index_content += """    </div>
"""
        
        # Add footer
        total_modules = sum(len(list((self.docs_output / s).glob("*.html"))) 
                          for s in self.services if (self.docs_output / s).exists())
        
        index_content += f"""
    <h2>📚 Additional Resources</h2>
    <ul>
        <li><a href="../PRD.md">Product Requirements Document</a></li>
        <li><a href="../architecture.md">System Architecture</a></li>
        <li><a href="../../bmad-core/core-config.yaml">BMAD Configuration</a></li>
        <li><a href="../../README.md">Project README</a></li>
    </ul>
    
    <div class="timestamp">
        Documentation generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    </div>
</body>
</html>
"""
        
        index_content = index_content.replace("{timestamp}", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        index_content = index_content.replace("{total_modules}", str(total_modules))
        
        # Write index file with UTF-8 encoding
        index_file = self.docs_output / "index.html"
        index_file.write_text(index_content, encoding='utf-8')
        logger.info(f"Generated index: {index_file}")
    
    def generate_config_file(self) -> None:
        """
        Generate pydoc configuration file for consistent documentation generation
        
        Creates a configuration file that can be used to regenerate documentation
        with the same settings
        """
        config = {
            "project": "Helios Career Operations System",
            "version": "1.0.0",
            "services": self.services,
            "output_dir": str(self.docs_output),
            "generated_at": datetime.now().isoformat(),
            "settings": {
                "include_tests": True,
                "include_private": False,
                "generate_index": True,
                "format": "html"
            }
        }
        
        config_file = self.root_dir / "docs" / "config" / "pydoc.conf"
        config_file.parent.mkdir(exist_ok=True)
        
        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)
            
        logger.info(f"Generated configuration: {config_file}")
    
    def run(self) -> None:
        """
        Execute the complete documentation generation process
        
        This method orchestrates the entire documentation generation workflow:
        1. Sets up the environment
        2. Generates documentation for each service
        3. Creates the main index
        4. Saves configuration
        """
        logger.info("Starting documentation generation...")
        start_time = datetime.now()
        
        # Setup
        self.setup_environment()
        
        # Generate docs for each service
        for service in self.services:
            docs = self.generate_service_docs(service)
            self.generated_files.extend(docs)
        
        # Generate index
        self.generate_index()
        
        # Save configuration
        self.generate_config_file()
        
        # Summary
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"Documentation generation complete!")
        logger.info(f"Generated {len(self.generated_files)} files in {duration:.2f} seconds")
        logger.info(f"Documentation available at: {self.docs_output}")


def main():
    """
    Main entry point for the documentation generator
    
    Parses command-line arguments and runs the documentation generator
    """
    parser = argparse.ArgumentParser(
        description="Generate comprehensive pydoc documentation for Helios Career Operations System"
    )
    parser.add_argument(
        "--root",
        type=str,
        help="Root directory of the project",
        default=os.getcwd()
    )
    parser.add_argument(
        "--service",
        type=str,
        help="Generate docs for specific service only",
        choices=["profile-ingestor", "orchestrator", "strategist", "analyst"]
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create and run generator
    generator = DocGenerator(args.root)
    
    if args.service:
        # Generate for specific service only
        generator.setup_environment()
        generator.generate_service_docs(args.service)
        generator.generate_index()
    else:
        # Generate for all services
        generator.run()


if __name__ == "__main__":
    main()