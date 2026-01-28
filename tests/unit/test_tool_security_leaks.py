import pytest
from unittest.mock import patch
from fastapi_autogen_team import tool


@pytest.mark.asyncio
async def test_async_search_exception_leak():
    """Test that async_search does NOT leak sensitive exception details."""
    sensitive_error = "Connection failed: password=secret123"

    # We patch the inner functions that safe_get_* calls
    with (
        patch("fastapi_autogen_team.tool.get_r2r_results") as mock_get_r2r,
        patch("fastapi_autogen_team.tool.get_jira_results") as mock_get_jira,
    ):
        # Configure mocks to raise exceptions with sensitive info
        mock_get_r2r.side_effect = ValueError(f"R2R {sensitive_error}")
        mock_get_jira.side_effect = ValueError(f"Jira {sensitive_error}")

        # Run the search
        result = await tool.async_search("test query")

        r2r_res = result.get("r2r", "")
        jira_res = result.get("jira", "")

        # Verify NO leak
        assert sensitive_error not in str(r2r_res), f"R2R result leaked sensitive error details: {r2r_res}"
        assert sensitive_error not in str(jira_res), f"Jira result leaked sensitive error details: {jira_res}"
