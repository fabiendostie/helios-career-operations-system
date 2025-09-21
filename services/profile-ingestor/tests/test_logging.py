#!/usr/bin/env python3
"""
Test script to demonstrate the enhanced logging functionality for entity extraction.
"""

import logging
from pathlib import Path
from resume_extractor.components.parsing import ParsingService, ConflictDetector
from resume_extractor.components.ingestion import Document


def setup_logging():
    """Setup detailed logging for testing."""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('parsing_debug.log', mode='w')
        ]
    )


def test_parsing_with_logging():
    """Test parsing with comprehensive logging output."""
    print("Testing ParsingService with Enhanced Logging")
    print("=" * 60)
    print("Logs will be saved to 'parsing_debug.log' and displayed below:")
    print("=" * 60)

    # Setup logging
    setup_logging()

    # Create test documents
    doc1_content = """
    Jane Smith
    Email: jane.smith@example.com
    Phone: (555) 123-4567

    Senior Software Engineer at Google (2021-2024)
    - Developed scalable web applications using Python and Django
    - Led a team of 5 engineers in microservices architecture
    - Improved system performance by 40%

    Software Engineer at Microsoft (2019-2021)
    - Built cloud-native applications using C# and .NET
    - Worked with Azure services and Docker containers

    Skills: Python, JavaScript, React, Django, Azure, Docker, Kubernetes

    Projects:
    - E-commerce Platform: Built full-stack solution with 10k+ users
    - Analytics Dashboard: Real-time data visualization using D3.js
    """

    doc2_content = """
    Jane Smith
    jane.smith@gmail.com
    555-123-4567

    Senior Engineer at Google Inc (2020-2024)  # Conflict: different start year
    - Built web applications with Python/Django
    - Team leadership and mentoring

    Developer at Microsoft Corporation (2019-2021)
    - Cloud application development
    - Azure and containerization expertise

    Technical Skills: Python, Javascript, ReactJS, Django, AWS, Docker  # Skill variations

    Project Work:
    - E-commerce System: Online shopping platform with React frontend  # Conflict: different description
    - Data Visualization Tool: Interactive charts and graphs
    """

    # Create documents
    doc1 = Document(
        file_path=Path("resume_v1.txt"),
        content=doc1_content,
        language="en",
        file_type="txt"
    )

    doc2 = Document(
        file_path=Path("resume_v2.txt"),
        content=doc2_content,
        language="en",
        file_type="txt"
    )

    # Parse documents
    service = ParsingService()

    print("\\n--- PARSING DOCUMENT 1 ---")
    parsed1 = service.parse_document(doc1)

    print("\\n--- PARSING DOCUMENT 2 ---")
    parsed2 = service.parse_document(doc2)

    print("\\n--- CONFLICT DETECTION ---")
    detector = ConflictDetector()
    conflicts = detector.find_conflicts([parsed1, parsed2])

    print("\\n" + "=" * 60)
    print("PARSING RESULTS SUMMARY")
    print("=" * 60)

    print(f"Document 1 Results:")
    print(f"  - Work Experiences: {len(parsed1.work_experiences)}")
    print(f"  - Projects: {len(parsed1.projects)}")
    print(f"  - Skills: {len(parsed1.skills)}")
    print(f"  - Contact Info: {list(parsed1.contact_info.keys())}")

    print(f"\\nDocument 2 Results:")
    print(f"  - Work Experiences: {len(parsed2.work_experiences)}")
    print(f"  - Projects: {len(parsed2.projects)}")
    print(f"  - Skills: {len(parsed2.skills)}")
    print(f"  - Contact Info: {list(parsed2.contact_info.keys())}")

    print(f"\\nConflicts Detected: {len(conflicts)}")
    for i, conflict in enumerate(conflicts, 1):
        print(f"  {i}. {conflict.field} ({conflict.entity_id})")
        print(f"     Variations: {conflict.variations}")
        print(f"     Sources: {conflict.sources}")

    print("\\n" + "=" * 60)
    print("Detailed logs have been written to 'parsing_debug.log'")
    print("=" * 60)


if __name__ == "__main__":
    test_parsing_with_logging()
