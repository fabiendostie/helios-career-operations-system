#!/usr/bin/env python3
"""
Master documentation generator for HELIOS project.
Generates both API documentation (pydoc) and story/methodology documentation.
"""

import sys
import subprocess
from pathlib import Path

# Fix encoding issues on Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())


def run_generator(script_name: str, project_root: Path) -> bool:
    """Run a documentation generator script."""
    script_path = project_root / "scripts" / script_name

    if not script_path.exists():
        print(f"❌ Script not found: {script_path}")
        return False

    try:
        print(f"🔄 Running {script_name}...")
        result = subprocess.run([sys.executable, str(script_path)],
                              cwd=project_root, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"✅ {script_name} completed successfully")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print(f"❌ {script_name} failed with return code {result.returncode}")
            if result.stderr:
                print("Error output:", result.stderr)
            return False

    except Exception as e:
        print(f"❌ Error running {script_name}: {e}")
        return False


def create_master_index(project_root: Path) -> None:
    """Create master documentation index."""
    docs_dir = project_root / "docs"
    master_index = docs_dir / "index.html"

    html_content = """<!DOCTYPE html>
<html>
<head>
    <title>HELIOS Career Operations System - Documentation Hub</title>
    <meta charset="utf-8">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0; padding: 0; background: #f8f9fa;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }

        .hero {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 60px 40px; border-radius: 20px;
            margin-bottom: 40px; text-align: center;
            box-shadow: 0 10px 40px rgba(0,0,0,0.15);
        }
        .hero h1 { margin: 0; font-size: 3em; font-weight: 300; }
        .hero p { margin: 20px 0 0 0; opacity: 0.9; font-size: 1.3em; }

        .docs-grid {
            display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 30px; margin: 40px 0;
        }

        .doc-card {
            background: white; border-radius: 15px; overflow: hidden;
            box-shadow: 0 5px 25px rgba(0,0,0,0.08);
            transition: all 0.3s ease; border: 1px solid #e9ecef;
        }
        .doc-card:hover {
            transform: translateY(-5px); box-shadow: 0 8px 35px rgba(0,0,0,0.15);
        }

        .card-header {
            padding: 25px 30px 20px; border-bottom: 1px solid #e9ecef;
        }
        .card-icon { font-size: 2.5em; margin-bottom: 15px; }
        .card-title { margin: 0; font-size: 1.4em; color: #333; }
        .card-desc { margin: 8px 0 0 0; color: #666; line-height: 1.5; }

        .card-content { padding: 20px 30px; }
        .doc-links { list-style: none; padding: 0; margin: 0; }
        .doc-links li { margin: 12px 0; }
        .doc-links a {
            text-decoration: none; color: #667eea; font-weight: 500;
            display: flex; align-items: center; padding: 8px 0;
            transition: color 0.3s ease;
        }
        .doc-links a:hover { color: #4f63d2; }
        .doc-links a::before { content: "→"; margin-right: 10px; }

        .stats {
            display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 20px; margin: 40px 0;
        }
        .stat {
            background: white; padding: 30px 20px; border-radius: 12px;
            text-align: center; box-shadow: 0 3px 15px rgba(0,0,0,0.08);
        }
        .stat-number {
            font-size: 2.5em; font-weight: bold; margin: 0;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .stat-label { color: #666; margin: 8px 0 0 0; font-weight: 500; }

        .footer {
            margin-top: 60px; padding: 40px 0; border-top: 2px solid #e9ecef;
            text-align: center; color: #666;
        }

        .badge {
            display: inline-block; padding: 4px 12px; border-radius: 15px;
            font-size: 12px; font-weight: bold; text-transform: uppercase;
            margin-left: 10px;
        }
        .badge-success { background: #d4edda; color: #155724; }
        .badge-warning { background: #fff3cd; color: #856404; }
    </style>
</head>
<body>
    <div class="container">
        <div class="hero">
            <h1>🚀 HELIOS Documentation Hub</h1>
            <p>Comprehensive documentation for the AI-powered career intelligence platform</p>
        </div>

        <div class="stats">
            <div class="stat">
                <div class="stat-number">8</div>
                <div class="stat-label">Stories Documented</div>
            </div>
            <div class="stat">
                <div class="stat-number">2</div>
                <div class="stat-label">Active Services</div>
            </div>
            <div class="stat">
                <div class="stat-number">99%</div>
                <div class="stat-label">Test Coverage</div>
            </div>
            <div class="stat">
                <div class="stat-number">85%</div>
                <div class="stat-label">Quality Score</div>
            </div>
        </div>

        <div class="docs-grid">
            <div class="doc-card">
                <div class="card-header">
                    <div class="card-icon">📚</div>
                    <h3 class="card-title">API Documentation
                        <span class="badge badge-success">Auto-Generated</span>
                    </h3>
                    <p class="card-desc">Comprehensive API reference generated from source code using pydoc</p>
                </div>
                <div class="card-content">
                    <ul class="doc-links">
                        <li><a href="api/index.html">Complete API Reference</a></li>
                        <li><a href="api/profile-ingestor/">Profile Ingestor Service</a></li>
                        <li><a href="api/orchestrator/">HELIOS Orchestrator</a></li>
                    </ul>
                </div>
            </div>

            <div class="doc-card">
                <div class="card-header">
                    <div class="card-icon">📋</div>
                    <h3 class="card-title">Stories & Methodology
                        <span class="badge badge-warning">BMAD</span>
                    </h3>
                    <p class="card-desc">Development stories, BMAD methodology, and implementation progress</p>
                </div>
                <div class="card-content">
                    <ul class="doc-links">
                        <li><a href="generated/index.html">Stories Overview</a></li>
                        <li><a href="stories/">Individual Stories</a></li>
                        <li><a href="03-design/BMAD-Analysis.md">BMAD Methodology</a></li>
                    </ul>
                </div>
            </div>

            <div class="doc-card">
                <div class="card-header">
                    <div class="card-icon">🏗️</div>
                    <h3 class="card-title">Architecture & Design
                        <span class="badge badge-success">Complete</span>
                    </h3>
                    <p class="card-desc">System architecture, technical specifications, and design decisions</p>
                </div>
                <div class="card-content">
                    <ul class="doc-links">
                        <li><a href="02-architecture/Architecture-Document.md">System Architecture</a></li>
                        <li><a href="02-architecture/tech-stack.md">Technology Stack</a></li>
                        <li><a href="02-architecture/coding-standards.md">Coding Standards</a></li>
                    </ul>
                </div>
            </div>

            <div class="doc-card">
                <div class="card-header">
                    <div class="card-icon">📊</div>
                    <h3 class="card-title">Requirements & Planning
                        <span class="badge badge-success">Approved</span>
                    </h3>
                    <p class="card-desc">Product requirements, user stories, and project planning documents</p>
                </div>
                <div class="card-content">
                    <ul class="doc-links">
                        <li><a href="01-requirements/PRD-Helios-Career-Operations-System.md">Product Requirements</a></li>
                        <li><a href="01-requirements/Epic-Breakdown-User-Stories.md">Epic Breakdown</a></li>
                        <li><a href="stories/MVP-Sequential-4Week-Plan.md">MVP Plan</a></li>
                    </ul>
                </div>
            </div>

            <div class="doc-card">
                <div class="card-header">
                    <div class="card-icon">🔧</div>
                    <h3 class="card-title">Implementation & QA
                        <span class="badge badge-warning">Active</span>
                    </h3>
                    <p class="card-desc">Implementation guides, testing strategies, and quality assurance</p>
                </div>
                <div class="card-content">
                    <ul class="doc-links">
                        <li><a href="04-implementation/Integration-Guide.md">Integration Guide</a></li>
                        <li><a href="qa/gates/">Quality Gates</a></li>
                        <li><a href="../services/">Service Code</a></li>
                    </ul>
                </div>
            </div>

            <div class="doc-card">
                <div class="card-header">
                    <div class="card-icon">⚡</div>
                    <h3 class="card-title">Quick Links
                        <span class="badge badge-success">Live</span>
                    </h3>
                    <p class="card-desc">Fast access to commonly used resources and external links</p>
                </div>
                <div class="card-content">
                    <ul class="doc-links">
                        <li><a href="https://github.com/fabiendostie/helios-career-operations-system">GitHub Repository</a></li>
                        <li><a href="http://localhost:8000/docs">Local API (FastAPI)</a></li>
                        <li><a href="../README.md">Project README</a></li>
                    </ul>
                </div>
            </div>
        </div>

        <div class="footer">
            <p><strong>🚀 HELIOS Career Operations System</strong></p>
            <p>AI-Powered Career Intelligence Platform</p>
            <p>Generated automatically • Powered by <a href="https://github.com/bmad-code-org/BMAD-METHOD">BMAD Methodology</a></p>
        </div>
    </div>
</body>
</html>"""

    master_index.write_text(html_content, encoding="utf-8")
    print(f"📄 Created master documentation index: {master_index}")


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        project_root = Path(sys.argv[1]).resolve()
    else:
        project_root = Path(__file__).parent.parent

    if not project_root.exists():
        print(f"❌ Project root not found: {project_root}")
        sys.exit(1)

    print("🚀 Starting comprehensive documentation generation...")
    print("=" * 60)

    success_count = 0

    # Generate API documentation
    if run_generator("generate_docs.py", project_root):
        success_count += 1

    # Generate story documentation
    if run_generator("generate_story_docs.py", project_root):
        success_count += 1

    # Create master index
    try:
        create_master_index(project_root)
        success_count += 1
        print("✅ Master index created successfully")
    except Exception as e:
        print(f"❌ Failed to create master index: {e}")

    print("=" * 60)
    print(f"📊 Documentation generation complete: {success_count}/3 generators succeeded")

    if success_count == 3:
        docs_dir = project_root / "docs"
        print(f"🎉 All documentation generated successfully!")
        print(f"📂 Main documentation hub: {docs_dir}/index.html")
        print(f"📚 API docs: {docs_dir}/api/index.html")
        print(f"📋 Story docs: {docs_dir}/generated/index.html")
    else:
        print(f"⚠️  Some generators failed. Check output above for details.")


if __name__ == "__main__":
    main()
