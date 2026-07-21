"""Tests for link predictor module."""

import pytest
import networkx as nx

from kg_builder.reasoning.graph_analytics import GraphAnalytics
from kg_builder.reasoning.link_predictor import LinkPredictor


class TestLinkPredictor:
    """Test LinkPredictor class."""

    @pytest.fixture
    def mock_analytics(self) -> GraphAnalytics:
        """Create mock analytics with a test graph."""
        # Create a simple graph
        G = nx.DiGraph()

        # Add nodes
        nodes = [
            ("A", {"type": "method", "description": "Method A"}),
            ("B", {"type": "method", "description": "Method B"}),
            ("C", {"type": "theory", "description": "Theory C"}),
            ("D", {"type": "application", "description": "Application D"}),
            ("E", {"type": "method", "description": "Method E"}),
        ]

        for name, attrs in nodes:
            G.add_node(name, **attrs)

        # Add edges (A-C, B-C, A-D, E-D)
        # This creates a structure where A and B share neighbor C
        # and A and E share neighbor D
        edges = [
            ("A", "C", "uses"),
            ("B", "C", "uses"),
            ("A", "D", "applies_to"),
            ("E", "D", "applies_to"),
        ]

        for source, target, rel_type in edges:
            G.add_edge(source, target, relationship=rel_type)

        analytics = GraphAnalytics(None)  # type: ignore
        analytics.graph = G

        return analytics

    def test_calculate_similarity_scores_jaccard(self, mock_analytics: GraphAnalytics) -> None:
        """Test Jaccard similarity calculation."""
        predictor = LinkPredictor(mock_analytics)

        predictions = predictor.calculate_similarity_scores("jaccard")

        # Should have predictions (all non-edges)
        assert len(predictions) > 0

        # Check structure
        for source, target, score in predictions:
            assert isinstance(source, str)
            assert isinstance(target, str)
            assert isinstance(score, float)
            assert score >= 0

    def test_calculate_similarity_scores_adamic_adar(self, mock_analytics: GraphAnalytics) -> None:
        """Test Adamic-Adar similarity calculation."""
        predictor = LinkPredictor(mock_analytics)

        predictions = predictor.calculate_similarity_scores("adamic_adar")

        assert len(predictions) > 0

    def test_calculate_similarity_scores_common_neighbors(
        self, mock_analytics: GraphAnalytics
    ) -> None:
        """Test common neighbors calculation."""
        predictor = LinkPredictor(mock_analytics)

        predictions = predictor.calculate_similarity_scores("common_neighbors")

        assert len(predictions) > 0

        # A and B should have similarity > 0 (they share neighbor C)
        a_b_prediction = next((s for s, t, sc in predictions if {s, t} == {"A", "B"}), None)
        if a_b_prediction is not None:
            _, _, score = next(p for p in predictions if {p[0], p[1]} == {"A", "B"})
            assert score > 0  # They share neighbor C

    def test_calculate_similarity_invalid_method(self, mock_analytics: GraphAnalytics) -> None:
        """Test invalid similarity method."""
        predictor = LinkPredictor(mock_analytics)

        with pytest.raises(ValueError, match="Unknown method"):
            predictor.calculate_similarity_scores("invalid_method")

    def test_get_top_predictions(self, mock_analytics: GraphAnalytics) -> None:
        """Test getting top predictions with metadata."""
        predictor = LinkPredictor(mock_analytics)

        predictions = predictor.get_top_predictions(method="jaccard", top_n=5, min_score=0.0)

        assert len(predictions) <= 5
        assert all("source" in p and "target" in p and "score" in p for p in predictions)
        assert all("source_type" in p and "target_type" in p for p in predictions)
        assert all("common_neighbors" in p for p in predictions)

        # Check sorting
        scores = [p["score"] for p in predictions]
        assert scores == sorted(scores, reverse=True)

    def test_get_top_predictions_with_filter(self, mock_analytics: GraphAnalytics) -> None:
        """Test predictions with type filtering."""
        predictor = LinkPredictor(mock_analytics)

        # Filter for methods only
        predictions = predictor.get_top_predictions(
            method="jaccard", top_n=10, filter_types=["method"]
        )

        # All predictions should involve at least one method
        for p in predictions:
            assert p["source_type"] == "method" or p["target_type"] == "method"

    def test_find_cross_domain_links(self, mock_analytics: GraphAnalytics) -> None:
        """Test finding cross-domain links."""
        predictor = LinkPredictor(mock_analytics)

        cross_domain = predictor.find_cross_domain_links(method="jaccard", top_n=5, min_score=0.0)

        # All predictions should have different types
        for p in cross_domain:
            assert p["source_type"] != p["target_type"]

    def test_find_unexplored_connections(self, mock_analytics: GraphAnalytics) -> None:
        """Test finding unexplored connections for central concepts."""
        predictor = LinkPredictor(mock_analytics)

        results = predictor.find_unexplored_connections(
            central_concepts=["A", "B"],
            method="jaccard",
            top_n_per_concept=3,
            min_score=0.0,
        )

        assert "A" in results
        assert "B" in results

        # Check structure
        for concept, predictions in results.items():
            assert isinstance(predictions, list)
            for p in predictions:
                assert "target" in p
                assert "score" in p
                assert "target_type" in p

    def test_find_unexplored_connections_nonexistent(self, mock_analytics: GraphAnalytics) -> None:
        """Test with nonexistent concept."""
        predictor = LinkPredictor(mock_analytics)

        results = predictor.find_unexplored_connections(
            central_concepts=["Nonexistent"],
            method="jaccard",
            top_n_per_concept=3,
        )

        # Should return empty dict or skip the nonexistent concept
        assert "Nonexistent" not in results or len(results["Nonexistent"]) == 0
