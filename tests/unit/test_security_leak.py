import pytest
from unittest.mock import MagicMock, patch
from queue import Queue
from fastapi_autogen_team.autogen_workflow_team import AutogenWorkflow

def test_exception_leak_in_workflow_secured():
    """Test that exception details are NOT leaked in the workflow error response."""
    workflow = AutogenWorkflow()
    workflow.set_queue(MagicMock(spec=Queue))

    # Mock UserProxyAgent to raise an exception
    with patch.object(workflow.user_proxy, "initiate_chat", side_effect=Exception("SecretDBConnectionFailed: 127.0.0.1:5432")):
        # Run workflow with streaming enabled
        workflow.run("Test message", stream=True)

        # Check if the secret is leaked in the queue
        # The queue.put is called with a dict containing "delta" -> "content"

        # Get all calls to queue.put
        calls = workflow.queue.put.call_args_list

        found_leak = False
        found_generic_error = False

        for call_args in calls:
            arg = call_args[0][0]
            if isinstance(arg, dict) and "delta" in arg:
                content = arg["delta"].get("content", "")
                if "SecretDBConnectionFailed" in content:
                    found_leak = True
                if "An internal error occurred" in content:
                    found_generic_error = True

        assert not found_leak, "Exception details should NOT be leaked in the queue"
        assert found_generic_error, "Generic error message should be present in the queue"

def test_exception_leak_in_chat_result_secured():
    """Test that exception details are NOT leaked in the chat result."""
    workflow = AutogenWorkflow()

    # Mock UserProxyAgent to raise an exception
    with patch.object(workflow.user_proxy, "initiate_chat", side_effect=Exception("SecretDBConnectionFailed: 127.0.0.1:5432")):
        # Run workflow
        result = workflow.run("Test message", stream=False)

        # Check if the secret is leaked in the chat history
        found_leak = False
        found_generic_error = False

        for msg in result.chat_history:
            content = msg.get("content", "")
            if "SecretDBConnectionFailed" in content:
                found_leak = True
            if "An internal error occurred" in content:
                found_generic_error = True

        assert not found_leak, "Exception details should NOT be leaked in the chat result"
        assert found_generic_error, "Generic error message should be present in the chat result"
