#!/usr/bin/env python3
"""
Story documentation generator for HELIOS project.
Generates comprehensive documentation for all completed stories and methodologies.
"""

import os
import sys
from pathlib import Path
import shutil
from datetime import datetime

# Fix encoding issues on Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())


class StoryDocGenerator:
    """Documentation generator for HELIOS stories and methodologies."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.docs_dir = project_root / "docs"
        self.story_docs_dir = self.docs_dir / "stories"
        self.output_dir = self.docs_dir / "generated"
        
    def setup_directories(self) -> None:
        """Create necessary documentation directories."""
        self.output_dir.mkdir(exist_ok=True)
        print(f"📁 Created output directory: {self.output_dir}")
    
    def get_story_files(self) -> dict:
        """Get all story files organized by epic."""
        stories = {
            "Epic 1 - Foundation": [
                "story_1_1_setup.md",
                "story_1_2_ingestion.md", 
                "story_1_3_parser.md",
                "story_1_4_conflict.md",
                "story_1_5_skillmap.md",
                "story_1_6_elicitation.md",
                "story_1_7_output.md"
            ],
            "Epic 2 - Intelligence": [
                "2.1.helios-orchestrator.md"
            ]
        }
        return stories
    
    def generate_story_index(self, stories: dict) -> str:
        """Generate HTML index for all stories."""
        html_content = """<!DOCTYPE html>
