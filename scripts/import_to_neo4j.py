#!/usr/bin/env python3
"""
Import JSON knowledge graphs into Neo4j database.

This script loads knowledge graphs from JSON files (created by batch_extract_papers.py)
into Neo4j for advanced querying, analysis, and visualization.

Usage:
    # Import single file
    python scripts/import_to_neo4j.py data/exports/paper_knowledge_graph.json

    # Import all files in directory
    python scripts/import_to_neo4j.py data/exports/

    # Import combined graph
    python scripts/import_to_neo4j.py data/exports/combined_knowledge_graph.json

    # Clear database first
    python scripts/import_to_neo4j.py data/exports/ --clear

    # Dry run (validate without importing)
    python scripts/import_to_neo4j.py data/exports/ --dry-run
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from kg_builder.graph.neo4j_client import Neo4jClient


class KnowledgeGraphImporter:
    """Import knowledge graphs from JSON to Neo4j."""

    def __init__(self, neo4j_client: Neo4jClient, dry_run: bool = False):
        """Initialize importer.

        Args:
            neo4j_client: Neo4j client instance
            dry_run: If True, validate but don't import
        """
        self.client = neo4j_client
        self.dry_run = dry_run
        self.stats = {
            "files_processed": 0,
            "entities_created": 0,
            "relationships_created": 0,
            "papers_created": 0,
            "authors_created": 0,
            "errors": 0,
        }

    def import_from_file(self, json_path: Path) -> dict[str, Any]:
        """Import knowledge graph from a single JSON file.

        Args:
            json_path: Path to JSON file

        Returns:
            Import statistics
        """
        print(f"\n{'[DRY RUN] ' if self.dry_run else ''}Importing: {json_path.name}")

        try:
            with open(json_path) as f:
                data = json.load(f)
        except Exception as e:
            print(f"  ✗ Error reading file: {e}")
            self.stats["errors"] += 1
            return {}

        # Validate structure
        if "entities" not in data or "relationships" not in data:
            print("  ✗ Invalid JSON structure (missing 'entities' or 'relationships')")
            self.stats["errors"] += 1
            return {}

        # Extract metadata
        metadata = data.get("metadata", {})
        source_file = metadata.get("source_file", json_path.stem)
        arxiv_id = metadata.get("arxiv_id")
        title = metadata.get("title", "Unknown")
        authors = metadata.get("authors", [])

        print(f"  📄 Title: {title[:60]}...")
        if arxiv_id:
            print(f"  🔗 arXiv ID: {arxiv_id}")

        # Import paper
        if not self.dry_run:
            paper_props = {
                "title": title,
                "arxiv_id": arxiv_id,
                "source_file": source_file,
                "num_entities": len(data["entities"]),
                "num_relationships": len(data["relationships"]),
            }
            self.client.create_paper(source_file, paper_props)
            self.stats["papers_created"] += 1

            # Import authors
            for author in authors:
                self.client.create_author(author)
                self.client.link_paper_to_author(source_file, author)
                self.stats["authors_created"] += 1

        # Import entities
        entities = data.get("entities", [])
        print(f"  📊 Entities: {len(entities)}")

        entity_names = set()
        for entity in entities:
            name = entity.get("name")
            entity_type = entity.get("type", "unknown")
            confidence = entity.get("confidence", 0.0)

            if not name:
                continue

            entity_names.add(name)

            if not self.dry_run:
                # Create entity
                props = {
                    "confidence": confidence,
                    "description": entity.get("description", ""),
                }
                self.client.create_concept(name, entity_type, props)

                # Link to paper
                mention_props = {"confidence": confidence}
                self.client.link_paper_to_concept(source_file, name, mention_props)

                self.stats["entities_created"] += 1

        # Import relationships
        relationships = data.get("relationships", [])
        print(f"  🔗 Relationships: {len(relationships)}")

        for rel in relationships:
            source = rel.get("source")
            target = rel.get("target")
            rel_type = rel.get("type", "RELATED_TO")
            confidence = rel.get("confidence", 0.0)

            # Validate that entities exist
            if source not in entity_names or target not in entity_names:
                continue

            if not self.dry_run:
                props = {
                    "confidence": confidence,
                    "context": rel.get("context", ""),
                }
                self.client.create_relationship(source, target, rel_type, props)
                self.stats["relationships_created"] += 1

        self.stats["files_processed"] += 1
        print(f"  ✓ Imported successfully")

        return {
            "entities": len(entities),
            "relationships": len(relationships),
            "authors": len(authors),
        }

    def import_from_directory(self, directory: Path) -> dict[str, Any]:
        """Import all JSON knowledge graphs from directory.

        Args:
            directory: Directory containing JSON files

        Returns:
            Import statistics
        """
        json_files = list(directory.glob("*_knowledge_graph.json"))

        if not json_files:
            print(f"No knowledge graph files found in {directory}")
            return self.stats

        print(f"\n{'=' * 70}")
        print(f"Found {len(json_files)} knowledge graph files")
        print(f"{'=' * 70}")

        for json_file in json_files:
            self.import_from_file(json_file)

        return self.stats

    def print_summary(self):
        """Print import summary."""
        print(f"\n{'=' * 70}")
        print("Import Summary")
        print(f"{'=' * 70}")
        print(f"Files processed: {self.stats['files_processed']}")
        print(f"Papers created: {self.stats['papers_created']}")
        print(f"Authors created: {self.stats['authors_created']}")
        print(f"Entities created: {self.stats['entities_created']}")
        print(f"Relationships created: {self.stats['relationships_created']}")

        if self.stats["errors"] > 0:
            print(f"⚠️  Errors: {self.stats['errors']}")

        if not self.dry_run:
            # Get database statistics
            db_stats = self.client.get_statistics()
            print(f"\n{'=' * 70}")
            print("Database Statistics")
            print(f"{'=' * 70}")
            print(f"Total concepts: {db_stats.get('concepts', 0)}")
            print(f"Total papers: {db_stats.get('papers', 0)}")
            print(f"Total authors: {db_stats.get('authors', 0)}")
            print(f"Total relationships: {db_stats.get('relationships', 0)}")
            print(f"Total mentions: {db_stats.get('mentions', 0)}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Import JSON knowledge graphs into Neo4j",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Import single file
  python scripts/import_to_neo4j.py data/exports/paper_knowledge_graph.json

  # Import all files in directory
  python scripts/import_to_neo4j.py data/exports/

  # Clear database and import
  python scripts/import_to_neo4j.py data/exports/ --clear

  # Dry run (validate without importing)
  python scripts/import_to_neo4j.py data/exports/ --dry-run
        """,
    )

    parser.add_argument("path", type=Path, help="Path to JSON file or directory")
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear database before importing (WARNING: deletes all data)",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Validate files without importing"
    )
    parser.add_argument(
        "--neo4j-uri", type=str, help="Neo4j URI (overrides .env)"
    )
    parser.add_argument(
        "--neo4j-user", type=str, help="Neo4j username (overrides .env)"
    )
    parser.add_argument(
        "--neo4j-password", type=str, help="Neo4j password (overrides .env)"
    )

    args = parser.parse_args()

    # Validate path
    if not args.path.exists():
        print(f"Error: Path does not exist: {args.path}")
        sys.exit(1)

    print("=" * 70)
    print("Neo4j Knowledge Graph Importer")
    print("=" * 70)

    if args.dry_run:
        print("\n⚠️  DRY RUN MODE - No data will be imported")

    # Connect to Neo4j
    try:
        client = Neo4jClient(
            uri=args.neo4j_uri,
            username=args.neo4j_user,
            password=args.neo4j_password,
        )
        print(f"✓ Connected to Neo4j")
    except Exception as e:
        print(f"\n✗ Failed to connect to Neo4j: {e}")
        print("\nMake sure:")
        print("  1. Neo4j is running (docker-compose up -d neo4j)")
        print("  2. NEO4J_PASSWORD is set in .env")
        print("  3. Connection details are correct")
        sys.exit(1)

    # Create constraints and indexes
    if not args.dry_run:
        try:
            print("Creating database constraints and indexes...")
            client.create_constraints()
            print("✓ Constraints and indexes ready")
        except Exception as e:
            print(f"⚠️  Warning: {e}")

    # Clear database if requested
    if args.clear and not args.dry_run:
        print("\n⚠️  WARNING: About to clear entire database!")
        response = input("Type 'yes' to confirm: ")
        if response.lower() == "yes":
            client.clear_database()
            print("✓ Database cleared")
            # Recreate constraints
            client.create_constraints()
        else:
            print("Cancelled")
            sys.exit(0)

    # Create importer
    importer = KnowledgeGraphImporter(client, dry_run=args.dry_run)

    # Import
    try:
        if args.path.is_file():
            importer.import_from_file(args.path)
        else:
            importer.import_from_directory(args.path)

        importer.print_summary()

        if args.dry_run:
            print("\n✓ Validation complete (no data imported)")
        else:
            print("\n✓ Import complete!")
            print("\nYou can now:")
            print("  - Query the graph: http://localhost:7474")
            print("  - Use the API (coming soon)")
            print("  - Run graph algorithms (coming soon)")

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n✗ Error during import: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
    finally:
        client.close()


if __name__ == "__main__":
    main()
