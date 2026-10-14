"""Initial FastAPI application for Agentic RAG."""
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from database import check_database_connection
from schemas import HealthResponse

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Local-first Agentic RAG API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.get("/health", response_model=HealthResponse, tags=["system"])
def health_check() -> HealthResponse:
    """Liveness endpoint; does not require dependent services."""
    return HealthResponse()


@app.get("/health/ready", tags=["system"])
def readiness_check() -> dict[str, str]:
    """Readiness endpoint verifies PostgreSQL connectivity."""
    try:
        check_database_connection()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is not available",
        ) from exc
    return {"status": "ready", "database": "connected"}
