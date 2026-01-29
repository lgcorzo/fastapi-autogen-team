import pytest
from unittest.mock import patch, AsyncMock
from fastapi_autogen_team import tool

SENSITIVE_ERROR = "Connection failed: password=supersecret host=internal-db"


def test_safe_get_r2r_results_leak():
    """Test that safe_get_r2r_results does NOT leak sensitive exception details."""
    with patch("fastapi_autogen_team.tool.get_r2r_results") as mock_get:
        mock_get.side_effect = ValueError(SENSITIVE_ERROR)

        result = tool.safe_get_r2r_results("query")

        # Should return a generic error, not the sensitive one
        assert SENSITIVE_ERROR not in result
        assert "An internal error occurred" in result or "Error" in result  # Adjust based on implementation plan


def test_safe_get_jira_results_leak():
    """Test that safe_get_jira_results does NOT leak sensitive exception details."""
    with patch("fastapi_autogen_team.tool.get_jira_results") as mock_get:
        mock_get.side_effect = ValueError(SENSITIVE_ERROR)

        result = tool.safe_get_jira_results("query")

        # Should return a generic error, not the sensitive one
        assert SENSITIVE_ERROR not in result
        assert "An internal error occurred" in result or "Error" in result


@pytest.mark.asyncio
async def test_async_search_leak():
    """Test that async_search does NOT leak sensitive details when sub-tasks fail."""
    # We mock asyncio.gather to return exceptions or use side_effect on the safe functions if we want to test the gathering logic.
    # Actually, async_search calls safe_get_*, so if those are fixed, this might be fixed too,
    # but async_search also has logic to handle exceptions returned by gather if return_exceptions=True.

    # Let's mock the safe functions to return the sensitive error directly (simulating if they WEREN'T safe or if something else failed)
    # OR we can mock them to RAISE an exception if we want to test the try/except block in async_search (though async_search calls them via to_thread)

    # Wait, async_search logic is:
    # results = await asyncio.gather(..., return_exceptions=True)
    # r2r_result = results[0] if not isinstance(results[0], Exception) else f"R2R timeout/error: {results[0]}"

    # If safe_get_r2r_results raises an exception (which it shouldn't if it's safe, but let's say it does or timeout happens),
    # then results[0] will be an Exception object.
    # The code then does f"... {results[0]}", which calls str(exception), potentially leaking info.

    # So we need to test that path too.

    with (
        patch("fastapi_autogen_team.tool.safe_get_r2r_results") as mock_r2r,
        patch("fastapi_autogen_team.tool.safe_get_jira_results") as mock_jira,
    ):
        # Simulate them raising an exception (e.g. timeout or unexpected error not caught inside them)
        mock_r2r.side_effect = ValueError(SENSITIVE_ERROR)
        mock_jira.return_value = "jira ok"

        # We need to ensure asyncio.gather catches it.
        # But wait, to_thread runs them in a separate thread. If they raise, the await gets the exception.

        result = await tool.async_search("query")

        # Check r2r result
        r2r_res = result["r2r"]
        assert SENSITIVE_ERROR not in str(r2r_res)
        assert "An internal error occurred" in str(r2r_res) or "timeout/error" in str(r2r_res)
