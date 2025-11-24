#!/usr/bin/env python3
"""
Test script for exploring Knowledge Graph + Noesis theme.

This script:
1. Tests Neo4j connection
2. Imports test knowledge graph
3. Generates initial hypotheses
4. Performs recursive exploration
5. Shows SF-level imaginative results
"""

import json
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from kg_builder.config import get_settings
from kg_builder.graph.neo4j_client import Neo4jClient
from kg_builder.reasoning import HypothesisEngine, RecursiveAlchemist

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def test_neo4j_connection():
    """Test Neo4j connection."""
    logger.info("Testing Neo4j connection...")

    try:
        settings = get_settings()
        client = Neo4jClient(
            uri=settings.neo4j_uri,
            user=settings.neo4j_user,
            password=settings.neo4j_password,
        )

        stats = client.get_statistics()
        logger.info(f"✓ Neo4j connected: {stats}")
        return client
    except Exception as e:
        logger.error(f"✗ Neo4j connection failed: {e}")
        logger.error("Make sure Neo4j is running with:")
        logger.error("  docker-compose -f docker/docker-compose.yml up -d neo4j")
        return None


def import_test_kg(client):
    """Import test knowledge graph."""
    logger.info("\n" + "="*60)
    logger.info("Importing test knowledge graph (KG + Noesis)...")
    logger.info("="*60)

    kg_path = Path("data/exports/test_kg_noesis.json")

    if not kg_path.exists():
        logger.error(f"Test KG not found at: {kg_path}")
        return False

    with open(kg_path, "r", encoding="utf-8") as f:
        kg = json.load(f)

    logger.info(f"Loaded: {kg['metadata']['title']}")
    logger.info(f"  Entities: {len(kg['entities'])}")
    logger.info(f"  Relationships: {len(kg['relationships'])}")

    # Clear existing data
    logger.info("Clearing existing data...")
    client.clear_database()

    # Import entities
    logger.info("Importing entities...")
    for entity in kg["entities"]:
        client.create_concept(
            name=entity["name"],
            concept_type=entity["type"],
            description=entity["description"],
            confidence=entity["confidence"],
        )

    # Import relationships
    logger.info("Importing relationships...")
    for rel in kg["relationships"]:
        client.create_relationship(
            from_concept=rel["from"],
            to_concept=rel["to"],
            relationship_type=rel["type"],
            confidence=rel["confidence"],
        )

    # Verify
    stats = client.get_statistics()
    logger.info(f"✓ Import complete!")
    logger.info(f"  Concepts: {stats.get('concepts', 0)}")
    logger.info(f"  Relationships: {stats.get('relationships', 0)}")

    return True


def generate_base_hypotheses(client):
    """Generate base hypotheses (Layer 0)."""
    logger.info("\n" + "="*60)
    logger.info("LAYER 0: Generating Base Hypotheses")
    logger.info("="*60)

    engine = HypothesisEngine(client)

    results = engine.generate_hypotheses(
        similarity_method="adamic_adar",
        top_n=30,
        max_hypotheses=8,
        temperature=0.8,
        min_novelty=0.5,
    )

    hypotheses = results["hypotheses"]
    logger.info(f"\n✓ Generated {len(hypotheses)} hypotheses")

    # Show top 3
    logger.info("\nTop 3 Hypotheses:")
    for i, h in enumerate(hypotheses[:3], 1):
        hyp = h["hypothesis"]
        link = h["link_prediction"]
        logger.info(f"\n{i}. {hyp['title']}")
        logger.info(f"   Link: {link['source']} ↔ {link['target']}")
        logger.info(f"   Scores: N={hyp['novelty_score']:.2f}, "
                   f"F={hyp['feasibility_score']:.2f}, I={hyp['impact_score']:.2f}")
        logger.info(f"   Rationale: {hyp['rationale'][:100]}...")

    return engine, results


