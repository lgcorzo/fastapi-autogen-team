import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from fastapi_autogen_team.main import app, API_PREFIX

client = TestClient(app)


@pytest.fixture(autouse=True)
def mock_otel():
    with (
        patch("fastapi_autogen_team.main.log_with_trace"),
        patch("fastapi_autogen_team.main.logger_tracer"),
        patch("fastapi_autogen_team.main.meter"),
    ):
        yield


def test_security_headers_present():
    response = client.get(API_PREFIX + "/models")
    assert response.status_code == 200
    assert "X-Content-Type-Options" in response.headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "X-Frame-Options" in response.headers
    assert response.headers["X-Frame-Options"] == "DENY"
