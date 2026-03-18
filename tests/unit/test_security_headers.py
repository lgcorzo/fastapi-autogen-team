from fastapi.testclient import TestClient
from fastapi_autogen_team.main import app
import pytest
from unittest.mock import patch


@pytest.fixture(autouse=True)
def mock_telemetry():
    with (
        patch("fastapi_autogen_team.main.FastAPIInstrumentor.instrument_app"),
        patch("fastapi_autogen_team.main.BackgroundScheduler"),
    ):
        yield


client = TestClient(app)


def test_security_headers_present():
    response = client.get("/autogen/api/v1beta/models")
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
