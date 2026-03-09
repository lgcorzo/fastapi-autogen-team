import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from fastapi_autogen_team.main import app, BASE_PATH, API_PREFIX


@pytest.fixture
def client():
    # Mock OpenTelemetry stuff so it doesn't fail connecting to the collector
    with (
        patch("fastapi_autogen_team.main.otlp_exporter"),
        patch("fastapi_autogen_team.main.span_processor"),
        patch("fastapi_autogen_team.main.otlp_metric_exporter"),
        patch("fastapi_autogen_team.main.metric_reader"),
        patch("fastapi_autogen_team.main.otlp_log_exporter"),
    ):
        yield TestClient(app)


def test_security_headers_on_redirect(client: TestClient):
    """Test that security headers are present on a redirect endpoint."""
    response = client.get(BASE_PATH, follow_redirects=False)

    # It should be a redirect
    assert response.status_code == 307

    # Check for security headers
    assert "X-Content-Type-Options" in response.headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "X-Frame-Options" in response.headers
    assert response.headers["X-Frame-Options"] == "DENY"


def test_security_headers_on_standard_endpoint(client: TestClient):
    """Test that security headers are present on a standard endpoint."""
    response = client.get(API_PREFIX + "/models")

    # It should be a success
    assert response.status_code == 200

    # Check for security headers
    assert "X-Content-Type-Options" in response.headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "X-Frame-Options" in response.headers
    assert response.headers["X-Frame-Options"] == "DENY"


def test_security_headers_on_error_endpoint(client: TestClient):
    """Test that security headers are present even on an error endpoint (e.g. 404)."""
    response = client.get("/non-existent-endpoint")

    # It should be a 404
    assert response.status_code == 404

    # Check for security headers
    assert "X-Content-Type-Options" in response.headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "X-Frame-Options" in response.headers
    assert response.headers["X-Frame-Options"] == "DENY"
