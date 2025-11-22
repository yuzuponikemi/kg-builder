#!/usr/bin/env python3
"""
Batch process multiple papers to extract knowledge graphs.

This script processes all PDF files in a directory and extracts
knowledge graphs from each one, then optionally combines them
into a unified knowledge graph.

Usage:
    python scripts/batch_extract_papers.py [directory]

Examples:
    # Process all papers in data/papers/
    python scripts/batch_extract_papers.py

    # Process papers in custom directory
    python scripts/batch_extract_papers.py path/to/papers/

    # Combine into unified graph
    python scripts/batch_extract_papers.py --combine
"""

import argparse
import json
import sys
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from kg_builder.extractor.entity_extractor import EntityExtractor
from kg_builder.extractor.llm_client import get_llm_client
from kg_builder.extractor.relation_extractor import RelationshipExtractor
from kg_builder.processor.pdf_extractor import PDFExtractor


def extract_from_paper(pdf_path: Path, max_chunks: int = 3) -> dict:
    """Extract knowledge from a single paper.

    Args:
        pdf_path: Path to PDF file
        max_chunks: Maximum chunks to process per paper

    Returns:
        Dictionary with extracted knowledge
    """
    print(f"\nProcessing: {pdf_path.name}")
    print("-" * 70)

    try:
        # Extract text
        extractor = PDFExtractor(pdf_path)
        metadata = extractor.extract_metadata()
        chunks = extractor.extract_chunks(chunk_size=3000, overlap=300)

        print(f"  Title: {metadata.get('title', 'Unknown')[:60]}...")
        print(f"  Pages: {metadata.get('num_pages', 0)}")
        print(f"  Chunks: {len(chunks)} (processing {min(max_chunks, len(chunks))})")

        # Initialize extractors
        llm = get_llm_client()
        entity_extractor = EntityExtractor(llm)
        relation_extractor = RelationshipExtractor(llm)

        # Extract entities
        print(f"  Extracting entities...")
        entities = entity_extractor.extract_batch(chunks[:max_chunks])
        print(f"    ✓ Found {len(entities)} entities")

        # Extract relationships
        print(f"  Extracting relationships...")
        relationships = relation_extractor.extract_batch(chunks[:max_chunks], entities)
        print(f"    ✓ Found {len(relationships)} relationships")

        return {
            "pdf_path": str(pdf_path),
            "metadata": metadata,
            "entities": entities,
            "relationships": relationships,
            "statistics": {
                "num_entities": len(entities),
                "num_relationships": len(relationships),
                "chunks_processed": min(max_chunks, len(chunks)),
                "total_chunks": len(chunks),
            },
        }

    except Exception as e:
        print(f"  ✗ Error: {e}")
        return None


