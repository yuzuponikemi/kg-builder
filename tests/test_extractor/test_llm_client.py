"""Tests for LLM client."""

import json
import os
from unittest.mock import MagicMock, patch

import pytest

from kg_builder.extractor.llm_client import LLMClient, get_llm_client


class TestLLMClient:
    """Test LLM client functionality."""

    def test_init_with_ollama_provider(self, test_settings):
        """Test initialization with Ollama provider."""
        with patch("ollama.Client") as mock_client:
            client = LLMClient(provider="ollama")
            assert client.provider == "ollama"
            assert client.model == test_settings.ollama_model
            mock_client.assert_called_once()

    def test_init_with_openai_provider(self, test_env, tmp_path):
        """Test initialization with OpenAI provider."""
        with patch.dict(
            os.environ,
            {
                "NEO4J_PASSWORD": "test_password",
                "LLM_PROVIDER": "openai",
                "OPENAI_API_KEY": "test-key",
                "DATA_DIR": str(tmp_path / "data"),
            },
        ):
            with patch("openai.OpenAI") as mock_client:
                from kg_builder.config import get_settings

                get_settings.cache_clear()

                client = LLMClient(provider="openai")
                assert client.provider == "openai"
                mock_client.assert_called_once()

                get_settings.cache_clear()

    def test_init_with_anthropic_provider(self, test_env, tmp_path):
        """Test initialization with Anthropic provider."""
        with patch.dict(
            os.environ,
            {
                "NEO4J_PASSWORD": "test_password",
                "LLM_PROVIDER": "anthropic",
                "ANTHROPIC_API_KEY": "test-key",
                "DATA_DIR": str(tmp_path / "data"),
            },
        ):
            with patch("anthropic.Anthropic") as mock_client:
                from kg_builder.config import get_settings

                get_settings.cache_clear()

                client = LLMClient(provider="anthropic")
                assert client.provider == "anthropic"
                mock_client.assert_called_once()

                get_settings.cache_clear()

    def test_init_with_gemini_provider(self, test_env, tmp_path):
        """Test initialization with Gemini provider."""
        with patch.dict(
            os.environ,
            {
                "NEO4J_PASSWORD": "test_password",
                "LLM_PROVIDER": "gemini",
                "GEMINI_API_KEY": "test-key",
                "DATA_DIR": str(tmp_path / "data"),
            },
        ):
            with (
                patch("google.generativeai.configure"),
                patch("google.generativeai.GenerativeModel") as mock_model,
            ):
                from kg_builder.config import get_settings

                get_settings.cache_clear()

                client = LLMClient(provider="gemini")
                assert client.provider == "gemini"
                mock_model.assert_called_once()

                get_settings.cache_clear()

    def test_init_with_invalid_provider(self, test_settings):
        """Test initialization with invalid provider raises error."""
        with pytest.raises(ValueError, match="Unknown LLM provider"):
            LLMClient(provider="invalid_provider")

    def test_generate_ollama(self, test_settings, mock_ollama_client):
        """Test text generation with Ollama."""
        client = LLMClient(provider="ollama")
        client.client = mock_ollama_client

        response = client.generate(
            prompt="Test prompt", system="Test system", temperature=0.7, max_tokens=1000
        )

        assert isinstance(response, str)
        mock_ollama_client.chat.assert_called_once()

    def test_generate_ollama_json_format(self, test_settings, mock_ollama_client):
        """Test JSON generation with Ollama."""
        mock_ollama_client.chat.return_value = {"message": {"content": '{"key": "value"}'}}

        client = LLMClient(provider="ollama")
        client.client = mock_ollama_client

        response = client.generate(prompt="Test prompt", response_format="json")

        assert isinstance(response, str)
        call_args = mock_ollama_client.chat.call_args
        assert call_args.kwargs["options"]["format"] == "json"

    def test_generate_openai(self, test_env, tmp_path):
        """Test text generation with OpenAI."""
        with patch.dict(
            os.environ,
            {
                "NEO4J_PASSWORD": "test_password",
                "LLM_PROVIDER": "openai",
                "OPENAI_API_KEY": "test-key",
                "DATA_DIR": str(tmp_path / "data"),
            },
        ):
            with patch("openai.OpenAI") as mock_openai:
                from kg_builder.config import get_settings

                get_settings.cache_clear()

                # Setup mock
                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.choices[0].message.content = "Test response"
                mock_client.chat.completions.create.return_value = mock_response
                mock_openai.return_value = mock_client

                client = LLMClient(provider="openai")
                response = client.generate(prompt="Test prompt")

                assert response == "Test response"
                mock_client.chat.completions.create.assert_called_once()

                get_settings.cache_clear()

    def test_generate_openai_json_format(self, test_env, tmp_path):
        """Test JSON generation with OpenAI."""
        with patch.dict(
            os.environ,
            {
                "NEO4J_PASSWORD": "test_password",
                "LLM_PROVIDER": "openai",
                "OPENAI_API_KEY": "test-key",
                "DATA_DIR": str(tmp_path / "data"),
            },
        ):
            with patch("openai.OpenAI") as mock_openai:
                from kg_builder.config import get_settings

                get_settings.cache_clear()

                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.choices[0].message.content = '{"key": "value"}'
                mock_client.chat.completions.create.return_value = mock_response
                mock_openai.return_value = mock_client

                client = LLMClient(provider="openai")
                response = client.generate(prompt="Test", response_format="json")

                call_kwargs = mock_client.chat.completions.create.call_args.kwargs
                assert call_kwargs["response_format"] == {"type": "json_object"}

                get_settings.cache_clear()

    def test_extract_json_plain(self, test_settings):
        """Test JSON extraction from plain JSON string."""
        with patch("ollama.Client"):
            client = LLMClient(provider="ollama")

            json_str = '{"entities": [], "relationships": []}'
            result = client.extract_json(json_str)

            assert result == {"entities": [], "relationships": []}

    def test_extract_json_with_markdown(self, test_settings):
        """Test JSON extraction from markdown code block."""
        with patch("ollama.Client"):
            client = LLMClient(provider="ollama")

            json_str = '```json\n{"entities": [], "relationships": []}\n```'
            result = client.extract_json(json_str)

            assert result == {"entities": [], "relationships": []}

    def test_extract_json_with_plain_markdown(self, test_settings):
        """Test JSON extraction from plain markdown code block."""
        with patch("ollama.Client"):
            client = LLMClient(provider="ollama")

            json_str = '```\n{"entities": [], "relationships": []}\n```'
            result = client.extract_json(json_str)

            assert result == {"entities": [], "relationships": []}

    def test_extract_json_invalid(self, test_settings):
        """Test JSON extraction with invalid JSON raises error."""
        with patch("ollama.Client"):
            client = LLMClient(provider="ollama")

            with pytest.raises(ValueError, match="Failed to parse JSON"):
                client.extract_json("not valid json")

    def test_generate_with_default_parameters(self, test_settings, mock_ollama_client):
        """Test generation uses default parameters from settings."""
        client = LLMClient(provider="ollama")
        client.client = mock_ollama_client

        client.generate(prompt="Test")

        call_args = mock_ollama_client.chat.call_args
        options = call_args.kwargs["options"]
        assert options["temperature"] == test_settings.default_temperature
        assert options["num_predict"] == test_settings.max_tokens


class TestGetLLMClient:
    """Test get_llm_client factory function."""

    def test_get_llm_client_default(self, test_settings):
        """Test getting client with default provider."""
        with patch("ollama.Client"):
            client = get_llm_client()
            assert isinstance(client, LLMClient)
            assert client.provider == test_settings.llm_provider

    def test_get_llm_client_with_provider(self, test_env, tmp_path):
        """Test getting client with specific provider."""
        with patch.dict(
            os.environ,
            {
                "NEO4J_PASSWORD": "test_password",
                "OPENAI_API_KEY": "test-key",
                "DATA_DIR": str(tmp_path / "data"),
            },
        ):
            with patch("openai.OpenAI"):
                from kg_builder.config import get_settings

                get_settings.cache_clear()

                client = get_llm_client(provider="openai")
                assert isinstance(client, LLMClient)
                assert client.provider == "openai"

                get_settings.cache_clear()
