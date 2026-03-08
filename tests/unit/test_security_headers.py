from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

from fastapi_autogen_team.main import app

# Mock dependencies properly for TestClient
@pytest.fixture
def mock_telemetry():
    with patch("fastapi_autogen_team.main.log_with_trace"), \
         patch("fastapi_autogen_team.main.otlp_exporter"), \
         patch("fastapi_autogen_team.main.otlp_metric_exporter"), \
         patch("fastapi_autogen_team.main.otlp_log_exporter"), \
         patch("fastapi_autogen_team.main.BatchSpanProcessor"), \
         patch("fastapi_autogen_team.main.PeriodicExportingMetricReader"), \
         patch("fastapi_autogen_team.main.BatchLogRecordProcessor"):
        yield

@pytest.fixture
def client(mock_telemetry):
    return TestClient(app)

def test_security_headers_on_success(client):
    response = client.get("/autogen/api/v1beta/models")
    assert response.status_code == 200
    assert "X-Content-Type-Options" in response.headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "X-Frame-Options" in response.headers
    assert response.headers["X-Frame-Options"] == "DENY"

def test_security_headers_on_redirect(client):
    # Test the redirect endpoint directly, follow_redirects=False is important here
    response = client.get("/autogen", follow_redirects=False)
    assert response.status_code == 307
    assert "X-Content-Type-Options" in response.headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "X-Frame-Options" in response.headers
    assert response.headers["X-Frame-Options"] == "DENY"

def test_security_headers_on_error(client):
    # We trigger a 404 error
    response = client.get("/autogen/api/v1beta/nonexistent")
    assert response.status_code == 404
    assert "X-Content-Type-Options" in response.headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "X-Frame-Options" in response.headers
    assert response.headers["X-Frame-Options"] == "DENY"
