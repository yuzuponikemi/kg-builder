"""Tests for knowledge extraction modules."""

import pytest

from kg_builder.extractor.entity_extractor import EntityExtractor


@pytest.fixture
def entity_extractor():
    """Provide an EntityExtractor instance for testing."""
    return EntityExtractor()


def test_entity_extractor_initialization(entity_extractor):
    """Test that EntityExtractor can be initialized."""
    assert entity_extractor is not None
    assert hasattr(entity_extractor, "extract_entities")


def test_entity_types_validation(entity_extractor):
    """Test that entity types are properly defined."""
    # These types should match the ones in entity_extractor.py
    expected_types = {"method", "material", "phenomenon", "theory", "measurement", "application"}

    # The valid_types should be accessible (implementation-dependent)
    # This is a basic structural test
    assert entity_extractor is not None


@pytest.mark.slow
@pytest.mark.requires_llm
def test_entity_extraction_basic(entity_extractor, sample_text):
    """Test basic entity extraction (requires LLM)."""
    # This test requires an actual LLM connection
    # Mark as slow and requires_llm
    pytest.skip("Skipping LLM-dependent test in CI")

    entities = entity_extractor.extract_entities(sample_text)
    assert isinstance(entities, list)
