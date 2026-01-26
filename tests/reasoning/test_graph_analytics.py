"""Tests for graph analytics module."""

import pytest
import networkx as nx

from kg_builder.reasoning.graph_analytics import GraphAnalytics


class TestGraphAnalytics:
    """Test GraphAnalytics class."""

    @pytest.fixture
    def mock_graph(self) -> nx.DiGraph:
        """Create a mock graph for testing."""
        G = nx.DiGraph()

        # Add nodes with attributes
        nodes = [
            ("GNN", {"type": "method", "description": "Graph Neural Networks"}),
            ("Knowledge Graph", {"type": "application", "description": "Structured knowledge"}),
            ("Embedding", {"type": "method", "description": "Vector representations"}),
            ("Neural Network", {"type": "method", "description": "Deep learning model"}),
            ("Reasoning", {"type": "theory", "description": "Logical inference"}),
        ]

        for name, attrs in nodes:
            G.add_node(name, **attrs)

        # Add edges with relationships
        edges = [
            ("GNN", "Knowledge Graph", "applies_to"),
            ("GNN", "Embedding", "uses"),
            ("GNN", "Neural Network", "is_a"),
            ("Embedding", "Knowledge Graph", "applies_to"),
            ("Reasoning", "Knowledge Graph", "applies_to"),
        ]

        for source, target, rel_type in edges:
            G.add_edge(source, target, relationship=rel_type)

        return G

    def test_calculate_centrality_pagerank(self, mock_graph: nx.DiGraph) -> None:
        """Test PageRank centrality calculation."""
        # Create analytics with mock graph
        analytics = GraphAnalytics(None)  # type: ignore
        analytics.graph = mock_graph

        centrality = analytics.calculate_centrality("pagerank")

        assert len(centrality) == 5
        assert all(0 <= score <= 1 for score in centrality.values())
        assert "GNN" in centrality

    def test_calculate_centrality_betweenness(self, mock_graph: nx.DiGraph) -> None:
        """Test betweenness centrality calculation."""
        analytics = GraphAnalytics(None)  # type: ignore
        analytics.graph = mock_graph

        centrality = analytics.calculate_centrality("betweenness")

        assert len(centrality) == 5
        assert all(0 <= score <= 1 for score in centrality.values())

    def test_calculate_centrality_degree(self, mock_graph: nx.DiGraph) -> None:
        """Test degree centrality calculation."""
        analytics = GraphAnalytics(None)  # type: ignore
        analytics.graph = mock_graph

        centrality = analytics.calculate_centrality("degree")

        assert len(centrality) == 5
        assert all(0 <= score <= 1 for score in centrality.values())

    def test_calculate_centrality_invalid_metric(self, mock_graph: nx.DiGraph) -> None:
        """Test invalid centrality metric."""
        analytics = GraphAnalytics(None)  # type: ignore
        analytics.graph = mock_graph

        with pytest.raises(ValueError, match="Unknown metric"):
            analytics.calculate_centrality("invalid_metric")

    def test_detect_communities(self, mock_graph: nx.DiGraph) -> None:
        """Test community detection."""
        analytics = GraphAnalytics(None)  # type: ignore
        analytics.graph = mock_graph

        communities = analytics.detect_communities()

        assert len(communities) == 5
        assert all(isinstance(comm_id, int) for comm_id in communities.values())

    def test_get_graph_statistics(self, mock_graph: nx.DiGraph) -> None:
        """Test graph statistics calculation."""
        analytics = GraphAnalytics(None)  # type: ignore
        analytics.graph = mock_graph

        stats = analytics.get_graph_statistics()

        assert stats["num_nodes"] == 5
        assert stats["num_edges"] == 5
        assert "density" in stats
        assert "is_connected" in stats
        assert "node_type_distribution" in stats
        assert stats["node_type_distribution"]["method"] == 3

    def test_get_top_concepts(self, mock_graph: nx.DiGraph) -> None:
        """Test getting top concepts."""
        analytics = GraphAnalytics(None)  # type: ignore
        analytics.graph = mock_graph

        top_concepts = analytics.get_top_concepts("pagerank", top_n=3)

        assert len(top_concepts) == 3
        assert all(
            isinstance(name, str) and isinstance(score, float) for name, score in top_concepts
        )

        # Check that results are sorted
        scores = [score for _, score in top_concepts]
        assert scores == sorted(scores, reverse=True)

    def test_get_concept_neighbors(self, mock_graph: nx.DiGraph) -> None:
        """Test getting concept neighbors."""
        analytics = GraphAnalytics(None)  # type: ignore
        analytics.graph = mock_graph

        # Direct neighbors (distance=1)
        neighbors = analytics.get_concept_neighbors("GNN", distance=1)

        assert len(neighbors) == 3  # Knowledge Graph, Embedding, Neural Network
        assert "Knowledge Graph" in neighbors
        assert "Embedding" in neighbors
        assert "Neural Network" in neighbors

    def test_get_concept_neighbors_nonexistent(self, mock_graph: nx.DiGraph) -> None:
        """Test getting neighbors of nonexistent concept."""
        analytics = GraphAnalytics(None)  # type: ignore
        analytics.graph = mock_graph

        neighbors = analytics.get_concept_neighbors("Nonexistent", distance=1)

        assert len(neighbors) == 0
