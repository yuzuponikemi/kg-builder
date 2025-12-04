# UV Package Manager Guide

**CRITICAL**: This project **EXCLUSIVELY** uses `uv` for all Python package management and script execution.

## Table of Contents

1. [Why UV?](#why-uv)
2. [Installation](#installation)
3. [Basic Usage](#basic-usage)
4. [Common Tasks](#common-tasks)
5. [For AI Agents](#for-ai-agents)
6. [Migration from pip](#migration-from-pip)
7. [Troubleshooting](#troubleshooting)

---

## Why UV?

UV is the modern Python package manager that replaces `pip`, `pip-tools`, `virtualenv`, and more.

### Benefits

✅ **10-100x faster** than pip
✅ **Deterministic** builds with `uv.lock`
✅ **Unified** tool for package management and execution
✅ **Better dependency resolution** than pip
✅ **Built-in virtual environment** management
✅ **Full PEP 621** support (pyproject.toml)

### Performance Comparison

```
pip install:     ~30 seconds
uv sync:         ~2 seconds (15x faster)
```

---

## Installation

### Option 1: Official Installer (Recommended)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Option 2: Using pipx

```bash
pipx install uv
```

### Option 3: Using Homebrew (macOS)

```bash
brew install uv
```

### Verify Installation

```bash
uv --version
# Should output: uv 0.x.x or higher
```

---

## Basic Usage

### Installing Dependencies

```bash
# Install all dependencies (including dev)
uv sync

# Install only production dependencies
uv sync --no-dev

# Install with all optional extras
uv sync --all-extras
```

### Adding New Dependencies

```bash
# Add a production dependency
uv add requests

# Add a dev dependency
uv add --dev pytest

# Add with version constraint
uv add "fastapi>=0.109.0"
```

### Removing Dependencies

```bash
# Remove a dependency
uv remove requests
```

### Running Scripts

**CRITICAL**: Always use `uv run` to execute Python scripts and commands.

```bash
# Run a Python script
uv run python scripts/my_script.py

# Run a Python module
uv run python -m pytest

# Run an installed CLI tool
uv run black src/
uv run pytest tests/
uv run mypy src/
```

---

## Common Tasks

### Development Workflow

```bash
# 1. Clone and setup
git clone https://github.com/yourusername/kg-builder.git
cd kg-builder
uv sync

# 2. Make changes to code
vim src/kg_builder/...

# 3. Run tests
uv run pytest tests/ -v

# 4. Format code
uv run black src/

# 5. Lint code
uv run ruff check src/

# 6. Type check
uv run mypy src/
```

### Running Scripts

```bash
# Build knowledge graph
uv run python scripts/build_knowledge_graph.py "topic"

# Search and download papers
uv run python scripts/search_and_download_papers.py "topic"

# Import to Neo4j
uv run python scripts/import_to_neo4j.py data/exports/

# Export from Neo4j
uv run python scripts/export_from_neo4j.py --output backup.json
```

### Running the API Server

```bash
# Development mode with auto-reload
uv run uvicorn kg_builder.api.main:app --reload

# Production mode
uv run uvicorn kg_builder.api.main:app --host 0.0.0.0 --port 8000
```

### Running Tests

```bash
# All tests with coverage
uv run pytest tests/ -v --cov=kg_builder

# Specific test file
uv run pytest tests/test_specific.py -v

# With output
uv run pytest tests/ -v -s

# Only unit tests
uv run pytest tests/unit/ -v
```

### Code Quality

```bash
# Format code
uv run black src/

# Check formatting (without modifying)
uv run black --check src/

# Lint
uv run ruff check src/

# Lint with auto-fix
uv run ruff check --fix src/

# Type check
uv run mypy src/

# Run all pre-commit hooks
uv run pre-commit run --all-files
```

---

## For AI Agents

**MANDATORY RULES** for AI coding agents (Claude Code, Cursor, Copilot, etc.):

### ❌ NEVER DO THIS

```bash
# WRONG - Never use pip directly
pip install package
python -m pip install package

# WRONG - Never run Python without uv
python script.py
python -m module

# WRONG - Never run tools without uv
pytest tests/
black src/
mypy src/
```

### ✅ ALWAYS DO THIS

```bash
# CORRECT - Use uv for dependency management
uv add package
uv sync

# CORRECT - Use uv run for Python scripts
uv run python script.py
uv run python -m module

# CORRECT - Use uv run for all tools
uv run pytest tests/
uv run black src/
uv run mypy src/
```

### Detection Pattern

If you see any of these patterns in code or documentation:
- `pip install`
- `python script.py` (without `uv run`)
- `pytest` (without `uv run`)
- `black` (without `uv run`)

**Immediately recognize it as outdated** and use `uv` equivalents instead.

### Quick Reference Card

| Old Command | New Command |
|-------------|-------------|
| `pip install package` | `uv add package` |
| `pip install -e .` | `uv sync` |
| `pip install -e ".[dev]"` | `uv sync` |
| `python script.py` | `uv run python script.py` |
| `pytest` | `uv run pytest` |
| `black src/` | `uv run black src/` |
| `mypy src/` | `uv run mypy src/` |
| `uvicorn app:main` | `uv run uvicorn app:main` |

---

## Migration from pip

### For Developers

If you're migrating from pip:

1. **Install uv** (see [Installation](#installation))

2. **Remove old virtual environment**:
   ```bash
   rm -rf venv/
   rm -rf .venv/
   ```

3. **Install dependencies with uv**:
   ```bash
   uv sync
   ```

4. **Update your muscle memory**:
   - Replace `pip install` → `uv add`
   - Replace `python` → `uv run python`
   - Replace any tool → `uv run <tool>`

### For CI/CD

**GitHub Actions** (see `.github/workflows/build-knowledge-graph.yml`):

```yaml
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: '3.11'

- name: Set up uv
  uses: astral-sh/setup-uv@v4
  with:
    enable-cache: true
    cache-dependency-glob: "pyproject.toml"

- name: Install dependencies
  run: uv sync --all-extras

- name: Run tests
  run: uv run pytest tests/
```

---

## Troubleshooting

### UV not found

**Problem**: `command not found: uv`

**Solution**:
```bash
# Add to shell PATH (usually done automatically by installer)
export PATH="$HOME/.cargo/bin:$PATH"

# For permanent effect, add to ~/.bashrc or ~/.zshrc
echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
```

### Dependencies not installing

**Problem**: `uv sync` fails

**Solution**:
```bash
# Clear cache and retry
uv cache clean
uv sync

# Force reinstall
rm -rf .venv/
uv sync
```

### Import errors when running scripts

**Problem**: `ModuleNotFoundError` when running scripts

**Solution**:
```bash
# Make sure you're using uv run
uv run python script.py

# NOT: python script.py

# Verify dependencies are installed
uv sync
```

### Lock file conflicts

**Problem**: `uv.lock` has conflicts

**Solution**:
```bash
# Regenerate lock file
rm uv.lock
uv sync
```

---

## Advanced Usage

### Working with Multiple Python Versions

```bash
# Use specific Python version
uv venv --python 3.11
uv sync

# Use Python from pyenv
uv venv --python $(pyenv which python)
```

### Dependency Groups

```bash
# Install specific groups
uv sync --group dev
uv sync --group docs

# Install all groups
uv sync --all-groups
```

### Offline Mode

```bash
# Install from cache (no network)
uv sync --offline
```

---

## Best Practices

1. **Always commit `uv.lock`**: Ensures reproducible builds
2. **Use `uv run` for everything**: Consistency across environments
3. **Never mix pip and uv**: Stick to uv exclusively
4. **Keep uv updated**: `uv self update`
5. **Use `uv sync` after pulling**: Keep dependencies in sync

---

## Resources

- **UV Documentation**: https://docs.astral.sh/uv/
- **UV GitHub**: https://github.com/astral-sh/uv
- **This Project's Configuration**: See `pyproject.toml` and `.python-version`

---

**Remember**: UV is not just faster pip. It's a complete Python project manager. Use it for everything!
