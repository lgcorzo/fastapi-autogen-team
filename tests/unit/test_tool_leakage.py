import pytest
import os
import asyncio
from unittest.mock import AsyncMock, patch
from fastapi_autogen_team import tool


@pytest.mark.asyncio
async def test_async_search_leakage():
    with (
        patch("fastapi_autogen_team.tool.get_r2r_results", side_effect=ValueError("SECRET_DB_PASSWORD")),
        patch("fastapi_autogen_team.tool.get_jira_results", side_effect=ValueError("SECRET_API_KEY")),
    ):
        # Call the function
        result = await tool.async_search("test_query")

        # Check that secrets are NOT leaked
        assert "SECRET_DB_PASSWORD" not in str(result["r2r"])
        assert "SECRET_API_KEY" not in str(result["jira"])

        # Check that generic error messages are returned
        assert "An internal error occurred" in result["r2r"]
        assert "An internal error occurred" in result["jira"]
