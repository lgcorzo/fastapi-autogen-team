import pytest
import os
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi_autogen_team import tool


@pytest.mark.asyncio
async def test_async_search():
    with (
        patch("fastapi_autogen_team.tool.get_r2r_results", new_callable=AsyncMock) as mock_get_r2r_results,
        patch("fastapi_autogen_team.tool.get_jira_results", new_callable=AsyncMock) as mock_get_jira_results,
    ):
        mock_get_r2r_results.return_value = {"key": "r2r_result"}
        mock_get_jira_results.return_value = "jira_result"

        await tool.async_search("test_query")

        mock_get_r2r_results.assert_called_once_with("test_query")
        mock_get_jira_results.assert_called_once_with("test_query")


@pytest.mark.asyncio
async def test_get_r2r_results():
    with patch("fastapi_autogen_team.tool.R2RClient") as MockR2RClient:
        os.environ["R2R_USER"] = "test_user"
        os.environ["R2R_PWD"] = "mock_pwd"
        os.environ["R2R_URL"] = "http://test:7272"
        mock_client = MockR2RClient.return_value
        mock_client.users.login = AsyncMock()
        mock_client.retrieval.rag = AsyncMock(return_value={"key": "r2r_result"})

        result = await tool.get_r2r_results("test_query")  # Ensure this is awaited properly

        mock_client.users.login.assert_called_once()
        mock_client.retrieval.rag.assert_called_once_with(query="test_query")
        assert result == {"key": "r2r_result"}


@pytest.mark.asyncio
async def test_get_jira_results():
    with patch("fastapi_autogen_team.tool.Jira") as MockJira:
        # Simula entorno
        os.environ["JIRA_INSTANCE_URL"] = "http://example.jira.com"
        os.environ["JIRA_USERNAME"] = "mock_user"
        os.environ["JIRA_API_TOKEN"] = "mock_token"
        os.environ["JIRA_CLOUD"] = "true"

        # Mock de la clase Jira
        mock_jira_instance = MagicMock()
        MockJira.return_value = mock_jira_instance

        # Mock del resultado de jql
        mock_jira_instance.jql.return_value = {
            "issues": [
                {"key": "PROJ-1", "fields": {"summary": "Issue summary 1"}},
                {"key": "PROJ-2", "fields": {"summary": "Issue summary 2"}},
            ]
        }

        # Ejecutar
        result = await asyncio.to_thread(tool.get_jira_results, "test_query")

        # Verificaciones
        MockJira.assert_called_once_with(
            url="http://example.jira.com",
            username="mock_user",
            password="mock_token",
            cloud=True,
        )
        mock_jira_instance.jql.assert_called_once()
        assert "[PROJ-1] Issue summary 1" in result
        assert "[PROJ-2] Issue summary 2" in result


@pytest.mark.asyncio
async def test_get_jira_results_no_results():
    with patch("fastapi_autogen_team.tool.Jira") as MockJira:
        # Simula entorno
        os.environ["JIRA_INSTANCE_URL"] = "http://example.jira.com"
        os.environ["JIRA_USERNAME"] = "mock_user"
        os.environ["JIRA_API_TOKEN"] = "mock_token"

        mock_jira_instance = MagicMock()
        MockJira.return_value = mock_jira_instance
        mock_jira_instance.jql.return_value = {"issues": []}

        result = await asyncio.to_thread(tool.get_jira_results, "test_query")

        assert result == "No se encontraron resultados en Jira."


@pytest.mark.asyncio
async def test_async_search_exception_leak():
    """
    Test that async_search does NOT leak raw exception details in the result.
    It should return a generic error message instead of 'R2R timeout/error: ...' with the exception string.
    """
    sensitive_error_msg = "Connection failed to 192.168.1.5 with password=secret"

    with patch("fastapi_autogen_team.tool.get_r2r_results") as mock_get:
        mock_get.side_effect = ValueError(sensitive_error_msg)

        result = await tool.async_search("test")

        # Check r2r result
        r2r_res = result["r2r"]

        # Assertions for SAFE code:
        assert sensitive_error_msg not in r2r_res, "Vulnerability detected: Sensitive error message leaked!"
        assert "An internal error occurred" in r2r_res, "Generic error message not found"


@pytest.mark.asyncio
async def test_async_search_timeout_exception_leak():
    """
    Test that async_search does NOT leak exception details if asyncio.gather returns an exception
    (e.g. from wait_for timeout or other unhandled exception in the thread).
    """
    sensitive_error_msg = "Timeout contacting 10.0.0.1"

    with patch("fastapi_autogen_team.tool.asyncio.wait_for") as mock_wait_for:
        # Mock wait_for to raise an exception for the first call (r2r)
        mock_wait_for.side_effect = [ValueError(sensitive_error_msg), "jira_result"]

        result = await tool.async_search("test")

        r2r_res = result["r2r"]

        # Assertions for SAFE code:
        assert (
            sensitive_error_msg not in r2r_res
        ), "Vulnerability detected in timeout case: Sensitive error message leaked!"
        assert "An internal error occurred" in r2r_res, "Generic error message not found in timeout case"
