import pytest

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
