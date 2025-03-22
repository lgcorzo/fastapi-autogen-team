import pytest
from unittest.mock import patch, MagicMock, call
from queue import Queue
from autogen import Agent
from termcolor import colored


# Import the module to test
# Assuming the original code is in a file named fastapi_autogen_team.autogen_workflow_team.py
from fastapi_autogen_team.autogen_workflow_team import (
    AutogenWorkflow,
    create_llm_config,
    handle_tool_responses,
    handle_regular_message,
    handle_suggested_function_call,
    handle_function_tool_message,
    handle_suggested_tool_calls,
    streamed_print_received_message,
)


# Test fixtures
@pytest.fixture
def mock_iostream():
    """Mock the IOStream for testing print functions"""
    with patch("fastapi_autogen_team.autogen_workflow_team.IOStream") as mock_io:
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

@pytest.fixture
def mock_agent():
    """Create a mock agent for testing"""
    agent = MagicMock(spec=Agent)
    agent.name = "TestAgent"
    agent._message_to_dict = MagicMock(side_effect=lambda x: x if isinstance(x, dict) else {"content": x})
    return agent


@pytest.fixture
def mock_sender():
    """Create a mock sender for testing"""
    sender = MagicMock(spec=Agent)
    sender.name = "TestSender"
    return sender


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


def test_handle_function_tool_message_function(mock_iostream):
    """Test handle_function_tool_message function with a function call message"""
    message = {"role": "function", "name": "test_function", "content": "Function output"}
    result = handle_function_tool_message(message, mock_iostream, "Initial message")

    # Check the returned streaming message
    expected_func_print = "***** Response from calling function (test_function) *****"
    assert expected_func_print in result
    assert "Function output" in result
    assert "*" * len(expected_func_print) in result

    # Check the print calls
    mock_iostream.print.assert_has_calls(
        [
            call(colored(expected_func_print, "green"), flush=True),
            call("Function output", flush=True),
            call(colored("*" * len(expected_func_print), "green"), flush=True),
        ]
    )


def test_handle_function_tool_message_tool(mock_iostream):
    """Test handle_function_tool_message function with a tool call message"""
    message = {"role": "tool", "tool_call_id": "tool_123", "content": "Tool output"}
    result = handle_function_tool_message(message, mock_iostream, "Initial message")

    # Check the returned streaming message
    expected_func_print = "***** Response from calling tool (tool_123) *****"
    assert expected_func_print in result
    assert "Tool output" in result
    assert "*" * len(expected_func_print) in result

    # Check the print calls
    mock_iostream.print.assert_has_calls(
        [
            call(colored(expected_func_print, "green"), flush=True),
            call("Tool output", flush=True),
            call(colored("*" * len(expected_func_print), "green"), flush=True),
        ]
    )


def test_handle_function_tool_message_no_id(mock_iostream):
    """Test handle_function_tool_message function with no id in the message"""
    message = {"role": "function", "content": "Function output"}
    result = handle_function_tool_message(message, mock_iostream, "Initial message")

    # Check the returned streaming message
    expected_func_print = "***** Response from calling function (No id found) *****"
    assert expected_func_print in result
    assert "Function output" in result
    assert "*" * len(expected_func_print) in result

    # Check the print calls
    mock_iostream.print.assert_has_calls(
        [
            call(colored(expected_func_print, "green"), flush=True),
            call("Function output", flush=True),
            call(colored("*" * len(expected_func_print), "green"), flush=True),
        ]
    )


def test_handle_suggested_tool_calls_single_tool(mock_iostream):
    """Test handle_suggested_tool_calls with a single tool call"""
    tool_calls = [
        {
            "id": "tool_1",
            "function": {"name": "test_tool", "arguments": '{"arg1": "value1"}'},
        }
    ]
    result = handle_suggested_tool_calls(tool_calls, mock_iostream, "Initial message")

    # Check the returned streaming message
    expected_func_print = "***** Suggested tool call (tool_1): test_tool *****"
    assert expected_func_print in result
    assert 'Arguments: \n{"arg1": "value1"}' in result
    assert "*" * len(expected_func_print) in result

    # Check the print calls
    mock_iostream.print.assert_has_calls(
        [
            call(colored(expected_func_print, "green"), flush=True),
            call("Arguments: \n", '{"arg1": "value1"}', flush=True, sep=""),
            call(colored("*" * len(expected_func_print), "green"), flush=True),
        ]
    )


