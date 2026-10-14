from types import SimpleNamespace

from fastapi.testclient import TestClient

from auth import get_current_user
from main import app

client = TestClient(app)
app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(username="test-admin", role="admin")


def test_upload_rejects_unsupported_extension_before_database_access():
    response = client.post(
        "/api/documents",
        files={"file": ("payload.exe", b"not an executable", "application/octet-stream")},
    )
    assert response.status_code == 415
    assert "Unsupported file type" in response.json()["detail"]


def test_upload_rejects_empty_file_before_database_access():
    response = client.post(
        "/api/documents",
        files={"file": ("empty.txt", b"", "text/plain")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Uploaded file is empty."


def test_document_search_requires_authentication():
    app.dependency_overrides.pop(get_current_user, None)
    try:
        response = client.post("/api/search", json={"query": "test"})
        assert response.status_code == 401
    finally:
        app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(username="test-admin", role="admin")


def test_viewer_cannot_upload_documents():
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(username="read-only", role="viewer")
    response = client.post(
        "/api/documents",
        files={"file": ("notes.txt", b"sample", "text/plain")},
    )
    assert response.status_code == 403
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(username="test-admin", role="admin")
