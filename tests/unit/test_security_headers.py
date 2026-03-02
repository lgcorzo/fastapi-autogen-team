from fastapi.testclient import TestClient
from unittest.mock import patch

# Mock out OpenTelemetry setup completely before importing main to avoid connection errors
with (
    patch("opentelemetry.exporter.otlp.proto.http.trace_exporter.OTLPSpanExporter"),
    patch("opentelemetry.sdk.trace.export.BatchSpanProcessor"),
    patch("opentelemetry.exporter.otlp.proto.http.metric_exporter.OTLPMetricExporter"),
    patch("opentelemetry.sdk.metrics.export.PeriodicExportingMetricReader"),
    patch("opentelemetry.exporter.otlp.proto.http._log_exporter.OTLPLogExporter"),
    patch("opentelemetry.sdk._logs.export.BatchLogRecordProcessor"),
    patch("opentelemetry.instrumentation.fastapi.FastAPIInstrumentor.instrument_app"),
):
    from src.fastapi_autogen_team.main import app

client = TestClient(app)


def test_security_headers_present():
    """
    Tests that the security headers X-Content-Type-Options and X-Frame-Options
    are properly added to responses by the middleware.
    """
    response = client.get("/autogen/api/v1beta/docs")

    assert "X-Content-Type-Options" in response.headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"

    assert "X-Frame-Options" in response.headers
    assert response.headers["X-Frame-Options"] == "DENY"
