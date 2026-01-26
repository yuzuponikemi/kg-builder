# Knowledge Graph Builder

A comprehensive system for extracting, constructing, visualizing, and analyzing knowledge graphs from research papers using Neo4j and LLMs.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/yuzuponikemi/kg-builder/actions/workflows/ci.yml/badge.svg)](https://github.com/yuzuponikemi/kg-builder/actions/workflows/ci.yml)
[![Tests](https://github.com/yuzuponikemi/kg-builder/actions/workflows/test.yml/badge.svg)](https://github.com/yuzuponikemi/kg-builder/actions/workflows/test.yml)
[![Code Quality](https://github.com/yuzuponikemi/kg-builder/actions/workflows/lint.yml/badge.svg)](https://github.com/yuzuponikemi/kg-builder/actions/workflows/lint.yml)

## Overview

KG Builder transforms scientific papers into an ontological knowledge graph using generative AI. Based on the research paper ["Accelerating Scientific Discovery with Generative Knowledge Extraction, Graph-Based Representation, and Multimodal Intelligent Graph Reasoning"](https://arxiv.org/abs/2403.11996) by Markus J. Buehler.

### Key Features

- **🔍 Knowledge Extraction**: Extract entities and relationships from research papers using LLMs (GPT-4, Claude, Llama)
- **📊 Graph Construction**: Build scale-free knowledge graphs in Neo4j with semantic embeddings
- **🧠 Graph Reasoning**: Multi-hop reasoning, community detection, and path finding
- **🎨 Visualization**: Interactive 2D/3D graph visualization with multiple layout algorithms
- **🔌 API Access**: RESTful, WebSocket, and GraphQL APIs for agent integration
- **📈 Analytics**: Centrality metrics, degree distribution, clustering, and more

## Architecture

```
Papers (PDF) → Knowledge Extraction (LLM) → Neo4j Graph DB
                                                ↓
                    ← API Layer (REST/WS/GraphQL) →
                                                ↓
                    Visualization + Analysis + Agent Integration
```

## 🚀 Ollama Setup (Local LLM - Recommended)

KG Builder works best with **Ollama** for 100% local, private knowledge graph construction with no API costs!

### Quick Ollama Setup

1. **Install Ollama** (if not already installed):
```bash
# Linux
curl -fsSL https://ollama.com/install.sh | sh

# macOS
brew install ollama

# Windows: Download from https://ollama.com/download/windows
```

2. **Pull recommended model**:
```bash
ollama pull llama3.1:8b  # Good balance of speed and quality (8GB VRAM)
# or
ollama pull mistral:7b   # Faster, lower VRAM (6GB)
```

3. **Pull embedding model**:
```bash
ollama pull nomic-embed-text
```

4. **Run automated setup**:
```bash
uv run python scripts/setup_ollama.py
# This will check your system and recommend the best models
```

✅ **That's it!** KG Builder will automatically use Ollama (no API keys needed).

📖 **For detailed setup, GPU configuration, and model recommendations**, see [docs/OLLAMA_GUIDE.md](docs/OLLAMA_GUIDE.md)

---

## ⚡ End-to-End Pipeline (Recommended!)

**Build a complete knowledge graph in ONE command** - from topic to JSON:

```bash
# Complete pipeline: Search → Filter → Download → Extract → Save JSON
uv run python scripts/build_knowledge_graph.py "knowledge graph construction"
```

**That's it!** This single command will:
1. 🔍 Search arXiv for relevant papers (prioritizing review papers)
2. 🤖 Filter papers by relevance using LLM
3. 📥 Download selected papers
4. 🧠 Extract knowledge (entities and relationships)
5. 💾 Save as JSON knowledge graphs
6. 📋 Update papers index

**Features:**
- 📚 **Prioritizes review papers** by default (established knowledge)
- 🎯 **LLM-powered quality filtering** (relevance threshold: 0.7)
- 📊 **Detailed progress tracking** for each step
- 💾 **Automatic JSON export** (individual + combined graphs)
- 🔄 **Error-resilient** (continues on failures)

**Options:**
```bash
# Get 10 papers
uv run python scripts/build_knowledge_graph.py "graph neural networks" --max-papers 10

# Only review papers (established knowledge)
uv run python scripts/build_knowledge_graph.py "materials science" --review-papers-only

# Create combined graph
uv run python scripts/build_knowledge_graph.py "transformers" --combine

# Higher quality threshold
uv run python scripts/build_knowledge_graph.py "quantum computing" --threshold 0.85
```

**📖 Complete guide with step-by-step explanation**: [Pipeline Guide (日本語)](docs/PIPELINE_GUIDE.md)

---

## 🔍 Search & Download Papers

Automatically search arXiv and download relevant papers using LLM-powered filtering:

```bash
# Search for papers and download the most relevant ones
uv run python scripts/search_and_download_papers.py "knowledge graph construction"

# Search, filter, and extract knowledge in one command
uv run python scripts/search_and_download_papers.py "neural networks" --auto-extract

# Get top 5 most relevant papers
uv run python scripts/search_and_download_papers.py "LLM reasoning" --top-n 5
```

**Features:**
- 🔍 Smart arXiv search with field-specific queries
- 🤖 LLM-powered relevance assessment
- 📥 Automatic download of relevant papers
- ⚡ Batch processing for multiple papers
- 📊 Combined knowledge graph generation

See **[Search Guide](docs/SEARCH_GUIDE.md)** for complete documentation.

---

## 📊 Neo4j Import & Export

Load JSON knowledge graphs into Neo4j for powerful querying and analysis:

```bash
# Import all knowledge graphs into Neo4j
uv run python scripts/import_to_neo4j.py data/exports/

# Explore in browser
open http://localhost:7474

# Search for concepts
uv run python scripts/neo4j_manager.py search "neural network"

# Show statistics
uv run python scripts/neo4j_manager.py stats

# Export back to JSON (for sharing/backup)
uv run python scripts/export_from_neo4j.py --output backup.json
```

**Why Use Both JSON and Neo4j?**
- **JSON**: Portable, shareable on GitHub, human-readable
- **Neo4j**: Complex queries, graph algorithms, interactive visualization

**Workflow**: Extract to JSON → Share on GitHub → Import to Neo4j → Analyze → Export back to JSON

See **[Neo4j Guide](docs/NEO4J_GUIDE.md)** for complete documentation.

---

## 🤖 GitHub Actions Automation (NEW!)

**Fully automate the entire pipeline with GitHub Actions** - no local execution needed!

```yaml
# Runs automatically every Monday at 0:00 UTC
# Or trigger manually from GitHub UI
```

**What it does:**
1. 🔍 Search arXiv for papers (with your custom topic)
2. 🤖 Filter using Gemini 2.5 Flash (fast & free tier)
3. 📥 Download and extract knowledge
4. 💾 Save JSON files
5. 🚀 Auto-commit to GitHub
6. 📦 Archive results for 90 days

**Setup (5 minutes):**
1. Get [Gemini API key](https://aistudio.google.com/app/apikey) (free)
2. Add to GitHub: Settings → Secrets → `GEMINI_API_KEY`
3. Done! Runs automatically every week

**Manual trigger from GitHub:**
- Go to Actions tab
- Select "Build Knowledge Graph"
- Click "Run workflow"
- Enter your topic and parameters

**Cost:** **100% FREE** (uses Gemini free tier + GitHub Actions free tier)

**📖 Complete setup guide**: [GitHub Actions Guide (日本語)](docs/GITHUB_ACTIONS_GUIDE.md)

---

## Quick Start

### Prerequisites

- Python 3.11+
- Neo4j 5.x
- **Ollama** (recommended) OR OpenAI/Anthropic API keys
- Redis (optional, for caching)
- Docker (recommended)

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/kg-builder.git
cd kg-builder

# Install uv (modern Python package manager)
# Option 1: Using the official installer (recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Option 2: Using pipx (alternative)
# pipx install uv

# Install dependencies with uv
uv sync

# Set up environment
cp .env.example .env
# Edit .env - Ollama is already configured as default!
# (Optional: Add OpenAI/Anthropic keys if you want to use cloud APIs)
```

### Start Services (Docker)

```bash
# Option 1: Basic services (Neo4j, Redis) - Use host Ollama (recommended)
docker-compose -f docker/docker-compose.yml up -d neo4j redis

# Option 2: All services including API
docker-compose -f docker/docker-compose.yml up -d

# Option 3: Include Ollama in Docker with GPU support
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.ollama.yml up -d

# Option 4: Include Ollama in Docker (CPU only)
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.ollama-cpu.yml up -d
```

💡 **Tip**: Using host Ollama (Option 1-2) is recommended for better performance and easier model management.

### Initialize Database

```bash
# Set up Neo4j schema and indexes
uv run python scripts/setup_neo4j.py
```

### Start API Server (Development)

```bash
uv run uvicorn kg_builder.api.main:app --reload
```

Visit http://localhost:8000/docs for interactive API documentation.

## Usage

### Python SDK

```python
from kg_builder import KGClient

# Initialize client
client = KGClient(api_url="http://localhost:8000", api_key="your_api_key")

# Add paper
paper = client.papers.add(
    pdf_path="path/to/paper.pdf",
    auto_extract=True
)

# Semantic search
concepts = client.search.semantic(
    query="machine learning for materials science",
    limit=10
)

# Find paths between concepts
paths = client.reasoning.find_paths(
    from_concept="neural networks",
    to_concept="biomaterials",
    max_hops=3
)

# Detect communities
communities = client.analytics.detect_communities(algorithm="louvain")

# Export graph
client.viz.export(format="graphml", output_path="graph.graphml")
```

### REST API

```bash
# Upload paper
curl -X POST http://localhost:8000/api/v1/papers \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "file=@paper.pdf"

# Search concepts
curl -X POST http://localhost:8000/api/v1/search/semantic \
  -H "Content-Type: application/json" \
  -d '{"query": "neural networks", "limit": 10}'

# Find paths
curl -X POST http://localhost:8000/api/v1/reasoning/path \
  -H "Content-Type: application/json" \
  -d '{"from": "concept-id-1", "to": "concept-id-2", "max_hops": 3}'
```

### WebSocket (Real-time Updates)

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/graph/updates');

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log(`New ${update.type}:`, update.data);
};
```

## Project Structure

```
kg-builder/
├── src/kg_builder/
│   ├── config/           # Configuration management
│   ├── processor/        # PDF processing and text extraction
│   ├── extractor/        # LLM-based knowledge extraction
│   ├── graph/            # Neo4j graph management
│   ├── reasoning/        # Graph reasoning and analytics
│   ├── visualization/    # Graph visualization
│   ├── api/              # FastAPI server
│   └── sdk/              # Python SDK for client integration
├── tests/                # Test suite
├── docs/                 # Documentation
├── scripts/              # Utility scripts
├── docker/               # Docker configuration
└── data/                 # Local data storage
```

## Configuration

Key environment variables (see `.env.example`):

```bash
# LLM Provider (Default: Ollama for local usage)
LLM_PROVIDER=ollama  # Options: ollama, openai, anthropic

# Ollama Configuration (Local LLM - No API keys needed!)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b  # Or mistral:7b, mixtral:8x7b, etc.
OLLAMA_NUM_GPU=1  # Set to 0 for CPU-only
EMBEDDING_PROVIDER=local  # Or ollama

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_PASSWORD=your_password

# Optional: Cloud LLM API Keys (only if not using Ollama)
OPENAI_API_KEY=  # Leave empty if using Ollama
ANTHROPIC_API_KEY=  # Leave empty if using Ollama
GEMINI_API_KEY=  # Leave empty if using Ollama (required for GitHub Actions)

# Embedding Model
EMBEDDING_MODEL=BAAI/bge-large-en-v1.5  # For local embeddings
OLLAMA_EMBEDDING_MODEL=nomic-embed-text  # For Ollama embeddings
EMBEDDING_DEVICE=cuda  # Options: cuda, cpu, mps

# API
API_PORT=8000
```

### Switching LLM Providers

Simply change `LLM_PROVIDER` in `.env`:
- `ollama` - Local, private, no costs (default for local)
- `gemini` - Google Gemini, fast, generous free tier (default for GitHub Actions)
- `openai` - Cloud, requires API key
- `anthropic` - Cloud, requires API key

## Documentation

- **[🤖 GitHub Actions Guide (日本語)](docs/GITHUB_ACTIONS_GUIDE.md)**: Automate pipeline with GitHub Actions (Japanese)
- **[⚡ Pipeline Guide (日本語)](docs/PIPELINE_GUIDE.md)**: Complete end-to-end pipeline workflow (Japanese)
- **[📘 Ollama Setup Guide](docs/OLLAMA_GUIDE.md)**: Complete guide for local LLM setup
- **[🔍 Search & Download Guide](docs/SEARCH_GUIDE.md)**: How to search arXiv and download papers with LLM filtering
- **[📊 Neo4j Integration Guide](docs/NEO4J_GUIDE.md)**: Import, query, and export knowledge graphs with Neo4j
- **[Strategic Plan](STRATEGIC_PLAN.md)**: Comprehensive project roadmap and architecture
- **[API Documentation](http://localhost:8000/docs)**: Interactive OpenAPI docs (when server is running)
- **[API Specification](docs/API_SPECIFICATION.md)**: Detailed API reference for agent integration
- **[User Guide](docs/guides/)**: Detailed usage guides
- **[Examples](docs/examples/)**: Jupyter notebooks with examples

## Agent Integration

KG Builder is designed for seamless integration with agent-based AI systems:

### Features for Agents

1. **RESTful API**: Standard HTTP endpoints for all operations
2. **WebSocket**: Real-time graph updates and streaming analytics
3. **GraphQL**: Flexible graph queries with nested relationships
4. **Python SDK**: Type-safe client library
5. **Webhooks**: Event notifications for graph changes

### Example Agent Integration

```python
# In your agent code
from kg_builder import KGClient

class ResearchAgent:
    def __init__(self):
        self.kg = KGClient(api_url="http://kg-builder:8000")

    async def discover_related_concepts(self, topic: str):
        # Semantic search
        concepts = await self.kg.search.semantic(query=topic, limit=20)

        # Find connections
        paths = []
        for concept in concepts:
            paths.extend(
                await self.kg.reasoning.find_paths(
                    from_concept=topic,
                    to_concept=concept.id,
                    max_hops=3
                )
            )

        return paths
```

## Development

### Install Development Dependencies

```bash
# Development dependencies are automatically installed with uv sync
uv sync --all-extras
```

### Run Tests

```bash
uv run pytest tests/ -v --cov=kg_builder
```

### Code Quality

```bash
# Format code
uv run black src/

# Lint
uv run ruff check src/

# Type check
uv run mypy src/
```

### Pre-commit Hooks

```bash
uv run pre-commit install
uv run pre-commit run --all-files
```

## Roadmap

See [STRATEGIC_PLAN.md](STRATEGIC_PLAN.md) for detailed development phases.

### Phase 1: Foundation (Current)
- [x] Project structure and configuration
- [ ] Neo4j schema setup
- [ ] Basic API server
- [ ] PDF extraction pipeline

### Phase 2: Knowledge Extraction
- [ ] LLM integration (OpenAI, Anthropic, Ollama)
- [ ] Entity and relationship extraction
- [ ] Embedding generation

### Phase 3: Graph Construction
- [ ] Neo4j driver and query builder
- [ ] Graph construction pipeline
- [ ] Deduplication and validation

### Phase 4: Reasoning & Analytics
- [ ] Path finding algorithms
- [ ] Community detection
- [ ] Semantic search
- [ ] Graph analytics

### Phase 5: API Development
- [ ] Complete REST API
- [ ] WebSocket support
- [ ] GraphQL endpoint
- [ ] Python SDK

### Phase 6: Visualization
- [ ] React frontend
- [ ] Interactive graph rendering
- [ ] Export functionality

## Research Foundation

This project is based on:

**Buehler, M. J.** (2024). "Accelerating Scientific Discovery with Generative Knowledge Extraction, Graph-Based Representation, and Multimodal Intelligent Graph Reasoning." *arXiv:2403.11996*.

Key methodological insights:
- Generative knowledge extraction using LLMs
- Scale-free graph representation with embeddings
- Multi-hop reasoning via path sampling
- Community detection for research clustering

Reference implementation: [github.com/lamm-mit/GraphReasoning](https://github.com/lamm-mit/GraphReasoning)

## Contributing

Contributions welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Write tests
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

MIT License - see [LICENSE](LICENSE) for details.

## Citation

If you use this software in your research, please cite:

```bibtex
@software{kg_builder,
  title = {KG Builder: Knowledge Graph Builder for Research Papers},
  author = {KG Builder Team},
  year = {2025},
  url = {https://github.com/yourusername/kg-builder}
}
```

## Acknowledgments

- Based on research by Markus J. Buehler at MIT
- Built with Neo4j, FastAPI, and modern LLMs
- Inspired by the GraphReasoning project

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/kg-builder/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/kg-builder/discussions)
- **Email**: support@kg-builder.dev

---

**Built with ❤️ for accelerating scientific discovery**
