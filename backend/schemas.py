"""Pydantic schemas for API endpoints."""
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    app: str = "Agentic RAG API"


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=100)
    message: str = Field(min_length=1, max_length=10000)


class ChatResponse(BaseModel):
    answer: str
    tool_used: str = "none"
    sources: list[dict[str, str]] = Field(default_factory=list)


class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    chunks_created: int
    message: str
