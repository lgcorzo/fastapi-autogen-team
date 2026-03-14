import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from fastapi_autogen_team.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def mock_telemetry():
    with patch("fastapi_autogen_team.main.log_with_trace"):
        yield


def test_security_headers():
    response = client.get("/autogen/api/v1beta/models")
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
