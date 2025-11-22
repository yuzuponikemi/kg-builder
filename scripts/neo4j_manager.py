#!/usr/bin/env python3
"""
Neo4j database management utility.

Provides commands for common Neo4j operations: statistics, queries, clearing data, etc.

Usage:
    # Show database statistics
    python scripts/neo4j_manager.py stats

    # Search for concepts
    python scripts/neo4j_manager.py search "neural network"

    # Show concept details
    python scripts/neo4j_manager.py concept "graph transformer"

    # Show paper details
    python scripts/neo4j_manager.py paper "2403_11996"

    # List all papers
    python scripts/neo4j_manager.py papers

    # Clear database (with confirmation)
    python scripts/neo4j_manager.py clear

    # Run custom Cypher query
    python scripts/neo4j_manager.py query "MATCH (c:Concept) RETURN c.name LIMIT 10"
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from kg_builder.graph.neo4j_client import Neo4jClient


def show_statistics(client: Neo4jClient):
    """Show database statistics."""
    stats = client.get_statistics()

    print("=" * 70)
    print("Neo4j Database Statistics")
    print("=" * 70)
    print(f"Concepts:       {stats.get('concepts', 0):,}")
    print(f"Papers:         {stats.get('papers', 0):,}")
    print(f"Authors:        {stats.get('authors', 0):,}")
    print(f"Relationships:  {stats.get('relationships', 0):,}")
    print(f"Mentions:       {stats.get('mentions', 0):,}")
    print()

    # Get concept type breakdown
    query = """
    MATCH (c:Concept)
    RETURN c.type as type, count(*) as count
    ORDER BY count DESC
    """
    result = client.run_cypher(query)

    if result:
        print("Concepts by Type:")
        print("-" * 70)
        for record in result:
            concept_type = record.get("type", "unknown")
            count = record.get("count", 0)
            print(f"  {concept_type:20s} {count:,}")


def search_concepts(client: Neo4jClient, search_term: str):
    """Search for concepts."""
    results = client.search_concepts(search_term, limit=20)

    if not results:
        print(f"No concepts found matching '{search_term}'")
        return

    print(f"Found {len(results)} concepts matching '{search_term}':")
    print("-" * 70)

    for i, concept in enumerate(results, 1):
        name = concept["name"]
        concept_type = concept["type"]
        print(f"{i:2d}. {name} ({concept_type})")


def show_concept(client: Neo4jClient, concept_name: str):
    """Show concept details and relationships."""
    concept = client.get_concept(concept_name)

    if not concept:
        print(f"Concept not found: {concept_name}")
        return

    print("=" * 70)
    print(f"Concept: {concept_name}")
    print("=" * 70)
    print(f"Type:        {concept.get('type', 'unknown')}")
    print(f"Confidence:  {concept.get('confidence', 'N/A')}")

    description = concept.get("description", "")
    if description:
        print(f"Description: {description}")

    # Get relationships
    relationships = client.get_concept_relationships(concept_name)

    if relationships:
        print(f"\nRelationships ({len(relationships)}):")
        print("-" * 70)

        # Group by relationship type
        rel_types = {}
        for rel in relationships:
            rel_type = rel["relationship"]
            if rel_type not in rel_types:
                rel_types[rel_type] = []
            rel_types[rel_type].append(rel)

        for rel_type, rels in rel_types.items():
            print(f"\n{rel_type}:")
            for rel in rels:
                source = rel["source"]
                target = rel["target"]
                if source == concept_name:
                    print(f"  → {target}")
                else:
                    print(f"  ← {source}")

    # Get papers mentioning this concept
    query = """
    MATCH (p:Paper)-[m:MENTIONS]->(c:Concept {name: $name})
    RETURN p.id as paper_id, p.title as title, m.confidence as confidence
    LIMIT 10
    """
    papers = client.run_cypher(query, {"name": concept_name})

    if papers:
        print(f"\nMentioned in Papers ({len(papers)}):")
        print("-" * 70)
        for paper in papers:
            title = paper["title"][:50]
            conf = paper.get("confidence", "N/A")
            print(f"  - {title}... (confidence: {conf})")


def show_paper(client: Neo4jClient, paper_id: str):
    """Show paper details."""
    paper = client.get_paper(paper_id)

    if not paper:
        print(f"Paper not found: {paper_id}")
        return

    print("=" * 70)
    print(f"Paper: {paper_id}")
    print("=" * 70)
    print(f"Title:     {paper.get('title', 'Unknown')}")
    print(f"arXiv ID:  {paper.get('arxiv_id', 'N/A')}")

    # Get authors
    query = """
    MATCH (p:Paper {id: $paper_id})-[:AUTHORED_BY]->(a:Author)
    RETURN a.name as author
    """
    authors = client.run_cypher(query, {"paper_id": paper_id})

    if authors:
        author_names = [a["author"] for a in authors]
        print(f"Authors:   {', '.join(author_names)}")

    # Get concepts
    concepts = client.get_paper_concepts(paper_id)

    if concepts:
        print(f"\nConcepts ({len(concepts)}):")
        print("-" * 70)

        # Group by type
        by_type = {}
        for concept in concepts:
            concept_type = concept["type"]
            if concept_type not in by_type:
                by_type[concept_type] = []
            by_type[concept_type].append(concept["concept"])

        for concept_type, names in by_type.items():
            print(f"\n{concept_type}:")
            for name in sorted(names):
                print(f"  - {name}")


def list_papers(client: Neo4jClient):
    """List all papers."""
    query = """
    MATCH (p:Paper)
    RETURN p.id as id, p.title as title, p.arxiv_id as arxiv_id
    ORDER BY p.id
    """
    papers = client.run_cypher(query)

    if not papers:
        print("No papers in database")
        return

    print(f"Papers in Database ({len(papers)}):")
    print("=" * 70)

    for i, paper in enumerate(papers, 1):
        paper_id = paper["id"]
        title = paper["title"][:50] if paper["title"] else "Unknown"
        arxiv_id = paper.get("arxiv_id", "N/A")
        print(f"{i:2d}. {paper_id}")
        print(f"    {title}...")
        if arxiv_id != "N/A":
            print(f"    arXiv: {arxiv_id}")
        print()


def clear_database(client: Neo4jClient, force: bool = False):
    """Clear database with confirmation."""
    if not force:
        print("⚠️  WARNING: This will DELETE ALL data in the Neo4j database!")
        print("\nThis includes:")
        print("  - All concepts")
        print("  - All papers")
        print("  - All authors")
        print("  - All relationships")
        print()
        response = input("Type 'DELETE ALL' to confirm: ")

        if response != "DELETE ALL":
            print("Cancelled")
            return

    client.clear_database()
    print("✓ Database cleared")

    # Recreate constraints
    client.create_constraints()
    print("✓ Constraints recreated")


def run_query(client: Neo4jClient, query: str):
    """Run custom Cypher query."""
    print(f"Running query:\n{query}\n")

    try:
        results = client.run_cypher(query)

        if not results:
            print("No results")
            return

        print(f"Results ({len(results)}):")
        print("=" * 70)

        for i, record in enumerate(results, 1):
            print(f"{i}. {record}")

    except Exception as e:
        print(f"Query error: {e}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Neo4j database management utility",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  stats                    Show database statistics
  search <term>            Search for concepts
  concept <name>           Show concept details
  paper <id>               Show paper details
  papers                   List all papers
  clear                    Clear database (with confirmation)
  query <cypher>           Run custom Cypher query

Examples:
  python scripts/neo4j_manager.py stats
  python scripts/neo4j_manager.py search "neural"
  python scripts/neo4j_manager.py concept "graph transformer"
  python scripts/neo4j_manager.py paper "2403_11996"
  python scripts/neo4j_manager.py query "MATCH (c:Concept) RETURN c LIMIT 5"
        """,
    )

    parser.add_argument("command", help="Command to run")
    parser.add_argument("args", nargs="*", help="Command arguments")
    parser.add_argument("--neo4j-uri", type=str, help="Neo4j URI (overrides .env)")
    parser.add_argument("--neo4j-user", type=str, help="Neo4j username (overrides .env)")
    parser.add_argument("--neo4j-password", type=str, help="Neo4j password (overrides .env)")
    parser.add_argument("--force", action="store_true", help="Skip confirmations")

    args = parser.parse_args()

    # Connect to Neo4j
    try:
        client = Neo4jClient(
            uri=args.neo4j_uri,
            username=args.neo4j_user,
            password=args.neo4j_password,
        )
    except Exception as e:
        print(f"✗ Failed to connect to Neo4j: {e}")
        print("\nMake sure:")
        print("  1. Neo4j is running (docker-compose up -d neo4j)")
        print("  2. NEO4J_PASSWORD is set in .env")
        print("  3. Connection details are correct")
        sys.exit(1)

    # Run command
    try:
        if args.command == "stats":
            show_statistics(client)

        elif args.command == "search":
            if not args.args:
                print("Usage: neo4j_manager.py search <term>")
                sys.exit(1)
            search_concepts(client, args.args[0])

        elif args.command == "concept":
            if not args.args:
                print("Usage: neo4j_manager.py concept <name>")
                sys.exit(1)
            show_concept(client, args.args[0])

        elif args.command == "paper":
            if not args.args:
                print("Usage: neo4j_manager.py paper <id>")
                sys.exit(1)
            show_paper(client, args.args[0])

        elif args.command == "papers":
            list_papers(client)

        elif args.command == "clear":
            clear_database(client, args.force)

        elif args.command == "query":
            if not args.args:
                print("Usage: neo4j_manager.py query <cypher>")
                sys.exit(1)
            query = " ".join(args.args)
            run_query(client, query)

        else:
            print(f"Unknown command: {args.command}")
            print("Run with --help to see available commands")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
    finally:
        client.close()


if __name__ == "__main__":
    main()
