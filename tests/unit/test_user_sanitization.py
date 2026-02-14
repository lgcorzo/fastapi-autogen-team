import pytest
from unittest.mock import MagicMock, patch
from fastapi_autogen_team.autogen_server import serve_autogen
from fastapi_autogen_team.data_model import Input

@patch("fastapi_autogen_team.autogen_server.AutogenWorkflow")
def test_user_id_header_injection_mitigation(MockWorkflow):
    """
    Test that user input containing newlines (potential header injection)
    is sanitized before being passed to AutogenWorkflow.
    """
    # Setup mock
    mock_workflow_instance = MockWorkflow.return_value
    mock_workflow_instance.run.return_value = MagicMock(summary="Response")

    # User ID with potential header injection payload
    malicious_user = "user\nAuthentication: admin"

    # Input data
    input_data = Input(
        model="test-model",
        user=malicious_user,
        messages=[{"role": "user", "content": "Hello"}],
        stream=False
    )

    # Call the function
    try:
        serve_autogen(input_data)
    except Exception:
        pass

    # Check that AutogenWorkflow was initialized with sanitized user ID
    # sanitize_log_input replaces \n with \\n
    expected_user = "user\\nAuthentication: admin"

    # Assert that the user argument passed to AutogenWorkflow constructor was sanitized
    MockWorkflow.assert_called_with(user=expected_user)
