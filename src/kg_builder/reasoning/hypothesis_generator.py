"""
Hypothesis generation module using LLMs.

Generates novel research hypotheses from link predictions.
"""

import json
import logging
from pathlib import Path
from typing import Any

from kg_builder.extractor.llm_client import LLMClient, get_llm_client

logger = logging.getLogger(__name__)


class HypothesisGenerator:
    """Generates research hypotheses using LLMs."""

    def __init__(self, llm_client: LLMClient | None = None):
        """
        Initialize hypothesis generator.

        Args:
            llm_client: LLM client to use. If None, creates a new client.
        """
        self.llm = llm_client or get_llm_client()
        self.prompt_template = self._load_prompt_template()

    def _load_prompt_template(self) -> str:
        """Load the hypothesis generation prompt template."""
        template_path = Path(__file__).parent / "prompts" / "hypothesis_generation.txt"

        with open(template_path, encoding="utf-8") as f:
            return f.read()

    def generate_hypothesis(
        self, link_prediction: dict[str, Any], temperature: float = 0.7
    ) -> dict[str, Any] | None:
        """
        Generate a research hypothesis for a predicted link.

        Args:
            link_prediction: Link prediction dictionary with source, target, and metadata
            temperature: LLM temperature for creativity (0.0-1.0)

        Returns:
            Hypothesis dictionary or None if generation failed
        """
        # Format common neighbors for display
        common_neighbors_str = ", ".join(link_prediction.get("common_neighbors", [])[:5])
        if len(link_prediction.get("common_neighbors", [])) > 5:
            common_neighbors_str += ", ..."

        # Create prompt from template
        prompt = self.prompt_template.format(
            source_name=link_prediction["source"],
            source_type=link_prediction.get("source_type", "unknown"),
            source_description=link_prediction.get(
                "source_description", "No description available"
            ),
            target_name=link_prediction["target"],
            target_type=link_prediction.get("target_type", "unknown"),
            target_description=link_prediction.get(
                "target_description", "No description available"
            ),
            similarity_score=f"{link_prediction['score']:.4f}",
            common_neighbors=common_neighbors_str,
            num_common_neighbors=link_prediction.get("num_common_neighbors", 0),
        )

        try:
            logger.info(
                f"Generating hypothesis for: {link_prediction['source']} <-> {link_prediction['target']}"
            )

            # Generate hypothesis with JSON format
            response = self.llm.generate(
                prompt=prompt,
                temperature=temperature,
                max_tokens=1500,
                response_format="json",
            )

            # Parse JSON response
            result = self.llm.extract_json(response)

            # Add metadata
            result["link_prediction"] = {
                "source": link_prediction["source"],
                "target": link_prediction["target"],
                "similarity_score": link_prediction["score"],
                "source_type": link_prediction.get("source_type"),
                "target_type": link_prediction.get("target_type"),
            }

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response was: {response}")
            return None
        except Exception as e:
            logger.error(f"Error generating hypothesis: {e}")
            return None

    def generate_hypotheses_batch(
        self,
        link_predictions: list[dict[str, Any]],
        max_hypotheses: int | None = None,
        temperature: float = 0.7,
    ) -> list[dict[str, Any]]:
        """
        Generate hypotheses for multiple link predictions.

        Args:
            link_predictions: List of link prediction dictionaries
            max_hypotheses: Maximum number of hypotheses to generate (None = all)
            temperature: LLM temperature for creativity

        Returns:
            List of hypothesis dictionaries
        """
        hypotheses = []

        predictions_to_process = link_predictions
        if max_hypotheses:
            predictions_to_process = link_predictions[:max_hypotheses]

        logger.info(f"Generating {len(predictions_to_process)} hypotheses...")

        for i, prediction in enumerate(predictions_to_process, 1):
            logger.info(f"Processing {i}/{len(predictions_to_process)}...")

            hypothesis = self.generate_hypothesis(prediction, temperature)

            if hypothesis:
                hypotheses.append(hypothesis)
            else:
                logger.warning(
                    f"Failed to generate hypothesis for: "
                    f"{prediction['source']} <-> {prediction['target']}"
                )

        logger.info(f"Successfully generated {len(hypotheses)} hypotheses")

        return hypotheses

    def rank_hypotheses(
        self, hypotheses: list[dict[str, Any]], criterion: str = "combined"
    ) -> list[dict[str, Any]]:
        """
        Rank hypotheses by various criteria.

        Args:
            hypotheses: List of hypothesis dictionaries
            criterion: Ranking criterion - 'novelty', 'feasibility', 'impact', 'combined'

        Returns:
            Sorted list of hypotheses
        """
        if criterion == "combined":
            # Combined score: weighted average of all three metrics
            for h in hypotheses:
                hyp_data = h.get("hypothesis", {})
                h["combined_score"] = (
                    hyp_data.get("novelty_score", 0.5) * 0.4
                    + hyp_data.get("impact_score", 0.5) * 0.4
                    + hyp_data.get("feasibility_score", 0.5) * 0.2
                )
            hypotheses.sort(key=lambda x: x.get("combined_score", 0), reverse=True)

        elif criterion in ["novelty", "feasibility", "impact"]:
            score_key = f"{criterion}_score"
            hypotheses.sort(key=lambda x: x.get("hypothesis", {}).get(score_key, 0), reverse=True)

        else:
            raise ValueError(
                f"Unknown criterion: {criterion}. "
                "Choose from: novelty, feasibility, impact, combined"
            )

        return hypotheses

    def filter_hypotheses(
        self,
        hypotheses: list[dict[str, Any]],
        min_novelty: float = 0.0,
        min_feasibility: float = 0.0,
        min_impact: float = 0.0,
    ) -> list[dict[str, Any]]:
        """
        Filter hypotheses by minimum score thresholds.

        Args:
            hypotheses: List of hypothesis dictionaries
            min_novelty: Minimum novelty score
            min_feasibility: Minimum feasibility score
            min_impact: Minimum impact score

        Returns:
            Filtered list of hypotheses
        """
        filtered = []

        for h in hypotheses:
            hyp_data = h.get("hypothesis", {})

            if (
                hyp_data.get("novelty_score", 0) >= min_novelty
                and hyp_data.get("feasibility_score", 0) >= min_feasibility
                and hyp_data.get("impact_score", 0) >= min_impact
            ):
                filtered.append(h)

        logger.info(
            f"Filtered {len(hypotheses)} hypotheses to {len(filtered)} "
            f"(novelty>={min_novelty}, feasibility>={min_feasibility}, impact>={min_impact})"
        )

        return filtered
