#!/usr/bin/env python3
"""
Generate basic HTML documentation for missing services
"""

import os
import ast
from pathlib import Path


def extract_module_info(file_path):
    """Extract basic info from Python file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content)

        # Extract module docstring
        module_doc = None
        if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Constant):
            module_doc = tree.body[0].value.value

        # Extract classes and functions
        classes = []
        functions = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_doc = None
                if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant):
                    class_doc = node.body[0].value.value

                classes.append({
                    'name': node.name,
                    'doc': class_doc,
                    'line': node.lineno
                })

            elif isinstance(node, ast.FunctionDef):
                func_doc = None
                if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant):
                    func_doc = node.body[0].value.value

                functions.append({
                    'name': node.name,
                    'doc': func_doc,
                    'line': node.lineno,
                    'args': [arg.arg for arg in node.args.args]
                })

        return {
            'module_doc': module_doc,
            'classes': classes,
            'functions': functions
        }

    except Exception as e:
        return {'error': str(e)}


def generate_html_doc(module_name, module_info, file_path):
    """Generate basic HTML documentation"""

    html = f"""<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">
<html><head><title>Python: module {module_name}</title>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
</head><body bgcolor="#f0f0f8">

<table width="100%" cellspacing=0 cellpadding=2 border=0 summary="heading">
<tr bgcolor="#7799ee">
<td valign=bottom>&nbsp;<br>
<font color="#ffffff" face="helvetica, arial">&nbsp;<br><big><big><strong>{module_name}</strong></big></big></font></td>
<td align=right valign=bottom
><font color="#ffffff" face="helvetica, arial">{file_path}</font></td></tr></table>
"""

    if module_info.get('module_doc'):
        html += f"""
    <p><tt>{module_info['module_doc'].replace('<', '&lt;').replace('>', '&gt;')}</tt></p>
"""

    if 'error' in module_info:
        html += f"""
    <p><font color="#ff0000"><strong>Error parsing module:</strong> {module_info['error']}</font></p>
"""
    else:
        # Classes
        if module_info['classes']:
            html += """
<p>
<table width="100%" cellspacing=0 cellpadding=2 border=0 summary="section">
<tr bgcolor="#ffc8d8">
<td colspan=3 valign=bottom>&nbsp;<br>
<font color="#000000" face="helvetica, arial"><a name="Classes">Classes</a></font></td></tr>
"""
            for cls in module_info['classes']:
                html += f"""
<tr><td bgcolor="#ffc8d8"><tt>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</tt></td><td>&nbsp;</td>
<td width="100%"><dl>
<dt><font face="helvetica, arial"><strong>{cls['name']}</strong></font></dt>
"""
                if cls['doc']:
                    html += f"<dd><tt>{cls['doc'][:200]}...</tt></dd>"
                html += "</dl></td></tr>"

            html += "</table></p>"

        # Functions
        if module_info['functions']:
            html += """
<p>
<table width="100%" cellspacing=0 cellpadding=2 border=0 summary="section">
<tr bgcolor="#eeaa77">
<td colspan=3 valign=bottom>&nbsp;<br>
<font color="#ffffff" face="helvetica, arial"><a name="Functions">Functions</a></font></td></tr>
"""
            for func in module_info['functions']:
                args_str = ', '.join(func['args'])
                html += f"""
<tr><td bgcolor="#eeaa77"><tt>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</tt></td><td>&nbsp;</td>
<td width="100%"><dl><dt><a name="{func['name']}"><strong>{func['name']}</strong></a>({args_str})</dt>
"""
                if func['doc']:
                    html += f"<dd><tt>{func['doc'][:200]}...</tt></dd>"
                html += "</dl></td></tr>"

            html += "</table></p>"

    html += """
</body></html>
"""
    return html


def generate_docs_for_service(service_name):
    """Generate docs for a service"""
    print(f"Generating docs for {service_name}...")

    root_dir = Path.cwd()
    service_dir = root_dir / "services" / service_name
    output_dir = root_dir / "docs" / "api" / service_name

    if not service_dir.exists():
        print(f"  Service directory not found: {service_dir}")
        return

    output_dir.mkdir(exist_ok=True)

    # Find Python files
    py_files = list(service_dir.rglob("*.py"))
    generated = 0

    for py_file in py_files:
        # Skip certain files
        if any(skip in str(py_file) for skip in ["__pycache__", "venv", "test_", "conftest"]):
            continue

        # Get relative path for module name
        rel_path = py_file.relative_to(service_dir)
        module_name = str(rel_path.with_suffix("")).replace(os.sep, ".")

        # Extract module info
        module_info = extract_module_info(py_file)

        # Generate HTML
        html = generate_html_doc(module_name, module_info, str(py_file))

        # Save HTML file
        output_file = output_dir / f"{module_name}.html"
        output_file.write_text(html, encoding='utf-8')

        generated += 1
        print(f"  Generated: {module_name}.html")

    print(f"  Total: {generated} files generated")


def main():
    """Generate missing documentation"""
    print("Generating missing pydoc documentation...")

    services = ["strategist", "analyst"]

    for service in services:
        generate_docs_for_service(service)

    print("Documentation generation complete!")


if __name__ == "__main__":
    main()
