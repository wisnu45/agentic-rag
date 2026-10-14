from fastapi.testclient import TestClient

import main


client = TestClient(main.app)


def test_liveness_endpoint_does_not_require_database():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_readiness_endpoint_returns_ready_when_database_is_available(monkeypatch):
    monkeypatch.setattr(main, "check_database_connection", lambda: True)
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready", "database": "connected"}


def test_readiness_endpoint_returns_503_when_database_is_unavailable(monkeypatch):
    def fail_connection():
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(main, "check_database_connection", fail_connection)
    response = client.get("/health/ready")
    assert response.status_code == 503
    assert response.json()["detail"] == "Database is not available"
