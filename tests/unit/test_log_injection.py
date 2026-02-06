import pytest
from unittest.mock import MagicMock
from fastapi_autogen_team.main import route_query, Input
from fastapi_autogen_team.tool import async_search
from fastapi import Request, HTTPException


@pytest.mark.asyncio
async def test_log_injection_in_route_query(mocker):
    # Mock logger in main
    # Note: main.py imports logger. We need to patch where it is used.
    # main.py: logger = logging.getLogger(__name__)
    # But log_with_trace uses logger.
    # We can patch 'fastapi_autogen_team.main.logger'
    mock_logger = mocker.patch("fastapi_autogen_team.main.logger")

    # Mock request
    mock_request = MagicMock(spec=Request)
    mock_request.headers.get.return_value = None

    # Input with newline
    # Use a model name that likely exists or doesn't matter for the log call
    model_input = Input(model="internal-gpt", user="evil\nlog", messages=[])

    # Mock service to avoid actual execution
    mocker.patch("fastapi_autogen_team.main.serve_autogen", return_value={"choices": []})

    # Call the function
    # It might raise 404 if model not found, or execute if found.
    # We don't care about the result, only the log call.
    try:
        await route_query(model_input, mock_request)
    except HTTPException:
        pass

    # Check logger calls
    found_newline = False
    # log_with_trace calls logger.info or logger.error depending on level
    # It defaults to info
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
