from types import SimpleNamespace

import pytest

import rag


def test_generate_answer_sends_grounded_context(monkeypatch):
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"message": {"content": "Informasi utama ada pada dokumen [S1]."}}

    def fake_post(url, json, timeout):
        captured["url"] = url
        captured["payload"] = json
        return FakeResponse()

    monkeypatch.setattr(rag.httpx, "post", fake_post)
    answer = rag.generate_answer(
        "Apa poin pentingnya?",
        [{"source_id": "S1", "filename": "policy.txt", "page": "1", "content": "Kebijakan akses."}],
    )

    assert "[S1]" in answer
    assert captured["payload"]["stream"] is False
    assert "Kebijakan akses." in captured["payload"]["messages"][1]["content"]
    assert "untrusted data" in captured["payload"]["messages"][0]["content"]


def test_generate_answer_rejects_empty_model_output(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"message": {"content": ""}}

    monkeypatch.setattr(rag.httpx, "post", lambda *args, **kwargs: FakeResponse())
    with pytest.raises(rag.RAGGenerationError):
        rag.generate_answer("Question", [])
