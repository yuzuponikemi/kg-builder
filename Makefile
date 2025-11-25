.PHONY: help install install-dev compile test test-fast test-cov lint format type-check ci clean docs pre-commit setup

# Default target
help:
	@echo "🔧 KG-Builder Development Commands"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make setup         - Complete setup (install + pre-commit)"
	@echo "  make install       - Install production dependencies"
	@echo "  make install-dev   - Install development dependencies"
	@echo "  make compile       - Compile requirements.txt from requirements.in"
	@echo ""
	@echo "Testing:"
	@echo "  make test          - Run all tests with coverage"
	@echo "  make test-fast     - Run tests without slow/integration tests"
	@echo "  make test-cov      - Run tests and open coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint          - Run ruff linter (with auto-fix)"
	@echo "  make format        - Format code with ruff"
	@echo "  make type-check    - Run mypy type checker"
	@echo "  make ci            - Run all CI checks locally"
	@echo "  make pre-commit    - Run pre-commit hooks on all files"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean         - Remove build artifacts and cache"
	@echo "  make docs          - Build documentation"
	@echo ""

# Setup complete development environment
setup: install-dev
	@echo "✓ Installing pre-commit hooks..."
	pre-commit install
	@echo "✓ Setup complete!"

# Compile requirements.txt from requirements.in
compile:
	@echo "📦 Compiling requirements.txt..."
	uv pip compile requirements.in -o requirements.txt
	@echo "✓ requirements.txt updated"

# Install production dependencies
install: compile
	@echo "📦 Installing production dependencies..."
	uv pip install --system -r requirements.txt
	uv pip install --system -e .
	@echo "✓ Production dependencies installed"

# Install development dependencies
install-dev: compile
	@echo "📦 Installing development dependencies..."
	uv pip install --system -r requirements.txt
	uv pip install --system -e ".[dev]"
	@echo "✓ Development dependencies installed"

# Run all tests with coverage
test:
	@echo "🧪 Running tests with coverage..."
	python -m pytest tests/ -v --cov=kg_builder --cov-report=term-missing --cov-report=html

# Run fast tests only (exclude slow and integration tests)
test-fast:
	@echo "⚡ Running fast tests..."
	python -m pytest tests/ -v -m "not slow and not integration" --cov=kg_builder --cov-report=term-missing

# Run tests and open coverage report
test-cov: test
	@echo "📊 Opening coverage report..."
	@which open > /dev/null && open htmlcov/index.html || xdg-open htmlcov/index.html || echo "Please open htmlcov/index.html manually"

# Run ruff linter with auto-fix
lint:
	@echo "🔍 Running ruff linter..."
	ruff check . --fix
	@echo "✓ Linting complete"

# Format code with ruff
format:
	@echo "📝 Formatting code with ruff..."
	ruff format .
	@echo "✓ Formatting complete"

# Run mypy type checker
type-check:
	@echo "🔎 Running mypy type checker..."
	mypy src/kg_builder --ignore-missing-imports
	@echo "✓ Type checking complete"

# Run all CI checks locally
ci: lint format type-check test
	@echo "✅ All CI checks passed!"

# Run pre-commit hooks on all files
pre-commit:
	@echo "🔨 Running pre-commit hooks..."
	pre-commit run --all-files

# Clean build artifacts and cache
clean:
	@echo "🧹 Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "✓ Cleanup complete"

# Build documentation (if using Sphinx or MkDocs)
docs:
	@echo "📚 Building documentation..."
	@if [ -f "docs/conf.py" ]; then \
		cd docs && make html; \
	elif [ -f "mkdocs.yml" ]; then \
		mkdocs build; \
	else \
		echo "No documentation configuration found"; \
	fi

# Docker commands
.PHONY: docker-build docker-up docker-down docker-logs

docker-build:
	@echo "🐳 Building Docker images..."
	docker-compose -f docker/docker-compose.yml build

docker-up:
	@echo "🐳 Starting Docker services..."
	docker-compose -f docker/docker-compose.yml up -d

docker-down:
	@echo "🐳 Stopping Docker services..."
	docker-compose -f docker/docker-compose.yml down

docker-logs:
	@echo "📋 Showing Docker logs..."
	docker-compose -f docker/docker-compose.yml logs -f

# Neo4j specific commands
.PHONY: neo4j-setup neo4j-start neo4j-stop neo4j-status

neo4j-start:
	@echo "🗄️  Starting Neo4j..."
	docker-compose -f docker/docker-compose.yml up -d neo4j redis
	@echo "✓ Neo4j started on bolt://localhost:7687"

neo4j-stop:
	@echo "🗄️  Stopping Neo4j..."
	docker-compose -f docker/docker-compose.yml stop neo4j redis

neo4j-setup:
	@echo "🗄️  Setting up Neo4j schema..."
	python scripts/setup_neo4j.py
	@echo "✓ Neo4j schema initialized"

neo4j-status:
	@echo "🗄️  Neo4j status..."
	docker-compose -f docker/docker-compose.yml ps neo4j

# Pipeline commands
.PHONY: pipeline-test

pipeline-test:
	@echo "🚀 Running test pipeline..."
	python scripts/build_knowledge_graph.py "knowledge graph construction" --max-papers 2 --threshold 0.8
