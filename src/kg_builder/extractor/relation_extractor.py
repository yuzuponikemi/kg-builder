"""Relationship extraction from scientific text using LLMs."""

import json
from pathlib import Path
from typing import Any

from kg_builder.extractor.llm_client import get_llm_client


class RelationshipExtractor:
    """Extract relationships between scientific concepts using LLMs."""

    def __init__(self, llm_client: Any | None = None):
        """Initialize relationship extractor.

        Args:
            llm_client: LLM client instance. If None, creates a new one.
        """
        self.llm = llm_client or get_llm_client()
        self.prompt_template = self._load_prompt_template()

    def _load_prompt_template(self) -> str:
        """Load relationship extraction prompt template."""
        prompt_path = Path(__file__).parent / "prompts" / "relationship_extraction.txt"
        with open(prompt_path) as f:
            return f.read()

    def extract(
        self, text: str, entities: list[dict[str, Any]], max_retries: int = 2
    ) -> list[dict[str, Any]]:
        """Extract relationships from text given known entities.

        Args:
            text: Text to extract relationships from
            entities: List of entities found in the text
            max_retries: Maximum number of retries on failure

        Returns:
            List of extracted relationships
        """
        if not entities:
            return []

        # Truncate text if too long
        max_length = 6000
        if len(text) > max_length:
            text = text[:max_length] + "\n\n[... text truncated ...]"

        # Format entities for prompt
        entity_names = [e["name"] for e in entities]
        entity_list = "\n".join(f"- {name}" for name in entity_names)

        prompt = self.prompt_template.format(entities=entity_list, text=text)

        for attempt in range(max_retries + 1):
            try:
                response = self.llm.generate(
                    prompt=prompt,
                    temperature=0.0,
                    response_format="json",
                )

                # Parse JSON response
                data = self.llm.extract_json(response)

                if "relationships" not in data:
                    raise ValueError("Response missing 'relationships' field")

                relationships = data["relationships"]

                # Validate relationships
                validated_relationships = []
                for rel in relationships:
                    if self._validate_relationship(rel, entity_names):
                        validated_relationships.append(rel)

                return validated_relationships

            except Exception as e:
                if attempt == max_retries:
                    print(
                        f"Failed to extract relationships after {max_retries + 1} attempts: {e}"
                    )
                    return []
                print(f"Attempt {attempt + 1} failed: {e}. Retrying...")

        return []

    def _validate_relationship(
        self, relationship: dict[str, Any], valid_entity_names: list[str]
    ) -> bool:
        """Validate relationship structure.

        Args:
            relationship: Relationship dictionary to validate
            valid_entity_names: List of valid entity names

        Returns:
            True if valid, False otherwise
        """
        required_fields = ["from", "to", "type", "confidence"]

        # Check required fields
        for field in required_fields:
            if field not in relationship:
                return False

        # Validate type
        valid_types = [
            "is_a",
            "part_of",
            "uses",
            "enables",
            "measures",
            "applies_to",
            "based_on",
            "related_to",
        ]
        if relationship["type"] not in valid_types:
            return False

        # Validate confidence
        if not isinstance(relationship["confidence"], (int, float)) or not (
            0.0 <= relationship["confidence"] <= 1.0
        ):
            return False

        # Validate entity names (case-insensitive)
        from_name = relationship["from"]
        to_name = relationship["to"]

        valid_names_lower = [name.lower() for name in valid_entity_names]

        if from_name.lower() not in valid_names_lower:
            return False
        if to_name.lower() not in valid_names_lower:
            return False

        # No self-loops
        if from_name.lower() == to_name.lower():
            return False

        return True

    def extract_batch(
        self, text_chunks: list[str], entities: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Extract relationships from multiple text chunks.

        Args:
            text_chunks: List of text chunks to process
            entities: List of entities found in the text

        Returns:
            Combined list of relationships (deduplicated)
        """
        all_relationships: dict[str, dict[str, Any]] = {}

        for i, chunk in enumerate(text_chunks):
            print(f"Processing chunk {i + 1}/{len(text_chunks)} for relationships...")
            relationships = self.extract(chunk, entities)

            # Merge relationships, keeping highest confidence for duplicates
            for rel in relationships:
                # Create unique key
                key = f"{rel['from'].lower()}|{rel['type']}|{rel['to'].lower()}"

                if key not in all_relationships or rel["confidence"] > all_relationships[key][
                    "confidence"
                ]:
                    all_relationships[key] = rel

        return list(all_relationships.values())
