from fastapi.testclient import TestClient

from app.main import app
from app.security import DEFAULT_DEMO_KEY

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_run_rejects_disallowed_command() -> None:
    response = client.post(
        "/run",
        headers={"X-API-Key": DEFAULT_DEMO_KEY},
        json={"cmd": "cat /etc/passwd"},
    )
    assert response.status_code == 422
