# Coding Standards

## Architecture Principles

### CLI/API-First Design
**The Helios Career Operations System is fundamentally CLI/API-first.** Web UI development is explicitly out of scope for the MVP to maintain focus on core intelligence capabilities.

**Design Priorities:**
1. **Command-Line Interface** - Primary user interaction method
2. **REST API** - Service-to-service communication and external integrations
3. **Microservices Architecture** - Independent, scalable service components
4. **Agent Orchestration** - HELIOS coordinates specialized AI agents

**Web UI Exclusion:**
- No frontend frameworks (React, Vue, Angular)
- No web server components beyond API endpoints
- No browser-based user interfaces
- Focus remains on backend intelligence and CLI/API functionality

## Python Code Style

### Formatting
- **Black** for automatic code formatting
- **Ruff** for linting and additional style checks
- Maximum line length: 88 characters (Black default)
- Use double quotes for strings

### Naming Conventions

#### Classes
- **PascalCase** for class names
- Descriptive, noun-based names representing entities or services
- Include domain context in names

```python
# Good examples
class ParsingService:
class ConsolidationEngine:
class SkillVectorizer:
class OrchestratorClient:
class ServiceCoordinationError(Exception):
class DocumentGenerationError(Exception):

# Avoid generic names
class Manager:  # Too generic
class Handler:  # Too generic
```

#### Functions and Methods
- **snake_case** for function and method names
- Use descriptive verb-based names indicating action
- Include domain context for clarity

```python
# Good examples
def extract_entities_from_text():
def resolve_skill_conflicts():
def validate_resume_schema():
def initialize_language_models():
def _retry_operation():  # Private method
def _get_current_timestamp():  # Private function

# Avoid abbreviated or unclear names
def parse():  # Too generic
def proc_data():  # Abbreviated
def handle():  # Too generic
```

#### Variables
- **snake_case** for variable names
- Use descriptive names that indicate content/purpose
- Include type hint context when helpful

```python
# Good examples
file_path: Path
skill_mapping: Dict[str, List[str]]
language_models: Dict[str, spacy.Language]
max_retries: int = 3
retry_delay: float = 1.0
session_state: SessionState
current_timestamp: str

# Avoid single letters or unclear abbreviations
x: str  # Unclear
data: Any  # Too generic
temp: Dict  # Abbreviated
```

#### Constants
- **UPPER_SNAKE_CASE** for module-level constants
- Group related constants together
- Use descriptive names with domain context

```python
# Good examples
DEFAULT_TIMEOUT: int = 30
SUPPORTED_FORMATS: List[str] = ['.pdf', '.docx', '.md', '.txt']
MAX_RETRY_ATTEMPTS: int = 3
EXPONENTIAL_BACKOFF_BASE: float = 2.0
SCHEMA_VERSION: str = "1.0.0"
INTERNET_TIME_AVAILABLE: bool = True

# Service-specific constants
ORCHESTRATOR_BASE_URL: str = "http://localhost:8001"
STRATEGIST_SERVICE_PORT: int = 8002
ANALYST_SERVICE_PORT: int = 8003
```

#### Module and Package Names
- **snake_case** for module names
- Use descriptive names indicating module purpose
- Organize by functional domain

```python
# Good examples
resume_extractor/
├── components/
│   ├── output_generator.py
│   ├── skill_mapper.py
│   └── conflict_resolver.py
├── integrations/
│   ├── orchestrator.py
│   └── service_clients.py
└── schemas/
    └── master_schema.py
```

### Code Organization
- **Type hints** required for all public methods and functions
- **Docstrings** required for all classes and public methods (Google style)
- **Error handling** with specific exception types, not bare `except`
- **Logging** instead of print statements for debugging

#### Module Structure Pattern
```python
"""Module docstring describing purpose and domain."""

# Standard library imports
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from uuid import uuid4

# Third-party imports
import spacy
from fastapi import HTTPException
from pydantic import BaseModel, Field

# Local imports
from .schemas import ResumeData
from ..core.config import settings
from ..integrations.orchestrator import OrchestratorClient

logger = logging.getLogger(__name__)
```

### File Structure
- One class per file when possible
- Import order: standard library, third-party, local imports
- Group imports with blank lines between groups
- Logger initialization at module level: `logger = logging.getLogger(__name__)`

## Error Handling Standards

### Custom Exception Hierarchy
Create domain-specific exceptions that inherit from appropriate base classes:

```python
# Service-level exceptions
class OrchestratorError(Exception):
    """Exception raised during orchestrator operations."""
    pass

class ServiceCoordinationError(Exception):
    """Exception raised during service coordination."""
    pass

class DocumentGenerationError(Exception):
    """Exception raised during document generation."""
    pass

# Component-level exceptions
class SkillMappingError(Exception):
    """Exception raised during skill mapping operations."""
    pass

class SchemaValidationError(Exception):
    """Exception raised during schema validation."""
    pass
```

