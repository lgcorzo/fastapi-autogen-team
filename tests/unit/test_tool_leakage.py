import pytest
from unittest.mock import patch
from fastapi_autogen_team import tool

SENSITIVE_ERROR = "Connection failed: user=admin password=secret"


@pytest.mark.asyncio
async def test_async_search_leak():
    # Patch get_r2r_results and get_jira_results to raise exceptions with sensitive info
    with (
        patch("fastapi_autogen_team.tool.get_r2r_results") as mock_r2r,
        patch("fastapi_autogen_team.tool.get_jira_results") as mock_jira,
    ):
        mock_r2r.side_effect = Exception(SENSITIVE_ERROR)
        mock_jira.side_effect = Exception(SENSITIVE_ERROR)

        # safe_get_r2r_results catches the exception and returns generic message

        results = await tool.async_search("test query")

        # Verify it DOES NOT leak
        assert SENSITIVE_ERROR not in results["r2r"]
        assert SENSITIVE_ERROR not in results["jira"]
        assert "An internal error occurred while searching R2R." in results["r2r"]
        assert "An internal error occurred while searching Jira." in results["jira"]
