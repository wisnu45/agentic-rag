from types import SimpleNamespace

import pytest

import orchestration


def test_orchestration_disabled_returns_none(monkeypatch):
    monkeypatch.setattr(
        orchestration,
        "get_settings",
        lambda: SimpleNamespace(n8n_chat_webhook_url="", n8n_webhook_secret="", n8n_timeout_seconds=90),
    )
    assert orchestration.generate_agent_answer("question", []) is None


def test_orchestration_sends_question_and_context(monkeypatch):
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"answer": "Jawaban berbasis sumber [S1]."}

    def fake_post(url, json, headers, timeout):
        captured["url"] = url
        captured["json"] = json
        captured["headers"] = headers
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(
        orchestration,
        "get_settings",
        lambda: SimpleNamespace(
            n8n_chat_webhook_url="https://n8n.example/webhook/chat",
            n8n_webhook_secret="test-secret-value-with-at-least-32-characters",
            n8n_timeout_seconds=45,
        ),
    )
    monkeypatch.setattr(orchestration.httpx, "post", fake_post)

    answer = orchestration.generate_agent_answer(
        "Apa isi dokumen?",
        [{"source_id": "S1", "filename": "policy.pdf", "page": "1", "content": "Aturan akses."}],
    )

    assert answer == "Jawaban berbasis sumber [S1]."
    assert captured["json"]["event"] == "answer_question"
    assert captured["json"]["contexts"][0]["content"] == "Aturan akses."
    assert captured["headers"]["X-Agentic-RAG-Webhook-Secret"] == "test-secret-value-with-at-least-32-characters"
    assert captured["timeout"] == 45


def test_configured_webhook_requires_secret(monkeypatch):
    monkeypatch.setattr(
        orchestration,
        "get_settings",
        lambda: SimpleNamespace(
            n8n_chat_webhook_url="https://n8n.example/webhook/chat",
            n8n_webhook_secret="",
            n8n_timeout_seconds=90,
        ),
    )
    with pytest.raises(orchestration.OrchestrationError, match="N8N_WEBHOOK_SECRET"):
        orchestration.generate_agent_answer("question", [])


def test_invalid_webhook_response_is_rejected(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"output": "wrong response shape"}

    monkeypatch.setattr(
        orchestration,
        "get_settings",
        lambda: SimpleNamespace(
            n8n_chat_webhook_url="https://n8n.example/webhook/chat",
            n8n_webhook_secret="test-secret-value-with-at-least-32-characters",
            n8n_timeout_seconds=90,
        ),
    )
    monkeypatch.setattr(orchestration.httpx, "post", lambda *args, **kwargs: FakeResponse())
    with pytest.raises(orchestration.OrchestrationError, match="field named 'answer'"):
        orchestration.generate_agent_answer("question", [])


def test_non_object_webhook_response_is_rejected(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return ["not", "an", "object"]

    monkeypatch.setattr(
        orchestration,
        "get_settings",
        lambda: SimpleNamespace(
            n8n_chat_webhook_url="https://n8n.example/webhook/chat",
            n8n_webhook_secret="test-secret-value-with-at-least-32-characters",
            n8n_timeout_seconds=90,
        ),
    )
    monkeypatch.setattr(orchestration.httpx, "post", lambda *args, **kwargs: FakeResponse())
    with pytest.raises(orchestration.OrchestrationError, match="JSON object"):
        orchestration.generate_agent_answer("question", [])
