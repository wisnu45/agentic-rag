"""FastAPI application for Agentic RAG."""
import hashlib
import mimetypes
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from config import get_settings
from database import SessionLocal, check_database_connection
from ingestion import ALLOWED_EXTENSIONS, IngestionError, chunk_pages, embed_text, extract_pages
from models import Document, DocumentChunk
from rag import RAGGenerationError, generate_answer
from schemas import ChatRequest, ChatResponse, DocumentUploadResponse, HealthResponse, SearchRequest, SearchResponse, SearchResult
from security import StorageEncryptionError, encrypt_file

settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
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


@app.post(
    "/api/documents",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["documents"],
)
def upload_document(file: UploadFile = File(...)) -> DocumentUploadResponse:
    """Upload, extract, chunk, embed, and index a supported document.

    Supports TXT, Markdown, PDF, DOCX, and raster images. Scanned PDFs and
    images require the optional PaddleOCR dependencies in requirements-ocr.txt.
    """
    original_name = Path(file.filename or "").name
    suffix = Path(original_name).suffix.lower()
    if not original_name or suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type. Allowed extensions: {', '.join(sorted(ALLOWED_EXTENSIONS))}.",
        )

    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    data = file.file.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds the {settings.max_upload_size_mb} MB upload limit.",
        )
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

    digest = hashlib.sha256(data).hexdigest()
    storage_root = Path(settings.upload_dir).resolve()
    storage_root.mkdir(parents=True, exist_ok=True)
    stored_path = storage_root / f"{uuid4().hex}{suffix}"

    db = SessionLocal()
    try:
        existing = db.scalar(select(Document).where(Document.sha256 == digest))
        if existing:
            return DocumentUploadResponse(
                document_id=str(existing.id),
                filename=existing.filename,
                status=existing.status,
                chunks_created=len(existing.chunks),
                message="This file content has already been uploaded.",
            )

        try:
            pages = extract_pages(original_name, data)
        except IngestionError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

        if not pages:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No readable text was found in this file. For scanned PDFs/images, verify the optional PaddleOCR dependencies are installed.",
            )

        chunks = chunk_pages(pages)
        if not chunks:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No text chunks could be created.")

        try:
            encrypted_data = encrypt_file(data)
        except StorageEncryptionError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Encrypted file storage is not configured correctly.",
            ) from exc

        stored_path.write_bytes(encrypted_data)
        document = Document(
            filename=original_name[:255],
            mime_type=file.content_type or mimetypes.guess_type(original_name)[0],
            sha256=digest,
            storage_path=str(stored_path),
            status="processing",
            extra_metadata={"extension": suffix, "page_count": len(pages)},
        )
        db.add(document)
        db.flush()

        vector_rows = []
        try:
            for index, (page_number, content) in enumerate(chunks):
                vector_rows.append(
                    DocumentChunk(
                        document_id=document.id,
                        chunk_index=index,
                        content=content,
                        embedding=embed_text(content),
                        page_number=page_number,
                        extra_metadata={"source_filename": original_name},
                    )
                )
        except IngestionError as exc:
            db.rollback()
            stored_path.unlink(missing_ok=True)
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

        db.add_all(vector_rows)
        document.status = "indexed"
        db.commit()
        return DocumentUploadResponse(
            document_id=str(document.id),
            filename=document.filename,
            status=document.status,
            chunks_created=len(vector_rows),
            message="Document text extracted, chunked, and embedded successfully.",
        )
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        stored_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Document storage is unavailable. Verify the database schema and connection.",
        ) from exc
    finally:
        db.close()
        file.file.close()


@app.post("/api/search", response_model=SearchResponse, tags=["retrieval"])
def search_documents(payload: SearchRequest) -> SearchResponse:
    """Retrieve the most similar indexed chunks using cosine distance."""
    try:
        query_embedding = embed_text(payload.query)
    except IngestionError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    db = SessionLocal()
    try:
        distance = DocumentChunk.embedding.cosine_distance(query_embedding).label("distance")
        statement = (
            select(DocumentChunk, Document, distance)
            .join(Document, DocumentChunk.document_id == Document.id)
            .where(Document.status == "indexed")
            .order_by(distance)
            .limit(payload.top_k)
        )
        rows = db.execute(statement).all()
        results = [
            SearchResult(
                document_id=str(document.id),
                filename=document.filename,
                page_number=chunk.page_number,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                score=1.0 - float(distance_value),
            )
            for chunk, document, distance_value in rows
            if distance_value is not None
        ]
        return SearchResponse(query=payload.query, results=results)
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Vector search is unavailable. Verify the database schema and pgvector extension.",
        ) from exc
    finally:
        db.close()


@app.post("/api/chat", response_model=ChatResponse, tags=["rag"])
def chat_with_documents(payload: ChatRequest) -> ChatResponse:
    """Answer a question using retrieved document chunks and source markers."""
    try:
        query_embedding = embed_text(payload.message)
    except IngestionError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    db = SessionLocal()
    try:
        distance = DocumentChunk.embedding.cosine_distance(query_embedding).label("distance")
        statement = (
            select(DocumentChunk, Document, distance)
            .join(Document, DocumentChunk.document_id == Document.id)
            .where(Document.status == "indexed")
            .order_by(distance)
            .limit(5)
        )
        rows = db.execute(statement).all()
        if not rows:
            return ChatResponse(
                answer="Belum ada dokumen terindeks yang dapat dijadikan sumber jawaban. Unggah dokumen terlebih dahulu.",
                tool_used="pgvector_retrieval",
                sources=[],
            )

        contexts = []
        sources = []
        for index, (chunk, document, distance_value) in enumerate(rows, start=1):
            source_id = f"S{index}"
            page = str(chunk.page_number) if chunk.page_number is not None else "n/a"
            contexts.append({
                "source_id": source_id,
                "filename": document.filename,
                "page": page,
                "content": chunk.content,
            })
            sources.append({
                "source_id": source_id,
                "filename": document.filename,
                "page": page,
                "chunk_index": str(chunk.chunk_index),
            })

        try:
            answer = generate_answer(payload.message, contexts)
        except RAGGenerationError as exc:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

        return ChatResponse(
            answer=answer,
            tool_used="pgvector_retrieval+ollama",
            sources=sources,
        )
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Document retrieval is unavailable. Verify PostgreSQL and pgvector.",
        ) from exc
    finally:
        db.close()
