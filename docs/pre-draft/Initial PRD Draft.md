

---

# Intelligent Resume Data Extractor Product Requirements Document (PRD)

## Goals and Background Context

### Goals
* To create a structured, consolidated Master Career Database from various resume formats.
* To handle both English and French resume content seamlessly.
* To provide a clear, interactive mechanism for the user to resolve data conflicts.
* To map and consolidate bilingual skill definitions.
* To produce a final, enriched knowledge base ready for other tools or agents.

### Background Context
The system is designed to solve the problem of fragmented and incomplete professional histories spread across multiple resume files, formats, and languages. By ingesting various document types, interactively resolving conflicts with the user, and enriching the data with a guided Q&A session, it will produce a single, authoritative JSON database. This database will serve as a comprehensive and authentic foundation for downstream tools, such as an AI-powered resume and cover letter generator.

### Change Log
| Date | Version | Description | Author |
| :--- | :--- | :--- | :--- |
| 2025-08-28 | 1.0 | Initial PRD Draft | John, Product Manager |

## Requirements

### Functional
* **FR1:** The system must ingest all files with extensions `.pdf`, `.docx`, `.md`, `.txt`, `.yml`, and `.json` from a user-specified directory.
* **FR2:** The system must process text content in both English and French.
* **FR3:** When conflicting or duplicate information is detected (e.g., two different descriptions for the same job role), the system must interactively prompt the user to select the canonical version.
* **FR4:** The system must map and merge equivalent skills between English and French based on a predefined dictionary (e.g., "Project Management" and "Gestion de projet" are treated as the same skill).
* **FR5:** After initial parsing and conflict resolution, the system must conduct an interactive command-line interview to elicit and store qualitative data (transversal projects, aspirations, motivators, personal qualities).
* **FR6:** The system must generate a single, valid JSON file as its final output, strictly adhering to the specified schema.

### Non-Functional
* **NFR1:** The system must be a standalone Python application that runs from the command line (CLI).
* **NFR2:** The system must utilize high-performance and high-precision NLP libraries with robust support for both English and French.
* **NFR3:** The interactive CLI must be user-friendly and guide the user through all required inputs and decisions.

## Technical Assumptions

* **Repository Structure:** Polyrepo (a single, dedicated repository for this tool).
* **Service Architecture:** Monolithic Application (a single, cohesive Python script or package).
* **Testing Requirements:** A combination of Unit tests for individual functions (e.g., parsing, normalization) and Integration tests for the end-to-end pipeline is required.
* **Additional Technical Assumptions and Requests:**
    * The primary language will be Python.
    * NLP tasks will be handled by the `spaCy` library and its transformer models for English and French.
    * The interactive CLI will be built using the `questionary` or `Typer` library.

## Epic List

* **Epic 1: Core Data Extraction and Enrichment Pipeline:** Establish the complete, end-to-end pipeline for ingesting files, parsing data, handling conflicts, eliciting new information, and generating the final JSON output.

## Epic 1: Core Data Extraction and Enrichment Pipeline

This epic covers the implementation of the entire application, from setting up the project to delivering the final, enriched JSON file. It ensures a runnable and valuable tool is produced.

### Story 1.1: Project Initialization & Dependency Setup
**As a** developer, **I want** to set up the Python project structure with all necessary dependencies, **so that** I have a stable foundation for building the application.
#### Acceptance Criteria
1.  A new Python project is initialized with a virtual environment.
2.  All required libraries (`spaCy`, `python-docx`, `PyPDF2`, `PyYAML`, `mistune`, `questionary`) are installed.
3.  `spaCy` language models for English (`en_core_web_trf`) and French (`fr_dep_news_trf`) are downloaded.
4.  A basic `main.py` entry point script is created.

### Story 1.2: Implement File Ingestion & Language Detection
**As a** user, **I want** the system to read all supported document types from a directory **so that** all my resume data can be processed.
#### Acceptance Criteria
1.  The application accepts a directory path as a command-line argument.
2.  It successfully reads the content from all `.pdf`, `.docx`, `.md`, `.txt`, `.yml`, and `.json` files within that directory.
3.  For each document, it attempts to detect the primary language (English or French).
4.  The extracted text content and detected language for each file are stored in memory for the next stage.

### Story 1.3: Develop Bilingual Resume Parser
**As a** system, **I want** to parse key information from both English and French text **so that** a structured representation of the user's formal career can be built.
#### Acceptance Criteria
1.  A parsing function correctly uses the `spaCy` English model on English text to extract entities like work experience, projects, and skills.
2.  A parsing function correctly uses the `spaCy` French model on French text to extract the same entities.
3.  The extracted data from all files is consolidated into a single preliminary data structure.
4.  The system identifies potential conflicts (e.g., same company and role, but different descriptions or dates).

### Story 1.4: Build Interactive Conflict Resolution Module
**As a** user, **I want** to be prompted to resolve any conflicting information found in my resumes **so that** the final database is accurate and authoritative.
#### Acceptance Criteria
1.  When a data conflict is detected, the system presents the different versions to the user in a clear format.
2.  The system suggests the more detailed (higher character count) version as the default choice.
3.  The user's selection is captured and used as the canonical data point, discarding the other versions.
4.  The process repeats until all conflicts are resolved.

### Story 1.5: Implement Bilingual Skill Mapping
**As a** user, **I want** the system to recognize equivalent skills in English and French **so that** my skills inventory is consolidated and not duplicated.
#### Acceptance Criteria
1.  A predefined dictionary is used to map English and French skill terms.
2.  During data consolidation, skills like "Gestion de projet" are successfully merged with "Project Management".
3.  The final `skills_inventory` contains a single entry for each mapped skill, with evidence pointing to all original sources.

### Story 1.6: Build Interactive Elicitation Module
**As a** user, **I want** to be interviewed by the system **so that** I can add important professional context that isn't in my formal resumes.
#### Acceptance Criteria
1.  After parsing is complete, the system asks the user a series of targeted questions.
2.  The system successfully prompts for and captures at least one of each: transversal project, professional aspiration, core motivator, and personal quality.
3.  The user's answers are correctly structured and saved into the `holistic_profile` section of the database.

### Story 1.7: Generate Final JSON Output
**As a** user, **I want** the system to save the complete, enriched database to a file **so that** I can use it for my downstream tools.
#### Acceptance Criteria
1.  The application consolidates all parsed, conflict-resolved, and elicited data into a final Python dictionary.
2.  This dictionary is validated against the target JSON schema.
3.  The final data structure is written to a clean, well-formatted `master_career_database.json` file in the output directory.

## Checklist Results Report
I have internally validated this PRD against the `pm-checklist`. The document is comprehensive, the MVP scope is clear, and the epics and stories are logically sequenced to deliver value incrementally. The plan is ready for the Architect to begin the technical design phase. (UI/UX sections of the checklist were not applicable and skipped).

## Next Steps

### Architect Prompt
This Product Requirements Document (PRD) for the Intelligent Resume Data Extractor is complete. Please review it and create a detailed **Architecture Document**.

Your design should focus on:
* The Python-based application structure and the multi-stage pipeline.
* Specific usage patterns for the chosen libraries (`spaCy`, `questionary`, etc.).
* A definitive representation of the final JSON database schema.
* The detailed logic and data flow for the interactive modules (Conflict Resolution and Elicitation).

---
