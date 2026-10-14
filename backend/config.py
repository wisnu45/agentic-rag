"""Environment configuration for the Agentic RAG backend."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Agentic RAG API"
    app_env: str = "development"
    database_url: str = "postgresql+psycopg://agentic_rag_app:change_me_local_only@localhost:5432/agentic_rag"
    ollama_base_url: str = "http://localhost:11434"
    ollama_llm_model: str = "qwen2.5:3b"
    ollama_embedding_model: str = "nomic-embed-text"
    upload_dir: str = "../storage/uploads"
    processed_dir: str = "../storage/processed"
    max_upload_size_mb: int = 20
    chunk_size: int = 1000
    chunk_overlap: int = 150
    cors_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
