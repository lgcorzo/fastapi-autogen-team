import pytest
from unittest.mock import patch, MagicMock, call
from queue import Queue


# Import the module to test
# Assuming the original code is in a file named fastapi_autogen_team.autogen_workflow_team.py
from fastapi_autogen_team.autogen_workflow_team import (
    AutogenWorkflow,
    create_llm_config,
    handle_tool_responses,
    handle_regular_message,
    handle_suggested_function_call,
)


# Test fixtures
@pytest.fixture
def mock_iostream():
    """Mock the IOStream for testing print functions"""
    with patch("autogen.io.IOStream") as mock_io:
        mock_default = MagicMock()
        mock_io.get_default.return_value = mock_default
        yield mock_default


@pytest.fixture
def mock_queue():
    """Create a mock queue for testing streaming functions"""
    return MagicMock(spec=Queue)


@pytest.fixture
def workflow():
    """Create an instance of AutogenWorkflow for testing"""
    return AutogenWorkflow()


# Test create_llm_config function
def test_create_llm_config_default():
    """Test create_llm_config with default parameters"""
    config = create_llm_config()

    assert config["cache_seed"] is None
    assert config["temperature"] == 0
    assert config["timeout"] == 240
    assert len(config["config_list"]) == 1
    assert config["config_list"][0]["model"] == "azure-gpt"
    assert config["config_list"][0]["api_key"] == "sk-12345"
    assert config["config_list"][0]["base_url"] == "http://litellm:4000"


def test_create_llm_config_custom():
    """Test create_llm_config with custom parameters"""
    custom_config = [{"model": "test-model", "api_key": "test-key"}]
    config = create_llm_config(config_list=custom_config, temperature=0.7, timeout=120)

    assert config["cache_seed"] is None
    assert config["temperature"] == 0.7
    assert config["timeout"] == 120
    assert config["config_list"] == custom_config


# Test message handling functions
def test_handle_suggested_function_call(mock_iostream):
    """Test handle_suggested_function_call function"""
    function_call = {"name": "test_function", "arguments": '{"arg1": "value1", "arg2": 42}'}

    result = handle_suggested_function_call(function_call, mock_iostream, "Initial message")

    # Check the returned streaming message
    assert "***** Suggested function call: test_function *****" in result
    assert 'Arguments: \n{"arg1": "value1", "arg2": 42}' in result


@patch("fastapi_autogen_team.autogen_workflow_team.handle_function_tool_message")
@patch("fastapi_autogen_team.autogen_workflow_team.handle_suggested_function_call")
@patch("fastapi_autogen_team.autogen_workflow_team.handle_suggested_tool_calls")
def test_handle_regular_message(mock_tool_calls, mock_function_call, mock_function_tool, mock_iostream):
    """Test handle_regular_message function with various message types"""
    # Setup mocks
    mock_function_tool.return_value = "Updated message 1"
    mock_function_call.return_value = "Updated message 2"
    mock_tool_calls.return_value = "Updated message 3"

    # Test case: basic message
    agent = MagicMock()
    agent.llm_config = None

    message = {"content": "Test message content"}

    result = handle_regular_message(agent, message, mock_iostream, "Initial message")

    assert mock_iostream.print.call_args_list[0] == call("Test message content", flush=True)
    assert "Test message content" in result

    # Reset mocks for next test
    mock_iostream.reset_mock()

    # Test case: message with function_call
    message_with_function = {
        "content": "Message with function",
        "function_call": {"name": "test_func", "arguments": "{}"},
    }

    result = handle_regular_message(agent, message_with_function, mock_iostream, "Initial message")

    assert mock_function_call.called
    assert result == "Updated message 2"

    # Reset mocks for next test
    mock_iostream.reset_mock()
    mock_function_call.reset_mock()

    # Test case: message with tool_calls
    message_with_tools = {
        "content": "Message with tools",
        "tool_calls": [{"id": "1", "function": {"name": "test_tool", "arguments": "{}"}}],
    }

    result = handle_regular_message(agent, message_with_tools, mock_iostream, "Initial message")

    assert mock_tool_calls.called
    assert result == "Updated message 3"


@patch("fastapi_autogen_team.autogen_workflow_team.UserProxyAgent")
@patch("fastapi_autogen_team.autogen_workflow_team.AssistantAgent")
@patch("fastapi_autogen_team.autogen_workflow_team.GroupChat")
@patch("fastapi_autogen_team.autogen_workflow_team.GroupChatManager")
def test_autogen_workflow_run_without_streaming(mock_manager, mock_group_chat, mock_assistant, mock_user_proxy):
    """Test running the workflow without streaming enabled"""
    # Setup mocks
    mock_user = MagicMock(name="user_proxy")
    mock_user.initiate_chat.return_value = "chat_result"
    mock_user_proxy.return_value = mock_user

    mock_assistant.side_effect = [
        MagicMock(name="developer"),
        MagicMock(name="planner"),
        MagicMock(name="quality_assurance"),
    ]

    # Create and run workflow
    workflow = AutogenWorkflow()
    result = workflow.run("Test message")

    # Verify chat was initiated with correct parameters
    mock_user.initiate_chat.assert_called_once()
    assert result == "chat_result"


# Test edge cases and error handling
def test_handle_tool_responses_empty_response(mock_iostream, mock_queue):
    """Test handling empty tool responses"""
    agent = MagicMock()
    agent.name = "TestAgent"
    sender = MagicMock()
    sender.name = "TestSender"

    message = {"role": "tool", "tool_responses": []}

    result = handle_tool_responses(agent, message, sender, mock_queue, 1, mock_iostream, "Initial message")
    assert result == ""  # Should return empty string for tool role
    assert mock_queue.put.called


def test_handle_regular_message_with_context(mock_iostream):
    """Test handling messages with context field"""
    agent = MagicMock()
    agent.name = "TestAgent"
    agent.llm_config = {"allow_format_str_template": True}

    message = {"content": "Hello {name}", "context": {"name": "World"}}

    with patch("fastapi_autogen_team.autogen_workflow_team.OpenAIWrapper") as mock_wrapper:
        mock_wrapper.instantiate.return_value = "Hello World"
        result = handle_regular_message(agent, message, mock_iostream, "Initial message")

        assert "Hello World" in result
        mock_wrapper.instantiate.assert_called_with("Hello {name}", {"name": "World"}, True)
