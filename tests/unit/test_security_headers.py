from unittest.mock import patch
from fastapi.testclient import TestClient

# Mock open telemetry and scheduler before importing main
with (
    patch("opentelemetry.exporter.otlp.proto.http.trace_exporter.OTLPSpanExporter"),
    patch("opentelemetry.sdk.trace.export.BatchSpanProcessor"),
    patch("opentelemetry.exporter.otlp.proto.http.metric_exporter.OTLPMetricExporter"),
    patch("opentelemetry.sdk.metrics.export.PeriodicExportingMetricReader"),
    patch("opentelemetry.exporter.otlp.proto.http._log_exporter.OTLPLogExporter"),
    patch("apscheduler.schedulers.background.BackgroundScheduler"),
):
    from fastapi_autogen_team.main import app, BASE_PATH, API_PREFIX

client = TestClient(app)


def test_security_headers_present_on_standard_response():
    # Test a standard endpoint
    response = client.get(f"{API_PREFIX}/models")
    assert response.status_code == 200
    assert "X-Content-Type-Options" in response.headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "X-Frame-Options" in response.headers
    assert response.headers["X-Frame-Options"] == "DENY"


def test_security_headers_present_on_redirect_response():
    # Test a redirect endpoint without following redirects
    response = client.get(BASE_PATH, follow_redirects=False)
    assert response.status_code in (301, 302, 303, 307, 308)
    assert "X-Content-Type-Options" in response.headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "X-Frame-Options" in response.headers
    assert response.headers["X-Frame-Options"] == "DENY"


def test_security_headers_present_on_error_response():
    # Test an error response (e.g., 404 for a non-existent path)
    response = client.get("/non-existent-path-for-testing")
    assert response.status_code == 404
    assert "X-Content-Type-Options" in response.headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "X-Frame-Options" in response.headers
    assert response.headers["X-Frame-Options"] == "DENY"
