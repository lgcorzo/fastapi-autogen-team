import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from fastapi_autogen_team.main import app


@pytest.fixture
def client():
    # Mock OPENTELEMETRY endpoints to avoid connection errors during testing
    with (
        patch("fastapi_autogen_team.main.OTLPMetricExporter"),
        patch("fastapi_autogen_team.main.OTLPSpanExporter"),
        patch("fastapi_autogen_team.main.OTLPLogExporter"),
    ):
        with TestClient(app) as c:
            yield c


def test_security_headers_present(client):
    """Test that all API responses include the required security headers."""
    response = client.get("/autogen/api/v1beta/models")

    assert response.status_code == 200
    assert "X-Content-Type-Options" in response.headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "X-Frame-Options" in response.headers
    assert response.headers["X-Frame-Options"] == "DENY"


def test_security_headers_on_error(client):
    """Test that security headers are also present on error responses (like 404)."""
    response = client.get("/autogen/api/v1beta/nonexistent")

    assert response.status_code == 404
    assert "X-Content-Type-Options" in response.headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "X-Frame-Options" in response.headers
    assert response.headers["X-Frame-Options"] == "DENY"
