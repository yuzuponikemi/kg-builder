# Contributing to KG-Builder

Thank you for your interest in contributing to KG-Builder! This document provides guidelines and instructions for contributing.

## 🚀 Quick Start

### 1. Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/yuzuponikemi/kg-builder.git
cd kg-builder

# Install dependencies
make setup

# Start Neo4j (required for testing)
make neo4j-start
```

### 2. Create a Branch

```bash
# For bug fixes
git checkout -b fix/issue-description

# For features
git checkout -b feature/feature-name

# For Claude Code automation
git checkout -b claude/task-description
```

### 3. Make Changes

Follow our [Code Style](#code-style) and [Testing](#testing) guidelines.

### 4. Run CI Checks

```bash
# Run all CI checks locally
make ci

# Or run individually:
make lint        # Ruff linter
make format      # Code formatting
make type-check  # Mypy type checking
make test        # Pytest
```

### 5. Commit and Push

```bash
git add .
git commit -m "Your descriptive commit message"
git push origin your-branch-name
```

### 6. Create Pull Request

Open a PR on GitHub. The PR template will guide you through the required information.

---

## 📋 Development Workflow

### Code Style

We use several tools to maintain code quality:

- **Ruff**: Linting and formatting (replaces black, isort, flake8)
- **Mypy**: Static type checking
- **Pre-commit**: Git hooks for automatic checks

#### Running Code Quality Tools

```bash
# Format code
make format

# Lint code
make lint

# Type check
make type-check

# Run pre-commit on all files
make pre-commit
```

#### Code Style Guidelines

1. **Line Length**: Maximum 100 characters
2. **Type Hints**: Required for all functions (except tests)
3. **Docstrings**: Google-style docstrings for public APIs
4. **Imports**: Organized by ruff (automatic)

Example:

```python
def extract_entities(text: str, model: str = "llama3.1:8b") -> list[dict]:
    """Extract entities from scientific text using LLM.

    Args:
        text: Input text to extract entities from
        model: LLM model to use for extraction

    Returns:
        List of extracted entities with type, name, and confidence

    Raises:
        ValueError: If text is empty or model is not available
    """
    pass
```

### Testing

We follow Test-Driven Development (TDD) principles:

#### Writing Tests

1. **Test Organization**:
   ```
   tests/
   ├── conftest.py          # Shared fixtures
   ├── test_config.py       # Configuration tests
   ├── test_extractor.py    # Extraction tests
   └── test_graph.py        # Graph tests
   ```

2. **Test Naming**:
   ```python
   def test_function_name_scenario():
       """Test that function_name does X when Y."""
       pass
   ```

3. **Fixtures**: Use pytest fixtures from `conftest.py`

4. **Markers**: Use appropriate markers
   ```python
   @pytest.mark.slow           # Slow tests
   @pytest.mark.integration    # Integration tests
   @pytest.mark.requires_neo4j # Requires Neo4j
   @pytest.mark.requires_llm   # Requires LLM API
   ```

#### Running Tests

```bash
# All tests with coverage
make test

# Fast tests only (no slow/integration)
make test-fast

# Specific test file
pytest tests/test_config.py -v

# Specific test
pytest tests/test_config.py::test_settings_default_values -v

# With coverage report
make test-cov
```

#### Test Coverage

- Aim for >80% coverage for new code
- Critical paths should have 100% coverage
- Use `# pragma: no cover` sparingly

### Pre-commit Hooks

Pre-commit hooks run automatically before each commit:

```bash
# Install hooks (done by make setup)
pre-commit install

# Run manually
pre-commit run --all-files

# Update hooks
pre-commit autoupdate
```

---

## 🏗️ Architecture Guidelines

### Project Structure

```
src/kg_builder/
├── config/           # Settings and configuration
├── processor/        # PDF processing
├── extractor/        # Knowledge extraction
├── graph/            # Neo4j integration
├── search/           # ArXiv search
├── api/              # FastAPI server
└── reasoning/        # Graph reasoning
```

### Design Principles

1. **Modularity**: Each component should be independent
2. **Type Safety**: Use type hints everywhere
3. **Error Handling**: Explicit error handling with retries
4. **Configuration**: Use `Settings` from `config/settings.py`
5. **LLM Agnostic**: Support multiple LLM providers

### LLM Integration Pattern

Always use the unified `LLMClient`:

```python
from kg_builder.extractor.llm_client import get_llm_client

llm = get_llm_client()
response = llm.generate(
    prompt="...",
    response_format="json",
    temperature=0.0
)
result = llm.extract_json(response)
```

### Configuration Pattern

```python
from kg_builder.config import get_settings

settings = get_settings()
# Access: settings.neo4j_uri, settings.ollama_model, etc.
```

---

## 🐛 Reporting Bugs

Use the [Bug Report template](.github/ISSUE_TEMPLATE/bug_report.yml) and include:

1. Clear description
2. Steps to reproduce
3. Expected vs actual behavior
4. Environment details
5. Error logs

## ✨ Requesting Features

Use the [Feature Request template](.github/ISSUE_TEMPLATE/feature_request.yml) and include:

1. Problem statement
2. Proposed solution
3. Use case
4. Examples

## 🤖 Claude Code Tasks

For automated tasks, use the [Claude Task template](.github/ISSUE_TEMPLATE/claude_task.yml):

1. Describe the task clearly
2. Provide relevant files and context
3. Define acceptance criteria
4. Review Claude's work

---

## 🔄 Pull Request Process

### Before Submitting

1. ✅ Run `make ci` - all checks pass
2. ✅ Add/update tests
3. ✅ Update documentation
4. ✅ Follow code style
5. ✅ Write clear commit messages

### PR Review Process

1. **Automated Checks**: CI must pass
2. **Code Review**: At least one approval required
3. **Testing**: Manual testing if needed
4. **Documentation**: Docs updated if needed

### Commit Message Guidelines

Follow conventional commits:

```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance

Examples:
```
feat(extractor): add support for Gemini LLM
fix(graph): handle duplicate entity names
docs(readme): update installation instructions
test(config): add settings validation tests
```

---

## 📚 Documentation

### Code Documentation

- **Docstrings**: Google-style for all public functions/classes
- **Type Hints**: Required everywhere (except tests)
- **Comments**: For complex logic only

### Project Documentation

Located in `docs/`:
- `CLAUDE.md`: Developer guide
- `PIPELINE_GUIDE.md`: Pipeline usage
- `NEO4J_GUIDE.md`: Neo4j integration
- `PYTHON_UV_TEMPLATE_ARCHITECTURE.md`: Infrastructure reference

---

## 🆘 Getting Help

- **Documentation**: Check the [README](README.md) and `docs/` folder
- **Discussions**: Ask questions in GitHub Discussions
- **Issues**: Search existing issues first
- **Claude**: Use the Claude Task template for automated help

---

## 📜 Code of Conduct

### Our Standards

- Be respectful and inclusive
- Focus on constructive feedback
- Accept criticism gracefully
- Prioritize community well-being

### Enforcement

Violations can be reported to project maintainers. All complaints will be reviewed and investigated.

---

## 🙏 Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes
- GitHub contributors page

Thank you for contributing to KG-Builder! 🎉
