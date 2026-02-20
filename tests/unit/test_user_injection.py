import pytest
from unittest.mock import patch, MagicMock
from fastapi import Request
from fastapi_autogen_team.data_model import Input
from fastapi_autogen_team.main import route_query


@pytest.mark.asyncio
async def test_user_injection_passed_to_service():
    # Payload with injection characters
    malicious_user = "user\n[CRITICAL] User made a mistake"
    model_input = Input(model="internal-gpt", messages=[{"role": "user", "content": "Hello"}], user=malicious_user)

    # Mock Request
    mock_request = MagicMock(spec=Request)
    mock_request.headers = {}

    # Mock dependencies
    with patch("fastapi_autogen_team.main.serve_autogen") as mock_service:
        with patch("fastapi_autogen_team.main.log_with_trace"):
            # Run the function
            await route_query(model_input, mock_request)

            # Check what was passed to service
            mock_service.assert_called_once()
            called_input = mock_service.call_args[0][0]

            # If the newline is still there, it's vulnerable to downstream injection
            # because serve_autogen uses this user ID in headers/tags
            assert (
                "\n" not in called_input.user
            ), f"User ID passed to service contains newlines: {repr(called_input.user)}"
            assert called_input.user == "user\\n[CRITICAL] User made a mistake"
