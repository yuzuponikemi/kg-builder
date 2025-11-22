# Research Papers Directory

This directory stores PDF files of research papers for knowledge graph extraction.

## Quick Start

### Option 1: Download from arXiv

Use the provided script to download papers from arXiv:

```bash
# Download the paper this project is based on
python scripts/download_arxiv_paper.py 2403.11996

# Download any other arXiv paper
python scripts/download_arxiv_paper.py <arxiv_id>
```

### Option 2: Manual Download

1. Visit https://arxiv.org/abs/2403.11996
2. Click "Download PDF"
3. Save to this directory (`data/papers/`)

### Option 3: Add Your Own Papers

Simply copy any PDF research papers to this directory:

```bash
cp ~/Downloads/my_paper.pdf data/papers/
```

## Extract Knowledge

Once you have PDF files here, run:

```bash
python examples/ingest_paper.py data/papers/<paper_name>.pdf
```

## Recommended First Paper

We recommend starting with the paper this project is based on:

**Title**: Accelerating Scientific Discovery with Generative Knowledge Extraction, Graph-Based Representation, and Multimodal Intelligent Graph Reasoning

**ArXiv ID**: 2403.11996

**Download**:
```bash
python scripts/download_arxiv_paper.py 2403.11996
```

This paper demonstrates the exact techniques we're implementing!

## File Organization

```
data/papers/
├── 2403_11996.pdf          # Main reference paper
├── paper1.pdf              # Your papers
├── paper2.pdf
└── ...
```

## Next Steps

After downloading papers:

1. Extract knowledge: `python examples/ingest_paper.py data/papers/2403_11996.pdf`
2. View results: `data/exports/<paper_name>_knowledge_graph.json`
3. Visualize (coming soon)
4. Load into Neo4j (coming soon)

See `examples/README.md` for more details.
