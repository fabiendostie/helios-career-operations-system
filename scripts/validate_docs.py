#!/usr/bin/env python3
"""
Documentation validation script for HELIOS Career Operations System.
Validates that generated documentation is current, complete, and correct.
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Set, Tuple
from datetime import datetime, timedelta

# Fix encoding issues on Windows
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


class DocumentationValidator:
    """Validates documentation completeness and freshness."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.docs_dir = project_root / "docs" / "api"
        self.services_dir = project_root / "services"
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.stats = {
            'services_found': 0,
            'services_documented': 0,
            'total_modules': 0,
            'documented_modules': 0,
            'html_files': 0,
            'broken_links': 0,
            'outdated_files': 0
        }

    def log_error(self, message: str) -> None:
        """Log an error."""
        self.errors.append(message)
        print(f"❌ {message}")

    def log_warning(self, message: str) -> None:
        """Log a warning."""
        self.warnings.append(message)
        print(f"⚠️  {message}")

    def log_info(self, message: str) -> None:
        """Log an info message."""
        print(f"ℹ️  {message}")

    def log_success(self, message: str) -> None:
        """Log a success message."""
        print(f"✅ {message}")

    def check_basic_structure(self) -> bool:
        """Check basic documentation structure."""
        print("🔍 Checking basic documentation structure...")

        required_files = [
            self.docs_dir / "index.html",
        ]

        structure_ok = True

        for required_file in required_files:
            if required_file.exists():
                self.log_success(f"Found {required_file.name}")
            else:
                self.log_error(f"Missing required file: {required_file}")
                structure_ok = False

        # Check if docs directory exists
        if not self.docs_dir.exists():
            self.log_error(f"Documentation directory not found: {self.docs_dir}")
            return False

        return structure_ok

    def check_service_coverage(self) -> bool:
        """Check that all services have documentation."""
        print("\n📦 Checking service documentation coverage...")

        if not self.services_dir.exists():
            self.log_error(f"Services directory not found: {self.services_dir}")
            return False

        coverage_ok = True
        services = []

        # Find all services
        for service_dir in self.services_dir.iterdir():
            if service_dir.is_dir():
                # Check for either src directory or Python files directly
                if (service_dir / "src").exists() or any(service_dir.glob("*.py")):
                    services.append(service_dir.name)
                    self.stats['services_found'] += 1

        if not services:
            self.log_error("No services found to document")
            return False

        # Check documentation for each service
        for service_name in services:
            service_docs_dir = self.docs_dir / service_name

            if service_docs_dir.exists():
                html_files = list(service_docs_dir.glob("*.html"))
                if html_files:
                    self.log_success(f"Service '{service_name}' has {len(html_files)} documentation files")
                    self.stats['services_documented'] += 1
                    self.stats['html_files'] += len(html_files)
                else:
                    self.log_warning(f"Service '{service_name}' directory exists but contains no HTML files")
                    coverage_ok = False
            else:
                self.log_error(f"No documentation found for service: {service_name}")
                coverage_ok = False

        coverage_percentage = (self.stats['services_documented'] / self.stats['services_found']) * 100
        print(f"\n📊 Service coverage: {self.stats['services_documented']}/{self.stats['services_found']} ({coverage_percentage:.1f}%)")

        return coverage_ok

    def check_module_coverage(self) -> bool:
        """Check that Python modules have corresponding documentation."""
        print("\n🐍 Checking module documentation coverage...")

        coverage_ok = True

        # Count total Python modules
        for service_dir in self.services_dir.iterdir():
            if not service_dir.is_dir():
                continue

            # Determine source path
            src_path = service_dir / "src" if (service_dir / "src").exists() else service_dir

            for py_file in src_path.rglob("*.py"):
                if py_file.name.startswith("__") and py_file.stat().st_size < 100:
                    continue

                self.stats['total_modules'] += 1

                # Check if documentation exists
                rel_path = py_file.relative_to(src_path)
                module_name = str(rel_path).replace("/", ".").replace("\\", ".").replace(".py", "")

                doc_file = self.docs_dir / service_dir.name / f"{module_name}.html"
                if doc_file.exists():
                    self.stats['documented_modules'] += 1
                else:
                    self.log_warning(f"No documentation for module: {service_dir.name}/{module_name}")

        if self.stats['total_modules'] > 0:
            module_coverage = (self.stats['documented_modules'] / self.stats['total_modules']) * 100
            print(f"📊 Module coverage: {self.stats['documented_modules']}/{self.stats['total_modules']} ({module_coverage:.1f}%)")

            if module_coverage < 80:
                self.log_warning(f"Module coverage is below 80% ({module_coverage:.1f}%)")
                coverage_ok = False
        else:
            self.log_warning("No Python modules found")

        return coverage_ok

    def check_documentation_freshness(self) -> bool:
        """Check if documentation is up-to-date with source code."""
        print("\n🕐 Checking documentation freshness...")

        main_index = self.docs_dir / "index.html"
        if not main_index.exists():
            self.log_error("Main documentation index not found")
            return False

        index_mtime = main_index.stat().st_mtime
        freshness_ok = True
        outdated_threshold = timedelta(hours=24)  # Documentation should be updated within 24 hours

        # Check if any source files are newer than documentation
        for service_dir in self.services_dir.iterdir():
            if not service_dir.is_dir():
                continue

            src_path = service_dir / "src" if (service_dir / "src").exists() else service_dir

            for py_file in src_path.rglob("*.py"):
                if py_file.stat().st_mtime > index_mtime:
                    file_age = datetime.fromtimestamp(py_file.stat().st_mtime)
                    doc_age = datetime.fromtimestamp(index_mtime)

                    if file_age - doc_age > outdated_threshold:
                        self.log_warning(f"Source file newer than docs: {py_file.relative_to(self.project_root)}")
                        self.stats['outdated_files'] += 1
                        freshness_ok = False

        if freshness_ok:
            self.log_success("Documentation is up-to-date with source code")
        else:
            self.log_warning(f"Found {self.stats['outdated_files']} files newer than documentation")

        return freshness_ok

    def validate_html_files(self) -> bool:
        """Validate HTML file structure and content."""
        print("\n🌐 Validating HTML files...")

        validation_ok = True

        for html_file in self.docs_dir.rglob("*.html"):
            try:
                content = html_file.read_text(encoding='utf-8')

                # Basic HTML structure validation
                if not ('<html>' in content and '</html>' in content):
                    self.log_error(f"Invalid HTML structure: {html_file.relative_to(self.docs_dir)}")
                    validation_ok = False

                if not ('<title>' in content and '</title>' in content):
                    self.log_warning(f"Missing title tag: {html_file.relative_to(self.docs_dir)}")

                # Check for broken internal links
                if 'href="' in content:
                    # Simple check for obvious broken links
                    import re
                    links = re.findall(r'href="([^"]*)"', content)
                    for link in links:
                        if link.startswith('#') or link.startswith('http'):
                            continue  # Skip anchors and external links

                        link_path = html_file.parent / link
                        if not link_path.exists():
                            self.log_warning(f"Broken link in {html_file.name}: {link}")
                            self.stats['broken_links'] += 1

            except Exception as e:
                self.log_error(f"Error reading HTML file {html_file}: {e}")
                validation_ok = False

        if validation_ok and self.stats['broken_links'] == 0:
            self.log_success("All HTML files are valid")
        elif self.stats['broken_links'] > 0:
            self.log_warning(f"Found {self.stats['broken_links']} broken links")

        return validation_ok

    def generate_report(self) -> Dict:
        """Generate a validation report."""
        report = {
            'timestamp': datetime.now().isoformat(),
            'validation_status': 'PASS' if not self.errors else 'FAIL',
            'summary': {
                'errors': len(self.errors),
                'warnings': len(self.warnings),
                'services_coverage': f"{self.stats['services_documented']}/{self.stats['services_found']}",
                'module_coverage': f"{self.stats['documented_modules']}/{self.stats['total_modules']}",
                'html_files_generated': self.stats['html_files'],
                'broken_links': self.stats['broken_links'],
                'outdated_files': self.stats['outdated_files']
            },
            'errors': self.errors,
            'warnings': self.warnings,
            'stats': self.stats
        }

        return report

    def save_report(self, report: Dict) -> None:
        """Save validation report to file."""
        report_file = self.project_root / "docs" / "validation_report.json"

        try:
            report_file.write_text(json.dumps(report, indent=2), encoding='utf-8')
            self.log_success(f"Validation report saved: {report_file}")
        except Exception as e:
            self.log_error(f"Failed to save validation report: {e}")

    def validate_all(self) -> bool:
        """Run all validation checks."""
        print("🔍 HELIOS Documentation Validation")
        print("=" * 45)

        start_time = time.time()

        # Run all validation checks
        checks = [
            self.check_basic_structure,
            self.check_service_coverage,
            self.check_module_coverage,
            self.check_documentation_freshness,
            self.validate_html_files
        ]

        all_passed = True
        for check in checks:
            if not check():
                all_passed = False

        # Generate and save report
        report = self.generate_report()
        self.save_report(report)

        elapsed = time.time() - start_time

        # Print summary
        print("\n" + "=" * 45)
        print("📊 Validation Summary")
        print("=" * 45)

        if all_passed and not self.errors:
            print("🎉 All validation checks passed!")
        else:
            print(f"❌ Validation failed with {len(self.errors)} errors")

        print(f"⚠️  {len(self.warnings)} warnings found")
        print(f"📊 Generated {self.stats['html_files']} HTML files")
        print(f"⏱️  Validation completed in {elapsed:.1f} seconds")

        return all_passed and not self.errors


def main():
    """Main entry point."""
    project_root = Path(__file__).parent.parent

    if len(sys.argv) > 1:
        project_root = Path(sys.argv[1]).resolve()

    if not project_root.exists():
        print(f"❌ Project root not found: {project_root}")
        sys.exit(1)

    validator = DocumentationValidator(project_root)

    if validator.validate_all():
        print("\n✅ Documentation validation passed")
        sys.exit(0)
    else:
        print("\n❌ Documentation validation failed")
        print("💡 Run 'python scripts/generate_docs.py' to regenerate documentation")
        sys.exit(1)


if __name__ == "__main__":
    main()
