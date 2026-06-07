"""Smoke tests for configuration. Run without API keys."""

from config import get_settings


def test_settings_defaults():
    settings = get_settings()
    assert settings.embedding_model == "BAAI/bge-m3"
    assert settings.qdrant_collection == "courses"
    assert 0.0 <= settings.similarity_threshold <= 1.0


def test_settings_cached():
    assert get_settings() is get_settings()
