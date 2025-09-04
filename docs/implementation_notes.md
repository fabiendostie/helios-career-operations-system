# Implementation Notes for Developer

## Priority Order
1. **Story 1.1**: Project setup (current focus)
2. **Story 1.2**: File ingestion & language detection
3. **Story 1.3**: Bilingual resume parser
4. **Story 1.4**: Conflict resolution UI
5. **Story 1.5**: Skill mapping
6. **Story 1.6**: Elicitation module
7. **Story 1.7**: JSON output generation

## Critical Design Decisions

### Architecture Patterns
- **Pipeline Pattern**: Sequential data processing stages
- **Strategy Pattern**: Different parsers for file types/languages
- **Singleton Pattern**: Shared spaCy models

### Component Responsibilities
- **IngestionEngine**: File discovery and reading
- **LanguageDetector**: Determine English/French
- **ParsingService**: NLP entity extraction
- **ConsolidationEngine**: Merge data, find conflicts
- **ConflictResolverUI**: Interactive conflict resolution
- **SkillMapper**: Bilingual skill normalization
- **ElicitationUI**: Q&A for qualitative data
- **OutputGenerator**: Schema validation & JSON writing

### Data Flow
1. User provides directory path
2. System reads all supported files
3. Detects language per document
4. Parses with appropriate spaCy model
5. Consolidates and identifies conflicts
6. User resolves conflicts interactively
7. System maps bilingual skills
8. User provides additional context via Q&A
9. System generates validated JSON output

## Testing Strategy
- Unit tests for each component
- Mock external I/O in tests
- Integration test with sample_resumes directory
- Use pytest for all testing

## Code Quality Standards
- Type hints required
- Black formatting (line length 88)
- Ruff linting
- Centralized strings for i18n readiness
- Comprehensive error handling
- Logging to extractor.log

## Dependencies Version Lock
```
spacy==4.0.2
questionary==2.1.0
pypdf==4.5.1
python-docx==1.2.0
PyYAML==6.1.0
mistune==3.1.0
pytest==9.0.1
black==25.8.1
ruff==0.6.5
```

## Common Pitfalls to Avoid
- Don't load spaCy models multiple times (use singleton)
- Handle file encoding issues gracefully
- Validate user input at every interactive step
- Don't assume file permissions
- Test with both English and French content
- Ensure JSON output is valid before writing