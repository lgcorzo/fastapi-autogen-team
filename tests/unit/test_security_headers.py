from fastapi.testclient import TestClient
from unittest.mock import patch

from fastapi_autogen_team.main import app

# Mock OpenTelemetry setup for tests to avoid ConnectionError
with (
    patch("fastapi_autogen_team.main.FastAPIInstrumentor.instrument_app"),
    patch("fastapi_autogen_team.main.trace"),
    patch("fastapi_autogen_team.main.metrics"),
    patch("fastapi_autogen_team.main.set_logger_provider"),
):
    client = TestClient(app)


def test_security_headers_present_on_api_route():
    """Test that X-Content-Type-Options and X-Frame-Options are present on normal routes."""
    # We use a mocked route to avoid triggering other logic
    response = client.get("/autogen/api/v1beta/models")

    assert "X-Content-Type-Options" in response.headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"

    assert "X-Frame-Options" in response.headers
    assert response.headers["X-Frame-Options"] == "DENY"


def test_security_headers_present_on_redirect_route():
    """Test that security headers are present even on redirects."""
    response = client.get("/autogen", follow_redirects=False)

    # Check that it's a redirect
    assert response.status_code in (301, 302, 303, 307, 308)

    assert "X-Content-Type-Options" in response.headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"

    assert "X-Frame-Options" in response.headers
    assert response.headers["X-Frame-Options"] == "DENY"


def test_security_headers_present_on_404():
    """Test that security headers are present on error responses (like 404)."""
    response = client.get("/autogen/api/v1beta/non-existent-route")

    assert response.status_code == 404

    assert "X-Content-Type-Options" in response.headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"

    assert "X-Frame-Options" in response.headers
    assert response.headers["X-Frame-Options"] == "DENY"