def test_handle_suggested_tool_calls_multiple_tools(mock_iostream):
    """Test handle_suggested_tool_calls with multiple tool calls"""
    tool_calls = [
        {
            "id": "tool_1",
            "function": {"name": "test_tool_1", "arguments": '{"arg1": "value1"}'},
        },
        {
            "id": "tool_2",
            "function": {"name": "test_tool_2", "arguments": '{"arg2": "value2"}'},
        },
    ]
    result = handle_suggested_tool_calls(tool_calls, mock_iostream, "Initial message")

    # Check the returned streaming message
    expected_func_print_1 = "***** Suggested tool call (tool_1): test_tool_1 *****"
    expected_func_print_2 = "***** Suggested tool call (tool_2): test_tool_2 *****"
    assert expected_func_print_1 in result
    assert expected_func_print_2 in result
    assert 'Arguments: \n{"arg1": "value1"}' in result
    assert 'Arguments: \n{"arg2": "value2"}' in result
    assert "*" * len(expected_func_print_1) in result
    assert "*" * len(expected_func_print_2) in result

    # Check the print calls
    mock_iostream.print.assert_has_calls(
        [
            call(colored(expected_func_print_1, "green"), flush=True),
            call("Arguments: \n", '{"arg1": "value1"}', flush=True, sep=""),
            call(colored("*" * len(expected_func_print_1), "green"), flush=True),
            call(colored(expected_func_print_2, "green"), flush=True),
            call("Arguments: \n", '{"arg2": "value2"}', flush=True, sep=""),
            call(colored("*" * len(expected_func_print_2), "green"), flush=True),
        ]
    )


def test_handle_suggested_tool_calls_no_id(mock_iostream):
    """Test handle_suggested_tool_calls with no tool call id"""
    tool_calls = [
        {
            "function": {"name": "test_tool", "arguments": '{"arg1": "value1"}'},
        }
    ]
    result = handle_suggested_tool_calls(tool_calls, mock_iostream, "Initial message")

    # Check the returned streaming message
    expected_func_print = "***** Suggested tool call (No tool call id found): test_tool *****"
    assert expected_func_print in result
    assert 'Arguments: \n{"arg1": "value1"}' in result
    assert "*" * len(expected_func_print) in result

    # Check the print calls
    mock_iostream.print.assert_has_calls(
        [
            call(colored(expected_func_print, "green"), flush=True),
            call("Arguments: \n", '{"arg1": "value1"}', flush=True, sep=""),
            call(colored("*" * len(expected_func_print), "green"), flush=True),
        ]
    )


def test_handle_suggested_tool_calls_no_function_name(mock_iostream):
    """Test handle_suggested_tool_calls with no function name"""
    tool_calls = [
        {
            "id": "tool_1",
            "function": {"arguments": '{"arg1": "value1"}'},
        }
    ]
    result = handle_suggested_tool_calls(tool_calls, mock_iostream, "Initial message")

    # Check the returned streaming message
    expected_func_print = "***** Suggested tool call (tool_1): (No function name found) *****"
    assert expected_func_print in result
    assert 'Arguments: \n{"arg1": "value1"}' in result
    assert "*" * len(expected_func_print) in result

    # Check the print calls
    mock_iostream.print.assert_has_calls(
        [
            call(colored(expected_func_print, "green"), flush=True),
            call("Arguments: \n", '{"arg1": "value1"}', flush=True, sep=""),
            call(colored("*" * len(expected_func_print), "green"), flush=True),
        ]
    )


def test_handle_suggested_tool_calls_no_arguments(mock_iostream):
    """Test handle_suggested_tool_calls with no arguments"""
    tool_calls = [
        {
            "id": "tool_1",
            "function": {"name": "test_tool"},
        }
    ]
    result = handle_suggested_tool_calls(tool_calls, mock_iostream, "Initial message")

    # Check the returned streaming message
    expected_func_print = "***** Suggested tool call (tool_1): test_tool *****"
    assert expected_func_print in result
    assert "Arguments: \n(No arguments found)" in result
    assert "*" * len(expected_func_print) in result

    # Check the print calls
    mock_iostream.print.assert_has_calls(
        [
            call(colored(expected_func_print, "green"), flush=True),
            call("Arguments: \n", "(No arguments found)", flush=True, sep=""),
            call(colored("*" * len(expected_func_print), "green"), flush=True),
        ]
    )

def test_streamed_print_received_message_basic_message(mock_agent, mock_sender, mock_queue, mock_iostream):
    """Test streamed_print_received_message with a basic message"""
    message = {"content": "Test message content"}
    streamed_print_received_message(mock_agent, message, mock_sender, mock_queue, 0)

    # Check print calls
    mock_iostream.print.assert_has_calls(
        [
            call(colored("TestSender", "yellow"), "(to", "TestAgent):\n", flush=True),
            call("Test message content", flush=True),
            call("\n", "-" * 80, flush=True, sep=""),
        ]
    )

    # Check queue put
    mock_queue.put.assert_called_once()
    queue_call_args = mock_queue.put.call_args[0][0]
    assert queue_call_args["index"] == 0
    assert "TestSender (to TestAgent):\nTest message content\n" in queue_call_args["delta"]["content"]
    assert queue_call_args["finish_reason"] == "stop"


