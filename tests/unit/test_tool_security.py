import pytest
import unittest.mock as mock
from fastapi_autogen_team import tool


@pytest.mark.asyncio
async def test_safe_get_r2r_results_leak_prevention():
    sensitive_info = "DB_PASSWORD=highly_secret"
    with mock.patch("fastapi_autogen_team.tool.get_r2r_results", side_effect=Exception(sensitive_info)):
        result = tool.safe_get_r2r_results("query")
        assert sensitive_info not in result
        assert "An internal error occurred" in result


@pytest.mark.asyncio
async def test_safe_get_jira_results_leak_prevention():
    sensitive_info = "JIRA_TOKEN=highly_secret"
    with mock.patch("fastapi_autogen_team.tool.get_jira_results", side_effect=Exception(sensitive_info)):
        result = tool.safe_get_jira_results("query")
        assert sensitive_info not in result
        assert "An internal error occurred" in result


@pytest.mark.asyncio
async def test_async_search_exception_handling_leak_prevention():
    # Mocking the internal results returned by gather
    with mock.patch("asyncio.to_thread"):
        # Simulate instances where to_thread itself might fail or return an exception if used with gather(return_exceptions=True)
        # But wait_for is what wraps to_thread in tool.py.

        with mock.patch("asyncio.gather", return_value=[Exception("Sensitive R2R"), Exception("Sensitive Jira")]):
            result = await tool.async_search("query")
            assert "Sensitive R2R" not in str(result["r2r"])
            assert "Sensitive Jira" not in str(result["jira"])
            assert "An error occurred" in result["r2r"]
            assert "An error occurred" in result["jira"]


@pytest.mark.asyncio
async def test_async_search_total_failure_leak_prevention():
    # Scenario where async_search itself hits the top level except block
    with mock.patch("asyncio.gather", side_effect=Exception("Major collapse with SECRET_KEY=abc")):
        result = await tool.async_search("query")
        assert "SECRET_KEY=abc" not in str(result["r2r"])
        assert "SECRET_KEY=abc" not in str(result["jira"])
        assert "An error occurred" in result["r2r"]
