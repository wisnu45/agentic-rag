"""FastAPI entry point for the Agentic RAG application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Agentic RAG"
    app_env: str = "development"
    cors_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Local-first Agentic RAG API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    """Basic liveness endpoint; dependency checks will be added in later phases."""
    return {"status": "ok", "app": settings.app_name, "environment": settings.app_env}


@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    return {"message": "Agentic RAG API is running", "docs": "/docs"}
