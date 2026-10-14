import pytest

import ingestion
import ocr
from ingestion import IngestionError, chunk_pages, extract_pages


def test_extracts_utf8_text_file():
    pages = extract_pages("notes.txt", "Halo dunia".encode("utf-8"))
    assert pages == [(1, "Halo dunia")]


def test_extracts_markdown_as_text():
    pages = extract_pages("notes.md", b"# Catatan\n\nIsi dokumen")
    assert pages[0][0] == 1
    assert "Isi dokumen" in pages[0][1]


def test_rejects_unsupported_extension():
    with pytest.raises(IngestionError):
        extract_pages("payload.exe", b"not an executable")


def test_chunking_preserves_page_number_and_content():
    chunks = chunk_pages([(7, "A" * 600)])
    assert len(chunks) >= 1
    assert all(page == 7 for page, _ in chunks)
    assert "".join(piece for _, piece in chunks).startswith("A")


def test_mixed_pdf_ocr_only_fills_pages_without_text(monkeypatch):
    class FakePage:
        def __init__(self, text):
            self.text = text

        def extract_text(self):
            return self.text

    class FakeReader:
        def __init__(self, *_args, **_kwargs):
            self.pages = [
                FakePage("Selectable page one"),
                FakePage(""),
                FakePage("Selectable page three"),
            ]

    seen = {}

    def fake_ocr(_data, page_numbers):
        seen["page_numbers"] = page_numbers
        return [(2, "Recognized scanned page two")]

    monkeypatch.setattr(ingestion, "PdfReader", FakeReader)
    monkeypatch.setattr(ocr, "extract_scanned_pdf_text", fake_ocr)

    pages = extract_pages("mixed.pdf", b"fake pdf bytes")

    assert pages == [
        (1, "Selectable page one"),
        (2, "Recognized scanned page two"),
        (3, "Selectable page three"),
    ]
    assert seen["page_numbers"] == {2}
