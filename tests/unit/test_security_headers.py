import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from fastapi_autogen_team.main import app


# Mock OpenTelemetry setup to prevent ConnectionErrors during tests
@patch("opentelemetry.sdk.trace.export.BatchSpanProcessor")
@patch("opentelemetry.sdk.metrics.export.PeriodicExportingMetricReader")
@patch("opentelemetry.sdk._logs.export.BatchLogRecordProcessor")
def test_security_headers(mock_log, mock_metric, mock_span):
    client = TestClient(app)

    # Test a regular endpoint
    response = client.get("/autogen/api/v1beta/models")
    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"

    # Test an error response (should still have headers)
    response = client.get("/nonexistent")
    assert response.status_code == 404
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"

    # Test a redirect endpoint (should follow redirects is False to test the redirect itself)
    response = client.get("/autogen", follow_redirects=False)
    assert response.status_code in (301, 302, 303, 307, 308)
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
