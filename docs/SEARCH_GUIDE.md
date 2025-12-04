

# arXiv Search & Download Guide

Complete guide for searching, filtering, and downloading research papers using LLM-powered relevance assessment.

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Search Examples](#search-examples)
4. [LLM Filtering](#llm-filtering)
5. [Batch Processing](#batch-processing)
6. [Advanced Usage](#advanced-usage)
7. [Tips & Best Practices](#tips--best-practices)

---

## Overview

KG Builder includes powerful tools to:
- **Search arXiv** for papers matching your research interests
- **Use LLM** (Ollama) to assess relevance of each paper
- **Automatically download** only the most relevant papers
- **Batch process** multiple papers to build comprehensive knowledge graphs

### Workflow

```
User Query → arXiv Search → LLM Filtering → Download PDFs → Extract Knowledge
```

---

## Quick Start

### 1. Simple Search

Search for papers and download the most relevant ones:

```bash
uv run python scripts/search_and_download_papers.py "knowledge graph construction"
```

This will:
1. Search arXiv for papers about "knowledge graph construction"
2. Use your LLM (Ollama) to assess each paper's relevance
3. Download papers with relevance score ≥ 0.6 (configurable)
4. Save PDFs to `data/papers/`

### 2. Extract Knowledge

After downloading, extract knowledge graphs:

```bash
# Single paper
python examples/ingest_paper.py data/papers/paper_name.pdf

# All papers in directory
uv run python scripts/batch_extract_papers.py
```

### 3. One-Line Search & Extract

Search, download, and extract in one command:

```bash
uv run python scripts/search_and_download_papers.py "neural networks" --auto-extract
```

---

## Search Examples

### Basic Keyword Search

```bash
# Simple query
uv run python scripts/search_and_download_papers.py "machine learning"

# Multi-word query
uv run python scripts/search_and_download_papers.py "deep learning for materials science"
```

### Field-Specific Search

Use arXiv search syntax for precise queries:

```bash
# Title contains "neural"
uv run python scripts/search_and_download_papers.py "ti:neural"

# Author search
uv run python scripts/search_and_download_papers.py "au:Buehler"

# Abstract contains specific terms
uv run python scripts/search_and_download_papers.py "abs:knowledge AND abs:graph"

# Combine fields
uv run python scripts/search_and_download_papers.py "ti:neural AND cat:cs.AI"
```

### Category-Based Search

Search within specific arXiv categories:

```bash
# Computer Science - AI
uv run python scripts/search_and_download_papers.py "reasoning" --category cs.AI

# Physics - Computational Physics
uv run python scripts/search_and_download_papers.py "simulation" --category physics.comp-ph

# Quantitative Biology
uv run python scripts/search_and_download_papers.py "protein" --category q-bio.BM
```

### Time-Based Search

Get recent papers:

```bash
# Papers from last 7 days
uv run python scripts/search_and_download_papers.py "LLM" --recent-days 7

# Papers from last 30 days in specific category
uv run python scripts/search_and_download_papers.py "quantum" --category quant-ph --recent-days 30
```

### Control Number of Results

```bash
# Get more search results
uv run python scripts/search_and_download_papers.py "transformers" --max-results 20

# Get top 5 most relevant (regardless of threshold)
uv run python scripts/search_and_download_papers.py "graph neural networks" --top-n 5
```

---

## LLM Filtering

The LLM analyzes each paper's title, abstract, and metadata to assess relevance.

### How It Works

For each paper, the LLM:
1. Reads the title, authors, abstract, and categories
2. Compares to your research query
3. Assigns a relevance score (0.0 to 1.0)
4. Provides reasoning for the score

### Adjust Threshold

Control how selective the filter is:

```bash
# Strict (only highly relevant papers)
uv run python scripts/search_and_download_papers.py "neural networks" --threshold 0.8

# Balanced (default)
uv run python scripts/search_and_download_papers.py "neural networks" --threshold 0.6

# Permissive (cast a wide net)
uv run python scripts/search_and_download_papers.py "neural networks" --threshold 0.4
```

### Skip LLM Filtering

Download all search results without filtering:

```bash
uv run python scripts/search_and_download_papers.py "quantum" --no-filter
```

### Example LLM Output

```
[3/10] Assessing: 2403.11996
  ✓ Score: 0.92 - This paper directly addresses knowledge graph construction
    using generative AI, which is highly relevant to the query about knowledge
    graph methods.

[4/10] Assessing: 2301.00123
  ✗ Score: 0.45 - While this paper mentions graphs, it focuses on social network
    analysis rather than knowledge graphs, making it less relevant.
```

---

## Batch Processing

Process multiple papers at once to build comprehensive knowledge graphs.

### Process All Downloaded Papers

```bash
# Extract from all PDFs in data/papers/
uv run python scripts/batch_extract_papers.py

# Combine into unified graph
uv run python scripts/batch_extract_papers.py --combine
```

### Custom Directory

```bash
# Process papers in specific directory
uv run python scripts/batch_extract_papers.py path/to/papers/

# Custom output location
uv run python scripts/batch_extract_papers.py --output-dir results/
```

### Control Processing Depth

```bash
# Quick processing (3 chunks per paper)
uv run python scripts/batch_extract_papers.py --max-chunks 3

# Complete extraction (all chunks)
uv run python scripts/batch_extract_papers.py --max-chunks 999
```

### Output

Individual graphs:
```
data/exports/
├── paper1_knowledge_graph.json
├── paper2_knowledge_graph.json
└── paper3_knowledge_graph.json
```

Combined graph (with `--combine`):
```
data/exports/
└── combined_knowledge_graph.json
```

---

## Advanced Usage

### Complete Workflow Example

Build a knowledge graph on a specific topic:

```bash
# 1. Search and download papers
uv run python scripts/search_and_download_papers.py \
  "graph neural networks for molecular property prediction" \
  --max-results 15 \
  --threshold 0.7 \
  --category cs.LG

# 2. Batch extract knowledge
uv run python scripts/batch_extract_papers.py --combine

# 3. Result: Combined knowledge graph in data/exports/combined_knowledge_graph.json
```

### Multi-Topic Search

Build knowledge graphs across multiple topics:

```bash
# Search topic 1
uv run python scripts/search_and_download_papers.py "transformers attention mechanism" \
  --output-dir data/papers/transformers/ --top-n 5

# Search topic 2
uv run python scripts/search_and_download_papers.py "graph convolutional networks" \
  --output-dir data/papers/gcn/ --top-n 5

# Process separately
uv run python scripts/batch_extract_papers.py data/papers/transformers/ --combine
uv run python scripts/batch_extract_papers.py data/papers/gcn/ --combine
```

### Sort Options

```bash
# Most recent papers first
uv run python scripts/search_and_download_papers.py "LLM agents" \
  --sort-by submittedDate

# Recently updated papers
uv run python scripts/search_and_download_papers.py "diffusion models" \
  --sort-by lastUpdatedDate

# Most relevant (default)
uv run python scripts/search_and_download_papers.py "knowledge graphs" \
  --sort-by relevance
```

---

## Tips & Best Practices

### 1. Start Specific, Broaden if Needed

```bash
# Start specific
uv run python scripts/search_and_download_papers.py "graph transformers for molecules" --threshold 0.7

# If too few results, broaden
uv run python scripts/search_and_download_papers.py "graph transformers" --threshold 0.6
```

### 2. Use Categories for Precision

```bash
# Instead of this
uv run python scripts/search_and_download_papers.py "neural networks"

# Do this for better results
uv run python scripts/search_and_download_papers.py "neural networks" --category cs.LG
```

### 3. Recent Papers for Current Research

```bash
# Get latest papers from last week
uv run python scripts/search_and_download_papers.py "LLM reasoning" \
  --recent-days 7 \
  --sort-by submittedDate
```

### 4. Combine Top-N with Threshold

```bash
# Get top 10 papers, but ensure minimum quality
uv run python scripts/search_and_download_papers.py "quantum computing" \
  --max-results 30 \
  --top-n 10 \
  --threshold 0.5
```

### 5. Save Search Metadata

The script automatically saves a summary:
```
data/papers/search_results_<query>.txt
```

This includes:
- Search query
- All paper metadata
- Abstracts
- Download locations

### 6. Monitor LLM Performance

The LLM shows its reasoning for each assessment:
```
[5/10] Assessing: 2310.12345
  ✓ Score: 0.87 - This paper presents novel methods for knowledge graph
    construction using LLMs, directly addressing the query.
```

Use this to:
- Verify the LLM is assessing correctly
- Adjust threshold based on score distribution
- Improve your query if needed

### 7. Batch Processing Strategy

For large collections:

```bash
# Step 1: Download papers
uv run python scripts/search_and_download_papers.py "topic" \
  --max-results 50 \
  --threshold 0.6

# Step 2: Quick pass (3 chunks each)
uv run python scripts/batch_extract_papers.py --max-chunks 3

# Step 3: Review results, then full extraction on best papers
uv run python scripts/batch_extract_papers.py --max-chunks 999
```

---

## Common Queries by Field

### Computer Science

```bash
# AI/ML
uv run python scripts/search_and_download_papers.py "transformers" --category cs.AI

# Computer Vision
uv run python scripts/search_and_download_papers.py "object detection" --category cs.CV

# NLP
uv run python scripts/search_and_download_papers.py "language models" --category cs.CL

# Robotics
uv run python scripts/search_and_download_papers.py "robot learning" --category cs.RO
```

### Physics

```bash
# Quantum Physics
uv run python scripts/search_and_download_papers.py "quantum entanglement" --category quant-ph

# Condensed Matter
uv run python scripts/search_and_download_papers.py "superconductivity" --category cond-mat

# Computational Physics
uv run python scripts/search_and_download_papers.py "molecular dynamics" --category physics.comp-ph
```

### Biology

```bash
# Bioinformatics
uv run python scripts/search_and_download_papers.py "protein folding" --category q-bio.BM

# Genomics
uv run python scripts/search_and_download_papers.py "gene expression" --category q-bio.GN
```

### Mathematics

```bash
# Optimization
uv run python scripts/search_and_download_papers.py "convex optimization" --category math.OC

# Statistics
uv run python scripts/search_and_download_papers.py "bayesian inference" --category stat.ML
```

---

## Troubleshooting

### "No papers found"

**Try:**
- Broader query: "neural" instead of "neural networks for graph classification"
- Different category: `--category cs.LG` instead of `cs.AI`
- More results: `--max-results 20`

### "No relevant papers after filtering"

**Try:**
- Lower threshold: `--threshold 0.4`
- Skip filtering temporarily: `--no-filter`
- Broader query

### "LLM timeout or errors"

**Try:**
- Ensure Ollama is running: `ollama list`
- Use faster model: `OLLAMA_MODEL=mistral:7b` in `.env`
- Increase timeout in settings

### "Download failed (403 Forbidden)"

- arXiv may be rate-limiting
- Script includes 3-second delay between downloads
- Wait a few minutes and retry

---

## Performance

### Speed Estimates

| Task | Papers | Model | Time |
|------|--------|-------|------|
| Search | 10 | - | ~5 sec |
| LLM filtering | 10 | llama3.1:8b | ~2-3 min |
| LLM filtering | 10 | mistral:7b | ~1-2 min |
| Download | 5 | - | ~30 sec |
| Extract (3 chunks) | 5 | llama3.1:8b | ~5-10 min |

### Optimize for Speed

**Fast filtering:**
```bash
# In .env
OLLAMA_MODEL=mistral:7b
```

**Fast extraction:**
```bash
uv run python scripts/batch_extract_papers.py --max-chunks 2
```

---

## Examples: Real Use Cases

### 1. Literature Review

```bash
# Search for review papers
uv run python scripts/search_and_download_papers.py "ti:survey OR ti:review graph neural networks" \
  --max-results 15 \
  --top-n 5
```

### 2. Following a Researcher

```bash
# Get recent papers by specific author
uv run python scripts/search_and_download_papers.py "au:Buehler" \
  --recent-days 180 \
  --category cs.AI
```

### 3. Building Domain Knowledge Graph

```bash
# Comprehensive search on domain
uv run python scripts/search_and_download_papers.py "materials science AND machine learning" \
  --max-results 50 \
  --threshold 0.65 \
  --auto-extract

# Combine all knowledge
uv run python scripts/batch_extract_papers.py --combine
```

### 4. Tracking Research Trends

```bash
# Weekly update: get latest papers
uv run python scripts/search_and_download_papers.py "large language models" \
  --recent-days 7 \
  --sort-by submittedDate \
  --category cs.CL
```

---

## Next Steps

After searching and downloading:

1. **Extract knowledge**: `python scripts/batch_extract_papers.py --combine`
2. **Load into Neo4j**: (coming soon)
3. **Visualize**: (coming soon)
4. **Query**: (coming soon)

For more information:
- Full extraction guide: `examples/README.md`
- Ollama setup: `docs/OLLAMA_GUIDE.md`
- API reference: `docs/API_SPECIFICATION.md`
