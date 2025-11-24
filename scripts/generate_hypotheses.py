#!/usr/bin/env python3
"""
Generate research hypotheses from knowledge graph.

This script analyzes the knowledge graph in Neo4j and generates novel research
hypotheses by:
1. Analyzing graph structure (centrality, communities)
2. Predicting missing links (similar but unconnected concepts)
3. Generating creative hypotheses using LLMs

Example usage:
    # Basic usage
    python scripts/generate_hypotheses.py

    # Cross-domain only
    python scripts/generate_hypotheses.py --cross-domain

    # Focus on specific similarity method
    python scripts/generate_hypotheses.py --method adamic_adar --top-n 30

    # High-quality hypotheses only
    python scripts/generate_hypotheses.py --min-novelty 0.7 --min-impact 0.7

    # More creative hypotheses
    python scripts/generate_hypotheses.py --temperature 0.9

    # Limit number of hypotheses
    python scripts/generate_hypotheses.py --max-hypotheses 10
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

from kg_builder.config import get_settings
from kg_builder.graph.neo4j_client import Neo4jClient
from kg_builder.reasoning.hypothesis_engine import HypothesisEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate research hypotheses from knowledge graph",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Link prediction options
    parser.add_argument(
        "--method",
        type=str,
        default="jaccard",
        choices=[
            "jaccard",
            "adamic_adar",
            "resource_allocation",
            "common_neighbors",
            "preferential_attachment",
        ],
        help="Similarity method for link prediction (default: jaccard)",
    )

    parser.add_argument(
        "--top-n",
        type=int,
        default=50,
        help="Number of link predictions to generate (default: 50)",
    )

    parser.add_argument(
        "--min-similarity",
        type=float,
        default=0.1,
        help="Minimum similarity score for predictions (default: 0.1)",
    )

    # Filtering options
    parser.add_argument(
        "--cross-domain",
        action="store_true",
        help="Only generate hypotheses for cross-domain links (different concept types)",
    )

    parser.add_argument(
        "--no-central-focus",
        action="store_true",
        help="Don't prioritize central concepts (use all concepts equally)",
    )

    # Hypothesis generation options
    parser.add_argument(
        "--max-hypotheses",
        type=int,
        default=None,
        help="Maximum number of hypotheses to generate (default: all predictions)",
    )

    parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="LLM temperature for hypothesis generation (0.0-1.0, default: 0.7)",
    )

    # Quality filters
    parser.add_argument(
        "--min-novelty",
        type=float,
        default=0.0,
        help="Minimum novelty score (0.0-1.0, default: 0.0)",
    )

    parser.add_argument(
        "--min-feasibility",
        type=float,
        default=0.0,
        help="Minimum feasibility score (0.0-1.0, default: 0.0)",
    )

    parser.add_argument(
        "--min-impact",
        type=float,
        default=0.0,
        help="Minimum impact score (0.0-1.0, default: 0.0)",
    )

    # Output options
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output JSON file path (default: data/hypotheses/hypotheses_TIMESTAMP.json)",
    )

    parser.add_argument(
        "--no-summary",
        action="store_true",
        help="Don't print summary to console",
    )

    parser.add_argument(
        "--summary-top-n",
        type=int,
        default=10,
        help="Number of top hypotheses to show in summary (default: 10)",
    )

    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_args()

    # Load settings
    try:
        settings = get_settings()
    except Exception as e:
        logger.error(f"Failed to load settings: {e}")
        logger.error("Make sure .env file is configured correctly")
        return 1

    # Check Neo4j connection
    try:
        client = Neo4jClient(
            uri=settings.neo4j_uri,
            user=settings.neo4j_user,
            password=settings.neo4j_password,
        )

        # Test connection
        stats = client.get_statistics()
        if stats.get("concepts", 0) == 0:
            logger.error("No concepts found in Neo4j database")
            logger.error(
                "Please import knowledge graphs first using: python scripts/import_to_neo4j.py"
            )
            return 1

        logger.info(f"Connected to Neo4j: {stats['concepts']} concepts, {stats['papers']} papers")

    except Exception as e:
        logger.error(f"Failed to connect to Neo4j: {e}")
        logger.error("Make sure Neo4j is running and credentials are correct")
        return 1

    # Initialize hypothesis engine
    engine = HypothesisEngine(client)

    # Generate hypotheses
    try:
        logger.info("Starting hypothesis generation...")
        logger.info(f"Configuration:")
        logger.info(f"  - Similarity method: {args.method}")
        logger.info(f"  - Top N predictions: {args.top_n}")
        logger.info(f"  - Min similarity: {args.min_similarity}")
        logger.info(f"  - Cross-domain only: {args.cross_domain}")
        logger.info(f"  - Focus on central concepts: {not args.no_central_focus}")
        logger.info(f"  - Temperature: {args.temperature}")
        logger.info(f"  - Max hypotheses: {args.max_hypotheses or 'all'}")

        results = engine.generate_hypotheses(
            similarity_method=args.method,
            top_n=args.top_n,
            min_similarity=args.min_similarity,
            cross_domain_only=args.cross_domain,
            focus_on_central_concepts=not args.no_central_focus,
            max_hypotheses=args.max_hypotheses,
            temperature=args.temperature,
            min_novelty=args.min_novelty,
            min_feasibility=args.min_feasibility,
            min_impact=args.min_impact,
        )

    except Exception as e:
        logger.error(f"Error generating hypotheses: {e}", exc_info=True)
        return 1

    # Save results
    if args.output:
        output_path = args.output
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(f"data/hypotheses/hypotheses_{timestamp}.json")

    try:
        engine.save_results(results, output_path)
        logger.info(f"Results saved to: {output_path}")
    except Exception as e:
        logger.error(f"Failed to save results: {e}")
        return 1

    # Print summary
    if not args.no_summary:
        engine.print_summary(results, top_n=args.summary_top_n)

    logger.info("Hypothesis generation complete!")

    return 0


if __name__ == "__main__":
    sys.exit(main())
