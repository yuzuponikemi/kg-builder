"""Tests for configuration and settings."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from kg_builder.config import Settings, get_settings


class TestSettings:
    """Test Settings class."""

    def test_settings_with_required_fields(self, test_env, tmp_path):
        """Test settings creation with required fields."""
        with patch.dict(os.environ, {
            "NEO4J_PASSWORD": "test_password",
            "DATA_DIR": str(tmp_path / "data"),
        }):
            settings = Settings()
            assert settings.neo4j_password == "test_password"
            assert settings.neo4j_user == "neo4j"
            assert settings.neo4j_uri == "bolt://localhost:7687"

    def test_settings_missing_required_field(self):
        """Test that missing required field raises error."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValidationError):
                Settings()

    def test_llm_provider_default(self, test_settings):
        """Test default LLM provider is ollama."""
        assert test_settings.llm_provider == "ollama"
        assert test_settings.is_using_ollama is True

    def test_llm_provider_openai(self, test_env, tmp_path):
        """Test OpenAI as LLM provider."""
        with patch.dict(os.environ, {
            "NEO4J_PASSWORD": "test_password",
            "LLM_PROVIDER": "openai",
            "OPENAI_API_KEY": "test-key",
            "DATA_DIR": str(tmp_path / "data"),
        }):
            settings = Settings()
            assert settings.llm_provider == "openai"
            assert settings.is_using_ollama is False
            assert settings.has_openai is True

    def test_llm_provider_anthropic(self, test_env, tmp_path):
        """Test Anthropic as LLM provider."""
        with patch.dict(os.environ, {
            "NEO4J_PASSWORD": "test_password",
            "LLM_PROVIDER": "anthropic",
            "ANTHROPIC_API_KEY": "test-key",
            "DATA_DIR": str(tmp_path / "data"),
        }):
            settings = Settings()
            assert settings.llm_provider == "anthropic"
            assert settings.has_anthropic is True

    def test_llm_provider_gemini(self, test_env, tmp_path):
        """Test Gemini as LLM provider."""
        with patch.dict(os.environ, {
            "NEO4J_PASSWORD": "test_password",
            "LLM_PROVIDER": "gemini",
            "GEMINI_API_KEY": "test-key",
            "DATA_DIR": str(tmp_path / "data"),
        }):
            settings = Settings()
            assert settings.llm_provider == "gemini"
            assert settings.has_gemini is True

    def test_current_llm_model_ollama(self, test_settings):
        """Test current_llm_model returns ollama model."""
        assert test_settings.current_llm_model == test_settings.ollama_model

    def test_current_llm_model_openai(self, test_env, tmp_path):
        """Test current_llm_model returns openai model."""
        with patch.dict(os.environ, {
            "NEO4J_PASSWORD": "test_password",
            "LLM_PROVIDER": "openai",
            "OPENAI_API_KEY": "test-key",
            "DATA_DIR": str(tmp_path / "data"),
        }):
            settings = Settings()
            assert settings.current_llm_model == settings.openai_model

    def test_neo4j_config_property(self, test_settings):
        """Test neo4j_config property returns correct dict."""
        config = test_settings.neo4j_config
        assert config["uri"] == test_settings.neo4j_uri
        assert config["user"] == test_settings.neo4j_user
        assert config["password"] == test_settings.neo4j_password
        assert config["database"] == test_settings.neo4j_database

    def test_ollama_config_property(self, test_settings):
        """Test ollama_config property returns correct dict."""
        config = test_settings.ollama_config
        assert config["base_url"] == test_settings.ollama_base_url
        assert config["model"] == test_settings.ollama_model
        assert config["timeout"] == test_settings.ollama_timeout
        assert config["num_ctx"] == test_settings.ollama_num_ctx

    def test_cors_origins_parsing(self, test_env, tmp_path):
        """Test CORS origins are parsed correctly."""
        with patch.dict(os.environ, {
            "NEO4J_PASSWORD": "test_password",
            "CORS_ORIGINS": "http://localhost:3000, http://localhost:5173, http://example.com",
            "DATA_DIR": str(tmp_path / "data"),
        }):
            settings = Settings()
            assert len(settings.cors_origins) == 3
            assert "http://localhost:3000" in settings.cors_origins
            assert "http://example.com" in settings.cors_origins

    def test_path_creation(self, test_env, tmp_path):
        """Test that paths are created automatically."""
        data_dir = tmp_path / "data"
        papers_dir = tmp_path / "data/papers"

        with patch.dict(os.environ, {
            "NEO4J_PASSWORD": "test_password",
            "DATA_DIR": str(data_dir),
            "PAPERS_DIR": str(papers_dir),
        }):
            settings = Settings()
            assert settings.data_dir.exists()
            assert settings.papers_dir.exists()

    def test_embedding_configuration(self, test_settings):
        """Test embedding configuration defaults."""
        assert test_settings.embedding_provider == "local"
        assert test_settings.embedding_model == "BAAI/bge-large-en-v1.5"
        assert test_settings.embedding_dimension == 1024

    def test_feature_flags(self, test_settings):
        """Test feature flags defaults."""
        assert test_settings.enable_arxiv_integration is True
        assert test_settings.enable_pubmed_integration is False
        assert test_settings.enable_graphql is True
        assert test_settings.enable_websockets is True

    def test_log_configuration(self, test_settings):
        """Test logging configuration."""
        assert test_settings.log_level == "INFO"
        assert test_settings.log_format == "json"
        assert test_settings.log_file is not None


class TestGetSettings:
    """Test get_settings function."""

    def test_get_settings_cached(self, test_settings):
        """Test that get_settings returns cached instance."""
        # Clear cache first
        get_settings.cache_clear()

        # Get settings twice
        settings1 = get_settings()
        settings2 = get_settings()

        # Should be the same instance
        assert settings1 is settings2

        # Clean up
        get_settings.cache_clear()

    def test_get_settings_with_env_changes(self, test_env, tmp_path):
        """Test that cached settings don't reflect env changes."""
        # Clear cache
        get_settings.cache_clear()

        with patch.dict(os.environ, {
            "NEO4J_PASSWORD": "password1",
            "DATA_DIR": str(tmp_path / "data"),
        }):
            settings1 = get_settings()
            assert settings1.neo4j_password == "password1"

        # Change env (but cache should still return old instance)
        with patch.dict(os.environ, {
            "NEO4J_PASSWORD": "password2",
            "DATA_DIR": str(tmp_path / "data"),
        }):
            settings2 = get_settings()
            # Due to cache, should still be password1
            assert settings2 is settings1

        # Clear cache
        get_settings.cache_clear()
