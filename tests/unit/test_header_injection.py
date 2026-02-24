import pytest
from unittest.mock import MagicMock, patch
from fastapi import Request
from fastapi_autogen_team.data_model import Input
from fastapi_autogen_team.main import route_query

@pytest.mark.asyncio
async def test_header_injection_sanitization():
    """
    Test that the x-openwebui-user-id header is sanitized before being used.
    This prevents CRLF injection vulnerabilities where a malicious user ID
    could inject headers or manipulate logs/requests downstream.
    """
    # Malicious header with CRLF injection
    malicious_header = "user\r\nInjected-Header: malicious"

    # Input object
    model_input = Input(
        model="internal-gpt",
        messages=[{"role": "user", "content": "Hello"}],
        user="original_user"
    )

    # Mock Request with the malicious header
    mock_request = MagicMock(spec=Request)
    mock_request.headers.get.return_value = malicious_header

    # Mock serve_autogen to capture the input it receives
    with patch("fastapi_autogen_team.main.serve_autogen") as mock_service:
        mock_service.return_value = {"choices": []}

        # Call the route handler
        await route_query(model_input, mock_request)

        # Get the argument passed to serve_autogen
        called_input = mock_service.call_args[0][0]

        # Verify that CRLF characters are escaped
        assert "\r" not in called_input.user
        assert "\n" not in called_input.user
        assert "\\r" in called_input.user
        assert "\\n" in called_input.user
        assert called_input.user == "user\\r\\nInjected-Header: malicious"

@pytest.mark.asyncio
async def test_normal_header_user_id():
    """Test that a normal user ID from header is correctly assigned."""
    header_user = "safe_user_123"

    model_input = Input(
        model="internal-gpt",
        messages=[{"role": "user", "content": "Hello"}],
        user="original_user"
    )

    mock_request = MagicMock(spec=Request)
    mock_request.headers.get.return_value = header_user

    with patch("fastapi_autogen_team.main.serve_autogen") as mock_service:
        mock_service.return_value = {"choices": []}

        await route_query(model_input, mock_request)

        called_input = mock_service.call_args[0][0]
        assert called_input.user == "safe_user_123"
