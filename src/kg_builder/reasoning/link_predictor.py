"""
Link prediction module for discovering potential relationships.

Uses graph similarity metrics to find concept pairs that should be connected.
"""

import logging
from typing import Any

import networkx as nx

from kg_builder.reasoning.graph_analytics import GraphAnalytics

logger = logging.getLogger(__name__)


class LinkPredictor:
    """Predicts missing links in the knowledge graph."""

    def __init__(self, graph_analytics: GraphAnalytics):
        """
        Initialize link predictor.

        Args:
            graph_analytics: GraphAnalytics instance with loaded graph
        """
        self.analytics = graph_analytics
        self.graph = graph_analytics.graph

    def _ensure_graph_loaded(self) -> None:
        """Ensure graph is loaded."""
        if self.graph is None:
            self.analytics.load_graph_from_neo4j()
            self.graph = self.analytics.graph

    def calculate_similarity_scores(self, method: str = "jaccard") -> list[tuple[str, str, float]]:
        """
        Calculate similarity scores for all non-connected node pairs.

        Args:
            method: Similarity method - 'jaccard', 'adamic_adar', 'resource_allocation',
                   'common_neighbors', 'preferential_attachment'

        Returns:
            List of (source, target, score) tuples sorted by score
        """
        self._ensure_graph_loaded()
        assert self.graph is not None

        logger.info(f"Calculating {method} similarity scores...")

        # Convert to undirected for similarity calculations
        undirected = self.graph.to_undirected()

        # Get all non-edges (potential links)
        non_edges = nx.non_edges(undirected)

        # Calculate similarity based on method
        if method == "jaccard":
            preds = nx.jaccard_coefficient(undirected, non_edges)
        elif method == "adamic_adar":
            preds = nx.adamic_adar_index(undirected, non_edges)
        elif method == "resource_allocation":
            preds = nx.resource_allocation_index(undirected, non_edges)
        elif method == "common_neighbors":
            # Common neighbors count
            preds = []
            for u, v in non_edges:
                common = len(list(nx.common_neighbors(undirected, u, v)))
                preds.append((u, v, common))
        elif method == "preferential_attachment":
            preds = nx.preferential_attachment(undirected, non_edges)
        else:
            raise ValueError(
                f"Unknown method: {method}. Choose from: jaccard, adamic_adar, "
                "resource_allocation, common_neighbors, preferential_attachment"
            )

        # Convert to list and sort by score
        if method != "common_neighbors":
            predictions = [(u, v, score) for u, v, score in preds]
        else:
            predictions = preds

        predictions.sort(key=lambda x: x[2], reverse=True)

        logger.info(f"Generated {len(predictions)} link predictions")

        return predictions

    def get_top_predictions(
        self,
        method: str = "jaccard",
        top_n: int = 100,
        min_score: float = 0.0,
        filter_types: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get top N link predictions with detailed information.

        Args:
            method: Similarity method to use
            top_n: Number of top predictions to return
            min_score: Minimum similarity score threshold
            filter_types: If provided, only return predictions where at least one
                         node matches these types (e.g., ['method', 'theory'])

        Returns:
            List of prediction dictionaries with source, target, score, and metadata
        """
        predictions = self.calculate_similarity_scores(method)

        # Filter by score
        predictions = [(u, v, s) for u, v, s in predictions if s >= min_score]

        # Filter by node type if specified
        if filter_types:
            filtered = []
            for u, v, score in predictions:
                u_type = self.graph.nodes[u].get("type", "unknown") if u in self.graph.nodes else "unknown"  # type: ignore
                v_type = self.graph.nodes[v].get("type", "unknown") if v in self.graph.nodes else "unknown"  # type: ignore

                if u_type in filter_types or v_type in filter_types:
                    filtered.append((u, v, score))

            predictions = filtered

        # Take top N
        predictions = predictions[:top_n]

        # Enrich with metadata
        results = []
        for source, target, score in predictions:
            assert self.graph is not None

            source_data = self.graph.nodes[source] if source in self.graph.nodes else {}
            target_data = self.graph.nodes[target] if target in self.graph.nodes else {}

            # Get common neighbors
            undirected = self.graph.to_undirected()
            common_neighbors = list(nx.common_neighbors(undirected, source, target))

            results.append(
                {
                    "source": source,
                    "target": target,
                    "score": score,
                    "source_type": source_data.get("type", "unknown"),
                    "target_type": target_data.get("type", "unknown"),
                    "source_description": source_data.get("description", ""),
                    "target_description": target_data.get("description", ""),
                    "common_neighbors": common_neighbors,
                    "num_common_neighbors": len(common_neighbors),
                }
            )

        return results

    def find_cross_domain_links(
        self, method: str = "jaccard", top_n: int = 50, min_score: float = 0.1
    ) -> list[dict[str, Any]]:
        """
        Find potential links between different concept types (cross-domain).

        This is particularly useful for discovering novel research directions
        by connecting different types of concepts (e.g., methods + phenomena).

        Args:
            method: Similarity method to use
            top_n: Number of predictions to return
            min_score: Minimum similarity score

        Returns:
            List of cross-domain link predictions
        """
        predictions = self.get_top_predictions(method=method, top_n=top_n * 5, min_score=min_score)

        # Filter for cross-domain (different types)
        cross_domain = [pred for pred in predictions if pred["source_type"] != pred["target_type"]]

        return cross_domain[:top_n]

    def find_unexplored_connections(
        self,
        central_concepts: list[str],
        method: str = "jaccard",
        top_n_per_concept: int = 10,
        min_score: float = 0.1,
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Find unexplored connections for a list of central concepts.

        Useful for finding novel applications of important concepts.

        Args:
            central_concepts: List of concept names to analyze
            method: Similarity method to use
            top_n_per_concept: Number of predictions per concept
            min_score: Minimum similarity score

        Returns:
            Dictionary mapping concept names to their top predictions
        """
        self._ensure_graph_loaded()
        assert self.graph is not None

        results = {}

        for concept in central_concepts:
            if concept not in self.graph:
                logger.warning(f"Concept '{concept}' not found in graph")
                continue

            # Get all non-neighbors of this concept
            undirected = self.graph.to_undirected()
            neighbors = set(undirected.neighbors(concept))
            non_neighbors = set(undirected.nodes()) - neighbors - {concept}

            # Calculate similarity to non-neighbors
            non_edges = [(concept, n) for n in non_neighbors]

            if method == "jaccard":
                preds = list(nx.jaccard_coefficient(undirected, non_edges))
            elif method == "adamic_adar":
                preds = list(nx.adamic_adar_index(undirected, non_edges))
            elif method == "resource_allocation":
                preds = list(nx.resource_allocation_index(undirected, non_edges))
            elif method == "common_neighbors":
                preds = [
                    (u, v, len(list(nx.common_neighbors(undirected, u, v)))) for u, v in non_edges
                ]
            else:
                preds = list(nx.preferential_attachment(undirected, non_edges))

            # Filter and sort
            preds = [(u, v, s) for u, v, s in preds if s >= min_score]
            preds.sort(key=lambda x: x[2], reverse=True)
            preds = preds[:top_n_per_concept]

            # Enrich with metadata
            predictions = []
            for source, target, score in preds:
                target_data = self.graph.nodes[target] if target in self.graph.nodes else {}
                common_neighbors = list(nx.common_neighbors(undirected, source, target))

                predictions.append(
                    {
                        "target": target,
                        "score": score,
                        "target_type": target_data.get("type", "unknown"),
                        "target_description": target_data.get("description", ""),
                        "common_neighbors": common_neighbors,
                        "num_common_neighbors": len(common_neighbors),
                    }
                )

            results[concept] = predictions

        return results
