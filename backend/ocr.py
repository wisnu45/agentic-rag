"""Optional CPU OCR helpers for scanned PDFs and raster images.

Install the optional dependencies from requirements-ocr.txt to enable this module.
The default application requirements intentionally do not install PaddleOCR.
"""
from functools import lru_cache
from io import BytesIO
from pathlib import Path

from ingestion import IngestionError


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}


@lru_cache(maxsize=1)
def _ocr_engine():
    """Load PaddleOCR lazily so text-only deployments do not require OCR packages."""
    try:
        from paddleocr import PaddleOCR
    except ImportError as exc:
        raise IngestionError(
            "OCR dependencies are not installed. Install backend/requirements-ocr.txt to process scanned files."
        ) from exc

    try:
        return PaddleOCR(use_angle_cls=True, lang="en", use_gpu=False, show_log=False)
    except Exception as exc:
        raise IngestionError("PaddleOCR could not initialize in CPU mode.") from exc


def _recognize_image(image_bytes: bytes) -> str:
    """Recognize text from one image byte sequence using PaddleOCR 2.x API."""
    try:
        import numpy as np
        from PIL import Image
    except ImportError as exc:
        raise IngestionError(
            "OCR image dependencies are missing. Install backend/requirements-ocr.txt."
        ) from exc

    try:
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
        pixels = np.asarray(image)
        results = _ocr_engine().ocr(pixels, cls=True)
    except IngestionError:
        raise
    except Exception as exc:
        raise IngestionError("OCR failed to read the supplied image.") from exc

    lines: list[str] = []
    for page_result in results or []:
        for item in page_result or []:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                recognition = item[1]
                if isinstance(recognition, (list, tuple)) and recognition and recognition[0]:
                    lines.append(str(recognition[0]))
    return "\n".join(lines).strip()


def extract_image_text(filename: str, data: bytes) -> list[tuple[int, str]]:
    """Extract text from a supported raster image."""
    if Path(filename).suffix.lower() not in IMAGE_EXTENSIONS:
        raise IngestionError("Unsupported image type for OCR.")
    text = _recognize_image(data)
    return [(1, text)] if text else []


def extract_scanned_pdf_text(data: bytes) -> list[tuple[int, str]]:
    """Rasterize PDF pages and OCR each page, preserving 1-based page numbers."""
    try:
        import fitz
    except ImportError as exc:
        raise IngestionError(
            "PDF OCR dependencies are missing. Install backend/requirements-ocr.txt."
        ) from exc

    pages: list[tuple[int, str]] = []
    try:
        with fitz.open(stream=data, filetype="pdf") as pdf:
            for page_index, page in enumerate(pdf, start=1):
                # 1.5x scale balances legibility and memory use for CPU-only hosts.
                pixmap = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
                image_text = _recognize_image(pixmap.tobytes("png"))
                if image_text:
                    pages.append((page_index, image_text))
    except IngestionError:
        raise
    except Exception as exc:
        raise IngestionError("The scanned PDF could not be rasterized for OCR.") from exc
    return pages
