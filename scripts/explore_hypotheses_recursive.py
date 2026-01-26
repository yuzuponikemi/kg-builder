#!/usr/bin/env python3
"""
Recursive hypothesis exploration - multi-dimensional knowledge graph expansion.

This script performs iterative hypothesis generation, creating multiple
"what-if" layers that branch out in different directions, enabling
SF-prototype level imaginative exploration of research possibilities.

Example usage:
    # Basic recursive exploration
    python scripts/explore_hypotheses_recursive.py

    # Deep exploration with multiple branches
    python scripts/explore_hypotheses_recursive.py \
      --max-depth 3 \
      --branches-per-layer 3 \
      --hypotheses-per-layer 15

    # Diversity-focused exploration
    python scripts/explore_hypotheses_recursive.py \
      --branching-criteria diversity \
      --max-depth 4

    # Impact-focused exploration
    python scripts/explore_hypotheses_recursive.py \
      --branching-criteria impact \
      --temperature 0.9
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

from kg_builder.config import get_settings
from kg_builder.graph.neo4j_client import Neo4jClient
from kg_builder.reasoning.hypothesis_engine import HypothesisEngine
from kg_builder.reasoning.recursive_alchemist import RecursiveAlchemist

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Recursive hypothesis exploration for multi-dimensional KG expansion",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Exploration parameters
    parser.add_argument(
        "--max-depth",
        type=int,
        default=2,
        help="Maximum exploration depth (number of recursive iterations, default: 2)",
    )

    parser.add_argument(
        "--hypotheses-per-layer",
        type=int,
        default=10,
        help="Number of hypotheses to generate per layer (default: 10)",
    )

    parser.add_argument(
        "--branches-per-layer",
        type=int,
        default=2,
        help="Number of branches to create per layer (default: 2)",
    )

    parser.add_argument(
        "--branching-criteria",
        type=str,
        default="diversity",
        choices=["diversity", "impact", "novelty", "feasibility"],
        help="Criteria for creating branches (default: diversity)",
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
        "--temperature",
        type=float,
        default=0.7,
        help="LLM temperature for hypothesis generation (0.0-1.0, default: 0.7)",
    )

    # Quality filters (for Layer 0)
    parser.add_argument(
        "--min-novelty",
        type=float,
        default=0.0,
        help="Minimum novelty score for Layer 0 (0.0-1.0, default: 0.0)",
    )

    parser.add_argument(
        "--min-feasibility",
        type=float,
        default=0.0,
        help="Minimum feasibility score for Layer 0 (0.0-1.0, default: 0.0)",
    )

    parser.add_argument(
        "--min-impact",
        type=float,
        default=0.0,
        help="Minimum impact score for Layer 0 (0.0-1.0, default: 0.0)",
    )

    # Output options
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output JSON file path (default: data/hypotheses/exploration_tree_TIMESTAMP.json)",
    )

    parser.add_argument(
        "--no-summary",
        action="store_true",
        help="Don't print summary to console",
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

    # Initialize engines
    hypothesis_engine = HypothesisEngine(client)
    recursive_alchemist = RecursiveAlchemist(hypothesis_engine)

    # Perform recursive exploration
    try:
        logger.info("=" * 80)
        logger.info("RECURSIVE HYPOTHESIS EXPLORATION")
        logger.info("=" * 80)
        logger.info(f"Configuration:")
        logger.info(f"  Max Depth: {args.max_depth}")
        logger.info(f"  Hypotheses per Layer: {args.hypotheses_per_layer}")
        logger.info(f"  Branches per Layer: {args.branches_per_layer}")
        logger.info(f"  Branching Criteria: {args.branching_criteria}")
        logger.info(f"  Similarity Method: {args.method}")
        logger.info(f"  Temperature: {args.temperature}")
        logger.info("=" * 80 + "\n")

        # Generate Layer 0 first (with quality filters)
        recursive_alchemist.generate_layer_0(
            similarity_method=args.method,
            top_n=args.hypotheses_per_layer * 5,
            max_hypotheses=args.hypotheses_per_layer,
            temperature=args.temperature,
            min_novelty=args.min_novelty,
            min_feasibility=args.min_feasibility,
            min_impact=args.min_impact,
        )

        # Explore recursively
        layers = recursive_alchemist.explore_recursive(
            max_depth=args.max_depth,
            hypotheses_per_layer=args.hypotheses_per_layer,
            branches_per_layer=args.branches_per_layer,
            similarity_method=args.method,
            branching_criteria=args.branching_criteria,
        )

    except Exception as e:
        logger.error(f"Error during recursive exploration: {e}", exc_info=True)
        return 1

    # Save results
    if args.output:
        output_path = args.output
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(f"data/hypotheses/exploration_tree_{timestamp}.json")

    try:
        recursive_alchemist.export_exploration_tree(output_path)
        logger.info(f"\nExploration tree saved to: {output_path}")
    except Exception as e:
        logger.error(f"Failed to save results: {e}")
        return 1

    # Print summary
    if not args.no_summary:
        recursive_alchemist.print_tree_summary()

    logger.info("\n🌌 Recursive exploration complete!")
    logger.info(f"Total layers generated: {len(layers)}")
    logger.info(f"Total hypotheses across all layers: {sum(len(l.hypotheses) for l in layers)}")
    logger.info(f"Total expanded concepts: {sum(len(l.expanded_concepts) for l in layers)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
