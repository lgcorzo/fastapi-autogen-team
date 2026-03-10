from unittest.mock import patch
from fastapi.testclient import TestClient

from fastapi_autogen_team.main import app

# Mocking OpenTelemetry setup components to bypass remote calls during testing
with (
    patch("fastapi_autogen_team.main.OTLPMetricExporter"),
    patch("fastapi_autogen_team.main.OTLPSpanExporter"),
    patch("fastapi_autogen_team.main.OTLPLogExporter"),
    patch("fastapi_autogen_team.main.logger_tracer"),
):
    client = TestClient(app)


def test_security_headers_on_docs_redirect():
    """Test that security headers are present even on a redirect route."""
    # follow_redirects=False allows us to inspect the initial 307 response
    response = client.get("/autogen", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"


def test_security_headers_on_models_endpoint():
    """Test that security headers are present on a standard JSON route."""
    response = client.get("/autogen/api/v1beta/models")

    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"


@patch("fastapi_autogen_team.main.serve_autogen")
def test_security_headers_on_chat_completions(mock_serve_autogen):
    """Test that security headers are present on a POST route."""
    # Setup the mock to return a simple dict response
    mock_serve_autogen.return_value = {"status": "success"}

    payload = {
        "model": "internal-gpt",
        "messages": [{"role": "user", "content": "Hello"}],
        "user": "test_user",
    }
    response = client.post("/autogen/api/v1beta/chat/completions", json=payload)

    # Note: Depending on routing logic, if model isn't "internal-gpt", it might return 404,
    # which also should have the security headers.
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"


def test_security_headers_on_404():
    """Test that security headers are present on errors."""
    response = client.get("/non-existent-route")
    assert response.status_code == 404
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
