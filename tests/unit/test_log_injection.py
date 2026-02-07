import pytest
from unittest.mock import patch, MagicMock
from fastapi_autogen_team.utils import sanitize_log_input
from fastapi_autogen_team.main import route_query
from fastapi_autogen_team.data_model import Input
from fastapi_autogen_team.tool import async_search


def test_sanitize_log_input():
    assert sanitize_log_input("hello") == "hello"
    assert sanitize_log_input("hello\nworld") == "hello\\nworld"
    assert sanitize_log_input("hello\rworld") == "hello\\rworld"
    assert sanitize_log_input("hello\r\nworld") == "hello\\r\\nworld"
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
