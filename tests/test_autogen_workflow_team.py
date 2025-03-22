import pytest
from unittest.mock import MagicMock, patch
from queue import Queue
import types

from fastapi_autogen_team.autogen_workflow_team import (
    AutogenWorkflow,
    streamed_print_received_message,
    create_llm_config,
)
from autogen import UserProxyAgent, AssistantAgent, GroupChatManager


@pytest.fixture
def mock_agents():
    """Fixture to mock Autogen agents and configure AutogenWorkflow to use them."""
    with (
        patch("fastapi_autogen_team.autogen_workflow_team.UserProxyAgent", autospec=True) as MockUserProxyAgent,
        patch("fastapi_autogen_team.autogen_workflow_team.AssistantAgent", autospec=True) as MockAssistantAgent,
        patch("fastapi_autogen_team.autogen_workflow_team.GroupChatManager", autospec=True) as MockGroupChatManager,
        patch("fastapi_autogen_team.autogen_workflow_team.GroupChat", autospec=True) as MockGroupChat,
    ):
        user_proxy = MagicMock(spec=UserProxyAgent)
        developer = MagicMock(spec=AssistantAgent)
        planner = MagicMock(spec=AssistantAgent)
        executor = MagicMock(spec=UserProxyAgent)
        quality_assurance = MagicMock(spec=AssistantAgent)
        group_chat = MagicMock()
        group_chat_manager = MagicMock()

        MockUserProxyAgent.return_value = user_proxy
        MockAssistantAgent.return_value = developer
        # set side effects to return different mock agent for planner/QA agent
        MockAssistantAgent.side_effect = [developer, planner, quality_assurance]

        MockUserProxyAgent.side_effect = [user_proxy, executor]  # executor
        MockGroupChat.return_value = group_chat
        MockGroupChatManager.return_value = group_chat_manager

        # configure MockAutogenWorkflow to return the mocked agents
        def configure_mock_workflow(self):
            self.user_proxy = user_proxy
            self.developer = developer
            self.planner = planner
            self.executor = executor
            self.quality_assurance = quality_assurance
            self.group_chat_with_introductions = group_chat
            self.group_chat_manager_with_intros = group_chat_manager

        with patch.object(AutogenWorkflow, "__init__", new=configure_mock_workflow) as MockAutogenWorkflowInit:
            yield (
                user_proxy,
                developer,
                planner,
                executor,
                quality_assurance,
                group_chat,
                group_chat_manager,
                MockUserProxyAgent,
                MockAssistantAgent,
                MockGroupChatManager,
                MockGroupChat,
            )


def test_autogen_workflow_initialization(mock_agents):
    """Test AutogenWorkflow initializes agents correctly."""
    (
        user_proxy,
        developer,
        planner,
        executor,
        quality_assurance,
        group_chat,
        group_chat_manager,
        MockUserProxyAgent,
        MockAssistantAgent,
        MockGroupChatManager,
        MockGroupChat,
    ) = mock_agents

    workflow = AutogenWorkflow()

    assert workflow.user_proxy == user_proxy
    assert workflow.developer == developer
    assert workflow.planner == planner
    assert workflow.executor == executor
    assert workflow.quality_assurance == quality_assurance
    assert workflow.group_chat_with_introductions == group_chat
    assert workflow.group_chat_manager_with_intros == group_chat_manager


def test_autogen_workflow_set_queue():
    """Test that the set_queue method correctly sets the queue attribute."""
    workflow = AutogenWorkflow()
    mock_queue = MagicMock(spec=Queue)
    workflow.set_queue(mock_queue)
    assert workflow.queue == mock_queue


def test_autogen_workflow_run_streaming(mock_agents):
    """Test the run method in streaming mode."""
    (
        user_proxy,
        developer,
        planner,
        executor,
        quality_assurance,
        group_chat,
        group_chat_manager,
        MockUserProxyAgent,
        MockAssistantAgent,
        MockGroupChatManager,
        MockGroupChat,
    ) = mock_agents

    workflow = AutogenWorkflow()
    mock_queue = MagicMock(spec=Queue)
    workflow.set_queue(mock_queue)
    message = "Hello, Autogen!"

    workflow.run(message=message, stream=True)

    user_proxy.initiate_chat.assert_called_once_with(workflow.group_chat_manager_with_intros, message=message)
    mock_queue.put.assert_called_with("[DONE]")


def test_autogen_workflow_run_non_streaming(mock_agents):
    """Test the run method in non-streaming mode."""
    (
        user_proxy,
        developer,
        planner,
        executor,
        quality_assurance,
        group_chat,
        group_chat_manager,
        MockUserProxyAgent,
        MockAssistantAgent,
        MockGroupChatManager,
        MockGroupChat,
    ) = mock_agents
    workflow = AutogenWorkflow()
    message = "Hello, Autogen!"
    workflow.run(message=message, stream=False)
    user_proxy.initiate_chat.assert_called_once_with(workflow.group_chat_manager_with_intros, message=message)


def test_create_llm_config_default():
    """Test create_llm_config with default parameters."""
    config = create_llm_config()
    assert config["temperature"] == 0
    assert config["timeout"] == 240
    assert isinstance(config["config_list"], list)


def test_create_llm_config_custom():
    """Test create_llm_config with custom parameters."""
    custom_config_list = [{"model": "test_model"}]
    config = create_llm_config(config_list=custom_config_list, temperature=0.5, timeout=120)
    assert config["temperature"] == 0.5
    assert config["timeout"] == 120
    assert config["config_list"] == custom_config_list


def test_streamed_print_received_message(mock_agents, capsys):
    """Test streamed_print_received_message function."""
    (
        user_proxy,
        developer,
        planner,
        executor,
        quality_assurance,
        group_chat,
        group_chat_manager,
        MockUserProxyAgent,
        MockAssistantAgent,
        MockGroupChatManager,
        MockGroupChat,
    ) = mock_agents
    workflow = AutogenWorkflow()
    mock_queue = MagicMock(spec=Queue)
    message = {"role": "assistant", "content": "Test message"}
    index = 0

    # Mock the necessary attributes and methods
    group_chat_manager = MagicMock()
    group_chat_manager._message_to_dict.return_value = message
    group_chat_manager.llm_config = {}
    group_chat_manager._print_received_message = types.MethodType(streamed_print_received_message, group_chat_manager)

    streamed_print_received_message(group_chat_manager, message, user_proxy, mock_queue, index)

    mock_queue.put.assert_called()
    captured = capsys.readouterr()
    assert "Test message" in captured.out
