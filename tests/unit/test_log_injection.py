import pytest
from unittest.mock import patch, MagicMock
from fastapi import Request, HTTPException
from fastapi_autogen_team.data_model import Input
from fastapi_autogen_team.main import route_query
from fastapi_autogen_team.tool import async_search
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


def test_sanitize_log_input_ansi_escape():
    # \x1b is ESC, used in ANSI escape codes
    assert sanitize_log_input("hello\x1b[2Kworld") == "hello[2Kworld"


def test_sanitize_log_input_null_byte():
    assert sanitize_log_input("hello\x00world") == "helloworld"


def test_sanitize_log_input_mixed_control_chars():
    assert sanitize_log_input("hello\x07\x0b\x0cworld") == "helloworld"


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


@pytest.mark.asyncio
async def test_log_injection_in_route_query(mocker):
    # Mock logger in main
    mock_logger = mocker.patch("fastapi_autogen_team.main.logger")

    # Mock request
    mock_request = MagicMock(spec=Request)
    mock_request.headers.get.return_value = None

    # Input with newline
    model_input = Input(model="internal-gpt", user="evil\nlog", messages=[])

    # Mock service to avoid actual execution
    mocker.patch("fastapi_autogen_team.main.serve_autogen", return_value={"choices": []})

    # Call the function
    try:
        await route_query(model_input, mock_request)
    except HTTPException:
        pass

    # Check logger calls
    found_newline = False
    for call in mock_logger.info.call_args_list:
        if "\n" in call[0][0]:
            found_newline = True
            break

    assert not found_newline, "Log message contains a newline character (Log Injection Vulnerability)"


@pytest.mark.asyncio
async def test_log_injection_in_tool_search(mocker):
    # Mock logger in tool
    mock_logger = mocker.patch("fastapi_autogen_team.tool.logger")

    # Mock search functions to avoid external calls
    mocker.patch("fastapi_autogen_team.tool.safe_get_r2r_results", return_value="foo")
    mocker.patch("fastapi_autogen_team.tool.safe_get_jira_results", return_value="bar")

    await async_search("evil\nquery")

    found_newline = False
    for call in mock_logger.info.call_args_list:
        if "\n" in call[0][0]:
            found_newline = True
            break

    assert not found_newline, "Log message in tool contains a newline character (Log Injection Vulnerability)"
