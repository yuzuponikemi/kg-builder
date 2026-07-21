"""Tests for entity extraction."""

from unittest.mock import MagicMock, patch

from kg_builder.extractor.entity_extractor import EntityExtractor


class TestEntityExtractor:
    """Test entity extraction functionality."""

    def test_init_with_client(self, mock_ollama_client):
        """Test initialization with provided LLM client."""
        mock_llm = MagicMock()
        extractor = EntityExtractor(llm_client=mock_llm)
        assert extractor.llm == mock_llm
        assert isinstance(extractor.prompt_template, str)

    def test_init_without_client(self):
        """Test initialization creates LLM client if not provided."""
        with patch("kg_builder.extractor.entity_extractor.get_llm_client") as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client

            extractor = EntityExtractor()
            assert extractor.llm == mock_client
            mock_get_client.assert_called_once()

    def test_load_prompt_template(self):
        """Test prompt template loading."""
        with patch("kg_builder.extractor.entity_extractor.get_llm_client"):
            extractor = EntityExtractor()
            assert len(extractor.prompt_template) > 0
            # Should contain placeholder for text
            assert "{text}" in extractor.prompt_template

    def test_validate_entity_valid(self):
        """Test validation of valid entity."""
        with patch("kg_builder.extractor.entity_extractor.get_llm_client"):
            extractor = EntityExtractor()

            valid_entity = {
                "name": "Graph Neural Network",
                "type": "method",
                "description": "A neural network for graph data",
                "confidence": 0.95,
            }

            assert extractor._validate_entity(valid_entity) is True

    def test_validate_entity_missing_field(self):
        """Test validation fails for missing required field."""
        with patch("kg_builder.extractor.entity_extractor.get_llm_client"):
            extractor = EntityExtractor()

            invalid_entity = {
                "name": "Test",
                "type": "method",
                # Missing description and confidence
            }

            assert extractor._validate_entity(invalid_entity) is False

    def test_validate_entity_invalid_type(self):
        """Test validation fails for invalid entity type."""
        with patch("kg_builder.extractor.entity_extractor.get_llm_client"):
            extractor = EntityExtractor()

            invalid_entity = {
                "name": "Test",
                "type": "invalid_type",
                "description": "Test description",
                "confidence": 0.9,
            }

            assert extractor._validate_entity(invalid_entity) is False

    def test_validate_entity_invalid_confidence(self):
        """Test validation fails for invalid confidence value."""
        with patch("kg_builder.extractor.entity_extractor.get_llm_client"):
            extractor = EntityExtractor()

            invalid_entity = {
                "name": "Test",
                "type": "method",
                "description": "Test description",
                "confidence": 1.5,  # Invalid: > 1.0
            }

            assert extractor._validate_entity(invalid_entity) is False

    def test_extract_success(self, sample_text, sample_entities):
        """Test successful entity extraction."""
        mock_llm = MagicMock()
        mock_llm.generate.return_value = (
            '{"entities": ' + str(sample_entities).replace("'", '"') + "}"
        )
        mock_llm.extract_json.return_value = {"entities": sample_entities}

        with patch("kg_builder.extractor.entity_extractor.get_llm_client", return_value=mock_llm):
            extractor = EntityExtractor()
            entities = extractor.extract(sample_text)

            assert len(entities) == len(sample_entities)
            assert entities[0]["name"] == "Graph Neural Networks"
            mock_llm.generate.assert_called_once()
            mock_llm.extract_json.assert_called_once()

    def test_extract_truncates_long_text(self):
        """Test that long text is truncated before extraction."""
        long_text = "A" * 10000  # Very long text

        mock_llm = MagicMock()
        mock_llm.generate.return_value = '{"entities": []}'
        mock_llm.extract_json.return_value = {"entities": []}

        with patch("kg_builder.extractor.entity_extractor.get_llm_client", return_value=mock_llm):
            extractor = EntityExtractor()
            extractor.extract(long_text)

            # Check that generate was called with truncated text
            call_args = mock_llm.generate.call_args
            prompt = call_args.kwargs["prompt"]
            assert "[... text truncated ...]" in prompt

    def test_extract_filters_invalid_entities(self):
        """Test that invalid entities are filtered out."""
        mixed_entities = [
            {
                "name": "Valid Entity",
                "type": "method",
                "description": "Valid description",
                "confidence": 0.9,
            },
            {
                "name": "Invalid Entity",
                "type": "invalid_type",  # Invalid type
                "description": "Invalid description",
                "confidence": 0.9,
            },
        ]

        mock_llm = MagicMock()
        mock_llm.generate.return_value = '{"entities": []}'
        mock_llm.extract_json.return_value = {"entities": mixed_entities}

        with patch("kg_builder.extractor.entity_extractor.get_llm_client", return_value=mock_llm):
            extractor = EntityExtractor()
            entities = extractor.extract("test text")

            # Should only have the valid entity
            assert len(entities) == 1
            assert entities[0]["name"] == "Valid Entity"

    def test_extract_retries_on_failure(self):
        """Test that extraction retries on failure."""
        mock_llm = MagicMock()
        # First attempt fails, second succeeds
        mock_llm.generate.side_effect = [Exception("First attempt failed"), '{"entities": []}']
        mock_llm.extract_json.return_value = {"entities": []}

        with patch("kg_builder.extractor.entity_extractor.get_llm_client", return_value=mock_llm):
            extractor = EntityExtractor()
            entities = extractor.extract("test text", max_retries=2)

            # Should succeed on second attempt
            assert entities == []
            assert mock_llm.generate.call_count == 2

    def test_extract_returns_empty_after_max_retries(self):
        """Test that extraction returns empty list after max retries."""
        mock_llm = MagicMock()
        mock_llm.generate.side_effect = Exception("Always fails")

        with patch("kg_builder.extractor.entity_extractor.get_llm_client", return_value=mock_llm):
            extractor = EntityExtractor()
            entities = extractor.extract("test text", max_retries=2)

            assert entities == []
            assert mock_llm.generate.call_count == 3  # Initial + 2 retries

    def test_extract_missing_entities_field(self):
        """Test extraction handles missing entities field in response."""
        mock_llm = MagicMock()
        mock_llm.generate.return_value = '{"wrong_field": []}'
        mock_llm.extract_json.return_value = {"wrong_field": []}

        with patch("kg_builder.extractor.entity_extractor.get_llm_client", return_value=mock_llm):
            extractor = EntityExtractor()
            entities = extractor.extract("test text", max_retries=0)

            # Should return empty list due to missing 'entities' field
            assert entities == []

    def test_extract_uses_correct_parameters(self):
        """Test that extract uses correct LLM parameters."""
        mock_llm = MagicMock()
        mock_llm.generate.return_value = '{"entities": []}'
        mock_llm.extract_json.return_value = {"entities": []}

        with patch("kg_builder.extractor.entity_extractor.get_llm_client", return_value=mock_llm):
            extractor = EntityExtractor()
            extractor.extract("test text")

            call_kwargs = mock_llm.generate.call_args.kwargs
            assert call_kwargs["temperature"] == 0.0
            assert call_kwargs["response_format"] == "json"
