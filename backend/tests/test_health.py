"""Basic smoke tests for API gateway."""
from fastapi.testclient import TestClient

from apps.api_gateway.main import app


def test_root() -> None:
    """Ensure root endpoint responds."""

    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "CampuSwap API Gateway"
