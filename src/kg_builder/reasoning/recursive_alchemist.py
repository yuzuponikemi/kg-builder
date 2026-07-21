"""
Layered hypothesis expansion for multi-dimensional knowledge exploration.

This module enables iterative hypothesis generation by treating hypotheses
as potential new concepts/relationships that can be added to the graph,
creating multiple "what-if" layers for exploratory research.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from kg_builder.reasoning.hypothesis_engine import HypothesisEngine
from kg_builder.reasoning.hypothesis_generator import HypothesisGenerator

logger = logging.getLogger(__name__)


@dataclass
class HypothesisLayer:
    """
    Represents a layer in the hypothesis expansion tree.

    Each layer contains hypotheses generated from the previous layer,
    creating a branching exploration structure.
    """

    layer_id: int
    parent_layer_id: int | None
    branch_name: str
    hypotheses: list[dict[str, Any]]
    expanded_concepts: list[dict[str, Any]] = field(default_factory=list)
    expanded_relationships: list[dict[str, Any]] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "layer_id": self.layer_id,
            "parent_layer_id": self.parent_layer_id,
            "branch_name": self.branch_name,
            "hypotheses": self.hypotheses,
            "expanded_concepts": self.expanded_concepts,
            "expanded_relationships": self.expanded_relationships,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


class HypothesisExpander:
    """
    Expands hypotheses into new concepts and relationships.

    Takes generated hypotheses and extracts potential new entities
    and relationships that could extend the knowledge graph.
    """

    def __init__(self, hypothesis_generator: HypothesisGenerator):
        """
        Initialize hypothesis expander.

        Args:
            hypothesis_generator: HypothesisGenerator instance
        """
        self.generator = hypothesis_generator

    def extract_concepts_from_hypothesis(self, hypothesis: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Extract potential new concepts from a hypothesis.

        Args:
            hypothesis: Hypothesis dictionary

        Returns:
            List of concept dictionaries
        """
        hyp = hypothesis.get("hypothesis", {})
        link = hypothesis.get("link_prediction", {})

        concepts = []

        # Create a synthetic concept from the hypothesis
        synthetic_concept = {
            "name": hyp.get("title", "Untitled Hypothesis"),
            "type": "hypothesis",  # New type for hypothesis-derived concepts
            "description": hyp.get("rationale", ""),
            "confidence": (
                hyp.get("novelty_score", 0.5) * 0.4
                + hyp.get("feasibility_score", 0.5) * 0.3
                + hyp.get("impact_score", 0.5) * 0.3
            ),
            "source_hypothesis": {
                "source_concept": link.get("source"),
                "target_concept": link.get("target"),
                "similarity_score": link.get("similarity_score"),
            },
            "keywords": hyp.get("keywords", []),
            "layer": "expansion",
        }

        concepts.append(synthetic_concept)

        return concepts

    def extract_relationships_from_hypothesis(
        self, hypothesis: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Extract potential new relationships from a hypothesis.

        Args:
            hypothesis: Hypothesis dictionary

        Returns:
            List of relationship dictionaries
        """
        hyp = hypothesis.get("hypothesis", {})
        link = hypothesis.get("link_prediction", {})

        relationships = []

        # Create synthetic relationship from the predicted link
        source = link.get("source")
        target = link.get("target")

        if source and target:
            synthetic_relationship = {
                "from": source,
                "to": target,
                "type": "hypothesized_connection",
                "confidence": link.get("similarity_score", 0.5),
                "rationale": hyp.get("rationale", ""),
                "mechanism": hyp.get("mechanism", ""),
                "layer": "expansion",
            }

            relationships.append(synthetic_relationship)

            # Create relationships to the hypothesis concept itself
            hypothesis_name = hyp.get("title", "Untitled Hypothesis")

            # Link original concepts to hypothesis
            relationships.extend(
                [
                    {
                        "from": source,
                        "to": hypothesis_name,
                        "type": "contributes_to_hypothesis",
                        "confidence": 0.9,
                        "layer": "expansion",
                    },
                    {
                        "from": target,
                        "to": hypothesis_name,
                        "type": "contributes_to_hypothesis",
                        "confidence": 0.9,
                        "layer": "expansion",
                    },
                ]
            )

        return relationships


class RecursiveAlchemist:
    """
    Recursive hypothesis generation engine.

    Generates hypotheses, expands them into new concepts/relationships,
    and recursively generates new hypotheses from the expanded graph,
    creating a multi-layered exploration tree.
    """

    def __init__(self, hypothesis_engine: HypothesisEngine):
        """
        Initialize recursive alchemist.

        Args:
            hypothesis_engine: HypothesisEngine instance
        """
        self.engine = hypothesis_engine
        self.expander = HypothesisExpander(self.engine.hypothesis_generator)
        self.layers: list[HypothesisLayer] = []

    def generate_layer_0(
        self,
        similarity_method: str = "jaccard",
        top_n: int = 30,
        max_hypotheses: int = 10,
        **kwargs: Any,
    ) -> HypothesisLayer:
        """
        Generate the base layer (Layer 0) from the original knowledge graph.

        Args:
            similarity_method: Link prediction method
            top_n: Number of link predictions
            max_hypotheses: Maximum hypotheses to generate
            **kwargs: Additional arguments for hypothesis generation

        Returns:
            Layer 0 hypothesis layer
        """
        logger.info("Generating Layer 0 (base layer)...")

        results = self.engine.generate_hypotheses(
            similarity_method=similarity_method,
            top_n=top_n,
            max_hypotheses=max_hypotheses,
            **kwargs,
        )

        layer = HypothesisLayer(
            layer_id=0,
            parent_layer_id=None,
            branch_name="root",
            hypotheses=results["hypotheses"],
            metadata={
                "graph_analysis": results["graph_analysis"],
                "generation_params": {
                    "similarity_method": similarity_method,
                    "top_n": top_n,
                    "max_hypotheses": max_hypotheses,
                },
            },
        )

        self.layers.append(layer)
        logger.info(f"Layer 0 generated with {len(layer.hypotheses)} hypotheses")

        return layer

    def expand_layer(self, layer: HypothesisLayer) -> HypothesisLayer:
        """
        Expand a hypothesis layer by extracting concepts and relationships.

        Args:
            layer: Layer to expand

        Returns:
            Expanded layer (modified in place)
        """
        logger.info(f"Expanding Layer {layer.layer_id}...")

        for hypothesis in layer.hypotheses:
            # Extract concepts
            concepts = self.expander.extract_concepts_from_hypothesis(hypothesis)
            layer.expanded_concepts.extend(concepts)

            # Extract relationships
            relationships = self.expander.extract_relationships_from_hypothesis(hypothesis)
            layer.expanded_relationships.extend(relationships)

        logger.info(
            f"Extracted {len(layer.expanded_concepts)} concepts and "
            f"{len(layer.expanded_relationships)} relationships"
        )

        return layer

    def create_branches(
        self, parent_layer: HypothesisLayer, num_branches: int = 3, criteria: str = "diversity"
    ) -> list[dict[str, Any]]:
        """
        Create multiple branches from a parent layer.

        Selects diverse subsets of hypotheses to explore different directions.

        Args:
            parent_layer: Parent layer to branch from
            num_branches: Number of branches to create
            criteria: Branching criteria ('diversity', 'impact', 'novelty', 'feasibility')

        Returns:
            List of branch definitions
        """
        hypotheses = parent_layer.hypotheses

        if not hypotheses:
            return []

        branches = []

        if criteria == "diversity":
            # Create branches by clustering hypotheses by concept types
            type_groups: dict[str, list[dict[str, Any]]] = {}

            for h in hypotheses:
                link = h.get("link_prediction", {})
                key = f"{link.get('source_type', 'unknown')}x{link.get('target_type', 'unknown')}"
                if key not in type_groups:
                    type_groups[key] = []
                type_groups[key].append(h)

            # Take top groups
            for _i, (type_key, group) in enumerate(list(type_groups.items())[:num_branches]):
                branches.append(
                    {
                        "branch_name": f"Branch-{type_key}",
                        "hypotheses": group,
                        "description": f"Exploration of {type_key} connections",
                    }
                )

        elif criteria in ["impact", "novelty", "feasibility"]:
            # Sort by specific score and create quantile-based branches
            score_key = f"{criteria}_score"
            sorted_hyps = sorted(
                hypotheses,
                key=lambda x: x.get("hypothesis", {}).get(score_key, 0),
                reverse=True,
            )

            chunk_size = len(sorted_hyps) // num_branches
            for i in range(num_branches):
                start = i * chunk_size
                end = start + chunk_size if i < num_branches - 1 else len(sorted_hyps)
                branch_hyps = sorted_hyps[start:end]

                branches.append(
                    {
                        "branch_name": f"Branch-{criteria}-{i+1}",
                        "hypotheses": branch_hyps,
                        "description": f"{criteria.capitalize()} tier {i+1}",
                    }
                )

        return branches

    def explore_recursive(
        self,
        max_depth: int = 3,
        hypotheses_per_layer: int = 10,
        branches_per_layer: int = 2,
        similarity_method: str = "jaccard",
        branching_criteria: str = "diversity",
    ) -> list[HypothesisLayer]:
        """
        Perform recursive hypothesis exploration.

        Args:
            max_depth: Maximum exploration depth
            hypotheses_per_layer: Hypotheses to generate per layer
            branches_per_layer: Number of branches per layer
            similarity_method: Link prediction method
            branching_criteria: Criteria for creating branches

        Returns:
            List of all generated layers
        """
        logger.info(f"Starting recursive exploration (max_depth={max_depth})...")

        # Generate Layer 0
        if not self.layers:
            self.generate_layer_0(
                similarity_method=similarity_method,
                max_hypotheses=hypotheses_per_layer,
            )

        layer_0 = self.layers[0]
        self.expand_layer(layer_0)

        # Create branches from Layer 0
        branches = self.create_branches(
            layer_0, num_branches=branches_per_layer, criteria=branching_criteria
        )

        # Explore each branch
        for depth in range(1, max_depth + 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"Exploring depth {depth}/{max_depth}")
            logger.info(f"{'='*60}\n")

            for branch_idx, branch in enumerate(branches):
                branch_name = branch["branch_name"]
                logger.info(f"Branch: {branch_name}")

                # This is a simplified version - in reality, we'd need to:
                # 1. Add expanded concepts to a temporary graph
                # 2. Run hypothesis generation on that graph
                # 3. For now, we simulate by re-ranking existing hypotheses

                # Get parent layer
                parent_layers = [
                    layer for layer in self.layers if layer.layer_id == depth - 1
                ]
                if not parent_layers:
                    continue

                parent_layer = parent_layers[0]

                # Create new layer
                new_layer = HypothesisLayer(
                    layer_id=depth * 100 + branch_idx,  # Unique ID
                    parent_layer_id=parent_layer.layer_id,
                    branch_name=branch_name,
                    hypotheses=branch["hypotheses"][:hypotheses_per_layer],
                    metadata={
                        "depth": depth,
                        "branch_index": branch_idx,
                        "branching_criteria": branching_criteria,
                    },
                )

                # Expand the new layer
                self.expand_layer(new_layer)
                self.layers.append(new_layer)

                logger.info(
                    f"  → Layer {new_layer.layer_id}: {len(new_layer.hypotheses)} hypotheses"
                )

        logger.info(f"\nRecursive exploration complete! Generated {len(self.layers)} layers")

        return self.layers

    def export_exploration_tree(self, output_path: Path | str) -> None:
        """
        Export the entire exploration tree to JSON.

        Args:
            output_path: Path to save the exploration tree
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        tree = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "num_layers": len(self.layers),
                "max_depth": (
                    max(layer.layer_id for layer in self.layers) if self.layers else 0
                ),
            },
            "layers": [layer.to_dict() for layer in self.layers],
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(tree, f, indent=2, ensure_ascii=False)

        logger.info(f"Exploration tree saved to: {output_path}")

    def print_tree_summary(self) -> None:
        """Print a summary of the exploration tree."""
        print("\n" + "=" * 80)
        print("RECURSIVE HYPOTHESIS EXPLORATION TREE")
        print("=" * 80)

        print(f"\nTotal Layers: {len(self.layers)}")

        for layer in sorted(self.layers, key=lambda x: x.layer_id):
            indent = "  " * (layer.layer_id // 100)
            print(f"\n{indent}Layer {layer.layer_id} - {layer.branch_name}")
            print(f"{indent}  Hypotheses: {len(layer.hypotheses)}")
            print(f"{indent}  Expanded Concepts: {len(layer.expanded_concepts)}")
            print(f"{indent}  Expanded Relationships: {len(layer.expanded_relationships)}")

            # Show top hypothesis
            if layer.hypotheses:
                top_hyp = layer.hypotheses[0]
                title = top_hyp.get("hypothesis", {}).get("title", "No title")
                print(f"{indent}  Top: {title}")

        print("\n" + "=" * 80)