### Error Message Format Standards
Error messages should be:
1. **Descriptive** - Clearly explain what went wrong
2. **Actionable** - Suggest next steps when possible
3. **Contextual** - Include relevant identifiers/values
4. **Consistent** - Follow established patterns

```python
# Good error message examples
raise ValueError(f"Unsupported language: {language}. Supported: {list(self._models.keys())}")
raise FileNotFoundError(f"Role taxonomy file not found: {self.taxonomy_file_path}")
raise RuntimeError(f"Model {self.model_name} failed validation test")
raise OrchestratorError(f"Failed to start analysis operation: {error_msg}")
raise DocumentGenerationError(f"PDF generation failed: {e}")

# Include operation context
raise RuntimeError(
    f"Operation failed after {self.max_retries + 1} attempts. "
    f"Last error: {str(last_error)}"
)
```

### Exception Handling Patterns

```python
# Specific exception handling with context
try:
    result = await self._models[language](text)
except KeyError:
    raise ValueError(f"Unsupported language: {language}")
except Exception as e:
    logger.error(f"Model processing failed for language {language}: {str(e)}")
    raise RuntimeError(f"Model processing failed: {str(e)}")

# Resource cleanup with proper exception handling
try:
    async with aiohttp.ClientSession() as session:
        response = await session.post(url, json=data)
        return await response.json()
except aiohttp.ClientError as e:
    logger.error(f"HTTP request failed: {str(e)}")
    raise OrchestratorError(f"Service communication failed: {str(e)}")
finally:
    # Cleanup logic here
    pass
```

## Logging Standards

### Logger Configuration
```python
# Service-level logging setup (main.py)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("service_name.log"),
        logging.StreamHandler()
    ]
)

# Module-level logger
logger = logging.getLogger(__name__)
```

### Log Level Guidelines

```python
# DEBUG - Detailed diagnostic information
logger.debug(f"Processing skill vector for: {skill_name}")
logger.debug(f"Model embeddings shape: {embeddings.shape}")

# INFO - General operational information
logger.info("Starting Analyst service...")
logger.info(f"Initialized {len(language_models)} language models")
logger.info(f"Generated career paths for session {session_id}")

# WARNING - Recoverable issues or degraded functionality
logger.warning("Redis not available. Install redis package for distributed caching.")
logger.warning(f"Operation failed (attempt {attempt + 1}/{max_retries}), retrying...")
logger.warning("Internet time utilities not available, falling back to system time")

# ERROR - Serious problems that prevent normal operation
logger.error(f"HTTP request failed: {str(e)}")
logger.error(f"Model processing failed for language {language}: {str(e)}")
logger.error(f"Schema validation failed: {validation_error}")

# CRITICAL - Very serious errors that might cause service shutdown
logger.critical(f"Service initialization failed: {str(e)}")
logger.critical(f"Database connection lost: {str(e)}")
```

### Structured Logging Format
```python
# Include operation context and identifiers
logger.info(
    f"Career path generation completed",
    extra={
        "session_id": session_id,
        "user_id": user_id,
        "paths_generated": len(career_paths),
        "processing_time_ms": processing_time
    }
)

# Log service interactions
logger.info(
    f"Orchestrator operation: {operation_type}",
    extra={
        "operation_id": operation_id,
        "service": "strategist",
        "session_id": session_id,
        "status": "completed"
    }
)
```

## Resilience Patterns

### Retry Logic with Exponential Backoff

Implement retry logic for transient failures with exponential backoff:

```python
class AsyncOrchestratorIntegration:
    """Async orchestrator integration with error handling and retry logic."""

    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        """Initialize integration.

        Args:
            max_retries: Maximum number of retry attempts
            retry_delay: Base delay between retries in seconds
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    async def _retry_operation(self, operation, *args, **kwargs):
        """Retry operation with exponential backoff.

        Args:
            operation: Async function to retry
            *args: Operation arguments
            **kwargs: Operation keyword arguments

        Returns:
            Operation result

        Raises:
            RuntimeError: If all retry attempts fail
        """
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                return await operation(*args, **kwargs)

            except (OrchestratorError, aiohttp.ClientError) as e:
                last_error = e
                if attempt < self.max_retries:
                    # Exponential backoff: 1s, 2s, 4s, 8s...
                    delay = self.retry_delay * (2 ** attempt)
                    logger.warning(
                        f"Operation failed (attempt {attempt + 1}/{self.max_retries + 1}), "
                        f"retrying in {delay}s: {str(e)}"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Operation failed after {self.max_retries + 1} attempts")

        raise RuntimeError(
            f"Operation failed after {self.max_retries + 1} attempts. "
            f"Last error: {str(last_error)}"
        )
```

### Circuit Breaker Pattern

Implement circuit breakers to prevent cascading failures:

