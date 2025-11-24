"""Pytest configuration and shared fixtures."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pydantic_settings import BaseSettings

from kg_builder.config import Settings


@pytest.fixture
def test_env():
    """Set up test environment variables."""
    original_env = os.environ.copy()

    # Set minimal required environment variables
    os.environ["NEO4J_PASSWORD"] = "test_password"
    os.environ["LLM_PROVIDER"] = "ollama"

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def test_settings(test_env, tmp_path):
    """Create test settings with temporary directories."""
    with patch.dict(
        os.environ,
        {
            "NEO4J_PASSWORD": "test_password",
            "NEO4J_URI": "bolt://localhost:7687",
            "NEO4J_USER": "neo4j",
            "LLM_PROVIDER": "ollama",
            "OLLAMA_MODEL": "llama3.1:8b",
            "DATA_DIR": str(tmp_path / "data"),
            "PAPERS_DIR": str(tmp_path / "data/papers"),
            "EMBEDDINGS_CACHE_DIR": str(tmp_path / "data/embeddings"),
            "EXPORTS_DIR": str(tmp_path / "data/exports"),
        },
    ):
        # Clear the lru_cache to force recreation
        from kg_builder.config import get_settings

        get_settings.cache_clear()

        settings = Settings()
        yield settings

        # Clear cache again after test
        get_settings.cache_clear()


@pytest.fixture
def mock_ollama_client():
    """Mock Ollama client for testing."""
    with patch("ollama.Client") as mock_client:
        mock_instance = MagicMock()
        mock_instance.chat.return_value = {
            "message": {"content": '{"entities": [], "relationships": []}'}
        }
        mock_client.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    with patch("openai.OpenAI") as mock_client:
        mock_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"entities": [], "relationships": []}'
        mock_instance.chat.completions.create.return_value = mock_response
        mock_client.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client for testing."""
    with patch("anthropic.Anthropic") as mock_client:
        mock_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.content[0].text = '{"entities": [], "relationships": []}'
        mock_instance.messages.create.return_value = mock_response
        mock_client.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_gemini_client():
    """Mock Gemini client for testing."""
    with patch("google.generativeai.GenerativeModel") as mock_model:
        mock_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.text = '{"entities": [], "relationships": []}'
        mock_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def sample_pdf_path(tmp_path):
    """Create a sample PDF file for testing."""
    pdf_path = tmp_path / "test_paper.pdf"
    # Note: This creates an empty file. For real PDF testing,
    # you'd need to use a library like reportlab to generate a valid PDF
    pdf_path.write_bytes(b"%PDF-1.4\n%EOF")
    return pdf_path


@pytest.fixture
def sample_text():
    """Sample scientific text for testing extraction."""
    return """
    Graph Neural Networks (GNNs) are a powerful approach for learning on graph-structured data.
    They have been successfully applied to various domains including molecular property prediction,
    social network analysis, and recommendation systems. The Message Passing Neural Network (MPNN)
    framework provides a unified view of many GNN architectures.
    """


@pytest.fixture
def sample_entities():
    """Sample extracted entities for testing."""
    return [
        {
            "name": "Graph Neural Networks",
            "type": "method",
            "description": "A powerful approach for learning on graph-structured data",
            "confidence": 0.95,
        },
        {
            "name": "Message Passing Neural Network",
            "type": "method",
            "description": "A framework providing unified view of GNN architectures",
            "confidence": 0.90,
        },
        {
            "name": "molecular property prediction",
            "type": "application",
            "description": "Application of GNNs to predict molecular properties",
            "confidence": 0.85,
        },
    ]


@pytest.fixture
def sample_relationships():
    """Sample extracted relationships for testing."""
    return [
        {
            "source": "Graph Neural Networks",
            "target": "molecular property prediction",
            "relation": "applied_to",
            "description": "GNNs are applied to molecular property prediction",
            "confidence": 0.90,
        },
        {
            "source": "Message Passing Neural Network",
            "target": "Graph Neural Networks",
            "relation": "provides_framework_for",
            "description": "MPNN provides unified framework for GNNs",
            "confidence": 0.88,
        },
    ]


@pytest.fixture
def mock_neo4j_driver():
    """Mock Neo4j driver for testing."""
    with patch("neo4j.GraphDatabase.driver") as mock_driver:
        mock_session = MagicMock()
        mock_driver.return_value.session.return_value.__enter__.return_value = mock_session
        yield mock_driver
