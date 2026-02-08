
import pytest
import asyncio
from unittest.mock import patch, MagicMock, call
import os

from fastapi_autogen_team.utils import sanitize_log_input
# Need to mock environment variables before importing modules that use them at module level?
# main.py calls load_dotenv() and os.getenv() at module level.
# But since we are testing functions, it should be fine as long as we patch what we need.

from fastapi import HTTPException
from fastapi_autogen_team.data_model import Input, Message
from fastapi_autogen_team.main import route_query
from fastapi_autogen_team.tool import async_search, get_jira_results

def test_sanitize_log_input():
    assert sanitize_log_input("normal input") == "normal input"
    assert sanitize_log_input("input\nwith\nnewline") == "input\\nwith\\nnewline"
    assert sanitize_log_input("input\rwith\rcarriage return") == "input\\rwith\\rcarriage return"
    assert sanitize_log_input("input\r\nwith\r\nboth") == "input\\r\\nwith\\r\\nboth"
    assert sanitize_log_input("") == ""
    # If None is passed, typeshed says str, but runtime might be None if caller is sloppy.
    # The function check `if not input_str` handles None gracefully if typed as Optional[str] but here it is str.
    # However, in python None is falsy so it returns "".
    assert sanitize_log_input(None) == ""

@pytest.mark.asyncio
async def test_main_log_injection_prevention():
    # Mock Request
    mock_request = MagicMock()
    mock_request.headers.get.return_value = "user\ninput"

    # Mock Input
    model_input = Input(
        model="model\nname",
        messages=[],
        user="original_user"
    )

    # Mock log_with_trace
    # We patch it where it is used. Since it is defined in main.py and used in main.py,
    # we patch 'fastapi_autogen_team.main.log_with_trace'.
    with patch("fastapi_autogen_team.main.log_with_trace") as mock_log:
        # We also need to mock serve_autogen to avoid running actual logic
        with patch("fastapi_autogen_team.main.serve_autogen") as mock_service:
            # We also need to mock model_info because route_query accesses model_info.name
            # But model_info is imported/defined at module level.
            # It should be fine as long as we don't crash.

            # route_query signature: async def route_query(model_input: Input, request: Request) -> dict:
            # We expect HTTPException because model name mismatch
            with pytest.raises(HTTPException):
                await route_query(model_input, mock_request)

            # Verify the log call used sanitized strings
            mock_log.assert_called()
            # The first call should be the one logging the request
            # log_with_trace(f"Chat completion request for model: {safe_model}, user: {safe_user}")

            # Find the call with the message we expect
            found = False
            for c in mock_log.call_args_list:
                args = c[0]
                if "Chat completion request for model:" in args[0]:
                    assert "user\\ninput" in args[0]
                    assert "model\\nname" in args[0]
                    assert "\n" not in args[0] # Should not have raw newlines
                    found = True
            assert found, "Did not find the expected log message"

@pytest.mark.asyncio
async def test_tool_async_search_log_injection_prevention():
    query = "search\nquery"

    # We patch logger in tool.py
    with patch("fastapi_autogen_team.tool.logger") as mock_logger:
        # Mock the helper functions to avoid actual execution
        with patch("fastapi_autogen_team.tool.safe_get_r2r_results") as mock_r2r:
            with patch("fastapi_autogen_team.tool.safe_get_jira_results") as mock_jira:
                await async_search(query)

                # Check calls to logger.info
                # Expect: logger.info(f"Ejecutando búsqueda para: {safe_query}")
                found = False
                for c in mock_logger.info.call_args_list:
                    if "Ejecutando búsqueda para:" in c[0][0]:
                        assert "search\\nquery" in c[0][0]
                        assert "\n" not in c[0][0]
                        found = True
                assert found, "Did not find the expected log message in async_search"

def test_tool_get_jira_results_log_injection_prevention():
    query = "jira\nquery"

    # Need to set env vars for Jira to avoid ValueError
    with patch.dict("os.environ", {
        "JIRA_INSTANCE_URL": "http://jira",
        "JIRA_USERNAME": "user",
        "JIRA_API_TOKEN": "token"
    }):
        with patch("fastapi_autogen_team.tool.logger") as mock_logger:
            with patch("fastapi_autogen_team.tool.Jira") as mock_jira_class:
                mock_jira_instance = MagicMock()
                mock_jira_class.return_value = mock_jira_instance
                mock_jira_instance.jql.return_value = {}

                get_jira_results(query)

                # Check log call
                # It logs "Ejecutando consulta Jira JQL para: ..."
                found = False
                for c in mock_logger.info.call_args_list:
                    if "Ejecutando consulta Jira JQL para:" in c[0][0]:
                        assert "jira\\nquery" in c[0][0]
                        assert "\n" not in c[0][0]
                        found = True
                assert found, "Did not find the expected log message in get_jira_results"
