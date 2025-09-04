# Technology Stack

## Core Language & Runtime
- **Python 3.13.1** - Latest stable Python with enhanced performance and typing features
- **Virtual Environment** - Isolated dependency management using `venv`

## Natural Language Processing
- **spaCy 4.0.2** - Industrial-strength NLP library
  - `en_core_web_trf` - English transformer model for entity recognition
  - `fr_dep_news_trf` - French transformer model for entity recognition
- **langdetect** - Automatic language detection for multilingual resume processing

## Document Processing Libraries
- **pypdf 4.5.1** - PDF text extraction with robust handling of various PDF formats
- **python-docx 1.2.0** - Microsoft Word document parsing and text extraction
- **PyYAML 6.1.0** - YAML configuration and resume file parsing
- **Mistune 3.1.0** - Fast and flexible Markdown parsing

## User Interface & Interaction
- **Questionary 2.1.0** - Beautiful interactive command line prompts
  - Conflict resolution workflows
  - Data elicitation interviews
  - User confirmation dialogs

## Development & Quality Tools
- **pytest 9.0.1** - Comprehensive testing framework
  - Fixtures for test data management
  - Parametrized testing for multiple scenarios
  - Coverage reporting integration
- **Black 25.8.1** - Uncompromising code formatter
- **Ruff 0.6.5** - Fast Python linter with extensive rule coverage

## Data Handling
- **JSON** (built-in) - Master career database output format
- **Logging** (built-in) - Structured application logging
- **Dataclasses** (built-in) - Type-safe data structure definitions
- **Type Hints** (built-in) - Static type checking support

## Architecture Patterns
- **Pipeline Architecture** - Sequential processing stages with clear interfaces
- **Strategy Pattern** - Pluggable parsers for different file formats and languages
- **Singleton Pattern** - Shared spaCy model resources for memory efficiency
- **Factory Pattern** - Dynamic parser selection based on file type

## File System & I/O
- **pathlib** (built-in) - Modern path handling
- **tempfile** (built-in) - Secure temporary file operations
- **os/sys** (built-in) - System integration and environment handling

## Configuration Management
- **YAML-based configuration** - Skill mapping and system settings
- **Environment variables** - Runtime configuration overrides
- **Command-line arguments** - User-specified input directories

## Memory & Performance Considerations
- **Lazy loading** - spaCy models loaded on-demand
- **Streaming processing** - Large document handling without memory bloat
- **Caching** - Parsed document results for conflict resolution phase
- **Resource cleanup** - Proper file handle and model memory management

## Deployment & Distribution
- **pip requirements.txt** - Dependency specification
- **Virtual environment** - Isolated runtime environment
- **Cross-platform support** - Windows, macOS, Linux compatibility
- **CLI entry point** - `python -m resume_extractor.main` execution pattern