def combine_graphs(graphs: list[dict]) -> dict:
    """Combine multiple knowledge graphs into one.

    Args:
        graphs: List of extracted knowledge graphs

    Returns:
        Combined graph with deduplicated entities and relationships
    """
    print("\nCombining graphs...")
    print("-" * 70)

    # Deduplicate entities by name (case-insensitive)
    all_entities = {}
    for graph in graphs:
        if graph and "entities" in graph:
            for entity in graph["entities"]:
                name_lower = entity["name"].lower()
                # Keep entity with highest confidence
                if (
                    name_lower not in all_entities
                    or entity["confidence"] > all_entities[name_lower]["confidence"]
                ):
                    all_entities[name_lower] = entity

    # Deduplicate relationships
    all_relationships = {}
    for graph in graphs:
        if graph and "relationships" in graph:
            for rel in graph["relationships"]:
                # Create unique key
                key = f"{rel['from'].lower()}|{rel['type']}|{rel['to'].lower()}"
                # Keep relationship with highest confidence
                if (
                    key not in all_relationships
                    or rel["confidence"] > all_relationships[key]["confidence"]
                ):
                    all_relationships[key] = rel

    entities = list(all_entities.values())
    relationships = list(all_relationships.values())

    print(f"  Combined entities: {len(entities)}")
    print(f"  Combined relationships: {len(relationships)}")

    # Collect all paper metadata
    papers = []
    for graph in graphs:
        if graph and "metadata" in graph:
            papers.append(
                {
                    "title": graph["metadata"].get("title", "Unknown"),
                    "pdf_path": graph.get("pdf_path", ""),
                    "num_entities": graph["statistics"]["num_entities"],
                    "num_relationships": graph["statistics"]["num_relationships"],
                }
            )

    return {
        "combined": True,
        "num_papers": len(papers),
        "papers": papers,
        "entities": entities,
        "relationships": relationships,
        "statistics": {
            "total_entities": len(entities),
            "total_relationships": len(relationships),
            "papers_processed": len(papers),
        },
    }


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Batch extract knowledge graphs from multiple papers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "directory",
        nargs="?",
        type=Path,
        default=Path("data/papers"),
        help="Directory containing PDF files (default: data/papers)",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/exports"),
        help="Directory for output files (default: data/exports)",
    )

    parser.add_argument(
        "--max-chunks",
        type=int,
        default=3,
        help="Maximum chunks to process per paper (default: 3)",
    )

    parser.add_argument(
        "--combine",
        action="store_true",
        help="Combine all graphs into one unified knowledge graph",
    )

    parser.add_argument(
        "--pattern", default="*.pdf", help="File pattern to match (default: *.pdf)"
    )

    args = parser.parse_args()

    # Check directory exists
    if not args.directory.exists():
        print(f"Error: Directory not found: {args.directory}")
        sys.exit(1)

    # Find PDFs
    pdf_files = list(args.directory.glob(args.pattern))

    if not pdf_files:
        print(f"No PDF files found in {args.directory}")
        print(f"Pattern: {args.pattern}")
        sys.exit(1)

    print("=" * 70)
    print("Batch Knowledge Graph Extraction")
    print("=" * 70)
    print(f"Directory: {args.directory}")
    print(f"PDF files found: {len(pdf_files)}")
    print(f"Max chunks per paper: {args.max_chunks}")
    print(f"Combine graphs: {args.combine}")
    print()

    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Process each paper
    graphs = []
    successful = 0

    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"\n[{i}/{len(pdf_files)}] {pdf_path.name}")

        # Extract knowledge
        graph = extract_from_paper(pdf_path, max_chunks=args.max_chunks)

        if graph:
            graphs.append(graph)
            successful += 1

            # Save individual graph
            output_file = args.output_dir / f"{pdf_path.stem}_knowledge_graph.json"
            with open(output_file, "w") as f:
                json.dump(graph, f, indent=2)
            print(f"  ✓ Saved to: {output_file.name}")

    # Combine if requested
    if args.combine and graphs:
        print("\n" + "=" * 70)
        combined = combine_graphs(graphs)

        # Save combined graph
        combined_file = args.output_dir / "combined_knowledge_graph.json"
        with open(combined_file, "w") as f:
            json.dump(combined, f, indent=2)

        print(f"\n✓ Combined graph saved to: {combined_file}")

    # Summary
    print("\n" + "=" * 70)
    print("Batch Processing Summary")
    print("=" * 70)
    print(f"Total papers: {len(pdf_files)}")
    print(f"Successfully processed: {successful}")
    print(f"Failed: {len(pdf_files) - successful}")

    if graphs:
        total_entities = sum(g["statistics"]["num_entities"] for g in graphs)
        total_relationships = sum(g["statistics"]["num_relationships"] for g in graphs)

        print(f"\nTotal entities extracted: {total_entities}")
        print(f"Total relationships extracted: {total_relationships}")
        print(f"Average entities per paper: {total_entities / len(graphs):.1f}")
        print(f"Average relationships per paper: {total_relationships / len(graphs):.1f}")

        if args.combine:
            print(f"\nCombined graph statistics:")
            print(f"  Unique entities: {combined['statistics']['total_entities']}")
            print(f"  Unique relationships: {combined['statistics']['total_relationships']}")

    print(f"\nOutput directory: {args.output_dir}")
    print("\n✓ Batch processing complete!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
