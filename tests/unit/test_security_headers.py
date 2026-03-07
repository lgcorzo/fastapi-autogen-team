import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from fastapi_autogen_team.main import app


@pytest.fixture
def client():
    # Mock OpenTelemetry exporters to prevent connection errors during tests
    with (
        patch("fastapi_autogen_team.main.OTLPSpanExporter"),
        patch("fastapi_autogen_team.main.OTLPMetricExporter"),
        patch("fastapi_autogen_team.main.OTLPLogExporter"),
    ):
        yield TestClient(app)


def test_security_headers_present(client):
    """Test that security headers are added to responses."""
    # Using the docs redirect endpoint which is a simple GET request
    response = client.get("/autogen", follow_redirects=False)

    # Assert headers are present
    assert "X-Content-Type-Options" in response.headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"

    assert "X-Frame-Options" in response.headers
    assert response.headers["X-Frame-Options"] == "DENY"


def test_security_headers_on_api_endpoint(client):
    """Test that security headers are added to API endpoints."""
    # Assuming get_models is a valid endpoint
    response = client.get("/autogen/api/v1beta/models")

    # Assert headers are present
    assert "X-Content-Type-Options" in response.headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"

    assert "X-Frame-Options" in response.headers
    assert response.headers["X-Frame-Options"] == "DENY"


def test_security_headers_on_error_response(client):
    """Test that security headers are present even on error responses."""
    # Testing an endpoint that doesn't exist
    response = client.get("/autogen/api/v1beta/nonexistent")

    assert response.status_code == 404

    # Assert headers are present
    assert "X-Content-Type-Options" in response.headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"

    assert "X-Frame-Options" in response.headers
    assert response.headers["X-Frame-Options"] == "DENY"
