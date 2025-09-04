#!/usr/bin/env python3
"""
Documentation generation script using pydoc and additional tools.
Generates comprehensive API documentation for all services.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import List, Dict

# Fix encoding issues on Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())


class DocGenerator:
    """Automated documentation generator for HELIOS services."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.docs_dir = project_root / "docs" / "api"
        self.services_dir = project_root / "services"
    
    def setup_directories(self) -> None:
        """Create necessary documentation directories."""
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 Created docs directory: {self.docs_dir}")
    
    def get_services(self) -> List[Path]:
        """Get list of all services to document."""
        services = []
        for service_dir in self.services_dir.iterdir():
            if service_dir.is_dir() and (service_dir / "src").exists():
                services.append(service_dir)
        return services
    
    def generate_pydoc_html(self, service_path: Path) -> None:
        """Generate pydoc HTML documentation for a service."""
        service_name = service_path.name
        src_path = service_path / "src"
        output_dir = self.docs_dir / service_name
        output_dir.mkdir(exist_ok=True)
        
        print(f"📚 Generating docs for {service_name}...")
        
        # Add service src to Python path
        sys.path.insert(0, str(src_path))
        
        try:
            # Generate documentation for each Python module
            for py_file in src_path.rglob("*.py"):
                if py_file.name == "__init__.py" and py_file.stat().st_size == 0:
                    continue
                    
                # Get module path relative to src
                rel_path = py_file.relative_to(src_path)
                module_name = str(rel_path).replace("/", ".").replace("\\", ".").replace(".py", "")
                
                if module_name.endswith(".__init__"):
                    module_name = module_name[:-9]  # Remove .__init__
                
                try:
                    # Generate HTML documentation
                    cmd = [
                        sys.executable, "-m", "pydoc", "-w", module_name
                    ]
                    
                    result = subprocess.run(
                        cmd, 
                        cwd=src_path, 
                        capture_output=True, 
                        text=True,
                        timeout=30
                    )
                    
                    if result.returncode == 0:
                        # Move generated HTML to output directory
                        html_file = src_path / f"{module_name}.html"
                        if html_file.exists():
                            target_file = output_dir / f"{module_name}.html"
                            shutil.move(str(html_file), str(target_file))
                            print(f"  ✅ Generated: {module_name}.html")
                    else:
                        print(f"  ⚠️  Warning: Could not generate docs for {module_name}")
                        
                except subprocess.TimeoutExpired:
                    print(f"  ⏰ Timeout: {module_name}")
                except Exception as e:
                    print(f"  ❌ Error generating docs for {module_name}: {e}")
        
        finally:
            sys.path.remove(str(src_path))
    
    def create_index_html(self, services: List[Path]) -> None:
        """Create main index.html for documentation."""
        index_content = """<!DOCTYPE html>
<html>
<head>
    <title>HELIOS Career Operations System - API Documentation</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                 color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; }
        .service { margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
        .service h3 { color: #333; margin-top: 0; }
        .module-list { list-style-type: none; padding: 0; }
        .module-list li { margin: 5px 0; }
        .module-list a { text-decoration: none; color: #667eea; }
        .module-list a:hover { text-decoration: underline; }
        .status { display: inline-block; padding: 3px 8px; border-radius: 3px; font-size: 12px; }
        .completed { background: #d4edda; color: #155724; }
        .in-progress { background: #fff3cd; color: #856404; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 HELIOS Career Operations System</h1>
        <p>AI-Powered Career Intelligence Platform - API Documentation</p>
        <p>Generated automatically with pydoc</p>
    </div>
    
    <div class="services">
"""
        
        for service_path in services:
            service_name = service_path.name
            service_docs = self.docs_dir / service_name
            
            # Determine service status
            if service_name == "profile-ingestor":
                status = '<span class="status completed">✅ COMPLETED</span>'
            elif service_name == "orchestrator":
                status = '<span class="status in-progress">🔄 IN PROGRESS</span>'
            else:
                status = '<span class="status">📋 PLANNED</span>'
            
            index_content += f"""
        <div class="service">
            <h3>{service_name.replace('-', ' ').title()} Service {status}</h3>
            <ul class="module-list">
"""
            
            # List all HTML files for this service
            if service_docs.exists():
                for html_file in service_docs.glob("*.html"):
                    module_name = html_file.stem
                    relative_path = f"{service_name}/{html_file.name}"
                    index_content += f'                <li><a href="{relative_path}">{module_name}</a></li>\n'
            
            index_content += """            </ul>
        </div>
"""
        
        index_content += """    </div>
    
    <footer style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; color: #666;">
        <p>Generated with pydoc • HELIOS Career Operations System</p>
    </footer>
</body>
</html>"""
        
        index_file = self.docs_dir / "index.html"
        index_file.write_text(index_content, encoding="utf-8")
        print(f"📄 Created main index: {index_file}")
    
    def generate_all_docs(self) -> None:
        """Generate documentation for all services."""
        print("🚀 Starting documentation generation...")
        
        self.setup_directories()
        services = self.get_services()
        
        if not services:
            print("❌ No services found to document")
            return
        
        print(f"📦 Found {len(services)} services to document")
        
        # Generate docs for each service
        for service in services:
            try:
                self.generate_pydoc_html(service)
            except Exception as e:
                print(f"❌ Error generating docs for {service.name}: {e}")
        
        # Create main index
        self.create_index_html(services)
        
        print(f"✅ Documentation generation complete!")
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