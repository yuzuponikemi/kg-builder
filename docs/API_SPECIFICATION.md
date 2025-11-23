# API Specification for Agent Integration

Complete API reference for integrating external agent-based AI systems with KG Builder.

## Table of Contents

1. [Authentication](#authentication)
2. [REST API Endpoints](#rest-api-endpoints)
3. [WebSocket API](#websocket-api)
4. [GraphQL API](#graphql-api)
5. [Python SDK](#python-sdk)
6. [Error Handling](#error-handling)
7. [Rate Limiting](#rate-limiting)
8. [Webhooks](#webhooks)

---

## Authentication

### API Key Authentication

```http
Authorization: Bearer YOUR_API_KEY
```

### JWT Token Authentication

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}

Response:
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

Use the token in subsequent requests:

```http
Authorization: Bearer eyJ...
```

---

## REST API Endpoints

Base URL: `http://localhost:8000/api/v1`

### Papers

#### Upload Paper

```http
POST /papers
Content-Type: multipart/form-data
Authorization: Bearer YOUR_API_KEY

Form Data:
- file: PDF file
- auto_extract: boolean (default: true)
- metadata: JSON object (optional)

Response: 201 Created
{
  "id": "paper-uuid",
  "title": "Extracted Paper Title",
  "status": "processing" | "completed" | "failed",
  "created_at": "2025-11-22T10:00:00Z"
}
```

#### Get Paper

```http
GET /papers/{paper_id}
Authorization: Bearer YOUR_API_KEY

Response: 200 OK
{
  "id": "paper-uuid",
  "title": "Paper Title",
  "abstract": "Paper abstract...",
  "year": 2024,
  "authors": ["Author 1", "Author 2"],
  "concepts": ["concept-id-1", "concept-id-2"],
  "status": "completed"
}
```

#### List Papers

```http
GET /papers?limit=20&offset=0&year=2024
Authorization: Bearer YOUR_API_KEY

Response: 200 OK
{
  "items": [
    {
      "id": "paper-uuid",
      "title": "Paper Title",
      "year": 2024
    }
  ],
  "total": 100,
  "limit": 20,
  "offset": 0
}
```

#### Delete Paper

```http
DELETE /papers/{paper_id}
Authorization: Bearer YOUR_API_KEY

Response: 204 No Content
```

### Concepts

#### List Concepts

```http
GET /concepts?limit=20&offset=0&type=method
Authorization: Bearer YOUR_API_KEY

Response: 200 OK
{
  "items": [
    {
      "id": "concept-uuid",
      "name": "Neural Networks",
      "type": "method",
      "description": "...",
      "frequency": 15
    }
  ],
  "total": 500,
  "limit": 20,
  "offset": 0
}
```

#### Get Concept

```http
GET /concepts/{concept_id}
Authorization: Bearer YOUR_API_KEY

Response: 200 OK
{
  "id": "concept-uuid",
  "name": "Neural Networks",
  "type": "method",
  "description": "...",
  "embedding": [0.1, 0.2, ...],
  "related_concepts": ["concept-id-2", "concept-id-3"],
  "papers": ["paper-id-1", "paper-id-2"]
}
```

#### Create Concept

```http
POST /concepts
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "name": "Quantum Computing",
  "type": "method",
  "description": "Computing using quantum-mechanical phenomena"
}

Response: 201 Created
{
  "id": "concept-uuid",
  "name": "Quantum Computing",
  "type": "method"
}
```

#### Update Concept

```http
PUT /concepts/{concept_id}
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "description": "Updated description"
}

Response: 200 OK
```

### Relationships

#### Create Relationship

```http
POST /relationships
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "from_concept": "concept-id-1",
  "to_concept": "concept-id-2",
  "type": "causal",
  "confidence": 0.85,
  "context": "Based on experiment results..."
}

Response: 201 Created
{
  "id": "relationship-uuid",
  "from": "concept-id-1",
  "to": "concept-id-2",
  "type": "causal"
}
```

#### Query Relationships

```http
GET /relationships?from={concept_id}&type=causal
Authorization: Bearer YOUR_API_KEY

Response: 200 OK
{
  "items": [
    {
      "id": "rel-uuid",
      "from": "concept-id-1",
      "to": "concept-id-2",
      "type": "causal",
      "confidence": 0.85
    }
  ]
}
```

### Search

#### Semantic Search

```http
POST /search/semantic
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "query": "machine learning for materials science",
  "limit": 10,
  "threshold": 0.7
}

Response: 200 OK
{
  "results": [
    {
      "id": "concept-uuid",
      "name": "Neural Networks for Material Property Prediction",
      "similarity": 0.92,
      "type": "method"
    }
  ]
}
```

#### Full-Text Search

```http
POST /search/fulltext
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "query": "biomaterials AND neural",
  "node_types": ["Concept", "Paper"],
  "limit": 20
}

Response: 200 OK
{
  "results": [
    {
      "id": "uuid",
      "type": "Concept",
      "name": "Bio-inspired Neural Materials",
      "score": 0.95
    }
  ]
}
```

#### Custom Cypher Query

```http
POST /search/cypher
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "query": "MATCH (c:Concept)-[:RELATES_TO]->(c2:Concept) WHERE c.type = 'method' RETURN c, c2 LIMIT 10",
  "parameters": {}
}

Response: 200 OK
{
  "results": [
    {
      "c": {"id": "...", "name": "..."},
      "c2": {"id": "...", "name": "..."}
    }
  ]
}
```

### Graph Reasoning

#### Find Paths

```http
POST /reasoning/path
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "from": "concept-id-1",
  "to": "concept-id-2",
  "max_hops": 3,
  "algorithm": "shortest" | "alternative",
  "num_paths": 5
}

Response: 200 OK
{
  "paths": [
    {
      "length": 2,
      "nodes": [
        {"id": "concept-id-1", "name": "Neural Networks"},
        {"id": "concept-id-x", "name": "Deep Learning"},
        {"id": "concept-id-2", "name": "Biomaterials"}
      ],
      "relationships": [
        {"type": "IS_A", "confidence": 0.95},
        {"type": "RELATES_TO", "confidence": 0.85}
      ]
    }
  ]
}
```

#### Find Similar Concepts

```http
POST /reasoning/similar
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "concept_id": "concept-uuid",
  "limit": 10,
  "threshold": 0.8,
  "method": "embedding" | "graph_structure"
}

Response: 200 OK
{
  "similar_concepts": [
    {
      "id": "similar-concept-uuid",
      "name": "Similar Concept",
      "similarity": 0.92,
      "common_papers": 5
    }
  ]
}
```

#### Detect Communities

```http
POST /reasoning/community
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "algorithm": "louvain" | "label_propagation",
  "min_size": 3,
  "resolution": 1.0
}

Response: 200 OK
{
  "communities": [
    {
      "id": "community-uuid",
      "size": 25,
      "modularity": 0.82,
      "representative_concepts": [
        {"id": "...", "name": "..."}
      ]
    }
  ]
}
```

#### Extract Subgraph

```http
POST /reasoning/subgraph
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "center_concept": "concept-id",
  "radius": 2,
  "max_nodes": 100,
  "relationship_types": ["RELATES_TO", "IS_A"]
}

Response: 200 OK
{
  "nodes": [...],
  "edges": [...],
  "stats": {
    "num_nodes": 45,
    "num_edges": 78
  }
}
```

#### Recommend Related Items

```http
POST /reasoning/recommend
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "based_on": ["concept-id-1", "concept-id-2"],
  "type": "concepts" | "papers",
  "limit": 10,
  "algorithm": "collaborative" | "content_based"
}

Response: 200 OK
{
  "recommendations": [
    {
      "id": "recommended-id",
      "name": "Recommended Item",
      "score": 0.88,
      "reason": "Frequently co-occurs with input concepts"
    }
  ]
}
```

### Analytics

#### Graph Statistics

```http
GET /analytics/stats
Authorization: Bearer YOUR_API_KEY

Response: 200 OK
{
  "num_nodes": 5000,
  "num_edges": 12000,
  "node_types": {
    "Concept": 4000,
    "Paper": 800,
    "Author": 200
  },
  "avg_degree": 4.8,
  "density": 0.00096,
  "num_components": 1
}
```

#### Centrality Metrics

```http
POST /analytics/centrality
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "metric": "betweenness" | "closeness" | "eigenvector" | "pagerank",
  "node_type": "Concept",
  "limit": 10
}

Response: 200 OK
{
  "results": [
    {
      "id": "concept-uuid",
      "name": "Neural Networks",
      "centrality": 0.92
    }
  ]
}
```

#### Degree Distribution

```http
GET /analytics/distribution?metric=degree
Authorization: Bearer YOUR_API_KEY

Response: 200 OK
{
  "distribution": [
    {"value": 1, "count": 100},
    {"value": 2, "count": 80},
    ...
  ],
  "power_law_exponent": 2.3,
  "is_scale_free": true
}
```

#### Community Structure

```http
GET /analytics/communities
Authorization: Bearer YOUR_API_KEY

Response: 200 OK
{
  "communities": [
    {
      "id": "community-1",
      "size": 150,
      "modularity": 0.85,
      "top_concepts": [...]
    }
  ],
  "overall_modularity": 0.78
}
```

### Visualization

#### Get Graph Visualization Data

```http
POST /viz/graph
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "concept_ids": ["concept-1", "concept-2"],
  "include_neighbors": true,
  "max_depth": 2,
  "layout": "force_directed" | "hierarchical" | "circular"
}

Response: 200 OK
{
  "nodes": [
    {
      "id": "concept-1",
      "label": "Neural Networks",
      "type": "method",
      "x": 100,
      "y": 200,
      "size": 10,
      "color": "#4A90E2"
    }
  ],
  "edges": [
    {
      "id": "edge-1",
      "source": "concept-1",
      "target": "concept-2",
      "type": "RELATES_TO",
      "weight": 0.85
    }
  ]
}
```

#### Export Graph

```http
POST /viz/export
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "format": "graphml" | "json" | "csv" | "gexf",
  "filters": {
    "concept_types": ["method", "material"],
    "min_confidence": 0.7
  }
}

Response: 200 OK
Content-Type: application/octet-stream
Content-Disposition: attachment; filename="graph_export.graphml"

[Binary graph data]
```

#### Apply Layout Algorithm

```http
POST /viz/layout/{algorithm}
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "graph_data": {...},
  "parameters": {
    "iterations": 100,
    "gravity": 0.1
  }
}

Response: 200 OK
{
  "positioned_nodes": [
    {"id": "...", "x": 100, "y": 200}
  ]
}
```

---

## WebSocket API

### Connection

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/graph/updates?token=YOUR_API_KEY');

ws.onopen = () => {
  console.log('Connected');
};

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  handleUpdate(update);
};
```

### Message Types

#### Node Added

```json
{
  "type": "node_added",
  "timestamp": "2025-11-22T10:00:00Z",
  "data": {
    "id": "concept-uuid",
    "label": "New Concept",
    "node_type": "Concept",
    "properties": {...}
  }
}
```

#### Edge Added

```json
{
  "type": "edge_added",
  "timestamp": "2025-11-22T10:00:00Z",
  "data": {
    "id": "edge-uuid",
    "source": "concept-1",
    "target": "concept-2",
    "type": "RELATES_TO",
    "properties": {...}
  }
}
```

#### Node Updated

```json
{
  "type": "node_updated",
  "timestamp": "2025-11-22T10:00:00Z",
  "data": {
    "id": "concept-uuid",
    "changes": {
      "description": "Updated description"
    }
  }
}
```

#### Processing Status

```json
{
  "type": "processing_status",
  "timestamp": "2025-11-22T10:00:00Z",
  "data": {
    "paper_id": "paper-uuid",
    "status": "extracting_entities",
    "progress": 0.45,
    "message": "Extracting entities from section 3..."
  }
}
```

### Streaming Analysis

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/analysis/stream?token=YOUR_API_KEY');

// Send analysis request
ws.send(JSON.stringify({
  operation: "community_detection",
  params: {
    algorithm: "louvain",
    min_size: 3
  }
}));

// Receive streaming results
ws.onmessage = (event) => {
  const result = JSON.parse(event.data);
  console.log('Progress:', result.progress);
  console.log('Partial results:', result.partial_results);
};
```

---

## GraphQL API

Endpoint: `http://localhost:8000/graphql`

### Schema

```graphql
type Paper {
  id: ID!
  title: String!
  abstract: String
  year: Int
  doi: String
  concepts: [Concept!]! @relationship(type: "MENTIONED_IN", direction: IN)
  citations: [Paper!]! @relationship(type: "CITES", direction: OUT)
  authors: [Author!]! @relationship(type: "AUTHORED_BY", direction: OUT)
}

type Concept {
  id: ID!
  name: String!
  type: String!
  description: String
  embedding: [Float!]
  relatedConcepts(
    types: [String!]
    minConfidence: Float
  ): [ConceptRelationship!]!
  papers: [Paper!]! @relationship(type: "MENTIONED_IN", direction: OUT)
}

type ConceptRelationship {
  concept: Concept!
  type: String!
  confidence: Float!
  context: String
}

type Author {
  id: ID!
  name: String!
  papers: [Paper!]! @relationship(type: "AUTHORED_BY", direction: IN)
  collaborators: [Author!]!
}

type Query {
  papers(
    limit: Int = 20
    offset: Int = 0
    year: Int
  ): [Paper!]!

  paper(id: ID!): Paper

  concepts(
    filter: ConceptFilter
    limit: Int = 20
    offset: Int = 0
  ): [Concept!]!

  concept(id: ID!): Concept

  searchSemantic(
    query: String!
    limit: Int = 10
    threshold: Float = 0.7
  ): [ConceptSearchResult!]!

  findPath(
    from: ID!
    to: ID!
    maxHops: Int = 3
  ): Path

  communities(
    algorithm: String = "louvain"
    minSize: Int = 3
  ): [Community!]!
}

type Mutation {
  addPaper(input: PaperInput!): Paper!
  addConcept(input: ConceptInput!): Concept!
  addRelationship(input: RelationshipInput!): Relationship!
  updateConcept(id: ID!, input: ConceptUpdateInput!): Concept!
  deletePaper(id: ID!): Boolean!
}

input ConceptFilter {
  types: [String!]
  minFrequency: Int
  searchTerm: String
}

input PaperInput {
  title: String!
  abstract: String
  year: Int
  doi: String
}

input ConceptInput {
  name: String!
  type: String!
  description: String
}

input RelationshipInput {
  fromConcept: ID!
  toConcept: ID!
  type: String!
  confidence: Float
  context: String
}
```

### Example Queries

#### Get Paper with Related Concepts

```graphql
query GetPaper($id: ID!) {
  paper(id: $id) {
    title
    abstract
    year
    concepts {
      id
      name
      type
      relatedConcepts(minConfidence: 0.8) {
        concept {
          name
        }
        type
        confidence
      }
    }
  }
}
```

#### Semantic Search with Path Finding

```graphql
query SearchAndFindPaths($query: String!, $targetId: ID!) {
  searchSemantic(query: $query, limit: 5) {
    concept {
      id
      name
    }
    similarity
  }

  findPath(from: "source-id", to: $targetId, maxHops: 3) {
    length
    nodes {
      ... on Concept {
        name
        type
      }
    }
  }
}
```

---

## Python SDK

### Installation

```bash
pip install kg-builder-sdk
```

### Basic Usage

```python
from kg_builder import KGClient

# Initialize client
client = KGClient(
    api_url="http://localhost:8000",
    api_key="your_api_key"
)

# Upload paper
paper = client.papers.add(
    pdf_path="paper.pdf",
    auto_extract=True
)

# Semantic search
concepts = client.search.semantic(
    query="neural networks",
    limit=10
)

# Find paths
paths = client.reasoning.find_paths(
    from_concept="concept-id-1",
    to_concept="concept-id-2",
    max_hops=3
)

# Detect communities
communities = client.analytics.detect_communities(
    algorithm="louvain"
)
```

### Async Support

```python
from kg_builder import AsyncKGClient

async with AsyncKGClient(api_url="...", api_key="...") as client:
    paper = await client.papers.add(pdf_path="paper.pdf")
    concepts = await client.search.semantic(query="...")
```

### Streaming Updates

```python
async with client.stream() as stream:
    async for update in stream.graph_updates():
        print(f"Update: {update.type} - {update.data}")
```

---

## Error Handling

### Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid concept ID format",
    "details": {
      "field": "concept_id",
      "expected": "UUID format",
      "received": "invalid-id"
    },
    "request_id": "req-uuid"
  }
}
```

### Error Codes

- `AUTHENTICATION_ERROR` (401): Invalid or missing API key
- `AUTHORIZATION_ERROR` (403): Insufficient permissions
- `NOT_FOUND` (404): Resource not found
- `VALIDATION_ERROR` (422): Invalid request parameters
- `RATE_LIMIT_EXCEEDED` (429): Too many requests
- `INTERNAL_ERROR` (500): Server error
- `SERVICE_UNAVAILABLE` (503): Service temporarily unavailable

---

## Rate Limiting

### Headers

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1637849600
```

### Limits

- **Free Tier**: 100 requests/hour
- **Pro Tier**: 1000 requests/hour
- **Enterprise**: Custom limits

---

## Webhooks

### Configuration

```http
POST /api/v1/webhooks
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "url": "https://your-server.com/webhook",
  "events": ["paper.added", "concept.created", "processing.completed"],
  "secret": "your_webhook_secret"
}

Response: 201 Created
{
  "id": "webhook-uuid",
  "url": "https://your-server.com/webhook",
  "events": ["paper.added", "concept.created"]
}
```

### Event Payload

```json
{
  "event": "paper.added",
  "timestamp": "2025-11-22T10:00:00Z",
  "data": {
    "paper_id": "paper-uuid",
    "title": "Paper Title",
    "status": "processing"
  },
  "signature": "sha256=..."
}
```

### Signature Verification

```python
import hmac
import hashlib

def verify_webhook(payload, signature, secret):
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

---

## Best Practices for Agent Integration

1. **Use API Keys**: Store API keys securely in environment variables
2. **Handle Rate Limits**: Implement exponential backoff for retries
3. **Use WebSockets**: For real-time updates instead of polling
4. **Batch Operations**: Use batch endpoints when processing multiple items
5. **Cache Embeddings**: Cache embedding results to reduce API calls
6. **Error Handling**: Always handle errors gracefully with retries
7. **Logging**: Log all API interactions for debugging
8. **Webhooks**: Use webhooks for async notifications instead of polling

---

**Last Updated**: 2025-11-22
**Version**: 1.0
