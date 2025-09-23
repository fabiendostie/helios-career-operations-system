# Requirements Snapshot for Development

## Core Functional Requirements

### File Processing (FR1)
- Support: `.pdf`, `.docx`, `.md`, `.txt`, `.yml`, `.json`
- Read from user-specified directory
- Handle multiple file formats simultaneously

### Language Support (FR2)
- Process English and French content
- Automatic language detection per document
- Use appropriate spaCy model based on language

### Conflict Resolution (FR3)
- Interactive CLI prompts when conflicts detected
- Present multiple versions clearly
- Suggest most detailed version by default
- Store user's choice as canonical

### Skill Mapping (FR4)
- Bilingual skill dictionary (skill_map.json)
- Map "Project Management" ↔ "Gestion de projet"
- Single entry per skill with evidence pointers

### Data Elicitation (FR5)
- Interactive Q&A after parsing
- Capture: transversal projects, aspirations, motivators, qualities
- Store in holistic_profile section

### JSON Output (FR6)
- Validate against master schema
- Write to master_career_database.json
- Clean, formatted output

## Non-Functional Requirements

### NFR1: CLI Application
- Standalone Python application
- Command-line interface
- Accept directory path as argument

### NFR2: NLP Performance
- spaCy transformer models for precision
- en_core_web_trf for English
- fr_dep_news_trf for French

### NFR3: User Experience
- Clear prompts and instructions
- User-friendly error messages
- Progress indicators where appropriate

## Technical Constraints
- Python 3.13.1
- Monolithic architecture
- Local file processing only
- No external APIs
- Interactive (not batch) processing
