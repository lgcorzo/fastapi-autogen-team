import pytest
import os
from unittest.mock import MagicMock, patch
from queue import Queue
from fastapi import HTTPException
from fastapi_autogen_team.tool import search, get_r2r_results, get_jira_results
from fastapi_autogen_team.autogen_workflow_team import AutogenWorkflow
from fastapi_autogen_team.autogen_server import normalize_input_messages, generate_streaming_response, handle_response
from fastapi_autogen_team.data_model import Input, Message

# --- tool.py coverage ---


def test_search_already_running_loop():
    """Test the fallback mechanism when an event loop is already running."""
    # We simulate this by mocking asyncio.run to raise RuntimeError
    with patch("asyncio.run") as mock_run:
        # First call fails, second call (inside runner) succeeds
        mock_run.side_effect = [RuntimeError("loop already running"), {"r2r": "fallback_ok", "jira": "fallback_ok"}]
        with patch("threading.Thread") as mock_thread:
            # Mock thread to immediately execute target
            def side_effect(target, args=(), kwargs={}):
                target(*args, **kwargs)
                return MagicMock()

            mock_thread.side_effect = side_effect

            # This should trigger the fallback
            result = search("test query")
            assert result == {"r2r": "fallback_ok", "jira": "fallback_ok"}


@pytest.mark.asyncio
async def test_get_r2r_results_missing_creds():
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="Faltan credenciales R2R"):
            await get_r2r_results("query")


def test_get_jira_results_missing_creds():
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="Faltan credenciales Jira"):
            get_jira_results("query")


def test_get_jira_results_empty_list():
    with patch.dict(
        os.environ, {"JIRA_INSTANCE_URL": "http://jira", "JIRA_USERNAME": "user", "JIRA_API_TOKEN": "token"}
    ):
        with patch("fastapi_autogen_team.tool.Jira") as mock_jira_class:
            mock_jira = mock_jira_class.return_value
            mock_jira.jql.return_value = {"issues": []}
            result = get_jira_results("query")
            assert result == "No se encontraron resultados en Jira."


# --- autogen_workflow_team.py coverage ---


def test_handle_regular_message_with_context():
    from fastapi_autogen_team.autogen_workflow_team import handle_regular_message

    mock_agent = MagicMock()
    mock_agent.llm_config = {"allow_format_str_template": True}
    mock_agent.name = "Assistant"

    mock_iostream = MagicMock()

    message = {"content": "Hello {name}", "context": {"name": "User"}}

    with patch("fastapi_autogen_team.autogen_workflow_team.content_str", side_effect=lambda x: str(x)):
        res = handle_regular_message(mock_agent, message, mock_iostream, "")
        assert "Hello User" in res


@pytest.mark.asyncio
async def test_workflow_run_error_handling():
    with patch.dict(os.environ, {"LITELLM_API_KEY": "fake_key"}, clear=False):
        workflow = AutogenWorkflow(user="test_user")
        with patch.object(workflow.user_proxy, "initiate_chat", side_effect=Exception("Workflow Failure")):
            result = workflow.run("test", stream=False)
            assert result.summary == "Conversation failed due to system error"
            assert result.chat_history[0]["role"] == "error"


@pytest.mark.asyncio
async def test_workflow_run_stream_error():
    with patch.dict(os.environ, {"LITELLM_API_KEY": "fake_key"}, clear=False):
        workflow = AutogenWorkflow(user="test_user")
        queue = Queue()
        workflow.set_queue(queue)

        with patch.object(workflow.user_proxy, "initiate_chat", side_effect=Exception("Stream Failure")):
            workflow.run("test", stream=True)
            # Check if error message and [DONE] are in queue
            msgs = []
            while not queue.empty():
                msgs.append(queue.get())

            assert any(isinstance(m, dict) and m.get("finish_reason") == "error" for m in msgs)
            assert "[DONE]" in msgs


# --- autogen_server.py coverage ---


def test_normalize_input_messages_no_user():
    inp = Input(model="test", messages=[Message(role="system", content="sys")])
    prompt = normalize_input_messages(inp)
    assert "NO user message detected" in prompt


@pytest.mark.asyncio
async def test_generate_streaming_response_exception():
    queue = Queue()
    # Put a message that will cause serialization failure (e.g., circular reference)
    circular = {}
    circular["self"] = circular
    queue.put({"content": circular})

    gen = generate_streaming_response(Input(model="m", messages=[]), queue)

    with pytest.raises(HTTPException) as exc:
        # iterate the generator to trigger the loop
        list(gen)
    assert exc.value.status_code == 500


def test_handle_response_invalid_obj():
    with pytest.raises(HTTPException) as exc:
        handle_response("just a string")
    assert exc.value.status_code == 500


def test_handle_response_no_model_dump():
    class NoDump:
        pass

    with pytest.raises(HTTPException) as exc:
        handle_response(NoDump())
    assert exc.value.status_code == 500
