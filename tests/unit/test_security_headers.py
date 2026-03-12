import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from fastapi_autogen_team.main import app


@pytest.fixture
def test_client():
    """Fixture providing a TestClient configured properly for middleware testing."""
    # We must mock OpenTelemetry exports/setup that might cause errors
    with (
        patch("fastapi_autogen_team.main.log_with_trace"),
        patch("fastapi_autogen_team.main.BackgroundScheduler"),
        patch("fastapi_autogen_team.main.FastAPIInstrumentor.instrument_app"),
    ):
        with TestClient(app) as client:
            yield client


def test_security_headers_on_success(test_client):
    """Test that security headers are added to successful responses."""
    response = test_client.get("/autogen/api/v1beta/models")

    assert response.status_code == 200
    assert "X-Content-Type-Options" in response.headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"

    assert "X-Frame-Options" in response.headers
    assert response.headers["X-Frame-Options"] == "DENY"


def test_security_headers_on_error(test_client):
    """Test that security headers are added even to error responses."""
    # This route shouldn't exist
    response = test_client.get("/non_existent_route")

    assert response.status_code == 404
    assert "X-Content-Type-Options" in response.headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"

    assert "X-Frame-Options" in response.headers
    assert response.headers["X-Frame-Options"] == "DENY"


def test_security_headers_on_redirect(test_client):
    """Test that security headers are added to redirect responses."""
    response = test_client.get("/autogen", follow_redirects=False)

    assert response.status_code == 307
    assert "X-Content-Type-Options" in response.headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"

    assert "X-Frame-Options" in response.headers
    assert response.headers["X-Frame-Options"] == "DENY"
