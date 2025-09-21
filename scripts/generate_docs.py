#!/usr/bin/env python3
"""
Enhanced documentation generation script for HELIOS Career Operations System.
Generates comprehensive API documentation for all services using multiple methods.
"""

import os
import sys
import subprocess
import shutil
import ast
import importlib.util
from pathlib import Path
from typing import List, Dict, Optional, Set
import time
import json

# Fix encoding issues on Windows
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    # Reconfigure stdout and stderr to use UTF-8
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


class DocGenerator:
    """Enhanced automated documentation generator for HELIOS services."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.docs_dir = project_root / "docs" / "api"
        self.services_dir = project_root / "services"
        self.timeout = 15  # Reduced timeout for faster processing
        self.service_status = {
            "profile-ingestor": "✅ OPERATIONAL",
            "orchestrator": "✅ OPERATIONAL",
            "strategist": "✅ OPERATIONAL",
            "analyst": "✅ OPERATIONAL",
            "architect": "⚠️ IN DEVELOPMENT",
            "editor": "⚠️ IN DEVELOPMENT",
            "shared": "🔧 SHARED LIBRARY"
        }

    def setup_directories(self) -> None:
        """Create necessary documentation directories."""
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 Created docs directory: {self.docs_dir}")

    def get_services(self) -> List[Path]:
        """Get list of all services to document."""
        services = []
        for service_dir in self.services_dir.iterdir():
            if service_dir.is_dir():
                # Check for either src directory or Python files directly (for shared service)
                if (service_dir / "src").exists() or any(service_dir.glob("*.py")):
                    services.append(service_dir)
        return services

    def extract_docstrings(self, py_file: Path) -> Dict[str, str]:
        """Extract docstrings from Python file using AST."""
        try:
            content = py_file.read_text(encoding='utf-8')
            tree = ast.parse(content)

            docstrings = {}

            # Module docstring
            if (ast.get_docstring(tree)):
                docstrings['module'] = ast.get_docstring(tree)

            # Class and function docstrings
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    docstring = ast.get_docstring(node)
                    if docstring:
                        docstrings[f"{type(node).__name__}:{node.name}"] = docstring

            return docstrings
        except Exception as e:
            print(f"  ⚠️ Could not parse {py_file.name}: {e}")
            return {}

    def generate_simple_html_doc(self, service_path: Path) -> None:
        """Generate simple HTML documentation using AST parsing."""
        service_name = service_path.name

        # Determine the source path
        if (service_path / "src").exists():
            src_path = service_path / "src"
        else:
            src_path = service_path

        output_dir = self.docs_dir / service_name
        output_dir.mkdir(exist_ok=True)

        print(f"📚 Generating docs for {service_name}...")

        # Collect all Python files and their documentation
        modules = {}
        for py_file in src_path.rglob("*.py"):
            if py_file.name.startswith("__") and py_file.stat().st_size < 100:
                continue

            rel_path = py_file.relative_to(src_path)
            module_name = str(rel_path).replace("/", ".").replace("\\", ".").replace(".py", "")

            docstrings = self.extract_docstrings(py_file)
            if docstrings:
                modules[module_name] = {
                    'file_path': str(rel_path),
                    'docstrings': docstrings
                }

        # Generate HTML for each module
        for module_name, module_info in modules.items():
            self.create_module_html(service_name, module_name, module_info, output_dir)

        print(f"  ✅ Generated {len(modules)} module docs for {service_name}")

    def create_module_html(self, service_name: str, module_name: str, module_info: Dict, output_dir: Path) -> None:
        """Create HTML documentation for a single module."""
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>{module_name} - {service_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f8f9fa; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 5px; margin-bottom: 30px; }}
        .section {{ margin: 20px 0; padding: 20px; border-left: 4px solid #667eea; background: #f8f9ff; }}
        .docstring {{ background: #fff; padding: 15px; border-radius: 5px; border: 1px solid #e0e0e0; margin: 10px 0; white-space: pre-wrap; }}
        .nav {{ margin-bottom: 20px; }}
        .nav a {{ color: #667eea; text-decoration: none; margin-right: 20px; }}
        .nav a:hover {{ text-decoration: underline; }}
        h1, h2, h3 {{ color: #333; }}
        .module-path {{ color: #666; font-style: italic; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{module_name}</h1>
            <p class="module-path">Service: {service_name} • Path: {module_info['file_path']}</p>
        </div>

        <div class="nav">
            <a href="../index.html">← Back to API Index</a>
            <a href="../{service_name}/index.html">← {service_name} Overview</a>
        </div>
"""

        # Add module docstring if available
        if 'module' in module_info['docstrings']:
            html_content += f"""
        <div class="section">
            <h2>Module Description</h2>
            <div class="docstring">{module_info['docstrings']['module']}</div>
        </div>
"""

        # Add classes and functions
        classes = {k: v for k, v in module_info['docstrings'].items() if k.startswith('ClassDef:')}
        functions = {k: v for k, v in module_info['docstrings'].items() if k.startswith(('FunctionDef:', 'AsyncFunctionDef:'))}

        if classes:
            html_content += """
        <div class="section">
            <h2>Classes</h2>
"""
            for class_key, docstring in classes.items():
                class_name = class_key.split(':', 1)[1]
                html_content += f"""
            <h3>{class_name}</h3>
            <div class="docstring">{docstring}</div>
"""
            html_content += "        </div>"

        if functions:
            html_content += """
        <div class="section">
            <h2>Functions</h2>
"""
            for func_key, docstring in functions.items():
                func_name = func_key.split(':', 1)[1]
                func_type = "async " if func_key.startswith('AsyncFunctionDef:') else ""
                html_content += f"""
            <h3>{func_type}{func_name}()</h3>
            <div class="docstring">{docstring}</div>
"""
            html_content += "        </div>"

        html_content += """
    </div>
</body>
</html>"""

        # Write HTML file
        html_file = output_dir / f"{module_name}.html"
        html_file.write_text(html_content, encoding='utf-8')
        print(f"    → {module_name}.html")

    def create_index_html(self, services: List[Path]) -> None:
        """Create main index.html for documentation."""
        current_time = time.strftime("%B %d, %Y at %H:%M", time.localtime())

        index_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>HELIOS Career Operations System - API Documentation</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 40px; background: #f8f9fa; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                 color: white; padding: 40px; border-radius: 12px; margin-bottom: 40px; text-align: center; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
        .header h1 {{ margin: 0 0 10px 0; font-size: 2.5em; }}
        .header p {{ margin: 5px 0; opacity: 0.9; }}
        .services-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 25px; }}
        .service {{ background: white; padding: 25px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); transition: transform 0.2s; }}
        .service:hover {{ transform: translateY(-2px); box-shadow: 0 4px 20px rgba(0,0,0,0.15); }}
        .service-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }}
        .service h3 {{ color: #333; margin: 0; font-size: 1.3em; }}
        .module-list {{ list-style: none; padding: 0; margin: 0; }}
        .module-list li {{ margin: 8px 0; }}
        .module-list a {{ text-decoration: none; color: #667eea; padding: 5px 0; display: block; border-radius: 4px; transition: all 0.2s; }}
        .module-list a:hover {{ background: #f0f4ff; padding-left: 10px; }}
        .status {{ display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 500; }}
        .operational {{ background: #d4edda; color: #155724; }}
        .development {{ background: #fff3cd; color: #856404; }}
        .shared {{ background: #e3f2fd; color: #1565c0; }}
        .stats {{ background: white; padding: 20px; border-radius: 8px; margin-bottom: 30px; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 20px; margin-top: 15px; }}
        .stat {{ padding: 15px; background: #f8f9ff; border-radius: 6px; }}
        .stat-number {{ font-size: 1.8em; font-weight: bold; color: #667eea; }}
        .stat-label {{ color: #666; font-size: 0.9em; }}
        .footer {{ margin-top: 40px; padding: 20px; text-align: center; color: #666; border-top: 1px solid #eee; background: white; border-radius: 8px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 HELIOS Career Operations System</h1>
            <p>AI-Powered Career Intelligence Platform</p>
            <p>API Documentation • Generated automatically • {current_time}</p>
        </div>

        <div class="stats">
            <h2>System Overview</h2>
            <div class="stats-grid">
                <div class="stat">
                    <div class="stat-number">{len(services)}</div>
                    <div class="stat-label">Total Services</div>
                </div>
                <div class="stat">
                    <div class="stat-number">4</div>
                    <div class="stat-label">Operational</div>
                </div>
                <div class="stat">
                    <div class="stat-number">2</div>
                    <div class="stat-label">In Development</div>
                </div>
                <div class="stat">
                    <div class="stat-number">1</div>
                    <div class="stat-label">Shared Library</div>
                </div>
            </div>
        </div>

        <div class="services-grid">
"""

        for service_path in services:
            service_name = service_path.name
            service_docs = self.docs_dir / service_name

            # Get status from our service_status dict
            status_text = self.service_status.get(service_name, "📋 PLANNED")

            if "OPERATIONAL" in status_text:
                status_class = "operational"
            elif "DEVELOPMENT" in status_text:
                status_class = "development"
            elif "SHARED" in status_text:
                status_class = "shared"
            else:
                status_class = "development"

            index_content += f"""
        <div class="service">
            <div class="service-header">
                <h3>{service_name.replace('-', ' ').title()} Service</h3>
                <span class="status {status_class}">{status_text}</span>
            </div>
            <ul class="module-list">
"""

            # List all HTML files for this service
            module_count = 0
            if service_docs.exists():
                for html_file in service_docs.glob("*.html"):
                    module_name = html_file.stem
                    relative_path = f"{service_name}/{html_file.name}"
                    display_name = module_name.replace('.', ' › ')
                    index_content += f'                <li><a href="{relative_path}">{display_name}</a></li>\n'
                    module_count += 1

            if module_count == 0:
                index_content += '                <li style="color: #999; font-style: italic;">No modules documented yet</li>\n'

            index_content += """            </ul>
        </div>
"""

        index_content += """        </div>

        <div class="footer">
            <p><strong>HELIOS Career Operations System</strong> • Built with BMAD Methodology</p>
            <p>Documentation generated automatically from source code • <a href="https://github.com/bmad-code-org/BMAD-METHOD" style="color: #667eea;">Learn about BMAD</a></p>
        </div>
    </div>
</body>
</html>"""

        index_file = self.docs_dir / "index.html"
        index_file.write_text(index_content, encoding="utf-8")
        print(f"📄 Created main index: {index_file}")

    def generate_service_index(self, service_path: Path) -> None:
        """Generate service-specific index page."""
        service_name = service_path.name
        service_docs = self.docs_dir / service_name

        if not service_docs.exists():
            return

        # Count modules
        html_files = list(service_docs.glob("*.html"))
        if not html_files:
            return

        status_text = self.service_status.get(service_name, "📋 PLANNED")

        index_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>{service_name.replace('-', ' ').title()} Service - HELIOS</title>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; margin: 40px; background: #f8f9fa; }}
        .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 5px; margin-bottom: 30px; }}
        .nav {{ margin-bottom: 20px; }}
        .nav a {{ color: #667eea; text-decoration: none; }}
        .module-grid {{ display: grid; gap: 15px; }}
        .module {{ padding: 15px; border: 1px solid #e0e0e0; border-radius: 5px; background: #f8f9ff; }}
        .module a {{ color: #667eea; text-decoration: none; font-weight: 500; }}
        .module a:hover {{ text-decoration: underline; }}
        .status {{ display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; background: #e3f2fd; color: #1565c0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{service_name.replace('-', ' ').title()} Service</h1>
            <p>Status: <span class="status">{status_text}</span></p>
        </div>

        <div class="nav">
            <a href="../index.html">← Back to API Index</a>
        </div>

        <h2>Modules ({len(html_files)})</h2>
        <div class="module-grid">
"""

        for html_file in sorted(html_files):
            module_name = html_file.stem
            display_name = module_name.replace('.', ' › ')
            index_content += f"""
            <div class="module">
                <a href="{html_file.name}">{display_name}</a>
            </div>
"""

        index_content += """
        </div>
    </div>
</body>
</html>"""

        service_index = service_docs / "index.html"
        service_index.write_text(index_content, encoding='utf-8')
        print(f"  📄 Created service index: {service_name}/index.html")

    def generate_all_docs(self) -> None:
        """Generate documentation for all services."""
        start_time = time.time()
        print("🚀 Starting enhanced documentation generation...")

        self.setup_directories()
        services = self.get_services()

        if not services:
            print("❌ No services found to document")
            return

        print(f"📦 Found {len(services)} services to document")

        total_modules = 0
        # Generate docs for each service
        for service in services:
            try:
                print(f"\n📚 Processing {service.name}...")
                self.generate_simple_html_doc(service)
                self.generate_service_index(service)

                # Count modules for this service
                service_docs = self.docs_dir / service.name
                if service_docs.exists():
                    module_count = len(list(service_docs.glob("*.html"))) - 1  # Exclude index.html
                    total_modules += module_count

            except Exception as e:
                print(f"❌ Error generating docs for {service.name}: {e}")

        # Create main index
        self.create_index_html(services)

        elapsed = time.time() - start_time
        print(f"\n✅ Documentation generation complete!")
        print(f"📊 Generated {total_modules} module pages across {len(services)} services")
        print(f"⏱️  Completed in {elapsed:.1f} seconds")
        print(f"📂 Documentation available at: {self.docs_dir}/index.html")


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        project_root = Path(sys.argv[1]).resolve()
    else:
        project_root = Path(__file__).parent.parent

    if not project_root.exists():
        print(f"❌ Project root not found: {project_root}")
        sys.exit(1)

    generator = DocGenerator(project_root)
    generator.generate_all_docs()


if __name__ == "__main__":
    main()
