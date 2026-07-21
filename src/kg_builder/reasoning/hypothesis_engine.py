"""
Main hypothesis generation engine.

Orchestrates graph analytics, link prediction, and hypothesis generation.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from kg_builder.graph.neo4j_client import Neo4jClient
from kg_builder.reasoning.graph_analytics import GraphAnalytics
from kg_builder.reasoning.hypothesis_generator import HypothesisGenerator
from kg_builder.reasoning.link_predictor import LinkPredictor

logger = logging.getLogger(__name__)


class HypothesisEngine:
    """
    Main engine for hypothesis generation.

    Integrates graph analytics, link prediction, and LLM-based hypothesis generation
    to discover novel research directions from knowledge graphs.
    """

    def __init__(self, neo4j_client: Neo4jClient):
        """
        Initialize hypothesis engine.

        Args:
            neo4j_client: Neo4j client for database access
        """
        self.client = neo4j_client
        self.analytics = GraphAnalytics(neo4j_client)
        self.link_predictor = LinkPredictor(self.analytics)
        self.hypothesis_generator = HypothesisGenerator()

    def analyze_graph(self) -> dict[str, Any]:
        """
        Perform comprehensive graph analysis.

        Returns:
            Dictionary with graph statistics and analytics
        """
        logger.info("Analyzing knowledge graph...")

        # Load graph
        self.analytics.load_graph_from_neo4j()

        # Get statistics
        stats = self.analytics.get_graph_statistics()

        # Detect communities
        communities = self.analytics.detect_communities()

        # Get top concepts
        top_concepts_pr = self.analytics.get_top_concepts("pagerank", top_n=20)
        top_concepts_bw = self.analytics.get_top_concepts("betweenness", top_n=20)

        analysis = {
            "statistics": stats,
            "top_concepts_pagerank": [
                {"name": name, "score": score} for name, score in top_concepts_pr
            ],
            "top_concepts_betweenness": [
                {"name": name, "score": score} for name, score in top_concepts_bw
            ],
            "num_communities": len(set(communities.values())),
            "timestamp": datetime.now().isoformat(),
        }

        logger.info(
            f"Graph analysis complete: {stats['num_nodes']} nodes, {stats['num_edges']} edges"
        )

        return analysis

    def generate_hypotheses(
        self,
        similarity_method: str = "jaccard",
        top_n: int = 50,
        min_similarity: float = 0.1,
        cross_domain_only: bool = False,
        focus_on_central_concepts: bool = True,
        max_hypotheses: int | None = None,
        temperature: float = 0.7,
        min_novelty: float = 0.0,
        min_feasibility: float = 0.0,
        min_impact: float = 0.0,
    ) -> dict[str, Any]:
        """
        Generate research hypotheses from the knowledge graph.

        Args:
            similarity_method: Link prediction method ('jaccard', 'adamic_adar', etc.)
            top_n: Number of link predictions to generate
            min_similarity: Minimum similarity score for predictions
            cross_domain_only: Only generate hypotheses for cross-domain links
            focus_on_central_concepts: Prioritize central concepts from PageRank
            max_hypotheses: Maximum number of hypotheses to generate (None = all)
            temperature: LLM temperature for hypothesis generation (0.0-1.0)
            min_novelty: Minimum novelty score for filtering
            min_feasibility: Minimum feasibility score for filtering
            min_impact: Minimum impact score for filtering

        Returns:
            Dictionary with hypotheses and metadata
        """
        logger.info("Starting hypothesis generation pipeline...")

        # Step 1: Analyze graph
        analysis = self.analyze_graph()

        # Step 2: Generate link predictions
        logger.info("Generating link predictions...")

        if cross_domain_only:
            predictions = self.link_predictor.find_cross_domain_links(
                method=similarity_method, top_n=top_n, min_score=min_similarity
            )
        elif focus_on_central_concepts:
            # Get top central concepts
            top_concepts = [c["name"] for c in analysis["top_concepts_pagerank"][:20]]

            # Find unexplored connections for central concepts
            central_predictions = self.link_predictor.find_unexplored_connections(
                central_concepts=top_concepts,
                method=similarity_method,
                top_n_per_concept=5,
                min_score=min_similarity,
            )

            # Flatten predictions
            predictions = []
            for concept, preds in central_predictions.items():
                for pred in preds:
                    predictions.append(
                        {
                            "source": concept,
                            "target": pred["target"],
                            "score": pred["score"],
                            "source_type": self.analytics.graph.nodes[concept].get("type", "unknown") if concept in self.analytics.graph.nodes else "unknown",  # type: ignore
                            "target_type": pred["target_type"],
                            "source_description": self.analytics.graph.nodes[concept].get("description", "") if concept in self.analytics.graph.nodes else "",  # type: ignore
                            "target_description": pred["target_description"],
                            "common_neighbors": pred["common_neighbors"],
                            "num_common_neighbors": pred["num_common_neighbors"],
                        }
                    )

            # Sort by score and take top N
            predictions.sort(key=lambda x: x["score"], reverse=True)
            predictions = predictions[:top_n]
        else:
            predictions = self.link_predictor.get_top_predictions(
                method=similarity_method, top_n=top_n, min_score=min_similarity
            )

        logger.info(f"Generated {len(predictions)} link predictions")

        # Step 3: Generate hypotheses
        hypotheses = self.hypothesis_generator.generate_hypotheses_batch(
            link_predictions=predictions,
            max_hypotheses=max_hypotheses,
            temperature=temperature,
        )

        # Step 4: Filter hypotheses
        if min_novelty > 0 or min_feasibility > 0 or min_impact > 0:
            hypotheses = self.hypothesis_generator.filter_hypotheses(
                hypotheses=hypotheses,
                min_novelty=min_novelty,
                min_feasibility=min_feasibility,
                min_impact=min_impact,
            )

        # Step 5: Rank hypotheses
        hypotheses = self.hypothesis_generator.rank_hypotheses(hypotheses, criterion="combined")

        # Compile results
        results = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "similarity_method": similarity_method,
                "cross_domain_only": cross_domain_only,
                "focus_on_central_concepts": focus_on_central_concepts,
                "temperature": temperature,
                "num_predictions": len(predictions),
                "num_hypotheses": len(hypotheses),
            },
            "graph_analysis": analysis,
            "hypotheses": hypotheses,
        }

        logger.info(f"Generated {len(hypotheses)} hypotheses successfully!")

        return results

    def save_results(self, results: dict[str, Any], output_path: Path | str) -> None:
        """
        Save hypothesis generation results to JSON file.

        Args:
            results: Results dictionary from generate_hypotheses()
            output_path: Path to save JSON file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        logger.info(f"Results saved to: {output_path}")

    def print_summary(self, results: dict[str, Any], top_n: int = 10) -> None:
        """
        Print a summary of hypothesis generation results.

        Args:
            results: Results dictionary from generate_hypotheses()
            top_n: Number of top hypotheses to display
        """
        metadata = results["metadata"]
        analysis = results["graph_analysis"]
        hypotheses = results["hypotheses"]

        print("\n" + "=" * 80)
        print("HYPOTHESIS GENERATION SUMMARY")
        print("=" * 80)

        print(f"\nTimestamp: {metadata['timestamp']}")
        print(f"Similarity Method: {metadata['similarity_method']}")
        print(f"Total Link Predictions: {metadata['num_predictions']}")
        print(f"Total Hypotheses Generated: {metadata['num_hypotheses']}")

        print("\n" + "-" * 80)
        print("GRAPH STATISTICS")
        print("-" * 80)

        stats = analysis["statistics"]
        print(f"Nodes: {stats['num_nodes']}")
        print(f"Edges: {stats['num_edges']}")
        print(f"Density: {stats['density']:.4f}")
        print(f"Communities: {analysis['num_communities']}")

        print("\n" + "-" * 80)
        print(f"TOP {min(top_n, len(hypotheses))} HYPOTHESES (by combined score)")
        print("-" * 80)

        for i, h in enumerate(hypotheses[:top_n], 1):
            hyp = h["hypothesis"]
            link = h["link_prediction"]

            print(f"\n{i}. {hyp['title']}")
            print(
                f"   Link: {link['source']} ({link['source_type']}) <-> {link['target']} ({link['target_type']})"
            )
            print(f"   Similarity: {link['similarity_score']:.4f}")
            print(
                f"   Scores - Novelty: {hyp.get('novelty_score', 0):.2f}, "
                f"Feasibility: {hyp.get('feasibility_score', 0):.2f}, "
                f"Impact: {hyp.get('impact_score', 0):.2f}"
            )
            print(f"   Combined: {h.get('combined_score', 0):.2f}")
            print(f"\n   Rationale: {hyp['rationale']}")
            print(f"\n   Research Direction: {hyp['research_direction']}")

        print("\n" + "=" * 80)
