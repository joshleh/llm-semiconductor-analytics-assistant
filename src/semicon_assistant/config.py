from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centralized configuration.

    Reads from environment variables and optionally from a local `.env` file.
    Do NOT commit real secrets. Use `.env.example` as a template.
    """

    # LLM / API
    openai_api_key: str | None = None
    model_name: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"

    # Vector store
    vector_db: str = "chroma"
    chroma_persist_dir: str = ".chroma"

    # Retrieval / chunking
    chunk_size: int = 800
    chunk_overlap: int = 120
    top_k: int = 4

    # Logging
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()