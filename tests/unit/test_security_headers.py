from unittest.mock import patch
from fastapi.testclient import TestClient

# Mock opentelemetry exporters BEFORE importing the app
with (
    patch("opentelemetry.exporter.otlp.proto.http.trace_exporter.OTLPSpanExporter"),
    patch("opentelemetry.exporter.otlp.proto.http.metric_exporter.OTLPMetricExporter"),
    patch("opentelemetry.exporter.otlp.proto.http._log_exporter.OTLPLogExporter"),
    patch("fastapi_autogen_team.main.FastAPIInstrumentor.instrument_app"),
    patch("fastapi_autogen_team.main.BackgroundScheduler"),
):
    from fastapi_autogen_team.main import app

client = TestClient(app)


def test_security_headers_present_on_docs_redirect():
    response = client.get("/autogen", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"


def test_security_headers_present_on_models_endpoint():
    response = client.get("/autogen/api/v1beta/models")
    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"


def test_security_headers_present_on_404():
    response = client.get("/autogen/non_existent_route")
    assert response.status_code == 404
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
