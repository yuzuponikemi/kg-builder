"""Application settings and configuration management."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Neo4j Configuration
    neo4j_uri: str = Field(default="bolt://localhost:7687", description="Neo4j URI")
    neo4j_user: str = Field(default="neo4j", description="Neo4j username")
    neo4j_password: str = Field(..., description="Neo4j password")
    neo4j_database: str = Field(default="neo4j", description="Neo4j database name")

    # LLM Provider Configuration
    llm_provider: Literal["ollama", "openai", "anthropic", "gemini"] = Field(
        default="ollama", description="Primary LLM provider to use"
    )

    # Ollama Configuration (Local LLM)
    ollama_base_url: str = Field(
        default="http://localhost:11434", description="Ollama base URL"
    )
    ollama_model: str = Field(
        default="llama3.1:8b", description="Ollama model to use"
    )
    ollama_timeout: int = Field(default=300, description="Ollama request timeout in seconds")
    ollama_num_ctx: int = Field(default=8192, description="Ollama context window size")
    ollama_num_gpu: int = Field(default=1, description="Number of GPUs for Ollama (0 for CPU)")
    ollama_num_thread: int = Field(default=8, description="CPU threads for Ollama")

    # OpenAI Configuration (Optional)
    openai_api_key: str | None = Field(default=None, description="OpenAI API key")
    openai_model: str = Field(default="gpt-4-turbo", description="OpenAI model to use")

    # Anthropic Configuration (Optional)
    anthropic_api_key: str | None = Field(default=None, description="Anthropic API key")
    anthropic_model: str = Field(
        default="claude-3-5-sonnet-20241022", description="Anthropic model to use"
    )

    # Gemini Configuration (Optional)
    gemini_api_key: str | None = Field(default=None, description="Google Gemini API key")
    gemini_model: str = Field(
        default="gemini-2.5-flash", description="Gemini model to use"
    )

    # Embedding Configuration
    embedding_provider: Literal["local", "openai", "ollama"] = Field(
        default="local", description="Embedding provider to use"
    )
    embedding_model: str = Field(
        default="BAAI/bge-large-en-v1.5", description="Sentence transformer model for local embeddings"
    )
    ollama_embedding_model: str = Field(
        default="nomic-embed-text", description="Ollama model for embeddings"
    )
    embedding_device: Literal["cuda", "cpu", "mps"] = Field(
        default="cuda", description="Device for embedding generation"
    )
    embedding_batch_size: int = Field(default=32, description="Batch size for embeddings")
    embedding_dimension: int = Field(default=1024, description="Embedding vector dimension")

    # API Configuration
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    api_workers: int = Field(default=4, description="Number of API workers")
    api_key_salt: str = Field(default="change-me", description="Salt for API key hashing")
    jwt_secret_key: str = Field(default="change-me", description="JWT secret key")
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:5173",
        description="Comma-separated CORS origins",
    )

    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis URL")

    # Data Paths
    data_dir: Path = Field(default=Path("./data"), description="Base data directory")
    papers_dir: Path = Field(
        default=Path("./data/papers"), description="Directory for PDF papers"
    )
    embeddings_cache_dir: Path = Field(
        default=Path("./data/embeddings"), description="Directory for cached embeddings"
    )
    exports_dir: Path = Field(
        default=Path("./data/exports"), description="Directory for exports"
    )

    # Processing Configuration
    max_concurrent_extractions: int = Field(
        default=5, description="Maximum concurrent extraction tasks"
    )
    extraction_timeout: int = Field(
        default=300, description="Extraction timeout in seconds"
    )
    default_temperature: float = Field(
        default=0.0, description="Default LLM temperature"
    )
    max_tokens: int = Field(default=4000, description="Maximum tokens for LLM responses")

    # Logging Configuration
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Logging level"
    )
    log_format: Literal["json", "text"] = Field(
        default="json", description="Log format"
    )
    log_file: Path | None = Field(
        default=Path("./logs/kg-builder.log"), description="Log file path"
    )

    # Feature Flags
    enable_arxiv_integration: bool = Field(
        default=True, description="Enable ArXiv integration"
    )
    enable_pubmed_integration: bool = Field(
        default=False, description="Enable PubMed integration"
    )
    enable_graphql: bool = Field(default=True, description="Enable GraphQL endpoint")
    enable_websockets: bool = Field(default=True, description="Enable WebSocket support")

    @field_validator("cors_origins")
    @classmethod
    def parse_cors_origins(cls, v: str) -> list[str]:
        """Parse comma-separated CORS origins."""
        return [origin.strip() for origin in v.split(",")]

    @field_validator(
        "data_dir", "papers_dir", "embeddings_cache_dir", "exports_dir", mode="before"
    )
    @classmethod
    def validate_path(cls, v: str | Path) -> Path:
        """Validate and create path if it doesn't exist."""
        path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def neo4j_config(self) -> dict[str, str]:
        """Get Neo4j configuration as dictionary."""
        return {
            "uri": self.neo4j_uri,
            "user": self.neo4j_user,
            "password": self.neo4j_password,
            "database": self.neo4j_database,
        }

    @property
    def has_openai(self) -> bool:
        """Check if OpenAI API key is configured."""
        return self.openai_api_key is not None and len(self.openai_api_key) > 0

    @property
    def has_anthropic(self) -> bool:
        """Check if Anthropic API key is configured."""
        return self.anthropic_api_key is not None and len(self.anthropic_api_key) > 0

    @property
    def has_gemini(self) -> bool:
        """Check if Gemini API key is configured."""
        return self.gemini_api_key is not None and len(self.gemini_api_key) > 0

    @property
    def is_using_ollama(self) -> bool:
        """Check if using Ollama as LLM provider."""
        return self.llm_provider == "ollama"

    @property
    def current_llm_model(self) -> str:
        """Get the current LLM model based on provider."""
        if self.llm_provider == "ollama":
            return self.ollama_model
        elif self.llm_provider == "openai":
            return self.openai_model
        elif self.llm_provider == "anthropic":
            return self.anthropic_model
        elif self.llm_provider == "gemini":
            return self.gemini_model
        return self.ollama_model

    @property
    def ollama_config(self) -> dict[str, int | str]:
        """Get Ollama configuration as dictionary."""
        return {
            "base_url": self.ollama_base_url,
            "model": self.ollama_model,
            "timeout": self.ollama_timeout,
            "num_ctx": self.ollama_num_ctx,
            "num_gpu": self.ollama_num_gpu,
            "num_thread": self.ollama_num_thread,
        }


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
