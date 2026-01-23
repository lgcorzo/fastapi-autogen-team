import pytest
import asyncio
from unittest.mock import MagicMock, patch
from fastapi_autogen_team import tool

@pytest.mark.asyncio
async def test_safe_get_jira_results_leaks_exception():
    with patch("fastapi_autogen_team.tool.get_jira_results") as mock_get_jira_results:
        # Simulate an exception that contains sensitive internal information
        sensitive_info = "Connection failed to internal server 10.0.0.5:8080"
        mock_get_jira_results.side_effect = Exception(sensitive_info)

        # Call safe_get_jira_results
        result = await asyncio.to_thread(tool.safe_get_jira_results, "query")

        # Verify that the sensitive info is NOT leaked in the return value
        assert sensitive_info not in result
        assert result == "Error en Jira: An internal error occurred while retrieving results."

@pytest.mark.asyncio
async def test_safe_get_r2r_results_leaks_exception():
    with patch("fastapi_autogen_team.tool.get_r2r_results") as mock_get_r2r_results:
        # Simulate an exception that contains sensitive internal information
        sensitive_info = "Invalid credentials for user 'admin'"
        mock_get_r2r_results.side_effect = Exception(sensitive_info)

        # Call safe_get_r2r_results
        result = await asyncio.to_thread(tool.safe_get_r2r_results, "query")

        # Verify that the sensitive info is NOT leaked in the return value
        assert sensitive_info not in result
        assert result == "Error en R2R: An internal error occurred while retrieving results."
