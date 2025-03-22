import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException

from fastapi_autogen_team.autogen_server import (
    handle_response,
    serve_autogen,
    create_non_streaming_response,
    generate_streaming_response,
)
from fastapi_autogen_team.data_model import Input, Output

# Mock data for testing
MODEL_NAME = "test_model"
TEST_MESSAGE = "Hello, Autogen!"
TEST_INPUT = Input(model=MODEL_NAME, messages=[{"role": "user", "content": TEST_MESSAGE}])
TEST_CHAT_ID = "123"


@pytest.fixture
def mock_autogen_workflow():
    """Mocks AutogenWorkflow for testing."""
    with patch("fastapi_autogen_team.autogen_server.AutogenWorkflow") as MockWorkflow:
        workflow_instance = MockWorkflow.return_value
        # Make sure run returns the value we want
        mock_chat_result = MagicMock(
            chat_id=TEST_CHAT_ID, chat_history=[{"role": "assistant", "content": "Hi!"}], cost={}
        )
        workflow_instance.run.return_value = mock_chat_result
        yield workflow_instance


def test_handle_response_valid():
    """Test handle_response with a valid Output object."""
    output = Output(id="test_id", model=MODEL_NAME, choices=[], usage={})
    result = handle_response(output)
    assert isinstance(result, dict)
    assert result["id"] == "test_id"


def test_handle_response_invalid_string():
    """Test handle_response with an invalid string input."""
    with pytest.raises(HTTPException) as exc_info:
        handle_response("error")
    assert exc_info.value.status_code == 500
    assert "Unexpected string response" in exc_info.value.detail


def test_handle_response_missing_model_dump():
    """Test handle_response with an object missing model_dump method."""

    class MockObject:
        pass

    with pytest.raises(HTTPException) as exc_info:
        handle_response(MockObject())
    assert exc_info.value.status_code == 500
    assert "'model_dump' method" in exc_info.value.detail


def test_serve_autogen_streaming(mock_autogen_workflow):
    """Test serve_autogen with streaming response."""
    mock_autogen_workflow.run.return_value = None
    with (
        patch("fastapi_autogen_team.autogen_server.generate_streaming_response") as mock_generate_streaming_response,
        patch("fastapi_autogen_team.autogen_server.StreamingResponse") as MockStreamingResponse,
    ):
        test_input_streaming = Input(
            model=MODEL_NAME, messages=[{"role": "user", "content": TEST_MESSAGE}], stream=True
        )
        serve_autogen(test_input_streaming)
        MockStreamingResponse.assert_called_once()
        mock_autogen_workflow.set_queue.assert_called_once()
        mock_generate_streaming_response.assert_called_once()


def test_generate_streaming_response():
    """Test generate_streaming_response with a mock queue."""
    mock_queue = MagicMock()
    mock_queue.get.side_effect = ["Test chunk", "[DONE]"]
    generator = generate_streaming_response(TEST_INPUT, mock_queue)
    chunks = [chunk for chunk in generator]
    assert len(chunks) == 2
    assert "Test chunk" in chunks[0]
    assert "[DONE]" in chunks[1]


def test_create_non_streaming_response_success(mock_autogen_workflow):
    """Test create_non_streaming_response with successful chat results."""
    mock_chat_results = MagicMock(chat_id=TEST_CHAT_ID, chat_history=[{"role": "assistant", "content": "Hi!"}], cost={})
    result = create_non_streaming_response(mock_chat_results, MODEL_NAME)
    assert isinstance(result, dict)
    assert result["id"] == TEST_CHAT_ID
    assert len(result["choices"]) == 1


def test_create_non_streaming_response_no_results():
    """Test create_non_streaming_response with no chat results."""
    result = create_non_streaming_response(None, MODEL_NAME)
    assert result["id"] == "None"
    assert len(result["choices"]) == 1
    assert "Sorry, I am unable to assist" in result["choices"][0]["message"]["content"]
