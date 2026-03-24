import os
from unittest.mock import patch
from fastapi.testclient import TestClient


def get_test_client_with_origins(origins_str: str):
    """
    Helper to create a TestClient with a specific ALLOWED_ORIGINS setting.
    We import main inside so that the module is re-evaluated with the patched
    environment variable.
    """
    with patch.dict(os.environ, {"ALLOWED_ORIGINS": origins_str}, clear=True):
        # We need to reload the module to trigger the middleware addition logic
        import sys

        if "fastapi_autogen_team.main" in sys.modules:
            del sys.modules["fastapi_autogen_team.main"]

        # Mock opentelemetry to avoid connection errors during testing
        with (
            patch("opentelemetry.exporter.otlp.proto.http.metric_exporter.OTLPMetricExporter.export"),
            patch("opentelemetry.exporter.otlp.proto.http.trace_exporter.OTLPSpanExporter.export"),
            patch("opentelemetry.exporter.otlp.proto.http._log_exporter.OTLPLogExporter.export"),
            patch("apscheduler.schedulers.background.BackgroundScheduler.start"),
            patch("fastapi_autogen_team.main.FastAPIInstrumentor.instrument_app"),
        ):
            from fastapi_autogen_team.main import app

            return TestClient(app)


def test_cors_empty_origins():
    """Test that when ALLOWED_ORIGINS is empty, the CORS middleware is NOT added."""
    client = get_test_client_with_origins("")
    response = client.options(
        "/autogen/api/v1beta/models", headers={"Origin": "https://evil.com", "Access-Control-Request-Method": "GET"}
    )

    # Without CORS middleware, the pre-flight request will not have CORS headers
    assert "access-control-allow-origin" not in response.headers


def test_cors_specific_origins():
    """Test that when ALLOWED_ORIGINS has specific values, CORS middleware is active."""
    client = get_test_client_with_origins("https://good.com, https://another.com ")

    # Try with a good origin
    response_good = client.options(
        "/autogen/api/v1beta/models", headers={"Origin": "https://good.com", "Access-Control-Request-Method": "GET"}
    )

    # 200 OK because the CORS middleware handles the OPTIONS request
    assert response_good.status_code == 200
    assert response_good.headers.get("access-control-allow-origin") == "https://good.com"

    # Try with a bad origin
    response_bad = client.options(
        "/autogen/api/v1beta/models", headers={"Origin": "https://evil.com", "Access-Control-Request-Method": "GET"}
    )

    # 400 Bad Request because the origin is not allowed
    assert response_bad.status_code == 400
