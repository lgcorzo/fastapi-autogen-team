import pytest
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


def test_tool_safe_get_jira_results_leak():
    """Test that safe_get_jira_results does not leak exception details."""
    with patch("fastapi_autogen_team.tool.get_jira_results") as mock_get:
        mock_get.side_effect = ValueError(SENSITIVE_ERROR)
        result = tool.safe_get_jira_results("query")
        assert SENSITIVE_ERROR not in result
        assert "An internal error occurred" in result


def test_tool_safe_get_r2r_results_leak():
    """Test that safe_get_r2r_results does not leak exception details."""
    with patch("fastapi_autogen_team.tool.get_r2r_results") as mock_get:
        mock_get.side_effect = ValueError(SENSITIVE_ERROR)
        result = tool.safe_get_r2r_results("query")
        assert SENSITIVE_ERROR not in result
        assert "An internal error occurred" in result


@pytest.mark.asyncio
async def test_tool_async_search_leak():
    """Test that async_search does not leak exceptions from gather."""
    with patch("fastapi_autogen_team.tool.safe_get_r2r_results") as mock_r2r:
        # Mocking to raise exception directly (which asyncio.to_thread handles)
        mock_r2r.side_effect = ValueError(SENSITIVE_ERROR)

        # We also need to mock safe_get_jira_results to return something valid
        with patch("fastapi_autogen_team.tool.safe_get_jira_results") as mock_jira:
             mock_jira.return_value = "jira result"

             result = await tool.async_search("query")

             # result['r2r'] should be safe
             assert SENSITIVE_ERROR not in str(result["r2r"])
             assert "An internal error occurred" in str(result["r2r"])
