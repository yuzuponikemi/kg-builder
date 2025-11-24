"""Tests for hypothesis generator module."""

import json
from unittest.mock import Mock, patch

import pytest

from kg_builder.reasoning.hypothesis_generator import HypothesisGenerator


class TestHypothesisGenerator:
    """Test HypothesisGenerator class."""

    @pytest.fixture
    def mock_llm_client(self) -> Mock:
        """Create a mock LLM client."""
        mock_client = Mock()

        # Mock response
        mock_response = json.dumps(
            {
                "hypothesis": {
                    "title": "Test Hypothesis: Combining A and B",
                    "rationale": "These concepts share common neighbors.",
                    "research_direction": "Investigate novel applications.",
                    "mechanism": "Theoretical connection through shared principles.",
                    "next_steps": ["Step 1", "Step 2", "Step 3"],
                    "novelty_score": 0.85,
                    "feasibility_score": 0.75,
                    "impact_score": 0.90,
                    "keywords": ["keyword1", "keyword2", "keyword3"],
                }
            }
        )

        mock_client.generate.return_value = mock_response
        mock_client.extract_json.return_value = json.loads(mock_response)

        return mock_client

    @pytest.fixture
    def sample_link_prediction(self) -> dict:
        """Create a sample link prediction."""
        return {
            "source": "Graph Neural Networks",
            "target": "Knowledge Graphs",
            "score": 0.75,
            "source_type": "method",
            "target_type": "application",
            "source_description": "Neural networks for graph data",
            "target_description": "Structured knowledge representation",
            "common_neighbors": ["Embedding", "Reasoning"],
            "num_common_neighbors": 2,
        }

    def test_generate_hypothesis(self, mock_llm_client: Mock, sample_link_prediction: dict) -> None:
        """Test single hypothesis generation."""
        generator = HypothesisGenerator(mock_llm_client)

        hypothesis = generator.generate_hypothesis(sample_link_prediction)

        assert hypothesis is not None
        assert "hypothesis" in hypothesis
        assert "link_prediction" in hypothesis

        hyp = hypothesis["hypothesis"]
        assert "title" in hyp
        assert "rationale" in hyp
        assert "research_direction" in hyp
        assert "novelty_score" in hyp
        assert "feasibility_score" in hyp
        assert "impact_score" in hyp

        # Check LLM was called
        mock_llm_client.generate.assert_called_once()

    def test_generate_hypothesis_with_temperature(
        self, mock_llm_client: Mock, sample_link_prediction: dict
    ) -> None:
        """Test hypothesis generation with custom temperature."""
        generator = HypothesisGenerator(mock_llm_client)

        hypothesis = generator.generate_hypothesis(sample_link_prediction, temperature=0.9)

        assert hypothesis is not None

        # Check temperature was passed
        call_args = mock_llm_client.generate.call_args
        assert call_args.kwargs["temperature"] == 0.9

    def test_generate_hypothesis_json_error(self, sample_link_prediction: dict) -> None:
        """Test handling of JSON parsing errors."""
        mock_client = Mock()
        mock_client.generate.return_value = "Invalid JSON"
        mock_client.extract_json.side_effect = json.JSONDecodeError("test", "test", 0)

        generator = HypothesisGenerator(mock_client)

        hypothesis = generator.generate_hypothesis(sample_link_prediction)

        # Should return None on error
        assert hypothesis is None

    def test_generate_hypotheses_batch(
        self, mock_llm_client: Mock, sample_link_prediction: dict
    ) -> None:
        """Test batch hypothesis generation."""
        generator = HypothesisGenerator(mock_llm_client)

        predictions = [sample_link_prediction] * 3

        hypotheses = generator.generate_hypotheses_batch(predictions)

        assert len(hypotheses) == 3
        assert mock_llm_client.generate.call_count == 3

    def test_generate_hypotheses_batch_with_max(
        self, mock_llm_client: Mock, sample_link_prediction: dict
    ) -> None:
        """Test batch generation with max limit."""
        generator = HypothesisGenerator(mock_llm_client)

        predictions = [sample_link_prediction] * 10

        hypotheses = generator.generate_hypotheses_batch(predictions, max_hypotheses=5)

        assert len(hypotheses) == 5
        assert mock_llm_client.generate.call_count == 5

    def test_rank_hypotheses_combined(self) -> None:
        """Test ranking hypotheses by combined score."""
        generator = HypothesisGenerator(Mock())

        hypotheses = [
            {
                "hypothesis": {
                    "novelty_score": 0.8,
                    "feasibility_score": 0.7,
                    "impact_score": 0.9,
                }
            },
            {
                "hypothesis": {
                    "novelty_score": 0.6,
                    "feasibility_score": 0.8,
                    "impact_score": 0.6,
                }
            },
            {
                "hypothesis": {
                    "novelty_score": 0.9,
                    "feasibility_score": 0.9,
                    "impact_score": 0.95,
                }
            },
        ]

        ranked = generator.rank_hypotheses(hypotheses, criterion="combined")

        # Should be sorted by combined score
        assert len(ranked) == 3
        assert ranked[0]["combined_score"] > ranked[1]["combined_score"]
        assert ranked[1]["combined_score"] > ranked[2]["combined_score"]

    def test_rank_hypotheses_novelty(self) -> None:
        """Test ranking by novelty score."""
        generator = HypothesisGenerator(Mock())

        hypotheses = [
            {"hypothesis": {"novelty_score": 0.6}},
            {"hypothesis": {"novelty_score": 0.9}},
            {"hypothesis": {"novelty_score": 0.7}},
        ]

        ranked = generator.rank_hypotheses(hypotheses, criterion="novelty")

        scores = [h["hypothesis"]["novelty_score"] for h in ranked]
        assert scores == [0.9, 0.7, 0.6]

    def test_filter_hypotheses(self) -> None:
        """Test filtering hypotheses by thresholds."""
        generator = HypothesisGenerator(Mock())

        hypotheses = [
            {
                "hypothesis": {
                    "novelty_score": 0.8,
                    "feasibility_score": 0.7,
                    "impact_score": 0.9,
                }
            },
            {
                "hypothesis": {
                    "novelty_score": 0.5,
                    "feasibility_score": 0.8,
                    "impact_score": 0.6,
                }
            },
            {
                "hypothesis": {
                    "novelty_score": 0.9,
                    "feasibility_score": 0.4,
                    "impact_score": 0.8,
                }
            },
        ]

        # Filter: novelty >= 0.7, feasibility >= 0.6, impact >= 0.8
        filtered = generator.filter_hypotheses(
            hypotheses, min_novelty=0.7, min_feasibility=0.6, min_impact=0.8
        )

        # Only first hypothesis should pass
        assert len(filtered) == 1
        assert filtered[0]["hypothesis"]["novelty_score"] == 0.8
