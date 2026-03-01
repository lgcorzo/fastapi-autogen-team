import pytest
from fastapi.testclient import TestClient
from fastapi_autogen_team.main import app
from unittest.mock import patch

@pytest.fixture
def client():
    # Mock otel setup
    with patch("fastapi_autogen_team.main.otlp_exporter"), \
         patch("fastapi_autogen_team.main.span_processor"), \
         patch("fastapi_autogen_team.main.otlp_metric_exporter"), \
         patch("fastapi_autogen_team.main.metric_reader"), \
         patch("fastapi_autogen_team.main.otlp_log_exporter"):
        yield TestClient(app)

def test_security_headers(client):
    response = client.get("/autogen/api/v1beta/models")
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
