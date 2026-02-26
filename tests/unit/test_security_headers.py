from fastapi.testclient import TestClient
from fastapi_autogen_team.main import app

client = TestClient(app)

def test_security_headers_presence():
    """Test that security headers are present in the response."""
    response = client.get("/autogen/api/v1beta/models")
    assert response.status_code == 200

    # Check for X-Content-Type-Options
    assert "X-Content-Type-Options" in response.headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"

    # Check for X-Frame-Options
    assert "X-Frame-Options" in response.headers
    assert response.headers["X-Frame-Options"] == "DENY"

def test_security_headers_on_error():
    """Test that security headers are present even on 404 responses."""
    response = client.get("/autogen/api/v1beta/non-existent-route")
    assert response.status_code == 404

    assert "X-Content-Type-Options" in response.headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"

    assert "X-Frame-Options" in response.headers
    assert response.headers["X-Frame-Options"] == "DENY"
