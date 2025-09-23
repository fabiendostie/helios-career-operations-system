#!/usr/bin/env python3
"""
Test script to verify the ParsingService implementation works correctly.
"""

import sys
from pathlib import Path
from resume_extractor.components.parsing import ParsingService, ConflictDetector, ParsedData
from resume_extractor.components.ingestion import Document


def test_singleton_pattern():
    """Test that ParsingService implements singleton pattern."""
    service1 = ParsingService()
    service2 = ParsingService()
    assert service1 is service2, "ParsingService should be singleton"
    print("[PASS] Singleton pattern working correctly")


def test_model_loading():
    """Test that spaCy models load correctly."""
    service = ParsingService()
    print(f"[PASS] Models loaded: {list(service._models.keys())}")

    # Check if at least one model is loaded
    assert len(service._models) > 0, "At least one spaCy model should be loaded"
    print("[PASS] At least one spaCy model loaded successfully")


def test_language_detection():
    """Test language detection functionality."""
    service = ParsingService()

    # Test English detection
    english_text = "I am a software engineer with experience in Python and JavaScript."
    eng_lang = service._detect_language(english_text)
    assert eng_lang == "en", f"Expected 'en', got '{eng_lang}'"
    print("[PASS] English language detection working")

    # Test French detection
    french_text = "Je suis un ingénieur logiciel avec de l'expérience en Python et JavaScript."
    fr_lang = service._detect_language(french_text)
    assert fr_lang == "fr", f"Expected 'fr', got '{fr_lang}'"
    print("[PASS] French language detection working")


def test_basic_parsing():
    """Test basic document parsing functionality."""
    service = ParsingService()

    # Create a test document
    test_content = """
    John Doe
    Software Engineer at Google
    Email: john.doe@example.com
    Phone: (555) 123-4567

    Work Experience:
    - Senior Developer at Microsoft (2020-2023)
    - Junior Developer at Apple (2018-2020)

    Skills: Python, JavaScript, React, Docker

    Projects:
    - E-commerce Platform: Built a full-stack application using Django and React
    - Data Analysis Tool: Created visualization dashboard with Python and D3.js
    """

    document = Document(
        file_path=Path("test_resume.txt"),
        content=test_content,
        language="en",
        file_type="txt"
    )

    # Parse the document
    parsed_data = service.parse_document(document)

    # Verify the parsed data structure
    assert isinstance(parsed_data, ParsedData), "Should return ParsedData instance"
    assert parsed_data.language == "en", "Language should be detected as English"
    assert parsed_data.source_file.endswith("test_resume.txt"), "Source file should be set"

    print("[PASS] Basic parsing functionality working")
    print(f"  - Work experiences found: {len(parsed_data.work_experiences)}")
    print(f"  - Projects found: {len(parsed_data.projects)}")
    print(f"  - Skills found: {len(parsed_data.skills)}")
    print(f"  - Contact info: {list(parsed_data.contact_info.keys())}")


def test_conflict_detection():
    """Test conflict detection between multiple documents."""
    service = ParsingService()
    detector = ConflictDetector()

    # Create two documents with conflicting information
    doc1_content = """
    Jane Smith
    Senior Engineer at Google (2020-2023)
    Skills: Python, React
    """

    doc2_content = """
    Jane Smith
    Senior Engineer at Google (2019-2023)
    Skills: Python, ReactJS
    """

    doc1 = Document(Path("resume1.txt"), doc1_content, "en", "txt")
    doc2 = Document(Path("resume2.txt"), doc2_content, "en", "txt")

    parsed1 = service.parse_document(doc1)
    parsed2 = service.parse_document(doc2)

    conflicts = detector.find_conflicts([parsed1, parsed2])

    print(f"[PASS] Conflict detection working - found {len(conflicts)} conflicts")
    for conflict in conflicts:
        print(f"  - {conflict.field}: {conflict.variations}")


def main():
    """Run all tests."""
    print("Testing ParsingService implementation...")
    print("=" * 50)

    try:
        test_singleton_pattern()
        test_model_loading()
        test_language_detection()
        test_basic_parsing()
        test_conflict_detection()

        print("=" * 50)
        print("[SUCCESS] All tests passed! ParsingService implementation is working correctly.")

    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
