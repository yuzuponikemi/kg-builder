"""
Graph analytics module for knowledge graph analysis.

Provides centrality analysis, community detection, and graph statistics.
"""

import logging
from typing import Any

import community as community_louvain
import networkx as nx

from kg_builder.graph.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)


class GraphAnalytics:
    """Analyzes knowledge graph structure using graph algorithms."""

    def __init__(self, neo4j_client: Neo4jClient):
        """
        Initialize graph analytics.

        Args:
            neo4j_client: Neo4j client for database access
        """
        self.client = neo4j_client
        self.graph: nx.Graph | None = None

    def load_graph_from_neo4j(self) -> nx.Graph:
        """
        Load the knowledge graph from Neo4j into NetworkX.

        Returns:
            NetworkX graph with concepts as nodes and relationships as edges
        """
        logger.info("Loading graph from Neo4j...")

        # Query to get all concepts and their relationships
        query = """
        MATCH (c1:Concept)-[r]->(c2:Concept)
        RETURN c1.name as source,
               c2.name as target,
               type(r) as relationship,
               c1.type as source_type,
               c2.type as target_type,
               c1.description as source_description,
               c2.description as target_description
        """

        results = self.client.run_cypher(query)

        # Create directed graph
        G = nx.DiGraph()

        for record in results:
            source = record["source"]
            target = record["target"]
            rel_type = record["relationship"]

            # Add nodes with attributes
            if not G.has_node(source):
                G.add_node(
                    source,
                    type=record.get("source_type", "unknown"),
                    description=record.get("source_description", ""),
                )

            if not G.has_node(target):
                G.add_node(
                    target,
                    type=record.get("target_type", "unknown"),
                    description=record.get("target_description", ""),
                )

            # Add edge with relationship type
            G.add_edge(source, target, relationship=rel_type)

        self.graph = G
        logger.info(f"Loaded graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

        return G

    def calculate_centrality(self, metric: str = "pagerank") -> dict[str, float]:
        """
        Calculate node centrality using various metrics.

        Args:
            metric: Centrality metric - 'pagerank', 'betweenness', 'degree', 'eigenvector'

        Returns:
            Dictionary mapping node names to centrality scores
        """
        if self.graph is None:
            self.load_graph_from_neo4j()

        assert self.graph is not None

        logger.info(f"Calculating {metric} centrality...")

        if metric == "pagerank":
            centrality = nx.pagerank(self.graph)
        elif metric == "betweenness":
            centrality = nx.betweenness_centrality(self.graph)
        elif metric == "degree":
            centrality = dict(self.graph.degree())
            # Normalize
            max_degree = max(centrality.values()) if centrality else 1
            centrality = {k: v / max_degree for k, v in centrality.items()}
        elif metric == "eigenvector":
            try:
                centrality = nx.eigenvector_centrality(self.graph, max_iter=1000)
            except nx.PowerIterationFailedConvergence:
                logger.warning("Eigenvector centrality failed to converge, using PageRank instead")
                centrality = nx.pagerank(self.graph)
        else:
            raise ValueError(
                f"Unknown metric: {metric}. Choose from: pagerank, betweenness, degree, eigenvector"
            )

        return centrality

    def detect_communities(self) -> dict[str, int]:
        """
        Detect communities using Louvain method.

        Returns:
            Dictionary mapping node names to community IDs
        """
        if self.graph is None:
            self.load_graph_from_neo4j()

        assert self.graph is not None

        logger.info("Detecting communities using Louvain method...")

        # Convert to undirected graph for community detection
        undirected_graph = self.graph.to_undirected()

        # Apply Louvain community detection
        communities = community_louvain.best_partition(undirected_graph)

        num_communities = len(set(communities.values()))
        logger.info(f"Found {num_communities} communities")

        return communities

    def get_graph_statistics(self) -> dict[str, Any]:
        """
        Calculate comprehensive graph statistics.

        Returns:
            Dictionary with graph metrics
        """
        if self.graph is None:
            self.load_graph_from_neo4j()

        assert self.graph is not None

        logger.info("Calculating graph statistics...")

        undirected = self.graph.to_undirected()

        stats = {
            "num_nodes": self.graph.number_of_nodes(),
            "num_edges": self.graph.number_of_edges(),
            "density": nx.density(self.graph),
            "is_connected": nx.is_weakly_connected(self.graph),
            "num_connected_components": nx.number_weakly_connected_components(self.graph),
        }

        # Calculate clustering coefficient (for undirected graph)
        try:
            stats["average_clustering"] = nx.average_clustering(undirected)
        except Exception as e:
            logger.warning(f"Could not calculate clustering coefficient: {e}")
            stats["average_clustering"] = None

        # Calculate average shortest path (if connected)
        if stats["is_connected"]:
            try:
                stats["average_shortest_path"] = nx.average_shortest_path_length(self.graph)
            except Exception as e:
                logger.warning(f"Could not calculate average shortest path: {e}")
                stats["average_shortest_path"] = None
        else:
            stats["average_shortest_path"] = None

        # Node type distribution
        node_types = {}
        for _node, data in self.graph.nodes(data=True):
            node_type = data.get("type", "unknown")
            node_types[node_type] = node_types.get(node_type, 0) + 1

        stats["node_type_distribution"] = node_types

        # Relationship type distribution
        rel_types = {}
        for _, _, data in self.graph.edges(data=True):
            rel_type = data.get("relationship", "unknown")
            rel_types[rel_type] = rel_types.get(rel_type, 0) + 1

        stats["relationship_type_distribution"] = rel_types

        return stats

    def get_top_concepts(
        self, metric: str = "pagerank", top_n: int = 10
    ) -> list[tuple[str, float]]:
        """
        Get top N most important concepts based on centrality metric.

        Args:
            metric: Centrality metric to use
            top_n: Number of top concepts to return

        Returns:
            List of (concept_name, score) tuples sorted by score
        """
        centrality = self.calculate_centrality(metric)
        sorted_concepts = sorted(centrality.items(), key=lambda x: x[1], reverse=True)
        return sorted_concepts[:top_n]

    def get_concept_neighbors(self, concept_name: str, distance: int = 1) -> set[str]:
        """
        Get all concepts within a given distance from a concept.

        Args:
            concept_name: Name of the concept
            distance: Maximum distance (hops) from the concept

        Returns:
            Set of concept names within the distance
        """
        if self.graph is None:
            self.load_graph_from_neo4j()

        assert self.graph is not None

        if concept_name not in self.graph:
            return set()

        neighbors = set()

        # Use BFS to find all nodes within distance
        if distance == 1:
            # Direct neighbors (both incoming and outgoing)
            neighbors = set(self.graph.predecessors(concept_name)) | set(
                self.graph.successors(concept_name)
            )
        else:
            # Multi-hop neighbors
            for node in self.graph.nodes():
                if node == concept_name:
                    continue
                try:
                    # Check if there's a path within the distance
                    if nx.has_path(self.graph, concept_name, node):
                        path_length = nx.shortest_path_length(self.graph, concept_name, node)
                        if path_length <= distance:
                            neighbors.add(node)
                    if nx.has_path(self.graph, node, concept_name):
                        path_length = nx.shortest_path_length(self.graph, node, concept_name)
                        if path_length <= distance:
                            neighbors.add(node)
                except nx.NetworkXNoPath:
                    continue

        return neighbors
