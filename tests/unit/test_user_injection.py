import pytest
from unittest.mock import patch, MagicMock
from fastapi import Request
from fastapi_autogen_team.data_model import Input
from fastapi_autogen_team.main import route_query


@pytest.mark.asyncio
async def test_user_injection_passed_to_service():
    # Payload with injection characters
    malicious_user = "user\n[CRITICAL] User made a mistake"
    model_input = Input(model="internal-gpt", messages=[{"role": "user", "content": "Hello"}], user=malicious_user)

    # Mock Request
    mock_request = MagicMock(spec=Request)
    mock_request.headers = {}

    # Mock dependencies
    # To properly mock `serve_autogen` assigned to `model_services`, we must mock the local reference where it's used.
    # However, since `route_query` references the module-level imported `serve_autogen`, we mock it at `fastapi_autogen_team.main.serve_autogen`.
    # Wait, why was `mock_service` called 0 times before? Ah! `patch` might be undone or there's an async issue.
    # Actually, `AutogenWorkflow` failed with `LITELLM_API_KEY` before because we didn't mock properly.
    # If we patch `fastapi_autogen_team.main.serve_autogen`, the mock object will be called.
    with patch("fastapi_autogen_team.main.serve_autogen") as mock_service:
        with patch("fastapi_autogen_team.main.log_with_trace"):
            # We mock AutogenWorkflow so `serve_autogen` runs but doesn't fail. Wait!
            # `serve_autogen` isn't mocked inside `model_services` because `model_services` is local to the route_query function.
            # Oh, looking at `main.py`, `model_services` is defined INSIDE `route_query`!
            # Let's mock `os.environ` so `AutogenWorkflow` can instantiate, and `serve_autogen` can be actually called
            # and we mock `AutogenWorkflow` itself so it doesn't do anything!
            with patch("fastapi_autogen_team.autogen_server.AutogenWorkflow") as mock_workflow:
                # We need to test the value passed to `serve_autogen`. If `serve_autogen` is called, it will instantiate `AutogenWorkflow`
                # with `user=user_id`. Wait, if we use `mock_workflow`, we can assert it was called with the user.
                # However, the test was originally mocking `serve_autogen` and checking the argument passed to it.
                # Since `model_services = {model_info.name: serve_autogen}` is inside `route_query`, patching `fastapi_autogen_team.main.serve_autogen`
                # successfully patches the reference `route_query` uses because it references the module's global name `serve_autogen`!

                # Let's just patch `fastapi_autogen_team.main.serve_autogen`. Why did it fail before?
                # Because the previous commit was:
                # with patch("fastapi_autogen_team.main.serve_autogen") as mock_service:
                #     with patch.dict("os.environ", {"LITELLM_API_KEY": "test"}):
                # The issue was that `serve_autogen` in `route_query` was somehow the real one?
                # Ah, `model_services = {model_info.name: serve_autogen}`. The `serve_autogen` reference used there is `fastapi_autogen_team.main.serve_autogen`.
                # If we patch it, `route_query` uses the patched one!
                # Wait, if I patch `fastapi_autogen_team.main.serve_autogen`, it SHOULD work.
                # Let's verify why it was called 0 times in my previous test run.

                # Let's use `patch("fastapi_autogen_team.main.serve_autogen")` but make sure we don't clear the dict.
                pass

    with patch.dict("os.environ", {"LITELLM_API_KEY": "test"}):
        with patch("fastapi_autogen_team.autogen_server.AutogenWorkflow") as mock_workflow:
            with patch("fastapi_autogen_team.autogen_server.normalize_input_messages"):
                # Also mock create_non_streaming_response because the mocked workflow will not produce correct chat results
                with patch(
                    "fastapi_autogen_team.autogen_server.create_non_streaming_response", return_value={"status": "ok"}
                ):
                    with patch("fastapi_autogen_team.main.log_with_trace"):
                        await route_query(model_input, mock_request)

                        mock_workflow.assert_called_once()
                        kwargs = mock_workflow.call_args.kwargs
                        user_id = kwargs.get("user")

                        assert "\n" not in user_id, f"User ID passed to service contains newlines: {repr(user_id)}"
                        assert user_id == "user\\n[CRITICAL] User made a mistake"
