from fastapi.testclient import TestClient
from fastapi_autogen_team.main import app
from unittest.mock import patch

# Mock opentelemetry to avoid connection errors during testing
with (
    patch("opentelemetry.exporter.otlp.proto.http.metric_exporter.OTLPMetricExporter.export"),
    patch("opentelemetry.exporter.otlp.proto.http.trace_exporter.OTLPSpanExporter.export"),
    patch("opentelemetry.exporter.otlp.proto.http._log_exporter.OTLPLogExporter.export"),
):
    client = TestClient(app)

    def test_security_headers_present() -> None:
        """Test that security headers are present in the response."""
        response = client.get("/autogen/api/v1beta/models")

        # Check for X-Content-Type-Options
        assert "x-content-type-options" in response.headers
        assert response.headers["x-content-type-options"] == "nosniff"

        # Check for X-Frame-Options
        assert "x-frame-options" in response.headers
        assert response.headers["x-frame-options"] == "DENY"

        # Check for Strict-Transport-Security
        assert "strict-transport-security" in response.headers
        assert response.headers["strict-transport-security"] == "max-age=31536000; includeSubDomains"

        # Check for Referrer-Policy
        assert "referrer-policy" in response.headers
        assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"

        # Check for Content-Security-Policy
        assert "content-security-policy" in response.headers
        assert (
            response.headers["content-security-policy"]
            == "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; img-src 'self' data: https://fastapi.tiangolo.com;"
        )
