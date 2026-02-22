import pytest
from unittest.mock import MagicMock, patch
from fastapi import Request
from fastapi_autogen_team.data_model import Input
from fastapi_autogen_team.main import route_query


@pytest.mark.asyncio
async def test_header_injection_prevention():
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
        # The test PASSES if CRLF are ABSENT (meaning it WAS sanitized)
        # Or if they are escaped (i.e. present as literals but not control chars)

        # We expect "user\r\nInjected..." to become "user\\r\\nInjected..."
        sanitized_header = "user\\r\\nInjected-Header: malicious"

        assert (
            called_input.user == sanitized_header
        ), f"Vulnerability exists: serve_autogen received unsanitized user input: {repr(called_input.user)}"

        print(f"\n[SAFE] serve_autogen received sanitized user: {repr(called_input.user)}")
