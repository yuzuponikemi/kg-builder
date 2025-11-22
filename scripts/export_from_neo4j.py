#!/usr/bin/env python3
"""
Export knowledge graphs from Neo4j to JSON format.

This script extracts knowledge graphs from Neo4j and saves them as JSON files,
which can be shared, backed up, or re-imported.

Usage:
    # Export entire graph
    python scripts/export_from_neo4j.py --output data/exports/full_graph.json

    # Export specific paper
    python scripts/export_from_neo4j.py --paper "2403_11996" --output data/exports/paper.json

    # Export concepts matching pattern
    python scripts/export_from_neo4j.py --concept-pattern "neural" --output data/exports/neural.json
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from kg_builder.graph.neo4j_client import Neo4jClient


class KnowledgeGraphExporter:
    """Export knowledge graphs from Neo4j to JSON."""

    def __init__(self, neo4j_client: Neo4jClient):
        """Initialize exporter.

        Args:
            neo4j_client: Neo4j client instance
        """
        self.client = neo4j_client

    def export_entire_graph(self) -> dict[str, Any]:
        """Export entire knowledge graph.

        Returns:
            Complete graph as dictionary
        """
        print("Exporting entire knowledge graph...")

        # Get all concepts
        query_concepts = """
        MATCH (c:Concept)
        RETURN c.name as name, c.type as type, properties(c) as props
        """
        concepts_data = self.client.run_cypher(query_concepts)

        entities = []
        for record in concepts_data:
            entity = {
                "name": record["name"],
                "type": record["type"],
                "confidence": record["props"].get("confidence", 1.0),
                "description": record["props"].get("description", ""),
            }
            entities.append(entity)

        print(f"  ✓ Exported {len(entities)} entities")

        # Get all relationships between concepts
        query_rels = """
        MATCH (s:Concept)-[r]->(t:Concept)
        WHERE type(r) <> 'MENTIONS'
        RETURN s.name as source, t.name as target, type(r) as type, properties(r) as props
        """
        rels_data = self.client.run_cypher(query_rels)

        relationships = []
        for record in rels_data:
            rel = {
                "source": record["source"],
                "target": record["target"],
                "type": record["type"],
                "confidence": record["props"].get("confidence", 1.0),
                "context": record["props"].get("context", ""),
            }
            relationships.append(rel)

        print(f"  ✓ Exported {len(relationships)} relationships")

        # Get all papers
        query_papers = """
        MATCH (p:Paper)
        OPTIONAL MATCH (p)-[:AUTHORED_BY]->(a:Author)
        RETURN p.id as id, p.title as title, p.arxiv_id as arxiv_id,
               collect(a.name) as authors, properties(p) as props
        """
        papers_data = self.client.run_cypher(query_papers)

        papers = []
        for record in papers_data:
            paper = {
                "id": record["id"],
                "title": record["title"],
                "arxiv_id": record["arxiv_id"],
                "authors": record["authors"],
            }
            papers.append(paper)

        print(f"  ✓ Exported {len(papers)} papers")

        # Get statistics
        stats = self.client.get_statistics()

        return {
            "metadata": {
                "export_date": datetime.now().isoformat(),
                "source": "neo4j",
                "description": "Complete knowledge graph export from Neo4j",
            },
            "entities": entities,
            "relationships": relationships,
            "papers": papers,
            "statistics": {
                "num_entities": len(entities),
                "num_relationships": len(relationships),
                "num_papers": len(papers),
                "total_concepts_in_db": stats.get("concepts", 0),
                "total_relationships_in_db": stats.get("relationships", 0),
            },
        }

    def export_paper(self, paper_id: str) -> dict[str, Any]:
        """Export knowledge graph for specific paper.

        Args:
            paper_id: Paper identifier

        Returns:
            Paper's knowledge graph
        """
        print(f"Exporting knowledge graph for paper: {paper_id}")

        # Get paper info
        paper = self.client.get_paper(paper_id)
        if not paper:
            raise ValueError(f"Paper not found: {paper_id}")

        # Get concepts mentioned in paper
        query_concepts = """
        MATCH (p:Paper {id: $paper_id})-[m:MENTIONS]->(c:Concept)
        RETURN c.name as name, c.type as type, properties(c) as props, properties(m) as mention_props
        """
        concepts_data = self.client.run_cypher(query_concepts, {"paper_id": paper_id})

        entities = []
        concept_names = set()
        for record in concepts_data:
            entity = {
                "name": record["name"],
                "type": record["type"],
                "confidence": record["mention_props"].get("confidence", 1.0),
                "description": record["props"].get("description", ""),
            }
            entities.append(entity)
            concept_names.add(record["name"])

        print(f"  ✓ Found {len(entities)} entities")

        # Get relationships between these concepts
        query_rels = """
        MATCH (s:Concept)-[r]->(t:Concept)
        WHERE s.name IN $names AND t.name IN $names AND type(r) <> 'MENTIONS'
        RETURN s.name as source, t.name as target, type(r) as type, properties(r) as props
        """
        rels_data = self.client.run_cypher(query_rels, {"names": list(concept_names)})

        relationships = []
        for record in rels_data:
            rel = {
                "source": record["source"],
                "target": record["target"],
                "type": record["type"],
                "confidence": record["props"].get("confidence", 1.0),
                "context": record["props"].get("context", ""),
            }
            relationships.append(rel)

        print(f"  ✓ Found {len(relationships)} relationships")

        # Get authors
        query_authors = """
        MATCH (p:Paper {id: $paper_id})-[:AUTHORED_BY]->(a:Author)
        RETURN a.name as name
        """
        authors_data = self.client.run_cypher(query_authors, {"paper_id": paper_id})
        authors = [record["name"] for record in authors_data]

        return {
            "metadata": {
                "export_date": datetime.now().isoformat(),
                "source": "neo4j",
                "source_file": paper.get("source_file", paper_id),
                "title": paper.get("title", "Unknown"),
                "arxiv_id": paper.get("arxiv_id"),
                "authors": authors,
            },
            "entities": entities,
            "relationships": relationships,
            "statistics": {
                "num_entities": len(entities),
                "num_relationships": len(relationships),
            },
        }

    def export_concepts_by_pattern(self, pattern: str) -> dict[str, Any]:
        """Export concepts matching a pattern.

        Args:
            pattern: Search pattern (case-insensitive)

        Returns:
            Filtered knowledge graph
        """
        print(f"Exporting concepts matching pattern: '{pattern}'")

        # Search for concepts
        query_concepts = """
        MATCH (c:Concept)
        WHERE toLower(c.name) CONTAINS toLower($pattern)
        RETURN c.name as name, c.type as type, properties(c) as props
        """
        concepts_data = self.client.run_cypher(query_concepts, {"pattern": pattern})

        entities = []
        concept_names = set()
        for record in concepts_data:
            entity = {
                "name": record["name"],
                "type": record["type"],
                "confidence": record["props"].get("confidence", 1.0),
                "description": record["props"].get("description", ""),
            }
            entities.append(entity)
            concept_names.add(record["name"])

        print(f"  ✓ Found {len(entities)} matching entities")

        # Get relationships between these concepts
        query_rels = """
        MATCH (s:Concept)-[r]->(t:Concept)
        WHERE s.name IN $names AND t.name IN $names AND type(r) <> 'MENTIONS'
        RETURN s.name as source, t.name as target, type(r) as type, properties(r) as props
        """
        rels_data = self.client.run_cypher(query_rels, {"names": list(concept_names)})

        relationships = []
        for record in rels_data:
            rel = {
                "source": record["source"],
                "target": record["target"],
                "type": record["type"],
                "confidence": record["props"].get("confidence", 1.0),
                "context": record["props"].get("context", ""),
            }
            relationships.append(rel)

        print(f"  ✓ Found {len(relationships)} relationships")

        return {
            "metadata": {
                "export_date": datetime.now().isoformat(),
                "source": "neo4j",
                "filter": f"concepts matching '{pattern}'",
            },
            "entities": entities,
            "relationships": relationships,
            "statistics": {
                "num_entities": len(entities),
                "num_relationships": len(relationships),
            },
        }


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Export knowledge graphs from Neo4j to JSON",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export entire graph
  python scripts/export_from_neo4j.py --output data/exports/full_graph.json

  # Export specific paper
  python scripts/export_from_neo4j.py --paper "2403_11996" --output paper.json

  # Export concepts matching pattern
  python scripts/export_from_neo4j.py --concept-pattern "neural" --output neural.json
        """,
    )

    parser.add_argument("-o", "--output", type=Path, required=True, help="Output JSON file")
    parser.add_argument("--paper", type=str, help="Export specific paper by ID")
    parser.add_argument(
        "--concept-pattern", type=str, help="Export concepts matching pattern"
    )
    parser.add_argument("--neo4j-uri", type=str, help="Neo4j URI (overrides .env)")
    parser.add_argument("--neo4j-user", type=str, help="Neo4j username (overrides .env)")
    parser.add_argument("--neo4j-password", type=str, help="Neo4j password (overrides .env)")

    args = parser.parse_args()

    print("=" * 70)
    print("Neo4j Knowledge Graph Exporter")
    print("=" * 70)

    # Connect to Neo4j
    try:
        client = Neo4jClient(
            uri=args.neo4j_uri,
            username=args.neo4j_user,
            password=args.neo4j_password,
        )
        print(f"✓ Connected to Neo4j\n")
    except Exception as e:
        print(f"\n✗ Failed to connect to Neo4j: {e}")
        print("\nMake sure:")
        print("  1. Neo4j is running (docker-compose up -d neo4j)")
        print("  2. NEO4J_PASSWORD is set in .env")
        print("  3. Connection details are correct")
        sys.exit(1)

    # Export
    try:
        exporter = KnowledgeGraphExporter(client)

        if args.paper:
            data = exporter.export_paper(args.paper)
        elif args.concept_pattern:
            data = exporter.export_concepts_by_pattern(args.concept_pattern)
        else:
            data = exporter.export_entire_graph()

        # Save to file
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"\n{'=' * 70}")
        print("Export Summary")
        print(f"{'=' * 70}")
        print(f"Entities: {len(data['entities'])}")
        print(f"Relationships: {len(data['relationships'])}")
        print(f"Output file: {args.output}")
        print(f"File size: {args.output.stat().st_size / 1024:.1f} KB")
        print(f"\n✓ Export complete!")

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n✗ Error during export: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
    finally:
        client.close()


if __name__ == "__main__":
    main()
