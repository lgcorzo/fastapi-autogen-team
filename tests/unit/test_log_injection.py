import pytest
from unittest.mock import patch, MagicMock

from fastapi_autogen_team.utils import sanitize_log_input
from fastapi import HTTPException
from fastapi_autogen_team.data_model import Input
from fastapi_autogen_team.main import route_query
from fastapi_autogen_team.tool import async_search, get_jira_results


def test_sanitize_log_input():
    assert sanitize_log_input("normal input") == "normal input"
    assert sanitize_log_input("input\nwith\nnewline") == "input\\nwith\\nnewline"
    assert sanitize_log_input("input\rwith\rcarriage return") == "input\\rwith\\rcarriage return"
    assert sanitize_log_input("input\r\nwith\r\nboth") == "input\\r\\nwith\\r\\nboth"
    assert sanitize_log_input("") == ""
    assert sanitize_log_input(None) == ""


def test_sanitize_log_input_normal_string():
    """Test sanitization of a normal string."""
    input_str = "This is a normal string."
    assert sanitize_log_input(input_str) == "This is a normal string."


def test_sanitize_log_input_with_newlines():
    """Test sanitization of a string with newlines."""
    input_str = "Line 1\nLine 2"
    assert sanitize_log_input(input_str) == "Line 1\\nLine 2"


def test_sanitize_log_input_with_carriage_returns():
    """Test sanitization of a string with carriage returns."""
    input_str = "Line 1\rLine 2"
    assert sanitize_log_input(input_str) == "Line 1\\rLine 2"


def test_sanitize_log_input_with_mixed_newlines():
    """Test sanitization of a string with mixed newlines."""
    input_str = "Line 1\r\nLine 2"
    assert sanitize_log_input(input_str) == "Line 1\\r\\nLine 2"


def test_sanitize_log_input_none():
    """Test sanitization of None."""
    assert sanitize_log_input(None) == ""


def test_sanitize_log_input_empty_string():
    """Test sanitization of an empty string."""
    assert sanitize_log_input("") == ""


@pytest.mark.asyncio
async def test_main_log_injection_prevention():
    # Mock Request
    mock_request = MagicMock()
    mock_request.headers.get.return_value = "user\ninput"

    # Mock Input
    model_input = Input(model="model\nname", messages=[], user="original_user")

    # Mock log_with_trace
    with patch("fastapi_autogen_team.main.log_with_trace") as mock_log:
        with patch("fastapi_autogen_team.main.serve_autogen"):
            with pytest.raises(HTTPException):
                await route_query(model_input, mock_request)

            mock_log.assert_called()
            found = False
            for c in mock_log.call_args_list:
                args = c[0]
                if "Chat completion request for model:" in args[0]:
                    assert "user\\ninput" in args[0]
                    assert "model\\nname" in args[0]
                    assert "\n" not in args[0]
                    found = True
            assert found, "Did not find the expected log message"


@pytest.mark.asyncio
async def test_tool_async_search_log_injection_prevention():
    query = "search\nquery"

    with patch("fastapi_autogen_team.tool.logger") as mock_logger:
        with patch("fastapi_autogen_team.tool.safe_get_r2r_results"):
            with patch("fastapi_autogen_team.tool.safe_get_jira_results"):
                await async_search(query)

                found = False
                for c in mock_logger.info.call_args_list:
                    if "Ejecutando búsqueda para:" in c[0][0]:
                        assert "search\\nquery" in c[0][0]
                        assert "\n" not in c[0][0]
                        found = True
                assert found, "Did not find the expected log message in async_search"


def test_tool_get_jira_results_log_injection_prevention():
    query = "jira\nquery"

    with patch.dict(
        "os.environ", {"JIRA_INSTANCE_URL": "http://jira", "JIRA_USERNAME": "user", "JIRA_API_TOKEN": "token"}
    ):
        with patch("fastapi_autogen_team.tool.logger") as mock_logger:
            with patch("fastapi_autogen_team.tool.Jira") as mock_jira_class:
                mock_jira_instance = MagicMock()
                mock_jira_class.return_value = mock_jira_instance
                mock_jira_instance.jql.return_value = {}

                get_jira_results(query)

                found = False
                for c in mock_logger.info.call_args_list:
                    if "Ejecutando consulta Jira JQL para:" in c[0][0]:
                        assert "jira\\nquery" in c[0][0]
                        assert "\n" not in c[0][0]
                        found = True
                assert found, "Did not find the expected log message in get_jira_results"
