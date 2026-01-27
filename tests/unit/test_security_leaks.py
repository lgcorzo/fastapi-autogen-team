import pytest
import asyncio
from unittest.mock import patch
from fastapi import HTTPException
from fastapi_autogen_team.autogen_server import serve_autogen, generate_streaming_response
from fastapi_autogen_team.data_model import Input
from fastapi_autogen_team import tool
from queue import Queue

# Mock data
MODEL_NAME = "test_model"
TEST_MESSAGE = "Hello"
TEST_INPUT = Input(model=MODEL_NAME, messages=[{"role": "user", "content": TEST_MESSAGE}])
SENSITIVE_ERROR = "Database connection failed: user=admin password=secrethost"
GENERIC_ERROR_R2R = "An internal error occurred while retrieving R2R results."
GENERIC_ERROR_JIRA = "An internal error occurred while retrieving Jira results."


def test_serve_autogen_exception_leak():
    """Test that serve_autogen does NOT leak sensitive exception details."""
    with patch("fastapi_autogen_team.autogen_server.AutogenWorkflow") as MockWorkflow:
        workflow_instance = MockWorkflow.return_value
        # Simulate an exception with sensitive info
        workflow_instance.run.side_effect = ValueError(SENSITIVE_ERROR)

        with pytest.raises(HTTPException) as exc_info:
            serve_autogen(TEST_INPUT)

        # AFTER FIX: It should NOT leak.
        assert SENSITIVE_ERROR not in exc_info.value.detail
        assert "An internal error occurred during Autogen processing." in exc_info.value.detail
        assert exc_info.value.status_code == 500


def test_streaming_exception_leak():
    """Test that streaming response does NOT leak sensitive details in the stream."""
    queue = Queue()

    # Simulate what AutogenWorkflow NOW puts into the queue on error
    error_payload = {
        "index": 0,
        "delta": {"role": "assistant", "content": "An internal error occurred."},
        "finish_reason": "error",
    }

    queue.put(error_payload)
    queue.put("[DONE]")

    generator = generate_streaming_response(TEST_INPUT, queue)

    # Read the first chunk
    chunk = next(generator)
    # verify it does NOT contain the sensitive error
    assert SENSITIVE_ERROR not in chunk
    assert "An internal error occurred." in chunk


def test_safe_get_jira_results_leaks_exception():
    """Test that safe_get_jira_results DOES NOT leak sensitive exception details (FIXED)."""
    with patch("fastapi_autogen_team.tool.get_jira_results") as mock_get:
        mock_get.side_effect = Exception(f"Connection failed: {SENSITIVE_ERROR}")

        result = tool.safe_get_jira_results("query")

        # Should NOT leak
        assert SENSITIVE_ERROR not in result
        assert result == GENERIC_ERROR_JIRA


def test_safe_get_r2r_results_leaks_exception():
    """Test that safe_get_r2r_results DOES NOT leak sensitive exception details (FIXED)."""
    with patch("fastapi_autogen_team.tool.get_r2r_results") as mock_get:
        mock_get.side_effect = Exception(f"Connection failed: {SENSITIVE_ERROR}")

        result = tool.safe_get_r2r_results("query")

        # Should NOT leak
        assert SENSITIVE_ERROR not in result
        assert result == GENERIC_ERROR_R2R


@pytest.mark.asyncio
async def test_async_search_leaks_exception():
    """Test that async_search DOES NOT leak sensitive exception details (FIXED)."""
    with patch("fastapi_autogen_team.tool.safe_get_r2r_results") as mock_r2r, \
         patch("fastapi_autogen_team.tool.safe_get_jira_results") as mock_jira:

        # Scenario 1: safe_get_* returns the GENERIC message (because they caught the exception)
        mock_r2r.return_value = GENERIC_ERROR_R2R
        mock_jira.return_value = GENERIC_ERROR_JIRA

        result = await tool.async_search("query")

        assert SENSITIVE_ERROR not in result["r2r"]
        assert SENSITIVE_ERROR not in result["jira"]
        assert result["r2r"] == GENERIC_ERROR_R2R
        assert result["jira"] == GENERIC_ERROR_JIRA


@pytest.mark.asyncio
async def test_async_search_leaks_unhandled_exception():
    """Test that async_search DOES NOT leak unhandled exceptions (FIXED)."""
    # We mock asyncio.wait_for to raise an exception to simulate a timeout or other error
    # that happens INSIDE the gather but is returned as an exception object because return_exceptions=True

    with patch("asyncio.wait_for") as mock_wait_for:
        mock_wait_for.side_effect = [
            Exception(f"R2R Failed: {SENSITIVE_ERROR}"),
            Exception(f"Jira Failed: {SENSITIVE_ERROR}")
        ]

        # We also need to mock to_thread because async_search calls it before wait_for
        with patch("asyncio.to_thread"):
            result = await tool.async_search("query")

        # Should NOT leak
        assert SENSITIVE_ERROR not in result["r2r"]
        assert SENSITIVE_ERROR not in result["jira"]
        assert result["r2r"] == GENERIC_ERROR_R2R
        assert result["jira"] == GENERIC_ERROR_JIRA
