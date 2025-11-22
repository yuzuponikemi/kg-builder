#!/usr/bin/env python3
"""
Search arXiv for papers and download relevant ones using LLM filtering.

This script:
1. Searches arXiv based on your query
2. Uses LLM to assess relevance of each paper
3. Downloads papers that meet the relevance threshold
4. Optionally processes them to extract knowledge graphs

Usage:
    python scripts/search_and_download_papers.py "your research query"

Examples:
    # Search for papers on knowledge graphs
    python scripts/search_and_download_papers.py "knowledge graph construction from text"

    # Search with more results
    python scripts/search_and_download_papers.py "neural networks materials science" --max-results 20

    # Lower relevance threshold to get more papers
    python scripts/search_and_download_papers.py "quantum computing" --threshold 0.5

    # Download and extract knowledge immediately
    python scripts/search_and_download_papers.py "LLM reasoning" --auto-extract
"""

import argparse
import sys
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from kg_builder.search.arxiv_search import ArxivSearcher
from kg_builder.search.llm_filter import LLMRelevanceFilter


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Search arXiv and download relevant papers using LLM filtering",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Search for knowledge graph papers:
    python scripts/search_and_download_papers.py "knowledge graph construction"

  Get more results with lower threshold:
    python scripts/search_and_download_papers.py "machine learning" --max-results 20 --threshold 0.5

  Download and extract immediately:
    python scripts/search_and_download_papers.py "LLM agents" --auto-extract
        """,
    )

    parser.add_argument("query", help="Research query to search for")

    parser.add_argument(
        "--max-results",
        type=int,
        default=10,
        help="Maximum number of papers to search (default: 10)",
    )

    parser.add_argument(
        "--threshold",
        type=float,
        default=0.6,
        help="Relevance threshold 0.0-1.0 (default: 0.6). Papers scoring above this are downloaded.",
    )

    parser.add_argument(
        "--top-n",
        type=int,
        help="Download only top N most relevant papers (overrides threshold)",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/papers"),
        help="Directory to save PDFs (default: data/papers)",
    )

    parser.add_argument(
        "--no-filter",
        action="store_true",
        help="Skip LLM filtering and download all search results",
    )

    parser.add_argument(
        "--auto-extract",
        action="store_true",
        help="Automatically extract knowledge graphs after downloading",
    )

    parser.add_argument(
        "--category",
        help="Limit search to specific arXiv category (e.g., cs.AI, physics.comp-ph)",
    )

    parser.add_argument(
        "--recent-days", type=int, help="Only search papers from last N days"
    )

    parser.add_argument(
        "--sort-by",
        choices=["relevance", "lastUpdatedDate", "submittedDate"],
        default="relevance",
        help="Sort results by (default: relevance)",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("arXiv Paper Search & Download with LLM Filtering")
    print("=" * 70)
    print(f"\nQuery: {args.query}")
    print(f"Max results: {args.max_results}")

    if not args.no_filter:
        print(f"Relevance threshold: {args.threshold}")
        if args.top_n:
            print(f"Download top: {args.top_n} papers")

    print()

    # Step 1: Search arXiv
    print("Step 1: Searching arXiv...")
    print("-" * 70)

    with ArxivSearcher() as searcher:
        if args.category:
            print(f"Searching category: {args.category}")
            papers = searcher.search_by_category(
                category=args.category,
                max_results=args.max_results,
                recent_days=args.recent_days,
            )
        else:
            # Build query
            query = args.query
            if args.recent_days:
                from datetime import datetime, timedelta

                end_date = datetime.now()
                start_date = end_date - timedelta(days=args.recent_days)
                start_str = start_date.strftime("%Y%m%d0000")
                end_str = end_date.strftime("%Y%m%d2359")
                query += f" AND submittedDate:[{start_str} TO {end_str}]"

            papers = searcher.search(
                query=query, max_results=args.max_results, sort_by=args.sort_by
            )

        print(f"✓ Found {len(papers)} papers\n")

        if not papers:
            print("No papers found. Try a different query or increase max-results.")
            return

        # Show preview
        print("Preview of search results:")
        for i, paper in enumerate(papers[:3], 1):
            print(f"\n{i}. {paper.arxiv_id}: {paper.title}")
            print(f"   Authors: {', '.join(paper.authors[:2])}")
            if len(paper.authors) > 2:
                print(f"   ({len(paper.authors)} total authors)")
            print(f"   Published: {paper.published.strftime('%Y-%m-%d')}")

        if len(papers) > 3:
            print(f"\n... and {len(papers) - 3} more")

        # Step 2: LLM Filtering (unless disabled)
        to_download = papers

        if not args.no_filter:
            print("\n\nStep 2: Assessing relevance with LLM...")
            print("-" * 70)
            print("This will use your configured LLM (Ollama by default) to assess")
            print("how relevant each paper is to your query.\n")

            filter_obj = LLMRelevanceFilter(threshold=args.threshold)

            if args.top_n:
                # Get top N
                scores = filter_obj.batch_assess(papers, args.query, top_n=args.top_n)
                to_download = [s.paper for s in scores]

                print(f"\n✓ Selected top {len(to_download)} papers:")
                for score in scores:
                    print(f"  [{score.score:.2f}] {score.paper.arxiv_id}: {score.paper.title}")

            else:
                # Filter by threshold
                scores = filter_obj.filter_papers(papers, args.query, verbose=True)
                relevant_scores = [s for s in scores if s.is_relevant]
                to_download = [s.paper for s in relevant_scores]

                print(f"\n✓ {len(to_download)}/{len(papers)} papers meet relevance threshold")

                if relevant_scores:
                    print("\nRelevant papers:")
                    for score in relevant_scores:
                        print(f"  [{score.score:.2f}] {score.paper.arxiv_id}")
        else:
            print("\nStep 2: Skipping LLM filtering (--no-filter)")

        # Step 3: Download
        if not to_download:
            print("\n✗ No relevant papers to download.")
            print("Try lowering the threshold (--threshold 0.4) or increasing max-results.")
            return

        print(f"\n\nStep 3: Downloading {len(to_download)} papers...")
        print("-" * 70)

        downloaded = []
        for i, paper in enumerate(to_download, 1):
            print(f"\n[{i}/{len(to_download)}] {paper.arxiv_id}: {paper.title[:60]}...")
            try:
                pdf_path = searcher.download_paper(paper, output_dir=args.output_dir)
                downloaded.append((paper, pdf_path))
            except Exception as e:
                print(f"  ✗ Failed: {e}")

        print(f"\n✓ Downloaded {len(downloaded)}/{len(to_download)} papers")
        print(f"  Saved to: {args.output_dir}")

        # Step 4: Auto-extract (if requested)
        if args.auto_extract and downloaded:
            print("\n\nStep 4: Extracting knowledge graphs...")
            print("-" * 70)
            print("Running knowledge extraction on downloaded papers...\n")

            import subprocess

            for paper, pdf_path in downloaded:
                print(f"\nExtracting: {paper.arxiv_id}")
                try:
                    subprocess.run(
                        [sys.executable, "examples/ingest_paper.py", str(pdf_path)], check=True
                    )
                except Exception as e:
                    print(f"  ✗ Extraction failed: {e}")

        # Summary
        print("\n\n" + "=" * 70)
        print("Summary")
        print("=" * 70)
        print(f"Search query: {args.query}")
        print(f"Papers found: {len(papers)}")

        if not args.no_filter:
            print(f"Papers meeting threshold: {len(to_download)}")

        print(f"Papers downloaded: {len(downloaded)}")
        print(f"Location: {args.output_dir}")

        if downloaded:
            print("\nDownloaded papers:")
            for paper, pdf_path in downloaded:
                print(f"  • {pdf_path.name}")
                print(f"    {paper.title}")

            print(f"\n✓ Success! You can now extract knowledge from these papers:")
            print(f"  python examples/ingest_paper.py {args.output_dir}/<paper>.pdf")

        # Save paper list
        if downloaded:
            paper_list_file = args.output_dir / f"search_results_{args.query[:30].replace(' ', '_')}.txt"
            with open(paper_list_file, "w") as f:
                f.write(f"Search Query: {args.query}\n")
                f.write(f"Date: {__import__('datetime').datetime.now()}\n")
                f.write(f"Papers found: {len(papers)}\n")
                f.write(f"Papers downloaded: {len(downloaded)}\n\n")

                for paper, pdf_path in downloaded:
                    f.write(f"\n{'-' * 70}\n")
                    f.write(f"ID: {paper.arxiv_id}\n")
                    f.write(f"Title: {paper.title}\n")
                    f.write(f"Authors: {', '.join(paper.authors)}\n")
                    f.write(f"Published: {paper.published}\n")
                    f.write(f"File: {pdf_path.name}\n")
                    f.write(f"Abstract: {paper.abstract}\n")

            print(f"\nPaper list saved to: {paper_list_file}")


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
