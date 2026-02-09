import pytest
from unittest.mock import patch, MagicMock
from fastapi_autogen_team.data_model import Input
from fastapi_autogen_team.main import route_query
from fastapi import Request

@pytest.mark.asyncio
async def test_log_injection_reproduction():
    # Payload with log injection characters
    malicious_user = "user\n[CRITICAL] User made a mistake"
    model_input = Input(
        model="internal-gpt",
        messages=[{"role": "user", "content": "Hello"}],
        user=malicious_user
    )

    # Mock Request
    mock_request = MagicMock(spec=Request)
    mock_request.headers = {}

    # Mock dependencies
    with patch("fastapi_autogen_team.main.serve_autogen") as mock_serve:
        with patch("fastapi_autogen_team.main.logger") as mock_logger:
            # Run the function
            await route_query(model_input, mock_request)

            # Check what was logged
            mock_logger.info.assert_called()
            call_args = mock_logger.info.call_args[0][0]

            # Fail if newline is present in the logged message
            assert "\n" not in call_args, f"Log injection vulnerability detected! Logged message: {repr(call_args)}"
