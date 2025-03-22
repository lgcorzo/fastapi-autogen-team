


import pytest
from unittest.mock import patch, MagicMock, call
from queue import Queue
import types
from functools import partial

import autogen
from termcolor import colored
import logging

# Import the module to test
# Assuming the original code is in a file named fastapi_autogen_team.autogen_workflow_team.py
from fastapi_autogen_team.autogen_workflow_team import (
    AutogenWorkflow, 
    create_llm_config,
    streamed_print_received_message,
    handle_tool_responses,
    handle_function_tool_message,
    handle_regular_message,
    handle_suggested_function_call,
    handle_suggested_tool_calls
)

# Test fixtures
@pytest.fixture
def mock_iostream():
    """Mock the IOStream for testing print functions"""
    with patch('autogen.io.IOStream') as mock_io:
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
def test_handle_function_tool_message(mock_iostream):
    """Test handle_function_tool_message function"""
    message = {
        "role": "function",
        "name": "test_function",
        "content": "Function result content"
    }
    
    result = handle_function_tool_message(message, mock_iostream, "Initial message")
    
    # Check that correct calls were made to iostream.print
    expected_calls = [
        call(colored("***** Response from calling function (test_function) *****", "green"), flush=True),
        call("Function result content", flush=True),
        call(colored("*************************************************", "green"), flush=True)
    ]
    assert mock_iostream.print.call_args_list == expected_calls
    
    # Check the returned streaming message
    assert "***** Response from calling function (test_function) *****" in result
    assert "Function result content" in result
    assert "************************************************" in result

def test_handle_suggested_function_call(mock_iostream):
    """Test handle_suggested_function_call function"""
    function_call = {
        "name": "test_function",
        "arguments": '{"arg1": "value1", "arg2": 42}'
    }
    
    result = handle_suggested_function_call(function_call, mock_iostream, "Initial message")
    
    # Check the returned streaming message
    assert "***** Suggested function call: test_function *****" in result
    assert 'Arguments: \n{"arg1": "value1", "arg2": 42}' in result

@patch('fastapi_autogen_team.autogen_workflow_team.handle_function_tool_message')
@patch('fastapi_autogen_team.autogen_workflow_team.handle_suggested_function_call')
@patch('fastapi_autogen_team.autogen_workflow_team.handle_suggested_tool_calls')
def test_handle_regular_message(mock_tool_calls, mock_function_call, mock_function_tool, mock_iostream):
    """Test handle_regular_message function with various message types"""
    # Setup mocks
    mock_function_tool.return_value = "Updated message 1"
    mock_function_call.return_value = "Updated message 2"
    mock_tool_calls.return_value = "Updated message 3"
    
    # Test case: basic message
    agent = MagicMock()
    agent.llm_config = None
    
    message = {
        "content": "Test message content"
    }
    
    result = handle_regular_message(agent, message, mock_iostream, "Initial message")
    
    assert mock_iostream.print.call_args_list[0] == call("Test message content", flush=True)
    assert "Test message content" in result
    
    # Reset mocks for next test
    mock_iostream.reset_mock()
    
    # Test case: message with function_call
    message_with_function = {
        "content": "Message with function",
        "function_call": {"name": "test_func", "arguments": "{}"}
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
        "tool_calls": [{"id": "1", "function": {"name": "test_tool", "arguments": "{}"}}]
    }
    
    result = handle_regular_message(agent, message_with_tools, mock_iostream, "Initial message")
    
    assert mock_tool_calls.called
    assert result == "Updated message 3"

# Test the AutogenWorkflow class
@patch('fastapi_autogen_team.autogen_workflow_team.UserProxyAgent')
@patch('fastapi_autogen_team.autogen_workflow_team.AssistantAgent')
@patch('fastapi_autogen_team.autogen_workflow_team.GroupChat')
@patch('fastapi_autogen_team.autogen_workflow_team.GroupChatManager')
def test_autogen_workflow_initialization(mock_manager, mock_group_chat, mock_assistant, mock_user_proxy):
    """Test initialization of AutogenWorkflow class"""
    # Setup mocks
    mock_user_proxy.return_value = MagicMock(name="user_proxy")
    mock_assistant.side_effect = [
        MagicMock(name="developer"),
        MagicMock(name="planner"),
        MagicMock(name="quality_assurance")
    ]
    mock_group_chat.return_value = MagicMock(name="group_chat")
    mock_manager.return_value = MagicMock(name="manager")
    
    # Create workflow
    workflow = AutogenWorkflow()
    
    # Verify correct instantiation
    assert mock_user_proxy.call_count == 2  # user_proxy and executor
    assert mock_assistant.call_count == 3  # developer, planner, and qa
    assert mock_group_chat.call_count == 1
    assert mock_manager.call_count == 1
    
    # Test allowed transitions format
    assert len(workflow.allowed_transitions) == 5  # One for each agent

