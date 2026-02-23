import pytest
from unittest.mock import MagicMock, patch
from fastapi import Request
from fastapi_autogen_team.data_model import Input
from fastapi_autogen_team.main import route_query


@pytest.mark.asyncio
async def test_header_injection_vulnerability():
    """
    Test that the application sanitizes the x-openwebui-user-id header
    before using it in the application logic.
    """
    # Malicious header with CRLF injection
    malicious_header = "user\r\nInjected-Header: malicious"

    # Input object
    model_input = Input(model="internal-gpt", messages=[{"role": "user", "content": "Hello"}], user="original_user")

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

        # Check if the user field in the input contains the CRLF characters
        # It MUST NOT contain \r or \n
        assert (
            "\r" not in called_input.user and "\n" not in called_input.user
        ), f"Vulnerability detected: serve_autogen received unsanitized user input: {repr(called_input.user)}"
