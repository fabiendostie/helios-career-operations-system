#!/usr/bin/env python3
"""
Local documentation server for HELIOS API documentation.
Serves the generated pydoc HTML files for easy browsing.
"""

import os
import sys
import subprocess
import webbrowser
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import argparse


class DocumentationServer:
    """Local HTTP server for API documentation."""

    def __init__(self, project_root: Path, port: int = 8080):
        self.project_root = project_root
        self.docs_dir = project_root / "docs" / "api"
        self.port = port

    def start_server(self, open_browser: bool = True):
        """Start the local documentation server."""
        if not self.docs_dir.exists():
            print(f"❌ Documentation directory not found: {self.docs_dir}")
            print("Run 'python scripts/generate_docs.py' first to generate documentation.")
            return False

        # Change to docs directory
        os.chdir(self.docs_dir)

        print(f"Starting HELIOS Documentation Server...")
        print(f"Serving from: {self.docs_dir}")
        print(f"URL: http://localhost:{self.port}")
        print(f"Main index: http://localhost:{self.port}/index.html")
        print(f"Cross-service reference: http://localhost:{self.port}/cross-service-reference.html")
        print()
        print("Press Ctrl+C to stop the server")
        print("-" * 60)

        try:
            # Create HTTP server
            handler = SimpleHTTPRequestHandler
            httpd = HTTPServer(("localhost", self.port), handler)

            # Open browser if requested
            if open_browser:
                url = f"http://localhost:{self.port}/index.html"
                print(f"Opening browser: {url}")
                webbrowser.open(url)

            # Start server
            httpd.serve_forever()

        except KeyboardInterrupt:
            print("\nServer stopped by user")
            return True
        except OSError as e:
            if "Address already in use" in str(e):
                print(f"ERROR: Port {self.port} is already in use. Try a different port with --port")
            else:
                print(f"ERROR: Server error: {e}")
            return False

    def check_documentation(self):
        """Check if documentation files exist and are up to date."""
        print("Checking documentation status...")

        if not self.docs_dir.exists():
            print("ERROR: Documentation directory not found")
            return False

        # Check for main index file
        index_file = self.docs_dir / "index.html"
        if not index_file.exists():
            print("ERROR: Main index.html not found")
            return False

        # Check for service directories
        services = ["profile-ingestor", "orchestrator", "strategist", "analyst", "architect", "editor", "shared"]
        missing_services = []

        for service in services:
            service_dir = self.docs_dir / service
            if not service_dir.exists():
                missing_services.append(service)
            else:
                # Check for at least one HTML file in service directory
                html_files = list(service_dir.glob("*.html"))
                if not html_files:
                    missing_services.append(f"{service} (no HTML files)")

        if missing_services:
            print(f"WARNING: Missing documentation for: {', '.join(missing_services)}")
            print("Run 'python scripts/generate_docs.py' to generate missing documentation.")
        else:
            print("SUCCESS: All service documentation found")

        # Check for cross-service reference
        cross_ref = self.docs_dir / "cross-service-reference.html"
        if cross_ref.exists():
            print("SUCCESS: Cross-service reference documentation found")
        else:
            print("WARNING: Cross-service reference documentation missing")

        print(f"Documentation summary:")
        print(f"   - Total services documented: {len(services) - len(missing_services)}/{len(services)}")
        print(f"   - Documentation directory: {self.docs_dir}")

        return len(missing_services) == 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="HELIOS Documentation Server")
    parser.add_argument("--port", type=int, default=8080, help="Port to serve on (default: 8080)")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser automatically")
    parser.add_argument("--check", action="store_true", help="Check documentation status and exit")
    parser.add_argument("--project-root", type=Path, help="Project root directory")

    args = parser.parse_args()

    # Determine project root
    if args.project_root:
        project_root = args.project_root.resolve()
    else:
        project_root = Path(__file__).parent.parent

    if not project_root.exists():
        print(f"❌ Project root not found: {project_root}")
        sys.exit(1)

    server = DocumentationServer(project_root, args.port)

    if args.check:
        # Just check documentation status
        success = server.check_documentation()
        sys.exit(0 if success else 1)
    else:
        # Check first, then start server
        server.check_documentation()
        print()
        success = server.start_server(open_browser=not args.no_browser)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
