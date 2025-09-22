import os
import asyncio
import logging
from r2r import R2RClient
from langchain_community.utilities.jira import JiraAPIWrapper
from langchain_community.agent_toolkits.jira.toolkit import JiraToolkit
from langchain.agents import initialize_agent, AgentType
from langchain_litellm import ChatLiteLLM
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def search(query: str):
    """
    Esta función puede ser llamada directamente por un agente LLM como herramienta sincrónica.
    Internamente ejecuta en paralelo las tareas usando asyncio y to_thread.
    """
    try:
        # Ejecuta un nuevo event loop y espera a que termine
        return asyncio.run(async_search(query))
    except RuntimeError:
        # Si ya hay un event loop corriendo (p.ej., si se llama dentro de otro loop)
        # Usa el loop existente pero espera el resultado sincrónicamente
        logger.warning("Event loop ya en ejecución. Usando alternativa con create_task y threading.")
        result = []

        def runner():
            result.append(asyncio.run(async_search(query)))

        import threading

        t = threading.Thread(target=runner)
        t.start()
        t.join()
        return result[0]


async def async_search(query: str, timeout: float = 10.0):
    logger.info(f"Ejecutando búsqueda para: {query}")

    try:
        r2r_task = asyncio.to_thread(safe_get_r2r_results, query)
        jira_task = asyncio.to_thread(safe_get_jira_results, query)

        results = await asyncio.gather(
            asyncio.wait_for(r2r_task, timeout=timeout),
            asyncio.wait_for(jira_task, timeout=timeout),
            return_exceptions=True,  # evita que falle todo si una tarea da error/timeout
        )

        # Manejo de timeouts o errores
        r2r_result = results[0] if not isinstance(results[0], Exception) else f"R2R timeout/error: {results[0]}"
        jira_result = results[1] if not isinstance(results[1], Exception) else f"Jira timeout/error: {results[1]}"

        logger.info("Búsqueda completada")
        return {"r2r": r2r_result, "jira": jira_result}

    except Exception as e:
        logger.error(f"Error en async_search: {e}")
        return {"r2r": [], "jira": []}


def safe_get_r2r_results(query: str):
    try:
        return get_r2r_results(query)
    except Exception as e:
        logger.exception("Error al obtener resultados de R2R:")
        return f"Error en R2R: {e}"


def safe_get_jira_results(query: str):
    try:
        return get_jira_results(query)
    except Exception as e:
        logger.exception("Error al obtener resultados de Jira:")
        return f"Error en Jira: {e}"


def get_r2r_results(query: str):
    user = os.getenv("R2R_USER")
    pwd = os.getenv("R2R_PWD")
    base_url = os.getenv("R2R_URL", "http://r2r:7272")

    if not user or not pwd:
        raise ValueError("Faltan credenciales R2R (R2R_USER o R2R_PWD)")

    client = R2RClient(base_url=base_url)
    client.users.login(user, pwd)

    response = client.retrieval.rag(query=query)
    return response


def get_jira_results(query: str):
    litellm_model = os.getenv("LITELLM_MODEL", "openai/azure-gpt")
    litellm_pwd = os.getenv("LITELLM_PWD", "sk-12345")
    litellm_url = os.getenv("LITELLM_URL", "http://litellm:4000/")

    if not litellm_pwd:
        raise ValueError("Falta la clave LiteLLM (LITELLM_PWD)")

    llm = ChatLiteLLM(
        model=litellm_model,
        api_base=litellm_url,
        api_key=litellm_pwd,
        temperature=0,
    )

    jira = JiraAPIWrapper()
    toolkit = JiraToolkit.from_jira_api_wrapper(jira)

    agent = initialize_agent(toolkit.get_tools(), llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True)

    logger.info("Ejecutando consulta Jira con LLM...")
    result = agent.run(query)
    logger.info("Consulta Jira completada.")
    return result
