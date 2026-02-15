import pytest
import os
from unittest.mock import patch, MagicMock
from fastapi_autogen_team.data_model import Input
from fastapi_autogen_team.autogen_server import serve_autogen
from fastapi import HTTPException

# Set required environment variables for the test
@pytest.fixture(autouse=True)
def set_env_vars():
    with patch.dict(os.environ, {"LITELLM_API_KEY": "test-key"}):
        yield

@patch("fastapi_autogen_team.autogen_server.AutogenWorkflow")
def test_user_header_injection(MockWorkflow):
    # Setup mock
    mock_workflow_instance = MockWorkflow.return_value
    mock_workflow_instance.run.return_value = MagicMock(summary="Response", cost=None)

    # Malicious user input with CRLF injection
    malicious_user = "user\r\nLocation: malicious.com"
    input_data = Input(
        model="test-model", messages=[{"role": "user", "content": "Hello"}], user=malicious_user, stream=False
    )

    # Call the function
    try:
        serve_autogen(input_data)
    except HTTPException:
        # Ignore exception, we want to check the mock call
        pass

    # Check what user ID was passed to AutogenWorkflow
    MockWorkflow.assert_called_once()
    called_user = MockWorkflow.call_args.kwargs.get('user')

    # We assert that the user ID is sanitized (escaped backslashes)
    assert called_user == "user\\r\\nLocation: malicious.com", f"User ID was not sanitized! Got: {repr(called_user)}"

@patch("fastapi_autogen_team.autogen_server.AutogenWorkflow")
def test_user_log_injection_newline(MockWorkflow):
    mock_workflow_instance = MockWorkflow.return_value
    mock_workflow_instance.run.return_value = MagicMock(summary="Response", cost=None)

    malicious_user = "admin\nfake_log_entry"
    input_data = Input(
        model="test-model", messages=[{"role": "user", "content": "Hello"}], user=malicious_user, stream=False
    )

    try:
        serve_autogen(input_data)
    except HTTPException:
        pass

    MockWorkflow.assert_called_once()
    called_user = MockWorkflow.call_args.kwargs.get('user')

    assert called_user == "admin\\nfake_log_entry", f"User ID was not sanitized! Got: {repr(called_user)}"
