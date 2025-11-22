# Knowledge Graph Extraction Examples

This directory contains examples for using the KG Builder knowledge extraction pipeline.

## Prerequisites

1. **Install Ollama** (if not already done):
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

2. **Pull recommended model**:
```bash
ollama pull llama3.1:8b
# or for faster processing
ollama pull mistral:7b
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

## Quick Start: Extract Knowledge from a Paper

### Option 1: Use Your Own PDF

```bash
python examples/ingest_paper.py path/to/your/paper.pdf
```

### Option 2: Download from arXiv

First, download a paper from arXiv:
```bash
# Download the paper this project is based on
python scripts/download_arxiv_paper.py 2403.11996

# Or any other arXiv paper
python scripts/download_arxiv_paper.py 2301.00001
```

Then extract knowledge:
```bash
python examples/ingest_paper.py data/papers/2403_11996.pdf
```

### Option 3: Test with Sample Text

For quick testing without Ollama, you can use the test script:
```bash
python examples/test_extraction.py
```

## What the Extraction Does

The `ingest_paper.py` script performs the following steps:

1. **PDF Text Extraction**
   - Extracts text from PDF using pdfplumber
   - Organizes text by sections (Abstract, Introduction, Methods, etc.)
   - Splits into chunks for processing

2. **Entity Extraction**
   - Uses LLM (Ollama) to identify scientific concepts
   - Extracts: methods, materials, phenomena, theories, measurements, applications
   - Assigns confidence scores to each entity

3. **Relationship Extraction**
   - Identifies relationships between extracted entities
   - Relationship types: is_a, part_of, uses, enables, measures, applies_to, based_on, related_to
   - Provides context and confidence for each relationship

4. **Save Results**
   - Saves extracted knowledge graph to JSON
   - Location: `data/exports/<paper_name>_knowledge_graph.json`

## Output Format

The generated JSON file contains:

```json
{
  "metadata": {
    "title": "Paper Title",
    "num_pages": 15,
    "file_size": 1234567
  },
  "statistics": {
    "num_entities": 45,
    "num_relationships": 67,
    "chunks_processed": 3
  },
  "entities": [
    {
      "name": "neural networks",
      "type": "method",
      "description": "Computational models inspired by biological neural networks",
      "confidence": 0.95,
      "context": "...text snippet..."
    }
  ],
  "relationships": [
    {
      "from": "neural networks",
      "to": "deep learning",
      "type": "part_of",
      "confidence": 0.90,
      "context": "...text snippet..."
    }
  ]
}
```

## Customization

### Using Different LLM Models

Edit `.env` to change the Ollama model:

```bash
# Fast model (6GB VRAM)
OLLAMA_MODEL=mistral:7b

# Balanced (8GB VRAM) - Default
OLLAMA_MODEL=llama3.1:8b

# Best quality (40GB+ VRAM)
OLLAMA_MODEL=llama3.1:70b

# Technical papers
OLLAMA_MODEL=qwen2.5:7b
```

### Processing More/Fewer Chunks

Edit `examples/ingest_paper.py` line ~75:

```python
# Process first 3 chunks (fast demo)
max_chunks = min(3, len(chunks))

# Process all chunks (complete extraction)
max_chunks = len(chunks)
```

### Adjusting Chunk Size

Larger chunks = more context, but slower processing:

```python
chunks = extractor.extract_chunks(
    chunk_size=3000,  # Increase for more context
    overlap=300       # Overlap between chunks
)
```

## Tips for Best Results

1. **GPU Acceleration**: If you have an NVIDIA GPU, set in `.env`:
   ```bash
   OLLAMA_NUM_GPU=1
   EMBEDDING_DEVICE=cuda
   ```

2. **Quality vs Speed**: Use larger models for better extraction:
   - Fast: `mistral:7b` (~30 sec/chunk)
   - Balanced: `llama3.1:8b` (~45 sec/chunk)
   - Best: `llama3.1:70b` (~2 min/chunk)

3. **Paper Type**: Use specialized models:
   - CS/Code papers: `deepseek-coder:6.7b`
   - Technical papers: `qwen2.5:7b`
   - General science: `llama3.1:8b`

4. **First Run**: The first chunk takes longer as Ollama loads the model into memory

## Troubleshooting

### "Model not found"
```bash
ollama pull llama3.1:8b
```

### "Ollama connection refused"
```bash
# Start Ollama service
ollama serve
```

### "Out of memory"
- Use a smaller model (`mistral:7b`)
- Reduce `OLLAMA_NUM_CTX` in `.env`
- Set `OLLAMA_NUM_GPU=0` for CPU-only

### Slow extraction
- Ensure GPU is being used (`nvidia-smi`)
- Use faster model (`mistral:7b`)
- Process fewer chunks initially

## Next Steps

After extraction:

1. **Visualize the graph** (coming soon):
   ```bash
   python examples/visualize_graph.py data/exports/paper_knowledge_graph.json
   ```

2. **Load into Neo4j** (coming soon):
   ```bash
   python scripts/load_to_neo4j.py data/exports/paper_knowledge_graph.json
   ```

3. **Query the graph**:
   - Find related concepts
   - Trace research lineages
   - Identify knowledge gaps

## Example Output

```
Knowledge Graph Extraction from Research Paper
==============================================================

PDF: data/papers/2403_11996.pdf
File size: 1234.5 KB

Step 1: Extracting text from PDF...
------------------------------------------------------------
Title: Accelerating Scientific Discovery with...
Pages: 15
Sections found: 6
Total text length: 45,234 characters
Split into 15 chunks for processing

Step 2: Extracting entities (concepts, methods, etc.)...
------------------------------------------------------------
Processing first 3 chunks...
Processing chunk 1/3...
Processing chunk 2/3...
Processing chunk 3/3...

✓ Extracted 42 unique entities

Top entities by confidence:
  - generative AI (method) - confidence: 0.95
  - knowledge graphs (method) - confidence: 0.93
  - graph reasoning (method) - confidence: 0.91
  ...

Step 3: Extracting relationships between entities...
------------------------------------------------------------
Processing chunk 1/3 for relationships...
Processing chunk 2/3 for relationships...
Processing chunk 3/3 for relationships...

✓ Extracted 58 relationships

Step 4: Saving results...
------------------------------------------------------------
✓ Results saved to: data/exports/2403_11996_knowledge_graph.json

==============================================================
Extraction Summary
==============================================================

Entity Types:
  - method: 25
  - phenomenon: 8
  - theory: 5
  - application: 4

Relationship Types:
  - uses: 18
  - enables: 15
  - based_on: 12
  - related_to: 8
  - is_a: 5

Average entity confidence: 0.87
Average relationship confidence: 0.82

✓ Knowledge extraction complete!
```

## Support

- Full documentation: `docs/OLLAMA_GUIDE.md`
- Issues: https://github.com/yourusername/kg-builder/issues
