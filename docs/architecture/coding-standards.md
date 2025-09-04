# Coding Standards

## Python Code Style

### Formatting
- **Black** for automatic code formatting
- **Ruff** for linting and additional style checks
- Maximum line length: 88 characters (Black default)
- Use double quotes for strings

### Naming Conventions
- **Classes**: PascalCase (`ParsingService`, `ConsolidationEngine`)
- **Functions/Methods**: snake_case (`extract_text`, `resolve_conflicts`)
- **Variables**: snake_case (`file_path`, `skill_mapping`)
- **Constants**: UPPER_SNAKE_CASE (`DEFAULT_TIMEOUT`, `SUPPORTED_FORMATS`)
- **Private methods**: Leading underscore (`_validate_input`)

### Code Organization
- **Type hints** required for all public methods and functions
- **Docstrings** required for all classes and public methods (Google style)
- **Error handling** with specific exception types, not bare `except`
- **Logging** instead of print statements for debugging

### File Structure
- One class per file when possible
- Import order: standard library, third-party, local imports
- Group imports with blank lines between groups

### Testing Standards
- **pytest** for all testing
- Test coverage minimum 80%
- Test file naming: `test_{module_name}.py`
- Mock external dependencies in tests
- Use descriptive test method names: `test_should_extract_skills_from_french_resume`

### Documentation
- All public APIs documented with type hints and docstrings
- Complex algorithms commented inline
- README files for each major component directory

## Example Code Structure

```python
"""Module docstring describing purpose."""

import logging
from typing import List, Dict, Optional
from dataclasses import dataclass

import spacy
from questionary import prompt

from .schemas import ResumeData


class ParsingService:
    """Handles resume parsing with multilingual support."""
    
    def __init__(self, language_models: Dict[str, spacy.Language]) -> None:
        """Initialize parser with language models.
        
        Args:
            language_models: Dictionary mapping language codes to spaCy models
        """
        self._models = language_models
        self._logger = logging.getLogger(__name__)
    
    def extract_entities(self, text: str, language: str) -> List[Dict[str, str]]:
        """Extract named entities from text using appropriate language model.
        
        Args:
            text: Input text to parse
            language: Language code ('en' or 'fr')
            
        Returns:
            List of extracted entities with labels
            
        Raises:
            ValueError: If language not supported
        """
        if language not in self._models:
            raise ValueError(f"Unsupported language: {language}")
            
        doc = self._models[language](text)
        return [{"text": ent.text, "label": ent.label_} for ent in doc.ents]
```