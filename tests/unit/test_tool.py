import pytest
import os
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
        mock_client = MockR2RClient.return_value
        mock_client.users.login = AsyncMock()
        mock_client.retrieval.rag = AsyncMock(return_value={"key": "r2r_result"})

        result = await tool.get_r2r_results("test_query")  # Ensure this is awaited properly

        mock_client.users.login.assert_called_once()
        mock_client.retrieval.rag.assert_called_once_with(query="test_query")
        assert result == {"key": "r2r_result"}


@pytest.mark.asyncio
async def test_get_jira_results():
    with (
        patch("fastapi_autogen_team.tool.JiraAPIWrapper") as MockJiraAPIWrapper,
        patch("fastapi_autogen_team.tool.ChatLiteLLM") as MockChatLiteLLM,
        patch("fastapi_autogen_team.tool.initialize_agent") as MockInitializeAgent,
        patch("fastapi_autogen_team.tool.JiraToolkit") as MockJiraToolkit,
    ):
        # Simula entorno
        os.environ["JIRA_INSTANCE_URL"] = "http://example.jira.com"
        os.environ["JIRA_CLOUD"] = "true"
        os.environ["JIRA_API_TOKEN"] = "mock_token"
        os.environ["JIRA_USERNAME"] = "mock_user"

        os.environ["LITELLM_MODEL"] = "test_model"
        os.environ["LITELLM_PWD"] = "mock_pwd"
        os.environ["LITELLM_URL"] = "http://test:4000"

        # Mocks de clases
        mock_jira_wrapper = MagicMock()
        mock_toolkit = MagicMock()
        mock_tools = ["tool1", "tool2"]

        mock_llm = MagicMock()
        mock_agent = AsyncMock()
        mock_agent.run.return_value = "mock_result"

        # Configura lo que devuelven los mocks
        MockJiraAPIWrapper.return_value = mock_jira_wrapper
        MockJiraToolkit.from_jira_api_wrapper.return_value = mock_toolkit
        MockJiraToolkit.get_tools.return_value = mock_tools

        MockChatLiteLLM.return_value = mock_llm
        MockInitializeAgent.return_value = mock_agent

        # Ejecutar
        result = await tool.get_jira_results("test_query")

        # Verificaciones
        MockJiraAPIWrapper.assert_called_once()
        mock_toolkit.get_tools.assert_called_once()
        MockChatLiteLLM.assert_called_once_with(
            model="test_model", api_base="http://test:4000", api_key="mock_pwd", temperature=0
        )
        MockInitializeAgent.assert_called_once()
        mock_agent.run.assert_called_once_with("test_query")

        assert result == "mock_result"
