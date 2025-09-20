# Contributing to HELIOS Career Operations System

Thank you for your interest in contributing to the HELIOS Career Operations System! This document provides guidelines for contributing to our AI-powered career intelligence platform.

## 📋 Quality Standards

All contributions must meet the following mandatory requirements:

### 🧪 Testing Requirements

- **Minimum Test Coverage**: 85%
- **Minimum Test Pass Rate**: 85%
- **Test Types**: Unit tests, integration tests, and end-to-end tests where applicable
- **Test Framework**: pytest with coverage reporting

### 📊 Quality Metrics

Before submitting a pull request, ensure your code meets these standards:

1. **Test Coverage**: Run `pytest --cov=src --cov-report=html` and verify coverage ≥ 85%
2. **Test Pass Rate**: All tests must pass with ≥ 85% success rate
3. **Code Quality**: Pass all linting checks (Ruff + Black)
4. **Security**: No high-severity vulnerabilities (Bandit + CodeQL)
5. **Type Safety**: Include type hints where applicable

## 🚀 Development Workflow

### 1. Setup Development Environment

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/helios-career-operations-system.git
cd helios-career-operations-system

# Create a feature branch
git checkout -b feat/your-feature-name

# Set up virtual environment (for service development)
cd services/your-service
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install pytest pytest-cov pytest-mock  # Testing dependencies
```

### 2. Development Guidelines

#### Code Style
- Follow PEP 8 standards
- Use Ruff for linting and Black for formatting
- Include comprehensive docstrings
- Add type hints for all functions and methods

#### Testing Strategy
- Write tests BEFORE implementing features (TDD approach)
- Aim for >85% code coverage
- Include both positive and negative test cases
- Mock external dependencies appropriately
- Test error handling and edge cases

#### Commit Messages
Use conventional commits format:
```
feat: add new career path generation algorithm
fix: resolve session management race condition
docs: update API documentation for analyst service
test: add integration tests for orchestrator
```

### 3. Testing Your Changes

#### Run Full Test Suite
```bash
# For individual services
cd services/your-service
pytest --cov=src --cov-report=html --cov-report=term

# For project-wide testing
python -m pytest services/ --cov=services --cov-report=html
```

#### Coverage Requirements
- Verify coverage report shows ≥ 85%
- Check `htmlcov/index.html` for detailed coverage analysis
- Ensure critical code paths are well-tested

#### Performance Testing
- Profile performance-critical code
- Ensure response times meet project targets (<2s for API calls)
- Test with realistic data volumes

### 4. Pull Request Process

#### Before Submitting
1. **Run Tests**: Ensure all tests pass with ≥ 85% coverage
2. **Code Quality**: Run linting and formatting checks
3. **Documentation**: Update relevant documentation
4. **Changelog**: Add entry to appropriate changelog
5. **Security**: Run security scans

#### Pull Request Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass with ≥85% coverage
- [ ] Tests pass with ≥85% success rate
- [ ] Manual testing completed
- [ ] Performance impact assessed

## Quality Checks
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Security implications considered
```

## 🏗️ Service Architecture

### Adding New Services

When contributing new microservices:

1. **Structure**: Follow existing service patterns in `services/`
2. **Dependencies**: Add `requirements.txt` with pinned versions
3. **Tests**: Include comprehensive test suite (`tests/` directory)
4. **Documentation**: Add service-specific README and API docs
5. **CI/CD**: Ensure service integrates with existing workflows

### Service Requirements

Each service must include:
- Health check endpoint (`/health`)
- Comprehensive logging
- Error handling and graceful degradation
- Input validation and sanitization
- API documentation (OpenAPI/Swagger)

## 🔧 Tools and Technologies

### Required Tools
- **Python 3.13+**: Primary development language
- **pytest**: Testing framework
- **pytest-cov**: Coverage reporting
- **Ruff**: Fast Python linter
- **Black**: Code formatter
- **mypy**: Static type checker

### Optional Tools
- **Docker**: For containerized development
- **pre-commit**: Git hooks for code quality
- **bandit**: Security linting

## 📚 Resources

### Project Documentation
- [Architecture Overview](docs/02-architecture/)
- [BMAD Methodology](docs/03-design/BMAD-Analysis.md)
- [API Documentation](http://localhost:8000/docs)

### External Resources
- [BMAD Method Documentation](https://github.com/bmad-code-org/BMAD-METHOD)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [pytest Documentation](https://docs.pytest.org/)

## 🐛 Bug Reports

When reporting bugs:

1. **Search**: Check existing issues first
2. **Template**: Use the bug report template
3. **Details**: Include environment, steps to reproduce, expected vs actual behavior
4. **Tests**: If possible, include a failing test case

## 💡 Feature Requests

For new features:

1. **Discussion**: Open an issue to discuss the feature first
2. **Scope**: Clearly define the feature scope and requirements
3. **Design**: Consider architectural implications
4. **Tests**: Plan testing strategy

## 🔒 Security

### Security Guidelines
- Never commit secrets or credentials
- Use environment variables for configuration
- Follow OWASP security practices
- Report security vulnerabilities privately

### Security Testing
- Run `bandit` security linting
- Include security test cases
- Test input validation thoroughly
- Consider attack vectors and edge cases

## 📄 License

By contributing, you agree that your contributions will be licensed under the project's MIT License.

## 🤝 Code of Conduct

This project follows the [Contributor Covenant](https://www.contributor-covenant.org/). Please read and follow these guidelines to ensure a welcoming environment for all contributors.

## ❓ Questions

If you have questions:

1. Check the [documentation](docs/)
2. Search [existing issues](https://github.com/fabiendostie/helios-career-operations-system/issues)
3. Open a [discussion](https://github.com/fabiendostie/helios-career-operations-system/discussions)
4. Contact the maintainers

---

**Thank you for contributing to HELIOS! 🚀**