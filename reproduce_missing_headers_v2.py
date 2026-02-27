
from fastapi.testclient import TestClient
from fastapi_autogen_team.main import app
from unittest.mock import patch

# Mock opentelemetry to avoid connection errors during testing
with patch('opentelemetry.exporter.otlp.proto.http.metric_exporter.OTLPMetricExporter.export'), \
     patch('opentelemetry.exporter.otlp.proto.http.trace_exporter.OTLPSpanExporter.export'), \
     patch('opentelemetry.exporter.otlp.proto.http._log_exporter.OTLPLogExporter.export'):

    client = TestClient(app)

    def test_security_headers_missing():
        response = client.get("/autogen/api/v1beta/models")
        print("\nHeaders found:", response.headers)

        assert "x-content-type-options" not in response.headers
        assert "x-frame-options" not in response.headers
        print("\nSUCCESS: Security headers are currently MISSING as expected.")

    if __name__ == "__main__":
        try:
            test_security_headers_missing()
        except AssertionError as e:
            print(f"\nFAILURE: {e}")
        except Exception as e:
            print(f"\nERROR: {e}")
