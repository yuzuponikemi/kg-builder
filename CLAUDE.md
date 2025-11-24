# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

KG Builder transforms scientific papers into an ontological knowledge graph using generative AI. It extracts entities and relationships from research papers using LLMs (Ollama, OpenAI, Anthropic, or Gemini), builds a graph in Neo4j with semantic embeddings, and provides APIs for graph reasoning and visualization.

Based on the paper ["Accelerating Scientific Discovery with Generative Knowledge Extraction, Graph-Based Representation, and Multimodal Intelligent Graph Reasoning"](https://arxiv.org/abs/2403.11996) by Markus J. Buehler.

## Development Setup

### Installation

```bash
# Install dependencies with uv (preferred package manager)
pip install uv
uv pip install -e ".[dev]"

# Set up environment
cp .env.example .env
# Edit .env with required settings (Neo4j password is required)
```

### Start Services

```bash
# Option 1: Basic services (Neo4j, Redis) - Use host Ollama (recommended)
docker-compose -f docker/docker-compose.yml up -d neo4j redis

# Option 2: All services including API
docker-compose -f docker/docker-compose.yml up -d

# Initialize database schema
python scripts/setup_neo4j.py

# Start API server (development)
uvicorn kg_builder.api.main:app --reload
```

## Testing

```bash
# Run all tests with coverage
pytest tests/ -v --cov=kg_builder

# Run specific test file
pytest tests/test_specific.py -v

# Run tests with output
pytest tests/ -v -s
```

## Code Quality

```bash
# Format code (always run before committing)
black src/

# Lint code
ruff check src/

# Type check
mypy src/

# Run all pre-commit hooks
pre-commit run --all-files
```

## Architecture

### Core Components

**1. Knowledge Extraction Pipeline** (`src/kg_builder/extractor/`)
- `llm_client.py`: Unified LLM client supporting Ollama, OpenAI, and Anthropic
- `entity_extractor.py`: Extracts scientific entities (methods, materials, phenomena, theories, measurements, applications) from text chunks
- `relation_extractor.py`: Extracts relationships between entities
- Uses prompt templates from `prompts/` directory
- All extraction methods use `response_format="json"` for structured output

**2. PDF Processing** (`src/kg_builder/processor/`)
- `pdf_extractor.py`: Extracts text, metadata, and sections from PDFs using pdfplumber
- Supports chunking with overlap for processing large documents
- Can extract by sections (Abstract, Introduction, Methods, Results, etc.)

**3. Search Integration** (`src/kg_builder/search/`)
- `arxiv_search.py`: ArXiv API integration for paper discovery
- `llm_filter.py`: LLM-powered relevance filtering for search results
- Supports field-specific queries, category filtering, date ranges

**4. Graph Management** (`src/kg_builder/graph/`)
- Neo4j integration for graph storage and querying
- Scale-free graph representation with semantic embeddings
- Deduplication and validation

**5. Hypothesis Generation & Reasoning** (`src/kg_builder/reasoning/`)
- `graph_analytics.py`: Graph analytics (centrality analysis, community detection)
- `link_predictor.py`: Link prediction using similarity metrics
- `hypothesis_generator.py`: LLM-based hypothesis generation from predicted links
- `hypothesis_engine.py`: Orchestrates analysis, prediction, and generation
- `recursive_alchemist.py`: Multi-layered hypothesis expansion for SF-level exploration
- Discovers "unexplored territories" in knowledge graphs
- Generates novel research hypotheses by combining unconnected but structurally similar concepts
- Recursive exploration: hypotheses become new concepts for further hypothesis generation

**6. Configuration** (`src/kg_builder/config/`)
- `settings.py`: Pydantic settings model loaded from environment variables
- Supports multiple LLM providers via `llm_provider` setting
- Get settings: `from kg_builder.config import get_settings; settings = get_settings()`

### LLM Provider Architecture

The system is designed to be LLM-agnostic:

- **Default (Local)**: Ollama (local, private, no API costs)
- **Default (GitHub Actions)**: Gemini (fast, generous free tier)
- **Alternatives**: OpenAI, Anthropic
- **Configuration**: Set `LLM_PROVIDER` in `.env` (ollama/openai/anthropic/gemini)
- **Client Pattern**: Always use `get_llm_client()` to get the appropriate client

When working with LLM code:
- Use the unified `LLMClient` class, never hardcode provider-specific APIs
- Always specify `response_format="json"` when expecting structured output
- Use `llm.extract_json(response)` to safely parse JSON responses (handles markdown code blocks)
- Default temperature is 0.0 for deterministic extraction

### Data Flow

```
PDF → PDFExtractor → text chunks
                       ↓
              EntityExtractor (LLM) → entities
              RelationExtractor (LLM) → relationships
                       ↓
              Neo4j Graph (nodes + edges + embeddings)
                       ↓
              API Layer (REST/WebSocket/GraphQL)
```

### Configuration Management

Settings are loaded via Pydantic from `.env`:

```python
from kg_builder.config import get_settings

settings = get_settings()
# Access: settings.neo4j_uri, settings.ollama_model, etc.
```

Key configuration properties:
- `settings.is_using_ollama` - Check if using Ollama
- `settings.has_openai` - Check if OpenAI is configured
- `settings.current_llm_model` - Get active model based on provider
- `settings.neo4j_config` - Neo4j connection dict
- `settings.ollama_config` - Ollama configuration dict

## Common Development Tasks

### End-to-End Pipeline (Most Common)

**Recommended for building knowledge graphs from a topic:**

```bash
# Complete pipeline: Search → Filter → Download → Extract → Save JSON
python scripts/build_knowledge_graph.py "knowledge graph construction"

# With options
python scripts/build_knowledge_graph.py "graph neural networks" \
  --max-papers 10 \
  --review-papers-only \
  --combine \
  --threshold 0.8
```

This single script performs all steps:
1. Search arXiv (prioritizing review papers)
2. Filter by relevance (LLM-powered)
3. Download PDFs
4. Extract knowledge (entities + relationships)
5. Save as JSON
6. Update papers index

See `docs/PIPELINE_GUIDE.md` for detailed documentation (Japanese).

### Search and Download Papers

```bash
# Search arXiv and download relevant papers using LLM filtering
python scripts/search_and_download_papers.py "knowledge graph construction"

# With options
python scripts/search_and_download_papers.py "neural networks" \
  --max-results 20 \
  --threshold 0.6 \
  --top-n 5 \
  --auto-extract

# Search by category
python scripts/search_and_download_papers.py "recent advances" \
  --category cs.AI \
  --recent-days 30
```

### Extract Knowledge from Papers

```bash
# Process single paper
python examples/ingest_paper.py data/papers/paper.pdf

# Batch process multiple papers
python scripts/batch_extract_papers.py data/papers/
```

### Setup Ollama (Local LLM)

```bash
# Run automated setup script
python scripts/setup_ollama.py

# Or manually:
ollama pull llama3.1:8b  # Recommended model
ollama pull nomic-embed-text  # For embeddings
```

### Neo4j Import/Export

```bash
# Import JSON knowledge graphs to Neo4j
python scripts/import_to_neo4j.py data/exports/

# Import single file
python scripts/import_to_neo4j.py data/exports/paper_knowledge_graph.json

# Clear database and import
python scripts/import_to_neo4j.py data/exports/ --clear

# Export from Neo4j to JSON
python scripts/export_from_neo4j.py --output backup.json

# Export specific paper
python scripts/export_from_neo4j.py --paper "2403_11996" --output paper.json

# Database management
python scripts/neo4j_manager.py stats           # Show statistics
python scripts/neo4j_manager.py search "neural" # Search concepts
python scripts/neo4j_manager.py concept "GNN"   # Show concept details
python scripts/neo4j_manager.py papers          # List all papers
```

**Why both JSON and Neo4j?**
- JSON: Portable, shareable on GitHub, human-readable
- Neo4j: Complex queries, graph algorithms, fast traversal

See `docs/NEO4J_GUIDE.md` for complete documentation.

### Hypothesis Generation (NEW)

Generate novel research hypotheses from the knowledge graph:

```bash
# Basic usage
python scripts/generate_hypotheses.py

# Cross-domain hypotheses (different concept types)
python scripts/generate_hypotheses.py --cross-domain --max-hypotheses 20

# High-quality hypotheses with specific thresholds
python scripts/generate_hypotheses.py \
  --method adamic_adar \
  --min-novelty 0.7 \
  --min-impact 0.8 \
  --temperature 0.8

# Focus on central concepts
python scripts/generate_hypotheses.py \
  --method jaccard \
  --top-n 100 \
  --max-hypotheses 30

# More creative hypotheses
python scripts/generate_hypotheses.py --temperature 0.9
```

**Key Options:**
- `--method`: Similarity method (jaccard, adamic_adar, resource_allocation, common_neighbors, preferential_attachment)
- `--cross-domain`: Only cross-domain links (method + theory, etc.)
- `--max-hypotheses`: Limit number of hypotheses
- `--temperature`: Creativity level (0.3=conservative, 0.9=creative)
- `--min-novelty/feasibility/impact`: Quality filters (0.0-1.0)

**Output**: JSON file in `data/hypotheses/` with:
- Hypothesis title, rationale, research direction
- Novelty/feasibility/impact scores
- Predicted links with similarity scores
- Graph analytics (centrality, communities)

See `docs/HYPOTHESIS_GENERATION.md` for complete documentation.

### Recursive Hypothesis Exploration (SF-Level) (NEW)

Generate multi-layered hypothesis expansions for SF-prototype imagination:

```bash
# Basic recursive exploration
python scripts/explore_hypotheses_recursive.py

# Deep exploration (3 layers, 3 branches per layer)
python scripts/explore_hypotheses_recursive.py \
  --max-depth 3 \
  --branches-per-layer 3 \
  --hypotheses-per-layer 15

# SF-level creative exploration
python scripts/explore_hypotheses_recursive.py \
  --max-depth 4 \
  --temperature 0.95 \
  --branching-criteria novelty
```

**Concept**: Hypotheses become new concepts → generate new hypotheses → repeat.
Creates a multi-dimensional exploration tree with branches like:
- Layer 0: Original KG
- Layer 1: "Quantum + Biology", "AI + Materials"
- Layer 2: "Quantum-Bio City Design", "AI-Enhanced Metamaterials"
- Layer 3: "Self-Organizing Quantum Urban Organism" (SF territory!)

**Branching Criteria**:
- `diversity`: Branch by concept type combinations
- `impact`: Branch by high/medium/low impact
- `novelty`: Branch by innovation level
- `feasibility`: Branch by short/mid/long-term realizability

**Output**: Multi-layered JSON tree in `data/hypotheses/exploration_tree_*.json`

See `docs/RECURSIVE_HYPOTHESIS_EXPLORATION.md` for complete documentation.

## Important Patterns

### Entity Types

Valid entity types (defined in `entity_extractor.py:94`):
- `method` - Techniques, algorithms, approaches
- `material` - Physical materials, compounds
- `phenomenon` - Observable effects, behaviors
- `theory` - Theoretical frameworks, models
- `measurement` - Metrics, measurements, properties
- `application` - Use cases, applications

### Entity Structure

Extracted entities must have:
```python
{
    "name": str,  # Entity name (non-empty)
    "type": str,  # One of valid types above
    "description": str,  # Description
    "confidence": float  # 0.0-1.0
}
```

### Text Chunking

When processing long documents:
- Default chunk size: 2000 characters
- Default overlap: 200 characters
- PDFExtractor automatically chunks via `extract_chunks()`
- Entity extraction truncates at 6000 chars to fit context windows

### Error Handling in Extraction

Entity/relation extraction includes retry logic:
- Default: 2 retries (`max_retries=2`)
- JSON parsing handles markdown code blocks automatically
- Failed extractions return empty list, never crash
- Always validate entity structure before adding to results

## Project Structure

```
src/kg_builder/
├── config/           # Settings and configuration (Pydantic models)
├── processor/        # PDF processing and text extraction
├── extractor/        # LLM-based knowledge extraction
│   └── prompts/      # Prompt templates for extraction
├── search/           # ArXiv search and LLM filtering
├── graph/            # Neo4j graph management
├── reasoning/        # Graph reasoning, analytics, and hypothesis generation
│   ├── graph_analytics.py      # Centrality, community detection
│   ├── link_predictor.py       # Link prediction algorithms
│   ├── hypothesis_generator.py # LLM-based hypothesis generation
│   ├── hypothesis_engine.py    # Main orchestrator
│   └── prompts/                # Hypothesis generation prompts
├── visualization/    # Graph visualization
├── api/              # FastAPI server
└── sdk/              # Python client SDK (stub)

scripts/              # Utility scripts
├── search_and_download_papers.py    # Main paper acquisition workflow
├── batch_extract_papers.py          # Batch processing
├── generate_hypotheses.py           # Hypothesis generation from KG
├── explore_hypotheses_recursive.py  # Recursive multi-layer exploration
├── setup_ollama.py                  # Ollama setup helper
└── setup_neo4j.py                   # Database initialization

data/
├── papers/           # Downloaded PDFs
├── embeddings/       # Cached embeddings
├── exports/          # Graph exports (JSON)
└── hypotheses/       # Generated research hypotheses
```

## Key Dependencies

- **Neo4j** (5.x): Graph database - must be running
- **Ollama** (recommended): Local LLM server for knowledge extraction
- **NetworkX**: Graph algorithms (centrality, link prediction)
- **python-louvain**: Community detection (Louvain method)
- **FastAPI**: API framework
- **Pydantic**: Settings and validation
- **pdfplumber**: PDF text extraction (preferred over PyPDF2)
- **httpx**: Async HTTP client for arXiv API
- **feedparser**: Parse arXiv RSS feeds

## Environment Variables

Required:
- `NEO4J_PASSWORD` - Neo4j database password

Important:
- `LLM_PROVIDER` - llm provider (ollama/openai/anthropic), default: ollama
- `OLLAMA_MODEL` - Model to use, default: llama3.1:8b
- `EMBEDDING_PROVIDER` - Embedding provider (local/openai/ollama), default: local

Optional (for cloud APIs):
- `OPENAI_API_KEY` - Only needed if using OpenAI
- `ANTHROPIC_API_KEY` - Only needed if using Anthropic

See `.env.example` for all available settings.

## Special Notes

### When Adding New Entity Types

1. Update valid_types list in `entity_extractor.py` (line 94)
2. Update prompt template in `prompts/entity_extraction.txt`
3. Update any validation logic

### When Adding New LLM Providers

1. Add provider to `llm_provider` Literal in `settings.py`
2. Add initialization in `LLMClient.__init__` (llm_client.py)
3. Implement `_generate_<provider>` method
4. Add configuration properties to Settings

### Ollama Configuration

Ollama settings in `.env`:
- `OLLAMA_NUM_GPU` - Number of GPUs (0 for CPU-only)
- `OLLAMA_NUM_CTX` - Context window size (default: 8192)
- `OLLAMA_NUM_THREAD` - CPU threads when using CPU
- Always connects to `http://localhost:11434` by default

### Testing Against Neo4j

Tests requiring Neo4j should:
- Check if Neo4j is available before running
- Use test database or fixtures
- Clean up data after tests
