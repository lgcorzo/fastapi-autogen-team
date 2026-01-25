import pytest
import asyncio
from unittest.mock import patch
from fastapi_autogen_team import tool

@pytest.mark.asyncio
async def test_tool_exception_leak_jira():
    sensitive_info = "Connection failed to http://user:secretpass@jira.internal"
    with patch("fastapi_autogen_team.tool.get_jira_results") as mock_get:
        mock_get.side_effect = Exception(sensitive_info)

        # Call the safe wrapper via thread as it is done in async_search
        result = await asyncio.to_thread(tool.safe_get_jira_results, "query")

        # New secure behavior
        assert sensitive_info not in result, "Sensitive info leaked!"
        assert "An internal error occurred" in result

@pytest.mark.asyncio
async def test_tool_exception_leak_r2r():
    sensitive_info = "R2R internal error: partial key sk-12345 leaked"
    with patch("fastapi_autogen_team.tool.get_r2r_results") as mock_get:
        mock_get.side_effect = Exception(sensitive_info)

        result = await asyncio.to_thread(tool.safe_get_r2r_results, "query")

        # New secure behavior
        assert sensitive_info not in result, "Sensitive info leaked!"
        assert "An internal error occurred" in result

@pytest.mark.asyncio
async def test_async_search_leak():
    # Test leak prevention in async_search when tasks fail (e.g. timeout)
    sensitive_info = "Timeout connecting to DB 192.168.1.50"

    with patch("fastapi_autogen_team.tool.safe_get_r2r_results") as mock_r2r, \
         patch("fastapi_autogen_team.tool.safe_get_jira_results") as mock_jira:

        # Make one fail with an exception
        mock_r2r.side_effect = Exception(sensitive_info)
        mock_jira.return_value = "ok"

        result = await tool.async_search("query")

        assert sensitive_info not in str(result)
        assert "An internal error occurred" in result["r2r"]
