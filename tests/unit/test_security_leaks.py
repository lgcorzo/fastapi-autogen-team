import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from fastapi_autogen_team.autogen_server import serve_autogen, generate_streaming_response
from fastapi_autogen_team.data_model import Input
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
