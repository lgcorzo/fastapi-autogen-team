import pytest
import os
from unittest.mock import patch, MagicMock
from fastapi import Request, HTTPException
from fastapi_autogen_team.data_model import Input
from fastapi_autogen_team.main import route_query, log_with_trace
from fastapi_autogen_team.tool import async_search, get_jira_results
from fastapi_autogen_team.utils import sanitize_log_input


@pytest.mark.asyncio
async def test_log_injection_reproduction():
    # Payload with log injection characters
    malicious_user = "user\n[CRITICAL] User made a mistake"
    model_input = Input(model="internal-gpt", messages=[{"role": "user", "content": "Hello"}], user=malicious_user)

    # Mock Request
    mock_request = MagicMock(spec=Request)
    mock_request.headers = {}

    # Mock dependencies
    with patch("fastapi_autogen_team.main.serve_autogen"):
        with patch("fastapi_autogen_team.main.log_with_trace") as mock_log:
            # Run the function
            await route_query(model_input, mock_request)

            # Check what was logged
            mock_log.assert_called()
            call_args = mock_log.call_args[0][0]

            # Fail if newline is present in the logged message
            assert "\n" not in call_args, f"Log injection vulnerability detected! Logged message: {repr(call_args)}"


def test_sanitize_log_input_normal():
    assert sanitize_log_input("hello") == "hello"


def test_sanitize_log_input_newlines():
    assert sanitize_log_input("hello\nworld") == "hello\\nworld"


def test_sanitize_log_input_carriage_returns():
    assert sanitize_log_input("hello\rworld") == "hello\\rworld"


def test_sanitize_log_input_mixed():
    assert sanitize_log_input("hello\r\nworld") == "hello\\r\\nworld"


def test_sanitize_log_input_none():
    assert sanitize_log_input(None) == ""


def test_sanitize_log_input_empty():
    assert sanitize_log_input("") == ""
