import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from fastapi_autogen_team.main import app


# Mock OpenTelemetry to prevent connection errors
@pytest.fixture(autouse=True)
def mock_otel():
    with (
        patch("fastapi_autogen_team.main.OTLPMetricExporter"),
        patch("fastapi_autogen_team.main.OTLPSpanExporter"),
        patch("fastapi_autogen_team.main.OTLPLogExporter"),
    ):
        yield


client = TestClient(app)


def test_security_headers():
    response = client.get("/autogen/api/v1beta/models")
    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"


def test_security_headers_on_error():
    # Trigger 404 error
    response = client.get("/autogen/api/v1beta/not_found")
    assert response.status_code == 404
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
