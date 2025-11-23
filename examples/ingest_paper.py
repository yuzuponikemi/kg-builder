#!/usr/bin/env python3
"""
Example script to ingest a research paper and extract knowledge graph.

This script demonstrates the complete pipeline:
1. PDF text extraction
2. Entity extraction (concepts, methods, materials, etc.)
3. Relationship extraction (how concepts relate to each other)
4. Saving results to JSON

Usage:
    python examples/ingest_paper.py path/to/paper.pdf
"""

import json
import sys
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from kg_builder.extractor.entity_extractor import EntityExtractor
from kg_builder.extractor.llm_client import get_llm_client
from kg_builder.extractor.relation_extractor import RelationshipExtractor
from kg_builder.processor.pdf_extractor import PDFExtractor


def main():
    """Main function to process a research paper."""
    # Check arguments
    if len(sys.argv) < 2:
        print("Usage: python examples/ingest_paper.py <path_to_pdf>")
        print("\nExample:")
        print("  python examples/ingest_paper.py data/papers/example.pdf")
        sys.exit(1)

    pdf_path = Path(sys.argv[1])

    if not pdf_path.exists():
        print(f"Error: PDF file not found: {pdf_path}")
        sys.exit(1)

    print("=" * 60)
    print("Knowledge Graph Extraction from Research Paper")
    print("=" * 60)
    print(f"\nPDF: {pdf_path}")
    print(f"File size: {pdf_path.stat().st_size / 1024:.1f} KB\n")

    # Step 1: Extract text from PDF
    print("Step 1: Extracting text from PDF...")
    print("-" * 60)

    extractor = PDFExtractor(pdf_path)
    metadata = extractor.extract_metadata()

    print(f"Title: {metadata.get('title', 'Unknown')}")
    print(f"Pages: {metadata.get('num_pages', 0)}")

    # Extract by sections for better context
    sections = extractor.extract_by_sections()
    print(f"Sections found: {len(sections)}")
    print(f"Section names: {', '.join(sections.keys())}")

    # Get full text and chunks
    full_text = extractor.extract_text()
    print(f"Total text length: {len(full_text):,} characters")

    # Create chunks for processing
    chunks = extractor.extract_chunks(chunk_size=3000, overlap=300)
    print(f"Split into {len(chunks)} chunks for processing")

    # Step 2: Extract entities
    print("\n\nStep 2: Extracting entities (concepts, methods, etc.)...")
    print("-" * 60)

    llm = get_llm_client()
    entity_extractor = EntityExtractor(llm)

    # Process first 3 chunks for speed (or all for complete extraction)
    max_chunks = min(3, len(chunks))
    print(f"Processing first {max_chunks} chunks...")

    entities = entity_extractor.extract_batch(chunks[:max_chunks])

    print(f"\n✓ Extracted {len(entities)} unique entities")
    print("\nTop entities by confidence:")
    sorted_entities = sorted(entities, key=lambda x: x["confidence"], reverse=True)
    for entity in sorted_entities[:10]:
        print(
            f"  - {entity['name']} ({entity['type']}) - "
            f"confidence: {entity['confidence']:.2f}"
        )

    # Step 3: Extract relationships
    print("\n\nStep 3: Extracting relationships between entities...")
    print("-" * 60)

    relation_extractor = RelationshipExtractor(llm)

    relationships = relation_extractor.extract_batch(chunks[:max_chunks], entities)

    print(f"\n✓ Extracted {len(relationships)} relationships")
    print("\nTop relationships by confidence:")
    sorted_rels = sorted(relationships, key=lambda x: x["confidence"], reverse=True)
    for rel in sorted_rels[:10]:
        print(
            f"  - {rel['from']} --[{rel['type']}]--> {rel['to']} - "
            f"confidence: {rel['confidence']:.2f}"
        )

    # Step 4: Save results
    print("\n\nStep 4: Saving results...")
    print("-" * 60)

    # Create output filename
    output_dir = Path("data/exports")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"{pdf_path.stem}_knowledge_graph.json"

    # Prepare output data
    output_data = {
        "metadata": metadata,
        "statistics": {
            "num_entities": len(entities),
            "num_relationships": len(relationships),
            "chunks_processed": max_chunks,
            "total_chunks": len(chunks),
        },
        "entities": entities,
        "relationships": relationships,
    }

    # Save to JSON
    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"✓ Results saved to: {output_file}")

    # Step 5: Summary statistics
    print("\n\n" + "=" * 60)
    print("Extraction Summary")
    print("=" * 60)

    # Entity type distribution
    entity_types = {}
    for entity in entities:
        entity_type = entity["type"]
        entity_types[entity_type] = entity_types.get(entity_type, 0) + 1

    print("\nEntity Types:")
    for entity_type, count in sorted(entity_types.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {entity_type}: {count}")

    # Relationship type distribution
    rel_types = {}
    for rel in relationships:
        rel_type = rel["type"]
        rel_types[rel_type] = rel_types.get(rel_type, 0) + 1

    print("\nRelationship Types:")
    for rel_type, count in sorted(rel_types.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {rel_type}: {count}")

    # Average confidence
    if entities:
        avg_entity_conf = sum(e["confidence"] for e in entities) / len(entities)
        print(f"\nAverage entity confidence: {avg_entity_conf:.2f}")

    if relationships:
        avg_rel_conf = sum(r["confidence"] for r in relationships) / len(relationships)
        print(f"Average relationship confidence: {avg_rel_conf:.2f}")

    print("\n✓ Knowledge extraction complete!")
    print(f"\nTo view full results, open: {output_file}")

    # Optional: Visualize as simple graph
    print("\n\nSample Graph Structure:")
    print("-" * 60)
    shown = 0
    for rel in sorted_rels[:5]:
        print(f"{rel['from']} --[{rel['type']}]--> {rel['to']}")
        shown += 1

    print(f"\n(Showing {shown}/{len(relationships)} relationships)")


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
