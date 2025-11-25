"""Pytest configuration and shared fixtures for kg-builder tests."""

import random
import tempfile
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture(scope="session", autouse=True)
def set_random_seeds() -> None:
    """Fix random seeds for reproducibility across all tests."""
    random.seed(42)
    try:
        import numpy as np
        np.random.seed(42)
    except ImportError:
        pass


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Provide a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def sample_pdf_path(temp_dir: Path) -> Path:
    """Provide a sample PDF file path for testing."""
    pdf_path = temp_dir / "sample.pdf"
    pdf_path.touch()  # Create empty file for testing
    return pdf_path


@pytest.fixture
def sample_text() -> str:
    """Provide sample scientific text for testing."""
    return """
    Graph Neural Networks (GNNs) have emerged as a powerful approach for learning
    representations of graph-structured data. These networks leverage message passing
    mechanisms to aggregate information from neighboring nodes. Recent advances in
    attention-based GNNs have shown improved performance on node classification tasks.
    """


@pytest.fixture
def mock_neo4j_config() -> dict:
    """Provide mock Neo4j configuration for testing."""
    return {
        "uri": "bolt://localhost:7687",
        "user": "neo4j",
        "password": "test_password",
    }


def pytest_configure(config: pytest.Config) -> None:
    """Register custom pytest markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "requires_neo4j: marks tests that require Neo4j")
    config.addinivalue_line("markers", "requires_llm: marks tests that require LLM API")
