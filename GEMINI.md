# Project Overview

This is a Python project named "kg-builder" that constructs knowledge graphs from research papers. It uses Neo4j as the graph database and leverages Large Language Models (LLMs) for knowledge extraction. The project is designed to be highly configurable, supporting various LLM providers like Ollama, OpenAI, and Anthropic.

The architecture involves processing PDF papers, extracting entities and relationships using LLMs, and then building a graph in Neo4j. The system also includes a FastAPI-based API for interaction, a Python SDK, and various scripts for tasks like downloading papers and setting up the environment.

## Building and Running

### Prerequisites

*   Python 3.11+
*   Neo4j 5.x
*   Docker (recommended)
*   An LLM provider (Ollama is recommended for local use)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd kg-builder
    ```
2.  **Install dependencies:**
    The project uses `uv` for package management.
    ```bash
    pip install uv
    uv pip install -e ".[dev]"
    ```
3.  **Set up environment:**
    Copy the example `.env.example` file to `.env` and fill in the necessary details, such as Neo4j credentials and LLM API keys if not using Ollama.
    ```bash
    cp .env.example .env
    ```

### Running the Application

1.  **Start services (Docker):**
    The project includes Docker Compose files for running Neo4j and other services.
    ```bash
    # For Neo4j and Redis
    docker-compose -f docker/docker-compose.yml up -d neo4j redis
    ```
2.  **Run the API server:**
    The API server is a FastAPI application.
    ```bash
    uvicorn kg_builder.api.main:app --reload
    ```
3.  **Initialize the database:**
    A script is provided to set up the Neo4j schema.
    ```bash
    python scripts/setup_neo4j.py
    ```
## Development Conventions

### Code Style

*   The project uses `black` for code formatting and `ruff` for linting.
*   Configuration for these tools can be found in `pyproject.toml`.

### Testing

*   Tests are located in the `tests/` directory and are run using `pytest`.
*   Run tests with the following command:
    ```bash
    pytest tests/ -v --cov=kg_builder
    ```
### Pre-commit Hooks

*   The project uses `pre-commit` to ensure code quality before committing.
*   Install the hooks with:
    ```bash
    pre-commit install
    ```