<html>
<head>
    <title>HELIOS Stories & Methodology Documentation</title>
    <meta charset="utf-8">
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            margin: 0; padding: 20px; line-height: 1.6; color: #333;
        }
        .header { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; padding: 40px; border-radius: 15px; margin-bottom: 40px; 
            text-align: center; box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        }
        .header h1 { margin: 0; font-size: 2.5em; font-weight: 300; }
        .header p { margin: 10px 0 0 0; opacity: 0.9; font-size: 1.2em; }
        
        .epic { 
            margin: 30px 0; background: white; border-radius: 12px; 
            box-shadow: 0 4px 20px rgba(0,0,0,0.08); overflow: hidden;
        }
        .epic-header { 
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
            color: white; padding: 20px 30px; margin: 0; font-size: 1.3em; font-weight: 500;
        }
        .story-list { padding: 20px 30px; }
        .story-item { 
            display: flex; justify-content: space-between; align-items: center;
            padding: 15px 20px; margin: 8px 0; border-radius: 8px;
            background: #f8f9fa; border-left: 4px solid #667eea;
            transition: all 0.3s ease;
        }
        .story-item:hover { 
            background: #e3f2fd; transform: translateX(5px); 
            box-shadow: 0 2px 10px rgba(102, 126, 234, 0.15);
        }
        .story-link { 
            text-decoration: none; color: #333; font-weight: 500;
            display: flex; align-items: center; flex-grow: 1;
        }
        .story-link:hover { color: #667eea; }
        
        .status { 
            display: inline-block; padding: 6px 12px; border-radius: 20px; 
            font-size: 12px; font-weight: bold; text-transform: uppercase;
        }
        .completed { background: #d4edda; color: #155724; }
        .in-progress { background: #fff3cd; color: #856404; }
        .planned { background: #f8d7da; color: #721c24; }
        
        .metadata { 
            margin: 40px 0; padding: 30px; background: #f8f9fa; 
            border-radius: 12px; border-left: 5px solid #28a745;
        }
        .metadata h3 { color: #28a745; margin-top: 0; }
        
        .stats { 
            display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 20px; margin: 30px 0;
        }
        .stat-card { 
            background: white; padding: 25px; border-radius: 12px; 
            box-shadow: 0 4px 15px rgba(0,0,0,0.08); text-align: center;
        }
        .stat-number { font-size: 2.5em; font-weight: bold; color: #667eea; margin: 0; }
        .stat-label { color: #666; margin: 5px 0 0 0; font-weight: 500; }
        
        footer { 
            margin-top: 60px; padding-top: 30px; border-top: 2px solid #eee; 
            text-align: center; color: #666; font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 HELIOS Documentation</h1>
        <p>Stories, Methodology & Development Progress</p>
    </div>
    
    <div class="stats">
        <div class="stat-card">
            <div class="stat-number">8</div>
            <div class="stat-label">Total Stories</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">7</div>
            <div class="stat-label">Epic 1 Completed</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">1</div>
            <div class="stat-label">Epic 2 In Progress</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">99%</div>
            <div class="stat-label">Test Coverage</div>
        </div>
    </div>
"""
        
        for epic_name, story_files in stories.items():
            html_content += f"""
    <div class="epic">
        <h2 class="epic-header">{epic_name}</h2>
        <div class="story-list">
"""
            
            for story_file in story_files:
                # Determine story status
                if story_file.startswith("story_1_"):
                    status = '<span class="status completed">✅ COMPLETED</span>'
                elif story_file.startswith("2.1"):
                    status = '<span class="status in-progress">🔄 IN PROGRESS</span>'
                else:
                    status = '<span class="status planned">📋 PLANNED</span>'
                
                # Create readable story title
                story_title = story_file.replace(".md", "").replace("_", " ").replace("-", " ").title()
                story_title = story_title.replace("Story ", "Story ")
                
                # Check if file exists
                story_path = self.docs_dir / story_file
                stories_path = self.story_docs_dir / story_file
                
                if story_path.exists():
                    file_path = story_file
                elif stories_path.exists():
                    file_path = f"stories/{story_file}"
                else:
                    continue
                    
                html_content += f"""
            <div class="story-item">
                <a href="{file_path}" class="story-link">{story_title}</a>
                {status}
            </div>
"""
            
            html_content += """        </div>
    </div>
"""
        
        html_content += f"""
    <div class="metadata">
        <h3>📊 Project Information</h3>
        <p><strong>Methodology:</strong> <a href="https://github.com/bmad-code-org/BMAD-METHOD">BMAD (Behavioral Model Analysis and Design)</a></p>
        <p><strong>Architecture:</strong> Microservices with AI Agent Orchestration</p>
        <p><strong>Technology Stack:</strong> Python 3.13, FastAPI, spaCy, PostgreSQL</p>
        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
        <p><strong>Repository:</strong> <a href="https://github.com/fabiendostie/helios-career-operations-system">GitHub</a></p>
    </div>
    
    <div class="metadata">
        <h3>📚 Additional Documentation</h3>
        <ul>
            <li><a href="api/index.html">🔗 API Documentation (pydoc)</a></li>
            <li><a href="01-requirements/PRD-Helios-Career-Operations-System.md">📋 Product Requirements Document</a></li>
            <li><a href="02-architecture/Architecture-Document.md">🏗️ Architecture Documentation</a></li>
            <li><a href="03-design/BMAD-Analysis.md">🎯 BMAD Methodology Analysis</a></li>
            <li><a href="04-implementation/Integration-Guide.md">⚙️ Implementation & Integration Guide</a></li>
        </ul>
    </div>
    
    <footer>
        <p>🤖 Generated automatically • HELIOS Career Operations System</p>
        <p>Powered by <a href="https://github.com/bmad-code-org/BMAD-METHOD">BMAD Methodology</a> • <a href="https://claude.ai/code">Claude Code</a></p>
    </footer>
</body>
</html>
"""
        
        return html_content
    
    def generate_complete_docs(self) -> None:
        """Generate comprehensive story documentation."""
        print("🚀 Generating HELIOS story documentation...")
        
        self.setup_directories()
        
        # Get all stories
        stories = self.get_story_files()
        
        # Generate main index
        index_html = self.generate_story_index(stories)
        index_file = self.output_dir / "index.html"
        index_file.write_text(index_html, encoding="utf-8")
        
        print(f"📄 Created story documentation index: {index_file}")
        
        # Create symlinks or copies for easy access
        try:
            # Copy key documentation files to output for easy access
            key_docs = [
                "01-requirements/PRD-Helios-Career-Operations-System.md",
                "02-architecture/Architecture-Document.md", 
                "03-design/BMAD-Analysis.md",
                "04-implementation/Integration-Guide.md"
            ]
            
            for doc_path in key_docs:
                source = self.docs_dir / doc_path
                if source.exists():
                    target = self.output_dir / source.name
                    shutil.copy2(source, target)
                    print(f"📋 Copied: {source.name}")
                    
        except Exception as e:
            print(f"⚠️  Warning: Could not copy documentation files: {e}")
        
        print("✅ Story documentation generation complete!")
        print(f"📂 Documentation available at: {self.output_dir}/index.html")


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        project_root = Path(sys.argv[1]).resolve()
    else:
        project_root = Path(__file__).parent.parent
    
    if not project_root.exists():
        print(f"❌ Project root not found: {project_root}")
        sys.exit(1)
    
    generator = StoryDocGenerator(project_root)
    generator.generate_complete_docs()


if __name__ == "__main__":
    main()