```python
from enum import Enum
from datetime import datetime, timedelta
import asyncio

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open" # Testing if service recovered

class CircuitBreaker:
    """Circuit breaker for service resilience."""

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: int = 60,
        recovery_timeout: int = 30
    ):
        """Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            timeout: Timeout for operations in seconds
            recovery_timeout: Time to wait before attempting recovery
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED

    async def call(self, operation, *args, **kwargs):
        """Execute operation through circuit breaker.

        Args:
            operation: Async function to execute
            *args: Operation arguments
            **kwargs: Operation keyword arguments

        Returns:
            Operation result

        Raises:
            CircuitBreakerOpenError: If circuit is open
        """
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker transitioning to HALF_OPEN")
            else:
                raise CircuitBreakerOpenError("Circuit breaker is OPEN")

        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                operation(*args, **kwargs),
                timeout=self.timeout
            )
            self._on_success()
            return result

        except Exception as e:
            self._on_failure()
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return True
        return (
            datetime.utcnow() - self.last_failure_time >
            timedelta(seconds=self.recovery_timeout)
        )

    def _on_success(self):
        """Handle successful operation."""
        self.failure_count = 0
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            logger.info("Circuit breaker reset to CLOSED")

    def _on_failure(self):
        """Handle failed operation."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()

        if (
            self.failure_count >= self.failure_threshold and
            self.state != CircuitState.OPEN
        ):
            self.state = CircuitState.OPEN
            logger.warning(
                f"Circuit breaker OPENED after {self.failure_count} failures"
            )

class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass
```

### Graceful Degradation Strategies

```python
class SkillVectorizer:
    """Skill vectorization with graceful degradation."""

    def __init__(self):
        self.primary_model = None
        self.fallback_model = None
        self.cache = {}

    async def vectorize_skills(self, skills: List[str]) -> np.ndarray:
        """Vectorize skills with graceful degradation.

        Degradation levels:
        1. Primary ML model (high accuracy)
        2. Fallback simpler model (reduced accuracy)
        3. Cached results (stale but functional)
        4. Simple keyword matching (minimal functionality)
        """
        # Level 1: Try primary model
        try:
            if self.primary_model:
                return await self._vectorize_with_primary(skills)
        except Exception as e:
            logger.warning(f"Primary model failed: {e}, trying fallback")

        # Level 2: Try fallback model
        try:
            if self.fallback_model:
                return await self._vectorize_with_fallback(skills)
        except Exception as e:
            logger.warning(f"Fallback model failed: {e}, using cache")

        # Level 3: Use cached results
        cached_result = self._get_cached_vectors(skills)
        if cached_result is not None:
            logger.info("Using cached skill vectors (degraded mode)")
            return cached_result

        # Level 4: Simple keyword matching (minimal functionality)
        logger.warning("All models failed, using simple keyword matching")
        return self._simple_keyword_vectors(skills)

    def _simple_keyword_vectors(self, skills: List[str]) -> np.ndarray:
        """Fallback to simple keyword-based vectors."""
        # Create basic one-hot encoding or simple hash-based vectors
        vectors = []
        for skill in skills:
            # Simple hash-based vector (very basic fallback)
            vector = [hash(skill.lower()) % 100 for _ in range(50)]
            vectors.append(vector)
        return np.array(vectors)
```

### Health Check and Monitoring

```python
class ServiceHealthMonitor:
    """Monitor service health and dependencies."""

    def __init__(self):
        self.dependencies = {}
        self.last_check = {}
        self.health_status = {}

    async def check_service_health(self) -> Dict[str, Any]:
        """Comprehensive health check."""
        health_report = {
            "service": "strategist",
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "dependencies": {},
            "metrics": {}
        }

        # Check critical dependencies
        for service_name, client in self.dependencies.items():
            try:
                await client.health_check()
                health_report["dependencies"][service_name] = "healthy"
            except Exception as e:
                health_report["dependencies"][service_name] = f"unhealthy: {str(e)}"
                health_report["status"] = "degraded"

        # Check internal components
        try:
            await self._check_internal_components()
            health_report["internal"] = "healthy"
        except Exception as e:
            health_report["internal"] = f"unhealthy: {str(e)}"
            health_report["status"] = "unhealthy"

        return health_report

    async def _check_internal_components(self):
        """Check internal component health."""
        # Verify models are loaded
        if not hasattr(self, 'vectorizer') or not self.vectorizer:
            raise RuntimeError("Skill vectorizer not initialized")

        # Test model functionality
        test_skills = ["python", "machine learning"]
        vectors = await self.vectorizer.vectorize(test_skills)
        if vectors is None or len(vectors) == 0:
            raise RuntimeError("Vectorizer health check failed")
```

### Testing Standards
- **pytest** for all testing
- Test coverage minimum 80%
- Test file naming: `test_{module_name}.py`
- Mock external dependencies in tests
- Use descriptive test method names: `test_should_extract_skills_from_french_resume`
- Test resilience patterns: retry logic, circuit breakers, graceful degradation

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
