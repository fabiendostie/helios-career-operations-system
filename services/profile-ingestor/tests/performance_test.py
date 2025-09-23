#!/usr/bin/env python3
"""
Performance test for the ParsingService to ensure it meets the < 2 second requirement.
"""

import time
import statistics
from pathlib import Path
from resume_extractor.components.parsing import ParsingService
from resume_extractor.components.ingestion import Document


def create_test_documents():
    """Create test documents of various sizes."""
    documents = []

    # Small document
    small_content = """
    John Doe
    Software Engineer at Google (2020-2023)
    Skills: Python, JavaScript, React
    """
    documents.append(("small", Document(
        file_path=Path("small_resume.txt"),
        content=small_content,
        language="en",
        file_type="txt"
    )))

    # Medium document
    medium_content = """
    Jane Smith
    Email: jane.smith@example.com
    Phone: (555) 123-4567

    WORK EXPERIENCE

    Senior Software Engineer at Microsoft (2021-2024)
    - Developed cloud-native applications using Azure services
    - Led a team of 5 engineers in building microservices architecture
    - Improved system performance by 40% through optimization
    - Technologies: C#, .NET Core, Azure, Docker, Kubernetes

    Software Engineer at Amazon (2019-2021)
    - Built scalable web applications serving millions of users
    - Implemented CI/CD pipelines reducing deployment time by 60%
    - Collaborated with cross-functional teams on product features
    - Technologies: Java, Spring Boot, AWS, PostgreSQL

    Junior Developer at Startup Inc (2018-2019)
    - Developed full-stack web applications using modern frameworks
    - Participated in agile development processes
    - Technologies: Python, Django, React, MongoDB

    PROJECTS

    E-commerce Platform
    - Built a complete e-commerce solution with payment integration
    - Handled over 10,000 transactions per month
    - Technologies: React, Node.js, Stripe API, PostgreSQL

    Data Analytics Dashboard
    - Created real-time analytics dashboard for business metrics
    - Processed and visualized data from multiple sources
    - Technologies: Python, Pandas, D3.js, Flask

    EDUCATION

    Master of Science in Computer Science
    Stanford University (2016-2018)
    GPA: 3.8/4.0

    Bachelor of Science in Software Engineering
    UC Berkeley (2012-2016)
    GPA: 3.6/4.0

    SKILLS

    Programming Languages: Python, Java, JavaScript, C#, SQL
    Frameworks: Django, Flask, Spring Boot, React, Angular, .NET Core
    Databases: PostgreSQL, MongoDB, MySQL, Redis
    Cloud Platforms: AWS, Azure, Google Cloud Platform
    DevOps: Docker, Kubernetes, Jenkins, GitLab CI/CD
    """
    documents.append(("medium", Document(
        file_path=Path("medium_resume.txt"),
        content=medium_content,
        language="en",
        file_type="txt"
    )))

    # Large document (simulating a very detailed resume)
    large_content = medium_content * 3  # Triple the content
    documents.append(("large", Document(
        file_path=Path("large_resume.txt"),
        content=large_content,
        language="en",
        file_type="txt"
    )))

    # French document
    french_content = """
    Jean Dupont
    Email: jean.dupont@example.fr
    Téléphone: +33 1 23 45 67 89

    EXPÉRIENCE PROFESSIONNELLE

    Ingénieur Logiciel Senior chez Google France (2021-2024)
    - Développement d'applications web à grande échelle
    - Leadership d'une équipe de 6 développeurs
    - Amélioration des performances système de 35%
    - Technologies: Python, Django, PostgreSQL, Docker

    Développeur Full-Stack chez Orange (2019-2021)
    - Création d'applications mobiles et web
    - Intégration de services cloud et APIs
    - Participation aux méthodologies agiles
    - Technologies: JavaScript, React, Node.js, MongoDB

    PROJETS

    Plateforme E-commerce
    - Développement d'une solution complète de commerce en ligne
    - Gestion de plus de 5000 commandes par mois
    - Technologies: Vue.js, Express.js, MySQL

    Application Mobile de Gestion
    - Création d'une app mobile pour la gestion d'entreprise
    - Plus de 10000 utilisateurs actifs
    - Technologies: React Native, Firebase

    FORMATION

    Master en Informatique
    École Polytechnique (2017-2019)
    Mention Très Bien

    Licence en Génie Logiciel
    Université Pierre et Marie Curie (2014-2017)
    Mention Bien

    COMPÉTENCES

    Langages: Python, JavaScript, Java, C++, SQL
    Frameworks: Django, React, Vue.js, Spring
    Bases de données: PostgreSQL, MongoDB, MySQL
    Cloud: AWS, Google Cloud, Azure
    Outils: Docker, Jenkins, Git, Jira
    """
    documents.append(("french", Document(
        file_path=Path("french_resume.txt"),
        content=french_content,
        language="fr",
        file_type="txt"
    )))

    return documents


def test_parsing_performance():
    """Test parsing performance across different document sizes."""
    print("Testing ParsingService Performance")
    print("=" * 50)

    # Initialize service
    service = ParsingService()
    documents = create_test_documents()

    results = {}

    for doc_type, document in documents:
        print(f"\nTesting {doc_type} document ({len(document.content)} chars)...")

        # Run multiple iterations to get average
        times = []
        for i in range(3):  # Test 3 times
            start_time = time.time()
            parsed_data = service.parse_document(document)
            end_time = time.time()

            processing_time = end_time - start_time
            times.append(processing_time)

            print(f"  Run {i+1}: {processing_time:.3f}s")
            print(f"    - Work experiences: {len(parsed_data.work_experiences)}")
            print(f"    - Projects: {len(parsed_data.projects)}")
            print(f"    - Skills: {len(parsed_data.skills)}")
            print(f"    - Contact info fields: {len(parsed_data.contact_info)}")

        avg_time = statistics.mean(times)
        max_time = max(times)
        min_time = min(times)

        results[doc_type] = {
            'avg': avg_time,
            'max': max_time,
            'min': min_time,
            'char_count': len(document.content)
        }

        print(f"  Average: {avg_time:.3f}s")
        print(f"  Range: {min_time:.3f}s - {max_time:.3f}s")

        # Check performance requirement
        if max_time > 2.0:
            print(f"  [FAIL] PERFORMANCE ISSUE: Max time {max_time:.3f}s exceeds 2.0s limit")
        else:
            print(f"  [PASS] Performance OK: Max time {max_time:.3f}s within 2.0s limit")

    print("\n" + "=" * 50)
    print("PERFORMANCE SUMMARY")
    print("=" * 50)

    all_times = []
    for doc_type, metrics in results.items():
        print(f"{doc_type:10} | {metrics['char_count']:8} chars | {metrics['avg']:.3f}s avg | {metrics['max']:.3f}s max")
        all_times.append(metrics['max'])

    overall_max = max(all_times)
    print(f"\nOverall maximum processing time: {overall_max:.3f}s")

    if overall_max <= 2.0:
        print("[PASS] ALL TESTS PASSED: Performance requirement met (< 2 seconds)")
        return True
    else:
        print("[FAIL] PERFORMANCE REQUIREMENT FAILED: Some documents exceed 2 second limit")
        return False


if __name__ == "__main__":
    success = test_parsing_performance()
    exit(0 if success else 1)
