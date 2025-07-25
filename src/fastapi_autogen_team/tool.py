import os
from r2r import R2RClient
import asyncio

from langchain_community.utilities.jira import JiraAPIWrapper
from langchain_community.agent_toolkits.jira.toolkit import JiraToolkit
from langchain.agents import initialize_agent, AgentType
from langchain_litellm import ChatLiteLLM


def search(query: str):
    return asyncio.run(async_search(query))


async def async_search(query: str):
    r2r_results = await get_r2r_results(query)
    jira_results = await get_jira_results(query)
    combined_results = {"r2r": r2r_results, "jira": jira_results}
    return combined_results


async def get_r2r_results(query: str):
    user = os.getenv("R2R_USER")
    pwd = os.getenv("R2R_PWD")
    base_url = os.getenv("R2R_URL", "http://r2r:7272")
    client = R2RClient(base_url=base_url)
    await client.users.login(user, pwd)  # Await the login call

    response = await client.retrieval.rag(
        query=query,
    )
    return response


async def get_jira_results(query: str):

    litellm_model = os.getenv("LITELLM_MODEL", "openai/azure-gpt")
    litellm_pwd = os.getenv("LITELLM_PWD","sk-12345")
    litellm_url = os.getenv("LITELLM_URL", "http://litellm:4000/")
    
    llm = ChatLiteLLM(model=litellm_model, api_base=litellm_url, api_key=litellm_pwd, temperature=0)

    # Inicializar herramientas Jira
    jira = JiraAPIWrapper()
    toolkit = JiraToolkit.from_jira_api_wrapper(jira)

    # Inicializar el agente LangChain
    agent = initialize_agent(toolkit.get_tools(), llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True)
    content = await agent.run(query)

    return content
