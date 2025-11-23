#!/usr/bin/env python3
"""
End-to-end knowledge graph building pipeline.

This script performs the complete workflow from topic search to JSON knowledge graph:
1. Search arXiv for relevant papers (prioritizing review papers)
2. Filter papers by relevance using LLM
3. Download selected papers
4. Extract knowledge from papers
5. Save as JSON knowledge graphs
6. Update papers index

Usage:
    # Basic usage
    python scripts/build_knowledge_graph.py "knowledge graph construction"

    # Specify number of papers
    python scripts/build_knowledge_graph.py "graph neural networks" --max-papers 10

    # Prioritize review papers (default: True)
    python scripts/build_knowledge_graph.py "materials science" --review-papers-only

    # Include all paper types
    python scripts/build_knowledge_graph.py "quantum computing" --no-review-preference

    # Set relevance threshold
    python scripts/build_knowledge_graph.py "transformers" --threshold 0.8

    # Create combined graph
    python scripts/build_knowledge_graph.py "deep learning" --combine
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from kg_builder.config.settings import get_settings
from kg_builder.extractor.entity_extractor import EntityExtractor
from kg_builder.extractor.llm_client import get_llm_client
from kg_builder.extractor.relation_extractor import RelationshipExtractor
from kg_builder.processor.pdf_extractor import PDFExtractor
from kg_builder.search.arxiv_search import ArxivSearcher
from kg_builder.search.llm_filter import LLMRelevanceFilter


class ProgressTracker:
    """Track and display pipeline progress."""

    def __init__(self, verbose: bool = True):
        """Initialize progress tracker.

        Args:
            verbose: If True, show detailed progress
        """
        self.verbose = verbose
        self.current_step = 0
        self.total_steps = 6
        self.start_time = time.time()

    def start_step(self, step_name: str, description: str = ""):
        """Start a new step.

        Args:
            step_name: Name of the step
            description: Optional description
        """
        self.current_step += 1
        print(f"\n{'=' * 80}")
        print(f"Step {self.current_step}/{self.total_steps}: {step_name}")
        if description:
            print(f"Description: {description}")
        print(f"{'=' * 80}")

    def log(self, message: str, indent: int = 0):
        """Log a message.

        Args:
            message: Message to log
            indent: Indentation level
        """
        if self.verbose:
            prefix = "  " * indent
            print(f"{prefix}{message}")

    def complete_step(self, summary: str = ""):
        """Complete current step.

        Args:
            summary: Optional summary
        """
        if summary:
            print(f"✓ {summary}")

    def show_summary(self, stats: dict[str, Any]):
        """Show final summary.

        Args:
            stats: Pipeline statistics
        """
        elapsed = time.time() - self.start_time
        print(f"\n{'=' * 80}")
        print("Pipeline Summary")
        print(f"{'=' * 80}")
        print(f"Total time: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
        print(f"\nPapers:")
        print(f"  Searched:    {stats.get('papers_searched', 0)}")
        print(f"  Filtered:    {stats.get('papers_filtered', 0)}")
        print(f"  Downloaded:  {stats.get('papers_downloaded', 0)}")
        print(f"  Processed:   {stats.get('papers_processed', 0)}")
        print(f"\nKnowledge Extraction:")
        print(f"  Total entities:      {stats.get('total_entities', 0)}")
        print(f"  Total relationships: {stats.get('total_relationships', 0)}")
        print(f"\nOutput:")
        print(f"  JSON files created: {stats.get('json_files', 0)}")
        if stats.get('combined_graph'):
            print(f"  Combined graph:     {stats['combined_graph']}")
        print(f"\nFiles saved to:")
        print(f"  Papers:  {stats.get('papers_dir', 'data/papers/')}")
        print(f"  Exports: {stats.get('exports_dir', 'data/exports/')}")
        print(f"\n{'=' * 80}")


class KnowledgeGraphPipeline:
    """End-to-end pipeline for building knowledge graphs from research papers."""

    def __init__(
        self,
        topic: str,
        max_papers: int = 5,
        relevance_threshold: float = 0.7,
        prefer_reviews: bool = True,
        review_only: bool = False,
        combine: bool = False,
        verbose: bool = True,
    ):
        """Initialize pipeline.

        Args:
            topic: Research topic to search for
            max_papers: Maximum number of papers to process
            relevance_threshold: Minimum relevance score (0.0-1.0)
            prefer_reviews: Prefer review papers over regular papers
            review_only: Only select review papers
            combine: Create combined knowledge graph
            verbose: Show detailed progress
        """
        self.topic = topic
        self.max_papers = max_papers
        self.relevance_threshold = relevance_threshold
        self.prefer_reviews = prefer_reviews
        self.review_only = review_only
        self.combine = combine
        self.verbose = verbose

        # Initialize components
        self.settings = get_settings()
        self.progress = ProgressTracker(verbose=verbose)
        self.llm_client = get_llm_client()
        self.arxiv_searcher = ArxivSearcher()
        self.llm_filter = LLMRelevanceFilter(self.llm_client)
        self.entity_extractor = EntityExtractor(self.llm_client)
        self.relation_extractor = RelationshipExtractor(self.llm_client)

        # Statistics
        self.stats = {
            "papers_searched": 0,
            "papers_filtered": 0,
            "papers_downloaded": 0,
            "papers_processed": 0,
            "total_entities": 0,
            "total_relationships": 0,
            "json_files": 0,
            "combined_graph": None,
            "papers_dir": str(self.settings.papers_dir),
            "exports_dir": str(self.settings.exports_dir),
        }

    def build_search_query(self) -> str:
        """Build search query that prioritizes review papers.

        Returns:
            Enhanced search query
        """
        if self.review_only:
            # Only review papers
            return f'({self.topic}) AND (ti:"review" OR ti:"survey" OR abs:"review paper")'
        elif self.prefer_reviews:
            # Prefer but don't require reviews
            return f'{self.topic} (review OR survey OR overview)'
        else:
            # Original topic only
            return self.topic

    def step1_search_papers(self) -> list[Any]:
        """Step 1: Search arXiv for papers.

        Returns:
            List of ArxivPaper objects
        """
        self.progress.start_step(
            "Search arXiv",
            f"Searching for papers on: {self.topic}"
        )

        query = self.build_search_query()
        self.progress.log(f"Search query: {query}", indent=1)

        if self.prefer_reviews or self.review_only:
            self.progress.log("Priority: Review/Survey papers", indent=1)

        # Search with more results to filter from
        max_results = self.max_papers * 3

        papers = self.arxiv_searcher.search(
            query=query,
            max_results=max_results,
            sort_by="relevance"
        )

        self.stats["papers_searched"] = len(papers)
        self.progress.complete_step(f"Found {len(papers)} papers")

        return papers

    def step2_filter_papers(self, papers: list[Any]) -> list[tuple[Any, float, str]]:
        """Step 2: Filter papers by relevance using LLM.

        Args:
            papers: List of ArxivPaper objects

        Returns:
            List of (paper, score, reasoning) tuples
        """
        self.progress.start_step(
            "Filter by Relevance",
            f"Using LLM to assess relevance to: {self.topic}"
        )

        filtered = []
        for i, paper in enumerate(papers, 1):
            self.progress.log(f"[{i}/{len(papers)}] Assessing: {paper.title[:60]}...", indent=1)

            # Assess relevance
            result = self.llm_filter.assess_relevance(paper, self.topic)

            # Boost score for review papers if preferred
            score = result.score
            if self.prefer_reviews and self._is_review_paper(paper):
                original_score = score
                score = min(1.0, score * 1.15)  # 15% boost
                self.progress.log(
                    f"  Review paper boost: {original_score:.2f} → {score:.2f}",
                    indent=2
                )

            self.progress.log(f"  Score: {score:.2f} - {result.reasoning[:80]}...", indent=2)

            if score >= self.relevance_threshold:
                filtered.append((paper, score, result.reasoning))
                self.progress.log(f"  ✓ Selected", indent=2)
            else:
                self.progress.log(f"  ✗ Below threshold ({self.relevance_threshold})", indent=2)

        # Sort by score and take top N
        filtered.sort(key=lambda x: x[1], reverse=True)
        filtered = filtered[:self.max_papers]

        self.stats["papers_filtered"] = len(filtered)
        self.progress.complete_step(
            f"Selected {len(filtered)} papers (threshold: {self.relevance_threshold})"
        )

        return filtered

    def step3_download_papers(self, filtered_papers: list[tuple[Any, float, str]]) -> list[Path]:
        """Step 3: Download selected papers.

        Args:
            filtered_papers: List of (paper, score, reasoning) tuples

        Returns:
            List of downloaded PDF paths
        """
        self.progress.start_step(
            "Download Papers",
            f"Downloading {len(filtered_papers)} papers"
        )

        downloaded = []
        for i, (paper, score, _) in enumerate(filtered_papers, 1):
            self.progress.log(
                f"[{i}/{len(filtered_papers)}] Downloading: {paper.title[:60]}...",
                indent=1
            )

            try:
                pdf_path = self.arxiv_searcher.download_paper(
                    paper,
                    output_dir=self.settings.papers_dir
                )
                downloaded.append(pdf_path)
                self.progress.log(f"  ✓ Saved to: {pdf_path.name}", indent=2)
            except Exception as e:
                self.progress.log(f"  ✗ Error: {e}", indent=2)

            # Rate limiting
            if i < len(filtered_papers):
                time.sleep(1)

        self.stats["papers_downloaded"] = len(downloaded)
        self.progress.complete_step(f"Downloaded {len(downloaded)} papers")

        return downloaded

    def step4_extract_knowledge(self, pdf_paths: list[Path]) -> list[dict[str, Any]]:
        """Step 4: Extract knowledge from papers.

        Args:
            pdf_paths: List of PDF file paths

        Returns:
            List of knowledge graphs
        """
        self.progress.start_step(
            "Extract Knowledge",
            f"Extracting entities and relationships from {len(pdf_paths)} papers"
        )

        knowledge_graphs = []

        for i, pdf_path in enumerate(pdf_paths, 1):
            self.progress.log(f"[{i}/{len(pdf_paths)}] Processing: {pdf_path.name}", indent=1)

            try:
                # Extract text from PDF
                self.progress.log("Extracting text from PDF...", indent=2)
                pdf_extractor = PDFExtractor(pdf_path)
                metadata = pdf_extractor.extract_metadata()
                text_chunks = pdf_extractor.extract_chunks(chunk_size=2000, overlap=200)

                self.progress.log(f"  Extracted {len(text_chunks)} text chunks", indent=2)

                # Extract entities
                self.progress.log("Extracting entities...", indent=2)
                all_entities = []
                for chunk_idx, chunk in enumerate(text_chunks):
                    entities = self.entity_extractor.extract(chunk)
                    all_entities.extend(entities)
                    if (chunk_idx + 1) % 5 == 0:
                        self.progress.log(
                            f"  Processed {chunk_idx + 1}/{len(text_chunks)} chunks",
                            indent=3
                        )

                # Deduplicate entities
                unique_entities = self._deduplicate_entities(all_entities)
                self.progress.log(
                    f"  Found {len(unique_entities)} unique entities (from {len(all_entities)} total)",
                    indent=2
                )

                # Extract relationships
                self.progress.log("Extracting relationships...", indent=2)
                all_relationships = []
                for chunk_idx, chunk in enumerate(text_chunks):
                    relationships = self.relation_extractor.extract(chunk, unique_entities)
                    all_relationships.extend(relationships)
                    if (chunk_idx + 1) % 5 == 0:
                        self.progress.log(
                            f"  Processed {chunk_idx + 1}/{len(text_chunks)} chunks",
                            indent=3
                        )

                # Deduplicate relationships
                unique_relationships = self._deduplicate_relationships(all_relationships)
                self.progress.log(
                    f"  Found {len(unique_relationships)} unique relationships "
                    f"(from {len(all_relationships)} total)",
                    indent=2
                )

                # Create knowledge graph
                kg = {
                    "metadata": {
                        "source_file": pdf_path.name,
                        "title": metadata.get("title", pdf_path.stem),
                        "authors": metadata.get("authors", []),
                        "num_pages": metadata.get("num_pages", 0),
                        "extraction_date": datetime.now().isoformat(),
                        "arxiv_id": self._extract_arxiv_id(pdf_path.name),
                    },
                    "entities": unique_entities,
                    "relationships": unique_relationships,
                    "statistics": {
                        "num_entities": len(unique_entities),
                        "num_relationships": len(unique_relationships),
                        "num_chunks_processed": len(text_chunks),
                    },
                }

                knowledge_graphs.append(kg)

                self.stats["total_entities"] += len(unique_entities)
                self.stats["total_relationships"] += len(unique_relationships)
                self.stats["papers_processed"] += 1

                self.progress.log(
                    f"✓ Extracted {len(unique_entities)} entities, "
                    f"{len(unique_relationships)} relationships",
                    indent=2
                )

            except Exception as e:
                self.progress.log(f"✗ Error processing {pdf_path.name}: {e}", indent=2)
                import traceback
                if self.verbose:
                    traceback.print_exc()

        self.progress.complete_step(
            f"Processed {len(knowledge_graphs)} papers, "
            f"extracted {self.stats['total_entities']} entities, "
            f"{self.stats['total_relationships']} relationships"
        )

        return knowledge_graphs

    def step5_save_json(self, knowledge_graphs: list[dict[str, Any]]) -> list[Path]:
        """Step 5: Save knowledge graphs as JSON.

        Args:
            knowledge_graphs: List of knowledge graph dictionaries

        Returns:
            List of saved JSON file paths
        """
        self.progress.start_step(
            "Save JSON Files",
            f"Saving {len(knowledge_graphs)} knowledge graphs"
        )

        exports_dir = self.settings.exports_dir
        exports_dir.mkdir(parents=True, exist_ok=True)

        saved_files = []

        # Save individual graphs
        for i, kg in enumerate(knowledge_graphs, 1):
            source_file = kg["metadata"]["source_file"]
            json_name = source_file.replace(".pdf", "_knowledge_graph.json")
            json_path = exports_dir / json_name

            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(kg, f, indent=2, ensure_ascii=False)

            saved_files.append(json_path)
            self.stats["json_files"] += 1

            self.progress.log(
                f"[{i}/{len(knowledge_graphs)}] Saved: {json_path.name}",
                indent=1
            )

        # Save combined graph if requested
        if self.combine and len(knowledge_graphs) > 1:
            combined_kg = self._create_combined_graph(knowledge_graphs)
            combined_path = exports_dir / "combined_knowledge_graph.json"

            with open(combined_path, "w", encoding="utf-8") as f:
                json.dump(combined_kg, f, indent=2, ensure_ascii=False)

            saved_files.append(combined_path)
            self.stats["combined_graph"] = str(combined_path)

            self.progress.log(f"Saved combined graph: {combined_path.name}", indent=1)

        self.progress.complete_step(f"Saved {len(saved_files)} JSON files")

        return saved_files

    def step6_update_index(self, knowledge_graphs: list[dict[str, Any]]):
        """Step 6: Update papers index.

        Args:
            knowledge_graphs: List of knowledge graph dictionaries
        """
        self.progress.start_step(
            "Update Index",
            "Updating papers_index.json"
        )

        index_path = self.settings.papers_dir / "papers_index.json"

        # Load existing index
        if index_path.exists():
            with open(index_path, encoding="utf-8") as f:
                index = json.load(f)
        else:
            index = {
                "papers": [],
                "last_updated": None,
                "total_papers": 0,
            }

        # Add new papers
        existing_ids = {p["source_file"] for p in index["papers"]}

        for kg in knowledge_graphs:
            source_file = kg["metadata"]["source_file"]
            if source_file not in existing_ids:
                index["papers"].append({
                    "source_file": source_file,
                    "title": kg["metadata"]["title"],
                    "authors": kg["metadata"]["authors"],
                    "arxiv_id": kg["metadata"].get("arxiv_id"),
                    "num_entities": kg["statistics"]["num_entities"],
                    "num_relationships": kg["statistics"]["num_relationships"],
                    "extraction_date": kg["metadata"]["extraction_date"],
                })

        # Update metadata
        index["last_updated"] = datetime.now().isoformat()
        index["total_papers"] = len(index["papers"])

        # Save index
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2, ensure_ascii=False)

        self.progress.complete_step(f"Updated index: {len(index['papers'])} total papers")

    def run(self) -> dict[str, Any]:
        """Run complete pipeline.

        Returns:
            Pipeline statistics
        """
        try:
            # Step 1: Search papers
            papers = self.step1_search_papers()

            if not papers:
                self.progress.log("\n✗ No papers found. Try a different query.", indent=0)
                return self.stats

            # Step 2: Filter papers
            filtered_papers = self.step2_filter_papers(papers)

            if not filtered_papers:
                self.progress.log(
                    f"\n✗ No papers passed the relevance threshold ({self.relevance_threshold}). "
                    "Try lowering the threshold.",
                    indent=0
                )
                return self.stats

            # Step 3: Download papers
            pdf_paths = self.step3_download_papers(filtered_papers)

            if not pdf_paths:
                self.progress.log("\n✗ Failed to download papers.", indent=0)
                return self.stats

            # Step 4: Extract knowledge
            knowledge_graphs = self.step4_extract_knowledge(pdf_paths)

            if not knowledge_graphs:
                self.progress.log("\n✗ Failed to extract knowledge from papers.", indent=0)
                return self.stats

            # Step 5: Save JSON
            self.step5_save_json(knowledge_graphs)

            # Step 6: Update index
            self.step6_update_index(knowledge_graphs)

            # Show summary
            self.progress.show_summary(self.stats)

            return self.stats

        except KeyboardInterrupt:
            self.progress.log("\n\n⚠️  Pipeline interrupted by user", indent=0)
            self.progress.show_summary(self.stats)
            return self.stats
        except Exception as e:
            self.progress.log(f"\n\n✗ Pipeline error: {e}", indent=0)
            import traceback
            traceback.print_exc()
            return self.stats

    def _is_review_paper(self, paper: Any) -> bool:
        """Check if paper is a review paper.

        Args:
            paper: ArxivPaper object

        Returns:
            True if likely a review paper
        """
        review_keywords = ["review", "survey", "overview", "tutorial", "perspective"]
        title_lower = paper.title.lower()
        abstract_lower = paper.abstract.lower()

        return any(keyword in title_lower or keyword in abstract_lower for keyword in review_keywords)

    def _deduplicate_entities(self, entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Deduplicate entities by name.

        Args:
            entities: List of entity dictionaries

        Returns:
            Deduplicated entities
        """
        seen = {}
        for entity in entities:
            name = entity.get("name", "").lower().strip()
            if name and name not in seen:
                seen[name] = entity
            elif name and entity.get("confidence", 0) > seen[name].get("confidence", 0):
                # Keep higher confidence version
                seen[name] = entity

        return list(seen.values())

    def _deduplicate_relationships(self, relationships: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Deduplicate relationships.

        Args:
            relationships: List of relationship dictionaries

        Returns:
            Deduplicated relationships
        """
        seen = {}
        for rel in relationships:
            source = rel.get("source", "").lower().strip()
            target = rel.get("target", "").lower().strip()
            rel_type = rel.get("type", "").upper()
            key = (source, target, rel_type)

            if key not in seen:
                seen[key] = rel
            elif rel.get("confidence", 0) > seen[key].get("confidence", 0):
                seen[key] = rel

        return list(seen.values())

    def _create_combined_graph(self, graphs: list[dict[str, Any]]) -> dict[str, Any]:
        """Create combined knowledge graph from multiple graphs.

        Args:
            graphs: List of knowledge graphs

        Returns:
            Combined knowledge graph
        """
        all_entities = []
        all_relationships = []
        all_papers = []

        for graph in graphs:
            all_entities.extend(graph["entities"])
            all_relationships.extend(graph["relationships"])
            all_papers.append({
                "source_file": graph["metadata"]["source_file"],
                "title": graph["metadata"]["title"],
                "authors": graph["metadata"]["authors"],
            })

        # Deduplicate across all papers
        unique_entities = self._deduplicate_entities(all_entities)
        unique_relationships = self._deduplicate_relationships(all_relationships)

        return {
            "metadata": {
                "creation_date": datetime.now().isoformat(),
                "description": f"Combined knowledge graph from {len(graphs)} papers on: {self.topic}",
                "num_papers": len(graphs),
                "papers": all_papers,
            },
            "entities": unique_entities,
            "relationships": unique_relationships,
            "statistics": {
                "num_papers": len(graphs),
                "num_entities": len(unique_entities),
                "num_relationships": len(unique_relationships),
            },
        }

    def _extract_arxiv_id(self, filename: str) -> str | None:
        """Extract arXiv ID from filename.

        Args:
            filename: PDF filename

        Returns:
            arXiv ID or None
        """
        import re
        match = re.search(r'(\d{4}\.\d{4,5})', filename)
        return match.group(1) if match else None


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Build knowledge graph from research papers (end-to-end pipeline)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic: Get 5 papers on a topic
  python scripts/build_knowledge_graph.py "knowledge graph construction"

  # Specify number of papers
  python scripts/build_knowledge_graph.py "graph neural networks" --max-papers 10

  # Only review papers (established knowledge)
  python scripts/build_knowledge_graph.py "materials science" --review-papers-only

  # Include all paper types
  python scripts/build_knowledge_graph.py "quantum computing" --no-review-preference

  # Higher quality threshold
  python scripts/build_knowledge_graph.py "transformers" --threshold 0.8

  # Create combined graph
  python scripts/build_knowledge_graph.py "deep learning" --combine

  # Quiet mode
  python scripts/build_knowledge_graph.py "topic" --quiet
        """,
    )

    parser.add_argument("topic", help="Research topic to search for")
    parser.add_argument(
        "--max-papers",
        type=int,
        default=5,
        help="Maximum number of papers to process (default: 5)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.7,
        help="Relevance threshold 0.0-1.0 (default: 0.7)",
    )
    parser.add_argument(
        "--review-papers-only",
        action="store_true",
        help="Only select review/survey papers (established knowledge)",
    )
    parser.add_argument(
        "--no-review-preference",
        action="store_true",
        help="Don't prefer review papers (default: prefer reviews)",
    )
    parser.add_argument(
        "--combine",
        action="store_true",
        help="Create combined knowledge graph from all papers",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Reduce output verbosity",
    )

    args = parser.parse_args()

    # Validate threshold
    if not 0.0 <= args.threshold <= 1.0:
        print("Error: Threshold must be between 0.0 and 1.0")
        sys.exit(1)

    print("=" * 80)
    print("Knowledge Graph Builder - End-to-End Pipeline")
    print("=" * 80)
    print(f"Topic: {args.topic}")
    print(f"Max papers: {args.max_papers}")
    print(f"Relevance threshold: {args.threshold}")
    if args.review_papers_only:
        print("Mode: Review/Survey papers ONLY")
    elif not args.no_review_preference:
        print("Mode: Prefer review/survey papers")
    else:
        print("Mode: All paper types")
    print(f"Combined graph: {args.combine}")
    print()

    # Run pipeline
    pipeline = KnowledgeGraphPipeline(
        topic=args.topic,
        max_papers=args.max_papers,
        relevance_threshold=args.threshold,
        prefer_reviews=not args.no_review_preference,
        review_only=args.review_papers_only,
        combine=args.combine,
        verbose=not args.quiet,
    )

    stats = pipeline.run()

    # Exit with appropriate code
    if stats["papers_processed"] > 0:
        print("\n✓ Pipeline completed successfully!")
        print("\nNext steps:")
        print("  - Review JSON files in data/exports/")
        print("  - Import to Neo4j: python scripts/import_to_neo4j.py data/exports/")
        print("  - Explore in browser: http://localhost:7474")
        sys.exit(0)
    else:
        print("\n✗ Pipeline completed with no papers processed")
        sys.exit(1)


if __name__ == "__main__":
    main()
