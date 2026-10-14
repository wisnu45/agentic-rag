import sys
from types import SimpleNamespace

import pytest

import ocr
from ingestion import IngestionError


def test_extract_image_text_uses_ocr_result(monkeypatch):
    monkeypatch.setattr(ocr, "_recognize_image", lambda data: "Nomor surat 123")
    assert ocr.extract_image_text("scan.png", b"image") == [(1, "Nomor surat 123")]


def test_extract_image_text_rejects_other_extensions():
    with pytest.raises(IngestionError, match="Unsupported image type"):
        ocr.extract_image_text("file.pdf", b"not image")


def test_recognize_image_parses_paddleocr_2x_result(monkeypatch):
    class FakeImage:
        def convert(self, mode):
            return self

    class FakeImageModule:
        @staticmethod
        def open(_stream):
            return FakeImage()

    class FakeEngine:
        def ocr(self, _pixels, cls=True):
            return [[[[0, 0], ("Dokumen uji", 0.99)]]]

    fake_numpy = SimpleNamespace(asarray=lambda _image: "pixels")
    monkeypatch.setitem(sys.modules, "numpy", fake_numpy)
    monkeypatch.setitem(sys.modules, "PIL", SimpleNamespace(Image=FakeImageModule))
    monkeypatch.setattr(ocr, "_ocr_engine", lambda: FakeEngine())

    assert ocr._recognize_image(b"image") == "Dokumen uji"
