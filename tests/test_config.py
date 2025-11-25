"""Tests for configuration module."""

import pytest
from pydantic import ValidationError

from kg_builder.config.settings import Settings, get_settings


def test_settings_default_values():
    """Test that settings can be initialized with default values."""
    # This will use environment variables if available, or defaults
    settings = get_settings()
    assert settings is not None
    assert settings.neo4j_uri is not None
    assert settings.llm_provider in ["ollama", "openai", "anthropic", "gemini"]


def test_settings_singleton():
    """Test that get_settings returns the same instance."""
    settings1 = get_settings()
    settings2 = get_settings()
    assert settings1 is settings2


def test_settings_with_custom_values(monkeypatch):
    """Test settings with custom environment variables."""
    # Clear the settings cache
    get_settings.cache_clear()

    monkeypatch.setenv("NEO4J_URI", "bolt://testhost:7687")
    monkeypatch.setenv("NEO4J_USER", "testuser")
    monkeypatch.setenv("NEO4J_PASSWORD", "testpass")
    monkeypatch.setenv("LLM_PROVIDER", "gemini")

    settings = get_settings()
    assert settings.neo4j_uri == "bolt://testhost:7687"
    assert settings.neo4j_user == "testuser"
    assert settings.neo4j_password == "testpass"
    assert settings.llm_provider == "gemini"

    # Clean up
    get_settings.cache_clear()


def test_settings_neo4j_config():
    """Test Neo4j configuration dict generation."""
    settings = get_settings()
    config = settings.neo4j_config

    assert isinstance(config, dict)
    assert "uri" in config
    assert "user" in config
    assert "password" in config
