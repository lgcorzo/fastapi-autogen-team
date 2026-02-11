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


def test_sanitize_log_input_non_string():
    assert sanitize_log_input(123) == "123"


@patch("fastapi_autogen_team.main.log_with_trace")
@patch("fastapi_autogen_team.main.serve_autogen")
@pytest.mark.asyncio
async def test_main_log_sanitization(mock_serve, mock_log):
    mock_serve.return_value = {"status": "ok"}
    inp = Input(model="internal-gpt", messages=[{"role": "user", "content": "hi"}], user="user\nadmin")
    request = MagicMock()
    request.headers.get.return_value = None

    await route_query(inp, request)

    # Check if the log message contains the sanitized user ID
    args, _ = mock_log.call_args
    # Verify that the logged message contains the escaped version
    assert "user\\nadmin" in args[0]


@patch("fastapi_autogen_team.tool.logger")
@patch("fastapi_autogen_team.tool.get_r2r_results")
@patch("fastapi_autogen_team.tool.get_jira_results")
@pytest.mark.asyncio
async def test_tool_log_sanitization(mock_jira, mock_r2r, mock_logger):
    mock_r2r.return_value = "r2r"
    mock_jira.return_value = "jira"

    query = "query\nwith\nnewlines"
    await async_search(query)

    # verify logger.info was called with sanitized query
    found = False
    for call in mock_logger.info.call_args_list:
        if "Ejecutando búsqueda para:" in call[0][0]:
            if "query\\nwith\\nnewlines" in call[0][0]:
                found = True
                break

    assert found, "Logger did not log sanitized query"
