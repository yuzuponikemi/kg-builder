#!/usr/bin/env python3
"""
Create and maintain an index of processed papers.

This script creates a papers_index.json file that tracks all processed papers
without including the actual PDF files. This allows sharing the paper metadata
on GitHub while keeping PDFs local.

Usage:
    python scripts/create_papers_index.py
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from kg_builder.processor.pdf_extractor import PDFExtractor


def create_index(papers_dir: Path = Path("data/papers")) -> dict:
    """Create index of all papers in directory.

    Args:
        papers_dir: Directory containing PDFs

    Returns:
        Dictionary with paper index
    """
    papers_dir = Path(papers_dir)

    if not papers_dir.exists():
        print(f"Directory not found: {papers_dir}")
        return {"papers": [], "last_updated": datetime.now().isoformat()}

    # Find all PDFs
    pdf_files = list(papers_dir.glob("*.pdf"))

    print(f"Found {len(pdf_files)} PDF files")
    print("Extracting metadata...\n")

    papers = []

    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"[{i}/{len(pdf_files)}] {pdf_path.name}")

        try:
            extractor = PDFExtractor(pdf_path)
            metadata = extractor.extract_metadata()

            # Extract arXiv ID if present in filename
            arxiv_id = None
            if "_" in pdf_path.stem:
                # Format: 2403_11996.pdf -> 2403.11996
                parts = pdf_path.stem.split("_")
                if len(parts) >= 2 and parts[0].isdigit():
                    arxiv_id = f"{parts[0]}.{parts[1]}"

            paper_info = {
                "filename": pdf_path.name,
                "arxiv_id": arxiv_id,
                "title": metadata.get("title", "Unknown"),
                "author": metadata.get("author", ""),
                "num_pages": metadata.get("num_pages", 0),
                "file_size_mb": round(metadata.get("file_size", 0) / (1024 * 1024), 2),
                "creation_date": metadata.get("creation_date", ""),
                "added_to_index": datetime.now().isoformat(),
            }

            # Check if knowledge graph exists
            kg_path = Path("data/exports") / f"{pdf_path.stem}_knowledge_graph.json"
            paper_info["knowledge_graph_extracted"] = kg_path.exists()

            if paper_info["knowledge_graph_extracted"]:
                # Get stats from knowledge graph
                with open(kg_path) as f:
                    kg_data = json.load(f)
                    stats = kg_data.get("statistics", {})
                    paper_info["num_entities"] = stats.get("num_entities", 0)
                    paper_info["num_relationships"] = stats.get("num_relationships", 0)

            papers.append(paper_info)
            print(f"  ✓ {paper_info['title'][:60]}...")

        except Exception as e:
            print(f"  ✗ Error: {e}")
            papers.append(
                {
                    "filename": pdf_path.name,
                    "title": "Error extracting metadata",
                    "error": str(e),
                    "added_to_index": datetime.now().isoformat(),
                }
            )

    # Create index
    index = {
        "description": "Index of processed research papers (PDFs kept local)",
        "total_papers": len(papers),
        "papers": papers,
        "last_updated": datetime.now().isoformat(),
        "note": "PDF files are not included in version control. Only metadata is tracked.",
    }

    return index


def main():
    """Main function."""
    print("=" * 70)
    print("Creating Papers Index")
    print("=" * 70)
    print()

    # Create index
    index = create_index()

    # Save to JSON
    output_path = Path("data/papers/papers_index.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 70}")
    print("Index Summary")
    print("=" * 70)
    print(f"Total papers: {index['total_papers']}")

    with_kg = sum(1 for p in index["papers"] if p.get("knowledge_graph_extracted", False))
    print(f"Knowledge graphs extracted: {with_kg}/{index['total_papers']}")

    if index["papers"]:
        total_size = sum(p.get("file_size_mb", 0) for p in index["papers"])
        print(f"Total size (PDFs): {total_size:.2f} MB")

        avg_entities = 0
        avg_rels = 0
        count = 0
        for p in index["papers"]:
            if "num_entities" in p:
                avg_entities += p["num_entities"]
                avg_rels += p["num_relationships"]
                count += 1

        if count > 0:
            print(f"\nAverage per paper:")
            print(f"  Entities: {avg_entities / count:.1f}")
            print(f"  Relationships: {avg_rels / count:.1f}")

    print(f"\n✓ Index saved to: {output_path}")
    print("\nThis file can be committed to GitHub (PDFs stay local)")


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