def test_streamed_print_received_message_function_call(mock_agent, mock_sender, mock_queue, mock_iostream):
    """Test streamed_print_received_message with a function call message"""
    message = {"role": "function", "name": "test_function", "content": "Function output"}
    with patch("fastapi_autogen_team.autogen_workflow_team.handle_function_tool_message") as mock_handle_func:
        mock_handle_func.return_value = "Function message handled"
        streamed_print_received_message(mock_agent, message, mock_sender, mock_queue, 0)

        mock_handle_func.assert_called_once_with(message, mock_iostream, 'TestSender (to TestAgent):\n')

    # Check print calls
    mock_iostream.print.assert_has_calls(
        [
            call(colored("TestSender", "yellow"), "(to", "TestAgent):\n", flush=True),
            call("\n", "-" * 80, flush=True, sep=""),
        ]
    )

    # Check queue put
    mock_queue.put.assert_called_once()
    queue_call_args = mock_queue.put.call_args[0][0]
    assert queue_call_args["index"] == 0
    assert "Function message handled\n" in queue_call_args["delta"]["content"]
    assert queue_call_args["finish_reason"] == "stop"


def test_streamed_print_received_message_tool_call(mock_agent, mock_sender, mock_queue, mock_iostream):
    """Test streamed_print_received_message with a tool call message"""
    message = {"role": "tool", "tool_call_id": "tool_123", "content": "Tool output"}
    with patch("fastapi_autogen_team.autogen_workflow_team.handle_function_tool_message") as mock_handle_func:
        mock_handle_func.return_value = "Tool message handled"
        streamed_print_received_message(mock_agent, message, mock_sender, mock_queue, 0)

        mock_handle_func.assert_called_once_with(message, mock_iostream, 'TestSender (to TestAgent):\n')

    # Check print calls
    mock_iostream.print.assert_has_calls(
        [
            call(colored("TestSender", "yellow"), "(to", "TestAgent):\n", flush=True),
            call("\n", "-" * 80, flush=True, sep=""),
        ]
    )

    # Check queue put
    mock_queue.put.assert_called_once()
    queue_call_args = mock_queue.put.call_args[0][0]
    assert queue_call_args["index"] == 0
    assert "Tool message handled\n"  in queue_call_args["delta"]["content"]
    assert queue_call_args["finish_reason"] == "stop"


def test_streamed_print_received_message_tool_responses(mock_agent, mock_sender, mock_queue, mock_iostream):
    """Test streamed_print_received_message with tool responses"""
    message = {"tool_responses": [{"content": "Tool response 1"}, {"content": "Tool response 2"}]}
    with patch("fastapi_autogen_team.autogen_workflow_team.handle_tool_responses") as mock_handle_tool:
        mock_handle_tool.return_value = "Tool responses handled"
        streamed_print_received_message(mock_agent, message, mock_sender, mock_queue, 0)

        mock_handle_tool.assert_called_once_with(
            mock_agent, message, mock_sender, mock_queue, 0, mock_iostream, 'TestSender (to TestAgent):\n', *(), **{}
        )
    # Check print calls
    mock_iostream.print.assert_called_once_with(colored("TestSender", "yellow"), "(to", "TestAgent):\n", flush=True)
    # Check queue put
    assert mock_queue.put.call_count == 0


def test_handle_tool_responses_not_tool_role(mock_agent, mock_sender, mock_queue, mock_iostream):
    """Test handling tool responses when the message role is not tool"""
    message = {"tool_responses": [{"content": "Tool response 1"}], "role": "user"}
    with patch.object(mock_agent, "_print_received_message") as mock_print_received:
        result = handle_tool_responses(mock_agent, message, mock_sender, mock_queue, 0, mock_iostream, "")
        assert result == ""
        assert mock_queue.put.call_count == 1
        assert mock_print_received.call_count == 1


def test_handle_tool_responses_tool_role(mock_agent, mock_sender, mock_queue, mock_iostream):
    """Test handling tool responses when the message role is tool"""
    message = {"tool_responses": [{"content": "Tool response 1"}], "role": "tool"}
    with patch.object(mock_agent, "_print_received_message") as mock_print_received:
        result = handle_tool_responses(mock_agent, message, mock_sender, mock_queue, 0, mock_iostream, 'TestSender (to TestAgent):\n')
        assert result == ""
        assert mock_queue.put.call_count == 1
        assert mock_print_received.call_count == 1


def test_handle_regular_message_with_function_call(mock_iostream, mock_agent):
    """Test handling messages with function call"""
    message = {"content": "Hello", "function_call": {"name": "test_func", "arguments": "{}"}}
    with patch("fastapi_autogen_team.autogen_workflow_team.handle_suggested_function_call") as mock_handle_func:
        mock_handle_func.return_value = "Function call handled"
        result = handle_regular_message(mock_agent, message, mock_iostream, "Initial message")
        assert "Function call handled" in result
        mock_handle_func.assert_called_once_with(message["function_call"], mock_iostream, "Initial message")


def test_handle_regular_message_with_tool_calls(mock_iostream, mock_agent):
    """Test handling messages with tool calls"""
    message = {"content": "Hello", "tool_calls": [{"id": "1", "function": {"name": "test_tool", "arguments": "{}"}}]}
    with patch("fastapi_autogen_team.autogen_workflow_team.handle_suggested_tool_calls") as mock_handle_tool:
        mock_handle_tool.return_value = "Tool calls handled"
        result = handle_regular_message(mock_agent, message, mock_iostream, "Initial message")
        assert "Tool calls handled" in result
        mock_handle_tool.assert_called_once_with(message["tool_calls"], mock_iostream, "Initial message")