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
