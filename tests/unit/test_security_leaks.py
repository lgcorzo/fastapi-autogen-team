import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from fastapi_autogen_team.autogen_server import serve_autogen, generate_streaming_response
from fastapi_autogen_team.data_model import Input

MODEL_NAME = "test_model"
TEST_MESSAGE = "Hello, Autogen!"
TEST_INPUT = Input(model=MODEL_NAME, messages=[{"role": "user", "content": TEST_MESSAGE}])

@pytest.fixture
def mock_autogen_workflow_error():
    """Mocks AutogenWorkflow to raise an exception."""
    with patch("fastapi_autogen_team.autogen_server.AutogenWorkflow") as MockWorkflow:
        workflow_instance = MockWorkflow.return_value
        workflow_instance.run.side_effect = ValueError("Sensitive Internal Error Details")
        workflow_instance.set_queue = MagicMock()
        yield workflow_instance

def test_serve_autogen_does_not_leak_exception_details(mock_autogen_workflow_error):
    """Test that serve_autogen does NOT leak exception details."""
    with pytest.raises(HTTPException) as exc_info:
        serve_autogen(TEST_INPUT)

    assert exc_info.value.status_code == 500
    assert "Sensitive Internal Error Details" not in exc_info.value.detail
    assert "An internal error occurred during Autogen processing." in exc_info.value.detail

def test_generate_streaming_response_does_not_leak_exception_details():
    """Test that generate_streaming_response does NOT leak exception details."""
    mock_queue = MagicMock()
    mock_queue.get.side_effect = ValueError("Sensitive Stream Error")

    generator = generate_streaming_response(TEST_INPUT, mock_queue)

    with pytest.raises(HTTPException) as exc_info:
        next(generator)

    assert exc_info.value.status_code == 500
    assert "Sensitive Stream Error" not in exc_info.value.detail
    assert "An internal error occurred during streaming response." in exc_info.value.detail
