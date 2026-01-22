import pytest
from unittest.mock import patch
from fastapi_autogen_team import tool

def test_safe_get_r2r_results_no_leak_exception():
    """Test that safe_get_r2r_results does NOT leak the exception message."""
    with patch("fastapi_autogen_team.tool.get_r2r_results") as mock_get:
        sensitive_info = "Connection failed to 10.0.0.1 with user=admin pwd=secret"
        mock_get.side_effect = Exception(sensitive_info)

        result = tool.safe_get_r2r_results("query")

        # New behavior: generic message
        assert sensitive_info not in result
        assert "Ha ocurrido un error interno al consultar R2R" in result

def test_safe_get_jira_results_no_leak_exception():
    """Test that safe_get_jira_results does NOT leak the exception message."""
    with patch("fastapi_autogen_team.tool.get_jira_results") as mock_get:
        sensitive_info = "Jira API Error: 401 Unauthorized for user=jdoe token=xyz123"
        mock_get.side_effect = Exception(sensitive_info)

        result = tool.safe_get_jira_results("query")

        # New behavior: generic message
        assert sensitive_info not in result
        assert "Ha ocurrido un error interno al consultar Jira" in result
