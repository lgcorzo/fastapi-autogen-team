import pytest
import os
import asyncio
from unittest.mock import AsyncMock, patch
from fastapi_autogen_team import tool

@pytest.mark.asyncio
async def test_safe_get_r2r_results_no_leak():
    """Test that safe_get_r2r_results does not leak exception details."""
    with patch("fastapi_autogen_team.tool.get_r2r_results") as mock_get_r2r_results:
        # Simulate an exception with sensitive info
        sensitive_info = "Connection failed to https://user:secret@database.internal:5432"
        mock_get_r2r_results.side_effect = Exception(sensitive_info)

        result = tool.safe_get_r2r_results("test_query")

        # It should NOT contain the sensitive info
        assert sensitive_info not in result
        # It should return a generic error message
        assert "An internal error occurred" in result

@pytest.mark.asyncio
async def test_safe_get_jira_results_no_leak():
    """Test that safe_get_jira_results does not leak exception details."""
    with patch("fastapi_autogen_team.tool.get_jira_results") as mock_get_jira_results:
        # Simulate an exception with sensitive info
        sensitive_info = "Jira API Token 'secret-token' invalid"
        mock_get_jira_results.side_effect = Exception(sensitive_info)

        result = tool.safe_get_jira_results("test_query")

        # It should NOT contain the sensitive info
        assert sensitive_info not in result
        # It should return a generic error message
        assert "An internal error occurred" in result

@pytest.mark.asyncio
async def test_async_search_no_leak():
    """Test that async_search does not leak exception details from underlying tasks."""
    with (
        patch("fastapi_autogen_team.tool.safe_get_r2r_results") as mock_safe_r2r,
        patch("fastapi_autogen_team.tool.safe_get_jira_results") as mock_safe_jira,
    ):
        # Even if safe_get_* returns a safe string, async_search handles timeout/errors too.
        # But wait, async_search calls safe_get_*, so if safe_get_* catches exceptions,
        # async_search gets the return value.
        # However, asyncio.wait_for can raise TimeoutError or other errors if not caught inside safe_get_*.
        # safe_get_* catches Exception, so likely it returns a string.
        # But if we mock safe_get_* to raise an exception (which shouldn't happen but hypothetically):

        # Let's test the case where safe_get_* are mocked to raise an exception
        # (simulating an error in the wrapper itself or something unexpected).
        sensitive_info = "Critical failure in thread"
        mock_safe_r2r.side_effect = Exception(sensitive_info)
        mock_safe_jira.return_value = "jira_ok"

        # async_search calls safe_get_r2r_results via asyncio.to_thread
        # validation: async_search uses asyncio.gather(..., return_exceptions=True)

        # We need to mock asyncio.to_thread effectively or let it run.
        # Since we mock safe_get_r2r_results, to_thread will execute the mock.

        result = await tool.async_search("query")

        # result is a dict {"r2r": ..., "jira": ...}
        # In the current implementation:
        # r2r_result = results[0] if not isinstance(results[0], Exception) else f"R2R timeout/error: {results[0]}"

        # This will expose "Critical failure in thread"
        assert sensitive_info not in str(result["r2r"])
        assert "An internal error occurred" in str(result["r2r"])
