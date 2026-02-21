import pytest
from unittest.mock import MagicMock, patch
from fastapi import Request
from fastapi_autogen_team.data_model import Input
from fastapi_autogen_team.main import route_query


@pytest.mark.asyncio
async def test_header_crlf_injection():
    # Setup
    malicious_user_id = "attacker\r\nExploit: true"
    mock_request = MagicMock(spec=Request)
    mock_request.headers = {"x-openwebui-user-id": malicious_user_id}

    model_input = Input(model="internal-gpt", messages=[{"role": "user", "content": "Hello"}], user="normal_user")

    # Mock serve_autogen to capture the input
    with patch("fastapi_autogen_team.main.serve_autogen") as mock_serve:
        mock_serve.return_value = {"status": "ok"}

        # Action
        await route_query(model_input, mock_request)

        # Assertion
        # Check the user field in the Input object passed to serve_autogen
        called_input = mock_serve.call_args[0][0]

        # The user field should now be sanitized (newlines escaped)
        expected_sanitized_user = "attacker\\r\\nExploit: true"
        assert called_input.user == expected_sanitized_user
