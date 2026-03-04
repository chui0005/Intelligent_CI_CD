import os

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_run_rejects_disallowed_command() -> None:
    os.environ["APP_API_KEY"] = "test-key"
    response = client.post(
        "/run",
        headers={"X-API-Key": "test-key"},
        json={"cmd": "cat /etc/passwd"},
    )
    assert response.status_code == 422
