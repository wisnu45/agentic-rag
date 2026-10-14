"""Document extraction and embedding helpers for the initial RAG pipeline."""
from io import BytesIO
from pathlib import Path

import httpx
from docx import Document as DocxDocument
from pypdf import PdfReader

from config import get_settings
from models import EMBEDDING_DIMENSIONS

settings = get_settings()
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}
ALLOWED_EXTENSIONS = {".txt", ".md", ".pdf", ".docx"} | IMAGE_EXTENSIONS


class IngestionError(Exception):
    """Raised when a document cannot be extracted or embedded."""


def extract_pages(filename: str, data: bytes) -> list[tuple[int, str]]:
    """Extract text from supported documents, falling back to OCR for scans."""
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise IngestionError("Unsupported file type.")
    try:
        if suffix in {".txt", ".md"}:
            text = data.decode("utf-8-sig")
            return [(1, text)] if text.strip() else []
        if suffix in IMAGE_EXTENSIONS:
            from ocr import extract_image_text
            return extract_image_text(filename, data)
        if suffix == ".pdf":
            reader = PdfReader(BytesIO(data), strict=True)
            pages = []
            for index, page in enumerate(reader.pages, start=1):
                text = page.extract_text() or ""
                if text.strip():
                    pages.append((index, text))
            if pages:
                return pages
            from ocr import extract_scanned_pdf_text
            return extract_scanned_pdf_text(data)
        document = DocxDocument(BytesIO(data))
        text = "\n".join(p.text for p in document.paragraphs if p.text.strip())
        return [(1, text)] if text.strip() else []
    except IngestionError:
        raise
    except Exception as exc:
        raise IngestionError(
            "The document could not be read. Check that the file is valid and not encrypted."
        ) from exc


def chunk_pages(pages: list[tuple[int, str]]) -> list[tuple[int, str]]:
    """Split page text into overlapping character chunks while retaining page numbers."""
    size = max(200, settings.chunk_size)
    overlap = min(max(0, settings.chunk_overlap), size // 2)
    chunks: list[tuple[int, str]] = []
    for page_number, page_text in pages:
        normalized = " ".join(page_text.split())
        start = 0
        while start < len(normalized):
            end = min(len(normalized), start + size)
            piece = normalized[start:end].strip()
            if piece:
                chunks.append((page_number, piece))
            if end >= len(normalized):
                break
            start = end - overlap
    return chunks


def embed_text(text: str) -> list[float]:
    """Request one embedding from the configured Ollama host."""
    url = f"{settings.ollama_base_url.rstrip('/')}/api/embeddings"
    try:
        response = httpx.post(
            url,
            json={"model": settings.ollama_embedding_model, "prompt": text},
            timeout=90.0,
        )
        response.raise_for_status()
        embedding = response.json().get("embedding")
    except (httpx.HTTPError, ValueError) as exc:
        raise IngestionError(
            "Embedding service is unavailable. Verify Ollama and the configured embedding model."
        ) from exc
    if not isinstance(embedding, list) or len(embedding) != EMBEDDING_DIMENSIONS:
        raise IngestionError(
            f"Embedding model must return {EMBEDDING_DIMENSIONS} dimensions; verify the configured model."
        )
    return embedding
