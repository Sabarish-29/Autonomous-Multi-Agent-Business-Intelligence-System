"""
Autonomous Multi-Agent Business Intelligence System - Configuration Module

Centralized configuration management using Pydantic Settings.
Optimized for 8GB RAM systems with hybrid local/cloud deployment.
"""

import os
from pathlib import Path
from typing import Optional, List
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    _env_path = str(Path(__file__).resolve().parent.parent / ".env")
    model_config = SettingsConfigDict(
        env_file=_env_path,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # -------------------------------------------------------------------------
    # Application
    # -------------------------------------------------------------------------
    app_name: str = Field(default="Autonomous Multi-Agent Business Intelligence System", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    debug: bool = Field(default=True, description="Debug mode")
    environment: str = Field(default="development", description="Environment")

    # -------------------------------------------------------------------------
    # LLM Configuration
    # -------------------------------------------------------------------------
    use_local_llm: bool = Field(
        default=True,
        description="Use local Ollama LLM (set False for cloud-only)"
    )

    # Ollama (Local)
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Ollama API base URL"
    )
    ollama_model: str = Field(
        default="llama3:8b-instruct-q4_K_M",
        description="Ollama model name"
    )

    # Claude API (Cloud)
    anthropic_api_key: Optional[str] = Field(
        default=None,
        description="Anthropic API key for Claude"
    )
    anthropic_model: str = Field(
        default="claude-sonnet-4-20250514",
        description="Claude model to use"
    )

    # Groq API (Fast Cloud)
    groq_api_key: Optional[str] = Field(
        default=None,
        description="Groq API key for fast inference"
    )
    groq_model: str = Field(
        default="llama-3.1-70b-versatile",
        description="Groq model to use"
    )

    # -------------------------------------------------------------------------
    # Vector Database (ChromaDB)
    # -------------------------------------------------------------------------
    chroma_persist_dir: str = Field(
        default="./data/embeddings",
        description="ChromaDB persistence directory"
    )
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Sentence transformer model for embeddings"
    )

    # -------------------------------------------------------------------------
    # Database
    # -------------------------------------------------------------------------
    database_url: str = Field(
        default="sqlite:///./data/sample/sales_db.sqlite",
        description="Database connection URL"
    )

    # -------------------------------------------------------------------------
    # Power BI Integration
    # -------------------------------------------------------------------------
    powerbi_client_id: Optional[str] = Field(default=None)
    powerbi_client_secret: Optional[str] = Field(default=None)
    powerbi_tenant_id: Optional[str] = Field(default=None)
    powerbi_workspace_id: Optional[str] = Field(default=None)

    # -------------------------------------------------------------------------
    # Azure Configuration
    # -------------------------------------------------------------------------
    azure_subscription_id: Optional[str] = Field(default=None)
    azure_resource_group: str = Field(default="datagenie-rg")
    azure_storage_connection_string: Optional[str] = Field(default=None)
    azure_storage_container: str = Field(default="datagenie-data")

    # -------------------------------------------------------------------------
    # API Server
    # -------------------------------------------------------------------------
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    api_workers: int = Field(default=2)

    # -------------------------------------------------------------------------
    # Resource Limits (Optimized for 8GB RAM)
    # -------------------------------------------------------------------------
    max_concurrent_requests: int = Field(
        default=2,
        description="Maximum concurrent LLM requests"
    )
    ollama_num_ctx: int = Field(
        default=4096,
        description="Ollama context window size"
    )
    ollama_num_gpu: int = Field(
        default=0,
        description="Number of GPU layers (0 for CPU only)"
    )
    max_tokens_per_request: int = Field(
        default=2000,
        description="Maximum tokens per LLM request"
    )

    # -------------------------------------------------------------------------
    # Logging
    # -------------------------------------------------------------------------
    log_level: str = Field(default="INFO")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # -------------------------------------------------------------------------
    # Security
    # -------------------------------------------------------------------------
    secret_key: str = Field(
        default="dev-secret-key-change-in-production",
        description="Secret key for security"
    )
    cors_origins: str = Field(
        default="http://localhost:8501,http://localhost:3000",
        description="Comma-separated CORS origins"
    )

    # -------------------------------------------------------------------------
    # Computed Properties
    # -------------------------------------------------------------------------
    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment.lower() == "production"

    @property
    def has_anthropic_key(self) -> bool:
        """Check if Anthropic API key is configured."""
        return bool(self.anthropic_api_key)

    @property
    def has_groq_key(self) -> bool:
        """Check if Groq API key is configured."""
        return bool(self.groq_api_key)

    @property
    def has_powerbi_config(self) -> bool:
        """Check if Power BI is configured."""
        return all([
            self.powerbi_client_id,
            self.powerbi_client_secret,
            self.powerbi_tenant_id
        ])

    @property
    def has_azure_config(self) -> bool:
        """Check if Azure is configured."""
        return bool(self.azure_storage_connection_string)


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Returns:
        Settings: Application settings
    """
    return Settings()


# Create global settings instance
settings = get_settings()


# -------------------------------------------------------------------------
# Logging Configuration
# -------------------------------------------------------------------------
import logging


def setup_logging():
    """Configure application logging."""
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format=settings.log_format
    )
    
    # Reduce noise from third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)


# Setup logging on import
setup_logging()
