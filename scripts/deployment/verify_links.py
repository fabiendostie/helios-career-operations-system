#!/usr/bin/env python3
"""
Verify all links in the API documentation index
"""

import os
from pathlib import Path

def verify_links():
    """Verify all documentation links exist"""
    print("Verifying API documentation links...")

    root_dir = Path.cwd()
    api_dir = root_dir / "docs" / "api"

    # Links from index.html to verify
    links_to_verify = [
        # Orchestrator links
        "orchestrator/api.html",
        "orchestrator/core.html",
        "orchestrator/core.config.html",
        "orchestrator/models.commands.html",
        "orchestrator/models.session.html",
        "orchestrator/integrations.html",

        # Profile Ingestor links
        "profile-ingestor/components.html",
        "profile-ingestor/schemas.master_schema.html",
        "profile-ingestor/ui.conflict_resolver.html",
        "profile-ingestor/ui.elicitation.html",
        "profile-ingestor/src.resume_extractor.components.ingestion.html",
        "profile-ingestor/src.resume_extractor.components.output_generator.html",

        # Strategist links
        "strategist/src.api.career_paths.html",
        "strategist/src.core.career_generator.html",
        "strategist/src.core.fit_scorer.html",
        "strategist/src.core.skill_vectorizer.html",
        "strategist/src.models.career_path.html",
        "strategist/src.models.role_taxonomy.html",

        # Analyst links
        "analyst/src.core.resume_deconstructor.html",
        "analyst/src.core.market_analyzer.html",
        "analyst/src.core.ats_simulator.html",
        "analyst/src.core.skill_recalibrator.html",
        "analyst/src.core.career_inferencer.html",
        "analyst/src.models.analysis_request.html"
    ]

    # Additional resource links to verify
    resource_links = [
        "../01-requirements/PRD-Helios-Career-Operations-System.md",
        "../02-architecture/Architecture-Document.md",
        "../../bmad-core/core-config.yaml",
        "../07-operations/rollback-procedures.md",
        "../04-implementation/integration-points-analysis.md",
        "../../CLAUDE.md"
    ]

    missing_files = []
    existing_files = []

    print("Checking API documentation links:")
    for link in links_to_verify:
        file_path = api_dir / link
        if file_path.exists():
            existing_files.append(link)
            print(f"  [OK] {link}")
        else:
            missing_files.append(link)
            print(f"  [MISSING] {link}")

    print("\nChecking resource links:")
    for link in resource_links:
        # Resolve relative path from api directory
        file_path = api_dir / link
        file_path = file_path.resolve()
        if file_path.exists():
            existing_files.append(link)
            print(f"  [OK] {link}")
        else:
            missing_files.append(link)
            print(f"  [MISSING] {link}")

    print(f"\nLink Verification Summary:")
    print(f"  Total links checked: {len(links_to_verify) + len(resource_links)}")
    print(f"  Valid links: {len(existing_files)}")
    print(f"  Broken links: {len(missing_files)}")

    if missing_files:
        print(f"\nMissing files:")
        for file in missing_files:
            print(f"  - {file}")
        return False
    else:
        print("\nAll links verified successfully!")
        return True

if __name__ == "__main__":
    success = verify_links()
    exit(0 if success else 1)
