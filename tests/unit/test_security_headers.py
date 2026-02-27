
from fastapi.testclient import TestClient
from fastapi_autogen_team.main import app
from unittest.mock import patch

# Mock opentelemetry to avoid connection errors during testing
with patch('opentelemetry.exporter.otlp.proto.http.metric_exporter.OTLPMetricExporter.export'), \
     patch('opentelemetry.exporter.otlp.proto.http.trace_exporter.OTLPSpanExporter.export'), \
     patch('opentelemetry.exporter.otlp.proto.http._log_exporter.OTLPLogExporter.export'):

    client = TestClient(app)

    def test_security_headers_present():
        """Test that security headers are present in the response."""
        response = client.get("/autogen/api/v1beta/models")

        # Check for X-Content-Type-Options
        assert "x-content-type-options" in response.headers
        assert response.headers["x-content-type-options"] == "nosniff"

        # Check for X-Frame-Options
        assert "x-frame-options" in response.headers
        assert response.headers["x-frame-options"] == "DENY"
