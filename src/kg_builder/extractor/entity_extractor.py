"""Entity extraction from scientific text using LLMs."""

import json
from pathlib import Path
from typing import Any

from kg_builder.extractor.llm_client import get_llm_client


class EntityExtractor:
    """Extract scientific entities from text using LLMs."""

    def __init__(self, llm_client: Any | None = None):
        """Initialize entity extractor.

        Args:
            llm_client: LLM client instance. If None, creates a new one.
        """
        self.llm = llm_client or get_llm_client()
        self.prompt_template = self._load_prompt_template()

    def _load_prompt_template(self) -> str:
        """Load entity extraction prompt template."""
        prompt_path = Path(__file__).parent / "prompts" / "entity_extraction.txt"
        with open(prompt_path) as f:
            return f.read()

    def extract(self, text: str, max_retries: int = 2) -> list[dict[str, Any]]:
        """Extract entities from text.

        Args:
            text: Text to extract entities from
            max_retries: Maximum number of retries on failure

        Returns:
            List of extracted entities
        """
        # Truncate text if too long (keep first portion which usually has key concepts)
        max_length = 6000
        if len(text) > max_length:
            text = text[:max_length] + "\n\n[... text truncated ...]"

        prompt = self.prompt_template.format(text=text)

        for attempt in range(max_retries + 1):
            try:
                response = self.llm.generate(
                    prompt=prompt,
                    temperature=0.0,
                    response_format="json",
                )

                # Parse JSON response
                data = self.llm.extract_json(response)

                if "entities" not in data:
                    raise ValueError("Response missing 'entities' field")

                entities = data["entities"]

                # Validate entities
                validated_entities = []
                for entity in entities:
                    if self._validate_entity(entity):
                        validated_entities.append(entity)

                return validated_entities

            except Exception as e:
                if attempt == max_retries:
                    print(f"Failed to extract entities after {max_retries + 1} attempts: {e}")
                    return []
                print(f"Attempt {attempt + 1} failed: {e}. Retrying...")

        return []

    def _validate_entity(self, entity: dict[str, Any]) -> bool:
        """Validate entity structure.

        Args:
            entity: Entity dictionary to validate

        Returns:
            True if valid, False otherwise
        """
        required_fields = ["name", "type", "description", "confidence"]

        # Check required fields
        for field in required_fields:
            if field not in entity:
                return False

        # Validate type
        valid_types = ["method", "material", "phenomenon", "theory", "measurement", "application"]
        if entity["type"] not in valid_types:
            return False

        # Validate confidence
        if not isinstance(entity["confidence"], (int, float)) or not (
            0.0 <= entity["confidence"] <= 1.0
        ):
            return False

        # Name should not be empty
        if not entity["name"] or not isinstance(entity["name"], str):
            return False

        return True

    def extract_batch(self, text_chunks: list[str]) -> list[dict[str, Any]]:
        """Extract entities from multiple text chunks.

        Args:
            text_chunks: List of text chunks to process

        Returns:
            Combined list of entities (deduplicated by name)
        """
        all_entities: dict[str, dict[str, Any]] = {}

        for i, chunk in enumerate(text_chunks):
            print(f"Processing chunk {i + 1}/{len(text_chunks)}...")
            entities = self.extract(chunk)

            # Merge entities, keeping highest confidence for duplicates
            for entity in entities:
                name = entity["name"].lower()
                if name not in all_entities or entity["confidence"] > all_entities[name][
                    "confidence"
                ]:
                    all_entities[name] = entity

        return list(all_entities.values())
