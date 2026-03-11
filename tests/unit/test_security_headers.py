import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

# Mock the OpenTelemetry exporters before importing the app
with (
    patch("fastapi_autogen_team.main.OTLPSpanExporter"),
    patch("fastapi_autogen_team.main.OTLPMetricExporter"),
    patch("fastapi_autogen_team.main.OTLPLogExporter"),
    patch("fastapi_autogen_team.main.BatchSpanProcessor"),
    patch("fastapi_autogen_team.main.PeriodicExportingMetricReader"),
    patch("fastapi_autogen_team.main.BatchLogRecordProcessor"),
):
    from fastapi_autogen_team.main import app


@pytest.fixture
def client():
    # Use TestClient with raise_server_exceptions=False if needed
    return TestClient(app)


def test_security_headers_on_regular_endpoint(client):
    """Test that security headers are added to a standard JSON response."""
    response = client.get("/autogen/api/v1beta/models")
    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"


def test_security_headers_on_redirect(client):
    """Test that security headers are added to a redirect response."""
    # use follow_redirects=False to inspect the 307 response
    response = client.get("/autogen", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"


def test_security_headers_on_error_response(client):
    """Test that security headers are added to an error response (e.g., 404)."""
    response = client.get("/autogen/api/v1beta/non-existent-endpoint")
    assert response.status_code == 404
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
