#!/usr/bin/env python3
"""
Simple Documentation Generator for Helios Career Operations System
Generates documentation by parsing Python files without importing them
"""

import os
import ast
import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
import re


class SimpleDocGenerator:
    """Generate documentation by parsing Python AST"""

    def __init__(self, root_dir: str = None):
        self.root_dir = Path(root_dir) if root_dir else Path.cwd()
        self.docs_output = self.root_dir / "docs" / "api"
        self.services = ["profile-ingestor", "orchestrator", "strategist", "analyst"]

    def extract_docstring(self, node: ast.AST) -> Optional[str]:
        """Extract docstring from AST node"""
        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
            if node.body and isinstance(node.body[0], ast.Expr):
                if isinstance(node.body[0].value, ast.Constant):
                    return node.body[0].value.value
        return None

    def parse_python_file(self, file_path: Path) -> Dict[str, Any]:
        """Parse a Python file and extract documentation"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)

            doc_info = {
                "file": str(file_path),
                "module_doc": self.extract_docstring(tree),
                "classes": [],
                "functions": [],
                "imports": []
            }

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_info = {
                        "name": node.name,
                        "docstring": self.extract_docstring(node),
                        "methods": [],
                        "line": node.lineno
                    }

                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            method_info = {
                                "name": item.name,
                                "docstring": self.extract_docstring(item),
                                "args": [arg.arg for arg in item.args.args],
                                "line": item.lineno
                            }
                            class_info["methods"].append(method_info)

                    doc_info["classes"].append(class_info)

                elif isinstance(node, ast.FunctionDef):
                    # Only top-level functions
                    if not any(isinstance(parent, ast.ClassDef) for parent in ast.walk(tree)):
                        func_info = {
                            "name": node.name,
                            "docstring": self.extract_docstring(node),
                            "args": [arg.arg for arg in node.args.args],
                            "line": node.lineno
                        }
                        doc_info["functions"].append(func_info)

                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        doc_info["imports"].append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        doc_info["imports"].append(node.module)

            return doc_info

        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return None

    def generate_html_doc(self, doc_info: Dict[str, Any]) -> str:
        """Generate HTML documentation from parsed info"""
        file_path = Path(doc_info["file"])
        module_name = file_path.stem

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{module_name} - Documentation</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }}
        h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        h3 {{ color: #7f8c8d; }}
        .docstring {{ background: #ecf0f1; padding: 10px; border-radius: 4px; margin: 10px 0; }}
        .method {{ margin-left: 20px; margin-bottom: 20px; border-left: 3px solid #3498db; padding-left: 15px; }}
        .function {{ margin-bottom: 20px; border-left: 3px solid #2ecc71; padding-left: 15px; }}
        .class {{ margin-bottom: 30px; }}
        .args {{ color: #e74c3c; font-family: monospace; }}
        .line-number {{ color: #95a5a6; font-size: 0.9em; }}
        code {{ background: #f8f8f8; padding: 2px 5px; border-radius: 3px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📄 {module_name}</h1>
        <p><strong>File:</strong> <code>{doc_info["file"]}</code></p>
"""

        if doc_info["module_doc"]:
            html += f"""
        <div class="docstring">
            <strong>Module Documentation:</strong><br>
            {doc_info["module_doc"].replace(chr(10), '<br>')}
        </div>
"""

        if doc_info["imports"]:
            html += f"""
        <h2>Imports</h2>
        <ul>
"""
            for imp in doc_info["imports"][:10]:  # Limit to first 10
                html += f"            <li><code>{imp}</code></li>\n"
            if len(doc_info["imports"]) > 10:
                html += f"            <li>... and {len(doc_info["imports"]) - 10} more</li>\n"
            html += """        </ul>
"""

        if doc_info["classes"]:
            html += """
        <h2>Classes</h2>
"""
            for cls in doc_info["classes"]:
                html += f"""
        <div class="class">
            <h3>class {cls["name"]} <span class="line-number">(line {cls["line"]})</span></h3>
"""
                if cls["docstring"]:
                    html += f"""
            <div class="docstring">{cls["docstring"].replace(chr(10), '<br>')}</div>
"""

                if cls["methods"]:
                    html += """
            <h4>Methods:</h4>
"""
                    for method in cls["methods"]:
                        args_str = ", ".join(method["args"])
                        html += f"""
            <div class="method">
                <strong>{method["name"]}</strong>(<span class="args">{args_str}</span>)
                <span class="line-number">(line {method["line"]})</span>
"""
                        if method["docstring"]:
                            html += f"""
                <div class="docstring">{method["docstring"].replace(chr(10), '<br>')}</div>
"""
                        html += """            </div>
"""

                html += """        </div>
"""

        if doc_info["functions"]:
            html += """
        <h2>Functions</h2>
"""
            for func in doc_info["functions"]:
                args_str = ", ".join(func["args"])
                html += f"""
        <div class="function">
            <strong>{func["name"]}</strong>(<span class="args">{args_str}</span>)
            <span class="line-number">(line {func["line"]})</span>
"""
                if func["docstring"]:
                    html += f"""
            <div class="docstring">{func["docstring"].replace(chr(10), '<br>')}</div>
"""
                html += """        </div>
"""

        html += f"""
        <hr>
        <p style="text-align: right; color: #95a5a6; font-size: 0.9em;">
            Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </p>
    </div>
</body>
</html>
"""
        return html

    def generate_service_docs(self, service: str) -> List[str]:
        """Generate documentation for a service"""
        print(f"📦 Generating docs for {service}...")

        service_path = self.root_dir / "services" / service
        if not service_path.exists():
            print(f"  ⚠️ Service path not found: {service_path}")
            return []

        # Create output directory
        output_dir = self.docs_output / service
        output_dir.mkdir(parents=True, exist_ok=True)

        generated = []

        # Find Python files
        for py_file in service_path.rglob("*.py"):
            # Skip certain files/directories
            if any(skip in str(py_file) for skip in ["__pycache__", "venv", ".pyc", "setup.py"]):
                continue

            # Parse file
            doc_info = self.parse_python_file(py_file)
            if not doc_info:
                continue

            # Generate HTML
            html = self.generate_html_doc(doc_info)

            # Save HTML
            relative_path = py_file.relative_to(service_path)
            output_file = output_dir / f"{str(relative_path).replace(os.sep, '_')}.html"

            output_file.write_text(html, encoding='utf-8')
            generated.append(str(output_file))
            print(f"  ✅ Generated: {output_file.name}")

        print(f"  📊 Total: {len(generated)} files")
        return generated

    def generate_index(self) -> None:
        """Generate main index page"""
        print("📝 Generating index...")

        html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Helios API Documentation</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
        h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
        h2 { color: #34495e; margin-top: 30px; }
        .service { background: #ecf0f1; padding: 15px; margin: 15px 0; border-radius: 8px; }
        .service h3 { margin-top: 0; color: #2c3e50; }
        ul { list-style: none; padding: 0; }
        li { padding: 5px 0; }
        a { color: #3498db; text-decoration: none; }
        a:hover { text-decoration: underline; }
        .stats { background: #3498db; color: white; padding: 15px; border-radius: 8px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Helios Career Operations System - API Documentation</h1>

        <div class="stats">
            <strong>Documentation Coverage:</strong> Python API documentation for all services<br>
            <strong>Generated:</strong> """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """
        </div>
"""

        # Add services
        for service in self.services:
            service_dir = self.docs_output / service
            if not service_dir.exists():
                continue

            files = list(service_dir.glob("*.html"))
            if not files:
                continue

            html += f"""
        <div class="service">
            <h3>📦 {service.replace('-', ' ').title()}</h3>
            <p>{len(files)} documented modules</p>
            <ul>
"""

            # Group by type
            src_files = [f for f in files if "src_" in f.name]
            test_files = [f for f in files if "test" in f.name]
            other_files = [f for f in files if f not in src_files and f not in test_files]

            if src_files:
                html += "                <li><strong>Source Files:</strong></li>\n"
                for f in sorted(src_files)[:10]:
                    html += f'                <li>→ <a href="{service}/{f.name}">{f.stem}</a></li>\n'
                if len(src_files) > 10:
                    html += f"                <li>... and {len(src_files) - 10} more</li>\n"

            if test_files:
                html += "                <li><strong>Test Files:</strong></li>\n"
                for f in sorted(test_files)[:5]:
                    html += f'                <li>→ <a href="{service}/{f.name}">{f.stem}</a></li>\n'
                if len(test_files) > 5:
                    html += f"                <li>... and {len(test_files) - 5} more</li>\n"

            html += """            </ul>
        </div>
"""

        html += """
    </div>
</body>
</html>
"""

        # Save index
        index_file = self.docs_output / "index.html"
        index_file.write_text(html, encoding='utf-8')
        print(f"✅ Index generated: {index_file}")

    def run(self) -> None:
        """Run documentation generation"""
        print("\n" + "="*60)
        print("📚 SIMPLE DOCUMENTATION GENERATOR")
        print("="*60 + "\n")

        # Create output directory
        self.docs_output.mkdir(parents=True, exist_ok=True)

        # Generate docs for each service
        all_generated = []
        for service in self.services:
            generated = self.generate_service_docs(service)
            all_generated.extend(generated)

        # Generate index
        self.generate_index()

        print("\n" + "="*60)
        print(f"✅ Documentation generation complete!")
        print(f"📊 Total files generated: {len(all_generated)}")
        print(f"📁 Output directory: {self.docs_output}")
        print("="*60)


if __name__ == "__main__":
    generator = SimpleDocGenerator()
    generator.run()
