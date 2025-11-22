# Neo4j Integration Guide

Complete guide for using Neo4j with KG Builder: importing knowledge graphs, querying, analysis, and export.

## Table of Contents

1. [Overview](#overview)
2. [Setup](#setup)
3. [Import Workflow](#import-workflow)
4. [Querying the Graph](#querying-the-graph)
5. [Export Workflow](#export-workflow)
6. [Management Operations](#management-operations)
7. [Advanced Queries](#advanced-queries)
8. [Troubleshooting](#troubleshooting)

---

## Overview

### Why Use Neo4j?

While JSON files are portable and easy to share, Neo4j provides powerful capabilities for working with knowledge graphs:

**JSON Storage (Portable)**
- ✅ Easy to share on GitHub
- ✅ Human-readable
- ✅ Version controllable
- ❌ Limited query capabilities
- ❌ No graph algorithms
- ❌ Slow for complex relationships

**Neo4j Database (Analysis)**
- ✅ Complex graph queries (Cypher)
- ✅ Graph algorithms (PageRank, community detection, etc.)
- ✅ Fast relationship traversal
- ✅ Interactive visualization
- ✅ API for external tools
- ❌ Requires running database
- ❌ Not directly shareable

### Best Practice: Dual Storage

```
JSON Files (data/exports/)          Neo4j Database
        ↓                                  ↑
    [GitHub]  ←--share--→  [Collaborators]
        ↓                                  ↑
    import_to_neo4j.py  →  [Analysis & Queries]
        ↓                                  ↑
    [Your Machine]  ←--export--  export_from_neo4j.py
```

**Workflow:**
1. Extract knowledge from papers → JSON files
2. Commit JSON to GitHub (share)
3. Import JSON to Neo4j (analyze)
4. Export from Neo4j back to JSON (backup/share)

---

## Setup

### 1. Start Neo4j

Using Docker Compose (recommended):

```bash
# Start Neo4j
docker-compose up -d neo4j

# Check status
docker-compose ps
```

Or manually:

```bash
docker run -d \
  --name neo4j \
  -p 7474:7474 \
  -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your_password \
  -v $(pwd)/data/neo4j:/data \
  neo4j:5.25.1
```

### 2. Configure Connection

Create or update `.env`:

```bash
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_secure_password
NEO4J_DATABASE=neo4j
```

### 3. Verify Connection

```bash
# Check database statistics (should connect successfully)
python scripts/neo4j_manager.py stats
```

### 4. Access Browser Interface

Open in your browser:
- **Neo4j Browser**: http://localhost:7474
- Login with credentials from `.env`

---

## Import Workflow

### Basic Import

Import knowledge graphs from JSON files into Neo4j.

#### Import Single File

```bash
python scripts/import_to_neo4j.py data/exports/2403_11996_knowledge_graph.json
```

Output:
```
======================================================================
Neo4j Knowledge Graph Importer
======================================================================
✓ Connected to Neo4j
Creating database constraints and indexes...
✓ Constraints and indexes ready

Importing: 2403_11996_knowledge_graph.json
  📄 Title: Accelerating Scientific Discovery with Generative...
  🔗 arXiv ID: 2403.11996
  📊 Entities: 42
  🔗 Relationships: 58
  ✓ Imported successfully

======================================================================
Import Summary
======================================================================
Files processed: 1
Papers created: 1
Authors created: 1
Entities created: 42
Relationships created: 58
```

#### Import All Files in Directory

```bash
python scripts/import_to_neo4j.py data/exports/
```

This imports all `*_knowledge_graph.json` files.

#### Clear and Import

Start fresh by clearing existing data:

```bash
python scripts/import_to_neo4j.py data/exports/ --clear
```

**⚠️ WARNING**: This deletes all existing data! You'll be prompted to confirm.

#### Dry Run (Validate Only)

Validate JSON files without importing:

```bash
python scripts/import_to_neo4j.py data/exports/ --dry-run
```

---

## Querying the Graph

### Using Neo4j Browser

1. Open http://localhost:7474
2. Run Cypher queries in the console

#### Basic Queries

**See all node types:**
```cypher
CALL db.labels()
```

**Count nodes by type:**
```cypher
MATCH (n) RETURN labels(n)[0] as type, count(*) as count
```

**View random concepts:**
```cypher
MATCH (c:Concept)
RETURN c.name, c.type
LIMIT 10
```

**View papers:**
```cypher
MATCH (p:Paper)
RETURN p.title, p.arxiv_id
```

**View relationships:**
```cypher
MATCH (s:Concept)-[r]->(t:Concept)
RETURN type(r) as relationship, count(*) as count
ORDER BY count DESC
```

#### Graph Visualization

**Visualize concept neighborhood:**
```cypher
MATCH (c:Concept {name: 'graph neural network'})-[r]-(other)
RETURN c, r, other
LIMIT 25
```

**Visualize paper's knowledge graph:**
```cypher
MATCH (p:Paper {id: '2403_11996'})-[:MENTIONS]->(c:Concept)
MATCH (c)-[r]-(other:Concept)
RETURN p, c, r, other
LIMIT 50
```

### Using Python Scripts

#### Show Statistics

```bash
python scripts/neo4j_manager.py stats
```

Output:
```
======================================================================
Neo4j Database Statistics
======================================================================
Concepts:       156
Papers:         5
Authors:        8
Relationships:  234
Mentions:       312

Concepts by Type:
----------------------------------------------------------------------
  method               45
  material             38
  phenomenon           31
  theory               22
  measurement          12
  application          8
```

#### Search Concepts

```bash
python scripts/neo4j_manager.py search "neural"
```

Output:
```
Found 5 concepts matching 'neural':
----------------------------------------------------------------------
 1. neural network (method)
 2. graph neural network (method)
 3. neural architecture search (method)
 4. recurrent neural network (method)
 5. convolutional neural network (method)
```

#### Show Concept Details

```bash
python scripts/neo4j_manager.py concept "graph neural network"
```

Output:
```
======================================================================
Concept: graph neural network
======================================================================
Type:        method
Confidence:  0.95
Description: A type of neural network that operates on graph structures

Relationships (12):
----------------------------------------------------------------------

IS_A:
  ← neural network

USES:
  → message passing
  → attention mechanism
  → graph convolution

ENABLES:
  → node classification
  → link prediction

Mentioned in Papers (3):
----------------------------------------------------------------------
  - Accelerating Scientific Discovery with Generati... (confidence: 0.95)
  - Graph Neural Networks for Molecular Property... (confidence: 0.89)
  - Attention-based Graph Neural Networks... (confidence: 0.92)
```

#### Show Paper Details

```bash
python scripts/neo4j_manager.py paper "2403_11996"
```

#### List All Papers

```bash
python scripts/neo4j_manager.py papers
```

#### Run Custom Query

```bash
python scripts/neo4j_manager.py query "MATCH (c:Concept) WHERE c.type = 'method' RETURN c.name LIMIT 10"
```

---

## Export Workflow

Export knowledge graphs from Neo4j back to JSON format (for sharing, backup, or migration).

### Export Entire Graph

```bash
python scripts/export_from_neo4j.py --output data/exports/full_graph.json
```

This creates a complete snapshot of your knowledge graph.

### Export Specific Paper

```bash
python scripts/export_from_neo4j.py --paper "2403_11996" --output paper_export.json
```

Exports only the concepts and relationships for one paper.

### Export by Pattern

```bash
# Export all neural-network-related concepts
python scripts/export_from_neo4j.py --concept-pattern "neural" --output neural_concepts.json

# Export graph-related concepts
python scripts/export_from_neo4j.py --concept-pattern "graph" --output graph_concepts.json
```

### Use Cases for Export

1. **Backup**: Export entire graph before major changes
   ```bash
   python scripts/export_from_neo4j.py --output backups/backup_$(date +%Y%m%d).json
   ```

2. **Share subset**: Export specific topic to share with colleague
   ```bash
   python scripts/export_from_neo4j.py --concept-pattern "quantum" --output quantum_kg.json
   ```

3. **Migration**: Move to different Neo4j instance
   ```bash
   python scripts/export_from_neo4j.py --output migration.json
   # On new machine:
   python scripts/import_to_neo4j.py migration.json
   ```

---

## Management Operations

### Clear Database

```bash
# With confirmation prompt
python scripts/neo4j_manager.py clear

# Force (skip prompt)
python scripts/neo4j_manager.py clear --force
```

### Rebuild from JSON

```bash
# Clear and reimport
python scripts/neo4j_manager.py clear --force
python scripts/import_to_neo4j.py data/exports/
```

### Check Database Health

```bash
python scripts/neo4j_manager.py stats
```

---

## Advanced Queries

### Finding Knowledge Paths

**Find path between two concepts:**
```cypher
MATCH path = shortestPath(
  (start:Concept {name: 'neural network'})-[*..5]-(end:Concept {name: 'molecule'})
)
RETURN path
```

**Find all paths up to length 3:**
```cypher
MATCH path = (start:Concept {name: 'graph neural network'})-[*..3]-(end:Concept)
WHERE start <> end
RETURN path
LIMIT 10
```

### Concept Co-occurrence

**Find concepts frequently mentioned together:**
```cypher
MATCH (p:Paper)-[:MENTIONS]->(c1:Concept)
MATCH (p)-[:MENTIONS]->(c2:Concept)
WHERE c1.name < c2.name
RETURN c1.name, c2.name, count(p) as co_occurrence
ORDER BY co_occurrence DESC
LIMIT 20
```

### Most Connected Concepts

**Find hub concepts (most relationships):**
```cypher
MATCH (c:Concept)-[r]-()
RETURN c.name, c.type, count(r) as connections
ORDER BY connections DESC
LIMIT 20
```

**Find most mentioned concepts:**
```cypher
MATCH (p:Paper)-[m:MENTIONS]->(c:Concept)
RETURN c.name, c.type, count(p) as papers
ORDER BY papers DESC
LIMIT 20
```

### Paper Analysis

**Find papers with most concepts:**
```cypher
MATCH (p:Paper)-[:MENTIONS]->(c:Concept)
RETURN p.title, count(c) as num_concepts
ORDER BY num_concepts DESC
```

**Find papers by concept type:**
```cypher
MATCH (p:Paper)-[:MENTIONS]->(c:Concept)
WHERE c.type = 'method'
RETURN p.title, count(c) as method_count
ORDER BY method_count DESC
```

### Relationship Analysis

**Find relationship type distribution:**
```cypher
MATCH (s:Concept)-[r]->(t:Concept)
WHERE type(r) <> 'MENTIONS'
RETURN type(r) as relationship, count(*) as count
ORDER BY count DESC
```

**Find specific relationship patterns:**
```cypher
// What methods use what materials?
MATCH (method:Concept {type: 'method'})-[:USES]->(material:Concept {type: 'material'})
RETURN method.name, collect(material.name) as materials
```

### Graph Algorithms

**PageRank (concept importance):**
```cypher
CALL gds.pageRank.stream({
  nodeProjection: 'Concept',
  relationshipProjection: {
    REL: {type: '*', orientation: 'UNDIRECTED'}
  }
})
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).name as concept, score
ORDER BY score DESC
LIMIT 20
```

**Community Detection:**
```cypher
CALL gds.louvain.stream({
  nodeProjection: 'Concept',
  relationshipProjection: {
    REL: {type: '*', orientation: 'UNDIRECTED'}
  }
})
YIELD nodeId, communityId
RETURN communityId, collect(gds.util.asNode(nodeId).name) as concepts
ORDER BY size(concepts) DESC
LIMIT 10
```

---

## Troubleshooting

### Connection Issues

**Problem**: `Failed to connect to Neo4j`

**Solutions**:
1. Check Neo4j is running:
   ```bash
   docker-compose ps
   ```

2. Verify password in `.env`:
   ```bash
   cat .env | grep NEO4J_PASSWORD
   ```

3. Test browser access: http://localhost:7474

4. Check logs:
   ```bash
   docker-compose logs neo4j
   ```

### Import Errors

**Problem**: `Constraint already exists`

**Solution**: This is just a warning, import continues normally.

**Problem**: `No such file or directory`

**Solution**: Check file path is correct:
```bash
ls -la data/exports/
```

### Performance Issues

**Problem**: Slow queries

**Solutions**:
1. Ensure constraints/indexes exist:
   ```bash
   python scripts/neo4j_manager.py query "SHOW CONSTRAINTS"
   ```

2. Check database size:
   ```bash
   python scripts/neo4j_manager.py stats
   ```

3. Use EXPLAIN to analyze query:
   ```cypher
   EXPLAIN MATCH (c:Concept {name: 'neural network'}) RETURN c
   ```

### Memory Issues

**Problem**: Neo4j out of memory

**Solution**: Increase heap size in `docker-compose.yml`:
```yaml
environment:
  - NEO4J_dbms_memory_heap_initial__size=512m
  - NEO4J_dbms_memory_heap_max__size=2G
```

---

## Complete Workflow Example

Here's a complete example from paper search to Neo4j analysis:

```bash
# 1. Search and download papers
python scripts/search_and_download_papers.py "knowledge graph construction" \
  --max-results 10 \
  --threshold 0.7

# 2. Extract knowledge graphs
python scripts/batch_extract_papers.py --combine

# 3. Update papers index (for GitHub)
python scripts/create_papers_index.py

# 4. Import to Neo4j
python scripts/import_to_neo4j.py data/exports/

# 5. Verify import
python scripts/neo4j_manager.py stats

# 6. Explore in browser
open http://localhost:7474

# 7. Export for backup
python scripts/export_from_neo4j.py --output backups/backup_$(date +%Y%m%d).json

# 8. Commit results to GitHub (PDFs stay local!)
git add data/papers/papers_index.json
git add data/exports/*.json
git commit -m "Add knowledge graphs from 10 papers on knowledge graph construction"
git push
```

---

## Next Steps

- **Visualization**: Use Neo4j Bloom or Gephi for advanced visualization
- **API Integration**: Build REST API using FastAPI to query Neo4j
- **Graph Algorithms**: Apply community detection, centrality analysis
- **Embeddings**: Add vector embeddings to concepts for similarity search
- **Reasoning**: Implement graph reasoning and inference rules

For more information:
- Neo4j Documentation: https://neo4j.com/docs/
- Cypher Query Language: https://neo4j.com/docs/cypher-manual/
- Graph Data Science: https://neo4j.com/docs/graph-data-science/

---

**Summary**:
- JSON for sharing and portability
- Neo4j for analysis and queries
- Import/export scripts bridge the two
- Use both for best results! 🎉
