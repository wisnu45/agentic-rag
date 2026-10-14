from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


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
