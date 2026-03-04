from unittest.mock import patch
from fastapi.testclient import TestClient
from fastapi_autogen_team.main import app


@patch("fastapi_autogen_team.main.log_with_trace")
def test_security_headers(mock_log: any) -> None:
    client = TestClient(app)
    response = client.get("/autogen/api/v1beta/models")
    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