@patch('fastapi_autogen_team.autogen_workflow_team.UserProxyAgent')
@patch('fastapi_autogen_team.autogen_workflow_team.AssistantAgent')
@patch('fastapi_autogen_team.autogen_workflow_team.GroupChat')
@patch('fastapi_autogen_team.autogen_workflow_team.GroupChatManager')
def test_autogen_workflow_run_without_streaming(mock_manager, mock_group_chat, mock_assistant, mock_user_proxy):
    """Test running the workflow without streaming enabled"""
    # Setup mocks
    mock_user = MagicMock(name="user_proxy")
    mock_user.initiate_chat.return_value = "chat_result"
    mock_user_proxy.return_value = mock_user
    
    mock_assistant.side_effect = [
        MagicMock(name="developer"),
        MagicMock(name="planner"),
        MagicMock(name="quality_assurance")
    ]
    
    # Create and run workflow
    workflow = AutogenWorkflow()
    result = workflow.run("Test message")
    
    # Verify chat was initiated with correct parameters
    mock_user.initiate_chat.assert_called_once()
    assert result == "chat_result"

@patch('fastapi_autogen_team.autogen_workflow_team.UserProxyAgent')
@patch('fastapi_autogen_team.autogen_workflow_team.AssistantAgent')
@patch('fastapi_autogen_team.autogen_workflow_team.GroupChat')
@patch('fastapi_autogen_team.autogen_workflow_team.GroupChatManager')
@patch('fastapi_autogen_team.autogen_workflow_team.types.MethodType')
def test_autogen_workflow_run_with_streaming(mock_method_type, mock_manager, mock_group_chat, 
                                           mock_assistant, mock_user_proxy):
    """Test running the workflow with streaming enabled"""
    # Setup mocks
    mock_user = MagicMock(name="user_proxy")
    mock_user.initiate_chat.return_value = "chat_result"
    mock_user_proxy.return_value = mock_user
    
    mock_assistant.side_effect = [
        MagicMock(name="developer"),
        MagicMock(name="planner"),
        MagicMock(name="quality_assurance")
    ]
    
    mock_mgr = MagicMock()
    mock_manager.return_value = mock_mgr
    
    # Create workflow and set queue
    workflow = AutogenWorkflow()
    mock_queue = MagicMock(spec=Queue)
    workflow.set_queue(mock_queue)
    
    # Run workflow with streaming
    result = workflow.run("Test message", stream=True)
    
    # Verify method was patched for streaming
    assert mock_method_type.call_count >= 1
    
    # Verify queue received done signal
    mock_queue.put.assert_called_with("[DONE]")
    
    # Verify chat result
    assert result == "chat_result"

# Test the streamed_print_received_message function
def test_streamed_print_received_message(mock_iostream, mock_queue):
    """Test the streaming message function"""
    # Setup
    agent = MagicMock()
    agent.name = "TestAgent"
    sender = MagicMock()
    sender.name = "TestSender"
    
    message = {
        "role": "assistant",
        "content": "Test message content"
    }
    
    # Call function
    streamed_print_received_message(agent, message, sender, mock_queue, 1)
    
    # Verify print calls
    assert mock_iostream.print.call_args_list[0] == call(colored("TestSender", "yellow"), "(to", "TestAgent):\n", flush=True)
    assert mock_iostream.print.call_args_list[1] == call("Test message content", flush=True)
    
    # Verify queue put was called with correct format
    expected_queue_put = {
        "index": 1,
        "delta": {"role": "assistant", "content": any(str)},
        "finish_reason": "stop"
    }
    mock_queue.put.assert_called_once()
    assert mock_queue.put.call_args[0][0]["index"] == expected_queue_put["index"]
    assert mock_queue.put.call_args[0][0]["finish_reason"] == expected_queue_put["finish_reason"]
    assert isinstance(mock_queue.put.call_args[0][0]["delta"]["content"], str)

# Test edge cases and error handling
def test_handle_tool_responses_empty_response(mock_iostream, mock_queue):
    """Test handling empty tool responses"""
    agent = MagicMock()
    agent.name = "TestAgent"
    sender = MagicMock()
    sender.name = "TestSender"
    
    message = {
        "role": "tool",
        "tool_responses": []
    }
    
    result = handle_tool_responses(agent, message, sender, mock_queue, 1, mock_iostream, "Initial message")
    assert result == ""  # Should return empty string for tool role
    assert mock_queue.put.called

def test_handle_regular_message_with_context(mock_iostream):
    """Test handling messages with context field"""
    agent = MagicMock()
    agent.name = "TestAgent"
    agent.llm_config = {"allow_format_str_template": True}
    
    message = {
        "content": "Hello {name}",
        "context": {"name": "World"}
    }
    
    with patch('fastapi_autogen_team.autogen_workflow_team.OpenAIWrapper') as mock_wrapper:
        mock_wrapper.instantiate.return_value = "Hello World"
        result = handle_regular_message(agent, message, mock_iostream, "Initial message")
        
        assert "Hello World" in result
        mock_wrapper.instantiate.assert_called_with(
            "Hello {name}", 
            {"name": "World"}, 
            True
        )