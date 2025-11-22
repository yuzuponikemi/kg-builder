# Data Directory Structure

This directory contains all data files for the KG Builder project.

## 📁 Directory Layout

```
data/
├── papers/              # Research papers (PDFs - local only)
│   ├── README.md        # Documentation
│   ├── papers_index.json  # Paper metadata (committed to Git)
│   └── *.pdf            # PDF files (NOT committed - too large)
│
├── exports/             # Extracted knowledge graphs (committed to Git)
│   ├── *_knowledge_graph.json    # Individual paper graphs
│   └── combined_knowledge_graph.json  # Combined graph
│
├── embeddings/          # Cached embeddings (local only)
│   └── *.npy, *.pkl     # Vector embeddings
│
└── neo4j/              # Neo4j database (local only)
    └── data/           # Graph database files
```

## 🔄 What Gets Committed to GitHub

### ✅ Committed (Shared)

1. **Paper Metadata** (`papers_index.json`)
   - Paper titles, authors, arXiv IDs
   - Number of pages, creation dates
   - Extraction statistics
   - **Does NOT include actual PDFs**

2. **Extracted Knowledge Graphs** (`exports/*.json`)
   - Entity and relationship data
   - Metadata and statistics
   - Usually small (<1MB each)
   - The valuable processed output

3. **Directory Structure**
   - README files
   - Directory placeholders

### ❌ NOT Committed (Local Only)

1. **PDF Files** (`papers/*.pdf`)
   - Can be very large (10MB+ each)
   - Copyright considerations
   - Can be re-downloaded from arXiv
   - Listed in `.gitignore`

2. **Neo4j Database** (`neo4j/`)
   - Binary database files
   - Can be regenerated from JSON exports
   - Machine-specific

3. **Embedding Cache** (`embeddings/`)
   - Large binary files
   - Can be regenerated
   - Model-specific

## 📊 Creating the Papers Index

To create/update the papers index:

```bash
python scripts/create_papers_index.py
```

This generates `papers_index.json` with metadata for all PDFs without including the actual files.

## 🔍 Example Index Entry

```json
{
  "filename": "2403_11996.pdf",
  "arxiv_id": "2403.11996",
  "title": "Accelerating Scientific Discovery with...",
  "author": "Markus J. Buehler",
  "num_pages": 15,
  "file_size_mb": 12.5,
  "knowledge_graph_extracted": true,
  "num_entities": 42,
  "num_relationships": 58,
  "added_to_index": "2025-11-22T12:00:00"
}
```

## 🚀 Reproducing Results

Someone cloning this repo can:

1. **See what papers were used** (via `papers_index.json`)
2. **Download same papers**:
   ```bash
   # Use arXiv ID from index
   python scripts/download_arxiv_paper.py 2403.11996
   ```
3. **Use existing knowledge graphs** (already in `exports/`)
4. **Or re-extract** (if they want):
   ```bash
   python examples/ingest_paper.py data/papers/2403_11996.pdf
   ```

## 📝 Best Practices

### When Adding New Papers

1. Download PDFs to `data/papers/`
2. Extract knowledge graphs
3. Update index:
   ```bash
   python scripts/create_papers_index.py
   ```
4. Commit:
   ```bash
   git add data/papers/papers_index.json
   git add data/exports/*.json
   git commit -m "Add knowledge graphs from 5 new papers"
   ```

### When Sharing Results

```bash
# Commit the processed results, not the PDFs
git add data/papers/papers_index.json
git add data/exports/
git commit -m "Add knowledge graphs for topic X"
git push
```

## 🔐 Benefits of This Approach

1. **Size Management**: Git repo stays small (<10MB vs potentially GBs)
2. **Copyright Compliance**: Don't redistribute copyrighted PDFs
3. **Reproducibility**: Others can get same papers from arXiv
4. **Sharing Value**: Share the extracted knowledge, not raw papers
5. **Collaboration**: Multiple people can contribute knowledge graphs
6. **Transparency**: Clear record of what papers were processed

## 📚 Storage Estimates

| Item | Size | Committed? |
|------|------|-----------|
| Single PDF | 5-20 MB | ❌ No |
| Knowledge graph JSON | 50-500 KB | ✅ Yes |
| Papers index | 10-50 KB | ✅ Yes |
| 100 PDFs | ~1 GB | ❌ No |
| 100 knowledge graphs | ~10 MB | ✅ Yes |

## 🔄 Syncing Workflow

### On Your Machine

```bash
# Download and process papers
python scripts/search_and_download_papers.py "topic"
python scripts/batch_extract_papers.py

# Create index
python scripts/create_papers_index.py

# Commit results (not PDFs)
git add data/papers/papers_index.json
git add data/exports/
git commit -m "Add knowledge graphs for topic X"
git push
```

### On Another Machine

```bash
# Pull latest results
git pull

# Check what papers exist
cat data/papers/papers_index.json

# Use existing knowledge graphs from data/exports/
# Or download PDFs if needed
python scripts/download_arxiv_paper.py 2403.11996
```

## 📖 Related Documentation

- **Search Guide**: `docs/SEARCH_GUIDE.md` - How to find and download papers
- **Extraction Guide**: `examples/README.md` - How to extract knowledge
- **Main README**: `../README.md` - Project overview

---

**Summary**: PDFs stay local, knowledge graphs go to GitHub. Everyone wins! 🎉
