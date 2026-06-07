"""Central configuration and a model-agnostic LLM factory.

Models are never hard-coded in a node. Everything goes through `get_llm(role)`,
driven by environment variables, so models can be swapped without code changes.
"""

import os
from functools import lru_cache

from langchain.chat_models import init_chat_model
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, overridable via `.env` or environment variables."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "courses"

    # Multilingual embeddings (documents and questions are in French).
    embedding_model: str = "BAAI/bge-m3"

    # Retrieval threshold, calibrated empirically. Below it, the answer is refused.
    similarity_threshold: float = 0.5

    # Relational store (SQLite in development, PostgreSQL later).
    database_url: str = "sqlite:///./app.db"


@lru_cache
def get_settings() -> Settings:
    """Return cached settings."""
    return Settings()


def get_llm(role: str = "default"):
    """Build a chat model for the given role, selected by the `LLM_<ROLE>` env var.

    Defaults to `gpt-4o-mini`. Uses `temperature=0` for reproducibility.
    """
    model = os.getenv(f"LLM_{role.upper()}", "gpt-4o-mini")
    return init_chat_model(model, temperature=0)