def explore_recursive(engine):
    """Perform recursive hypothesis exploration."""
    logger.info("\n" + "="*60)
    logger.info("RECURSIVE EXPLORATION: Multi-Dimensional Expansion")
    logger.info("="*60)

    alchemist = RecursiveAlchemist(engine)

    # Load Layer 0 from previous generation
    # For simplicity, regenerate Layer 0
    logger.info("\nGenerating Layer 0...")
    alchemist.generate_layer_0(
        similarity_method="adamic_adar",
        top_n=30,
        max_hypotheses=8,
        temperature=0.8,
    )

    # Explore recursively
    logger.info("\nExploring recursively (depth=3, branches=2)...")
    layers = alchemist.explore_recursive(
        max_depth=3,
        hypotheses_per_layer=6,
        branches_per_layer=2,
        similarity_method="adamic_adar",
        branching_criteria="novelty",
    )

    # Save results
    output_path = Path("data/hypotheses/noesis_exploration_tree.json")
    alchemist.export_exploration_tree(output_path)
    logger.info(f"\n✓ Exploration tree saved to: {output_path}")

    return alchemist, layers


def show_sf_results(alchemist):
    """Show SF-level imaginative results."""
    logger.info("\n" + "="*60)
    logger.info("🌌 SF-LEVEL IMAGINATION RESULTS")
    logger.info("="*60)

    # Print tree summary
    alchemist.print_tree_summary()

    # Find deepest layers
    max_depth = max(l.layer_id for l in alchemist.layers) if alchemist.layers else 0
    deepest_layers = [l for l in alchemist.layers if l.layer_id >= max_depth - 100]

    logger.info("\n" + "-"*60)
    logger.info("DEEPEST EXPLORATIONS (Most SF-like):")
    logger.info("-"*60)

    for layer in deepest_layers:
        if not layer.hypotheses:
            continue

        logger.info(f"\n[{layer.branch_name}] (Layer {layer.layer_id})")

        # Show top hypothesis
        top_hyp = layer.hypotheses[0]
        hyp = top_hyp["hypothesis"]
        link = top_hyp["link_prediction"]

        logger.info(f"\n🚀 {hyp['title']}")
        logger.info(f"   Connection: {link['source']} ↔ {link['target']}")
        logger.info(f"   Novelty: {hyp.get('novelty_score', 0):.2f} "
                   f"(SF Level: {'🌌'*int(hyp.get('novelty_score', 0)*5)})")
        logger.info(f"\n   Rationale:")
        logger.info(f"   {hyp['rationale']}")
        logger.info(f"\n   Research Direction:")
        logger.info(f"   {hyp['research_direction']}")

        if hyp.get('next_steps'):
            logger.info(f"\n   Next Steps:")
            for step in hyp['next_steps'][:3]:
                logger.info(f"     • {step}")

    # Show expanded concepts from deepest layers
    logger.info("\n" + "-"*60)
    logger.info("NEW CONCEPTUAL TERRITORIES:")
    logger.info("-"*60)

    for layer in deepest_layers:
        if layer.expanded_concepts:
            logger.info(f"\n[{layer.branch_name}]")
            for concept in layer.expanded_concepts[:3]:
                logger.info(f"  • {concept['name']}")
                logger.info(f"    {concept['description'][:80]}...")


def main():
    """Main test flow."""
    logger.info("🌌 Testing Recursive Hypothesis Exploration")
    logger.info("Theme: Knowledge Graph × Noesis (Meta-Cognition)")
    logger.info("="*60)

    # 1. Test connection
    client = test_neo4j_connection()
    if not client:
        logger.error("\nCannot proceed without Neo4j connection.")
        logger.info("\nTo start Neo4j:")
        logger.info("  docker-compose -f docker/docker-compose.yml up -d neo4j")
        logger.info("\nOr check your .env file for correct Neo4j credentials.")
        return 1

    # 2. Import test KG
    if not import_test_kg(client):
        return 1

    # 3. Generate base hypotheses
    try:
        engine, base_results = generate_base_hypotheses(client)
    except Exception as e:
        logger.error(f"Error generating hypotheses: {e}", exc_info=True)
        return 1

    # 4. Recursive exploration
    try:
        alchemist, layers = explore_recursive(engine)
    except Exception as e:
        logger.error(f"Error in recursive exploration: {e}", exc_info=True)
        return 1

    # 5. Show SF results
    show_sf_results(alchemist)

    logger.info("\n" + "="*60)
    logger.info("✨ Test complete!")
    logger.info(f"Total layers: {len(layers)}")
    logger.info(f"Total hypotheses: {sum(len(l.hypotheses) for l in layers)}")
    logger.info(f"Total new concepts: {sum(len(l.expanded_concepts) for l in layers)}")
    logger.info("="*60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
