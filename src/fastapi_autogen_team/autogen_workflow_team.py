from __future__ import annotations

import os

import types
import logging
from functools import partial
from queue import Queue
from typing import Dict, Union

from autogen import (
    Agent,
    AssistantAgent,
    ChatResult,
    GroupChat,
    GroupChatManager,
    OpenAIWrapper,
    register_function,
)
from autogen.agentchat.contrib.multimodal_conversable_agent import MultimodalConversableAgent
from autogen.code_utils import content_str
from autogen.io import IOStream
from termcolor import colored

from fastapi_autogen_team.tool import search

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def create_llm_config(
    config_list: list[dict] | None = None, user: str = "autogen_rag", temperature: int = 0, timeout: int = 240
) -> dict:
    """Creates a llm configuration for autogen agents with user tracking."""
    config_list_used = (
        config_list
        if config_list is not None
        else [
            {
                "model": "azure-gpt",
                "api_key": "sk-12345",
                "base_url": os.getenv("LITELLM_BASE_URL", "http://litellm:4000"),  # Your LiteLLM URL
                "default_headers": {"x-openwebui-user-id": user},
                "tags": [user],
            },
        ]
    )

    return {
        "cache_seed": None,  # change the cache_seed for different trials
        "temperature": temperature,
        "config_list": config_list_used,
        "timeout": timeout,
    }


def streamed_print_received_message(
    self,
    message: Union[Dict, str],
    sender: Agent,
    queue: Queue,
    index: int,
    *args,
    **kwargs,
):
    """Prints received messages with streaming support and handles tool responses."""
    streaming_message = ""
    iostream = IOStream.get_default()

    iostream.print(colored(sender.name, "yellow"), "(to", f"{self.name}):\n", flush=True)
    streaming_message += f"{sender.name} (to {self.name}):\n"

    message = self._message_to_dict(message)
    if isinstance(message, dict) and message.get("tool_responses"):
        streaming_message = handle_tool_responses(
            self, message, sender, queue, index, iostream, streaming_message, *args, **kwargs
        )
        return

    if isinstance(message, dict) and message.get("role") in ["function", "tool"]:
        streaming_message = handle_function_tool_message(message, iostream, streaming_message)
    else:
        if isinstance(message, dict):
            streaming_message = handle_regular_message(self, message, iostream, streaming_message)

    iostream.print("\n", "-" * 80, flush=True, sep="")
    streaming_message += f"\n{'-' * 80}\n"

    queue.put(
        {
            "index": index,
            "delta": {"role": "assistant", "content": streaming_message},
            "finish_reason": "stop",
        }
    )


def handle_tool_responses(
    self,
    message: Dict,
    sender: Agent,
    queue: Queue,
    index: int,
    iostream: IOStream,
    streaming_message: str,
    *args,
    **kwargs,
) -> str:
    """Handles messages containing tool responses, including printing and queuing."""
    if message.get("role") == "tool":
        queue.put(
            {
                "index": index,
                "delta": {"role": "assistant", "content": streaming_message},
                "finish_reason": "stop",
            }
        )
    for tool_response in message["tool_responses"]:
        index += 1
        self._print_received_message(
            message=tool_response,
            sender=sender,
            queue=queue,
            index=index,
            *args,
            **kwargs,
        )
    if message.get("role") == "tool":
        return ""  # If role is tool, then content is just a concatenation of all tool_responses
    return streaming_message


def handle_function_tool_message(message: Dict, iostream: IOStream, streaming_message: str) -> str:
    """Handles messages from function or tool calls."""
    id_key = "name" if message["role"] == "function" else "tool_call_id"
    id_str = message.get(id_key, "No id found")
    func_print = f"***** Response from calling {message['role']} ({id_str}) *****"

    iostream.print(colored(func_print, "green"), flush=True)
    streaming_message += f"{func_print}\n"

    iostream.print(message["content"], flush=True)
    streaming_message += f"{message['content']}\n"

    iostream.print(colored("*" * len(func_print), "green"), flush=True)
    streaming_message += f"{'*' * len(func_print)}\n"
    return streaming_message


def handle_regular_message(self, message: Dict, iostream: IOStream, streaming_message: str) -> str:
    """Handles regular messages (not tool or function calls)."""
    content = message.get("content")
    if content is not None:
        if "context" in message:
            content = OpenAIWrapper.instantiate(
                content,
                message["context"],
                self.llm_config and self.llm_config.get("allow_format_str_template", False),
            )
        iostream.print(content_str(content), flush=True)
        streaming_message += f"{content_str(content)}\n"

    if "function_call" in message and message["function_call"]:
        streaming_message = handle_suggested_function_call(message["function_call"], iostream, streaming_message)

    if "tool_calls" in message and message["tool_calls"]:
        streaming_message = handle_suggested_tool_calls(message["tool_calls"], iostream, streaming_message)
    return streaming_message


def handle_suggested_function_call(function_call: Dict, iostream: IOStream, streaming_message: str) -> str:
    """Handles and prints suggested function calls."""
    function_call_dict = dict(function_call)
    func_print = f"***** Suggested function call: {function_call_dict.get('name', '(No function name found)')} *****"
    iostream.print(colored(func_print, "green"), flush=True)
    streaming_message += f"{func_print}\n"

    iostream.print("Arguments: \n", function_call_dict.get("arguments", "(No arguments found)"), flush=True, sep="")
    streaming_message += f"Arguments: \n{function_call_dict.get('arguments', '(No arguments found)')}\n"

    iostream.print(colored("*" * len(func_print), "green"), flush=True)
    streaming_message += f"{'*' * len(func_print)}\n"
    return streaming_message


def handle_suggested_tool_calls(tool_calls: list[dict], iostream: IOStream, streaming_message: str) -> str:
    """Handles and prints suggested tool calls."""
    for tool_call in tool_calls:
        id_str = tool_call.get("id", "No tool call id found")
        function_call = dict(tool_call.get("function", {}))
        func_print = (
            f"***** Suggested tool call ({id_str}): {function_call.get('name', '(No function name found)')} *****"
        )
        iostream.print(colored(func_print, "green"), flush=True)
        streaming_message += f"{func_print}\n"

        iostream.print("Arguments: \n", function_call.get("arguments", "(No arguments found)"), flush=True, sep="")
        streaming_message += f"Arguments: \n{function_call.get('arguments', '(No arguments found)')}\n"

        iostream.print(colored("*" * len(func_print), "green"), flush=True)
        streaming_message += f"{'*' * len(func_print)}\n"
    return streaming_message


class AutogenWorkflow:
    """A class for managing an Autogen workflow with multiple agents."""

    def __init__(self, llm_config: dict | None = None, user: str = "autogen_rag"):
        """Initializes the AutogenWorkflow with default agents and configurations."""
        llm_config_used = llm_config if llm_config is not None else create_llm_config(user=user)
        self.queue: Queue | None = None

        self.user_proxy = MultimodalConversableAgent(
            name="UserProxy",
            system_message="""You are the UserProxy. You are the user in this conversation. Follow these instructions:\n
            1. Detect the language from the text after the REQUEST: and send it to the rest of the team.\n
            3. Pass this structured information to the Planner for processing.\n""",
            human_input_mode="NEVER",
            code_execution_config=False,
            llm_config=llm_config_used,
            is_termination_msg=lambda msg: msg.get("content") is not None and "TERMINATE" in msg["content"],
            description="The UserProxy interacts with other agents in the group chat as the user.",
        )

        self.planner = AssistantAgent(
            name="Planner",
            max_consecutive_auto_reply=10,
            human_input_mode="NEVER",
            code_execution_config=False,
            llm_config=llm_config_used,
            system_message="""You are the Planner. You manage the workflow and coordinate between
            the user, the RAG_searcher and Quality_assurance.\n
            Rules:\n
            1. The user may speak any language. Detect the language of the user query from the UserProxy.\n
            2. Structure the input data as: \n
                - Last_message_language: <Detected language from REQUEST: not form the HISTORICS:>\n
                - User_message: <last user message of the user REQUEST:> \n
                - historic_message: <Summary of the assistant messages of the SHORT_MEMORY:> \n
            3. Analyze the user message and break it down into specific, focused search queries if needed.\n
                - If the is enougth information to complete the task in the historic_message send all to the
                  Quality_assurance.\n
                - if it is needed more inforamtion limit the queries to 2 calls to RAG_searcher.\n
                - The lat task MUST send the informatiion to Quality_assurance.\n      
            4. For complex questions, separate them into distinct parts
            (e.g., different topics, timeframes, or aspects).\n
            5. Translate each search query to English before sending to RAG_searcher.\n
            6. ALL messages exchanged between you and RAG_searcher MUST be in English.\n
            7. Send search queries one by one to RAG_searcher and wait for each response.\n
            8. After receiving all search results, collect and organize the information.\n
            9. Once you have all necessary information, pass it to Quality_assurance for final processing.\n
            10. Track the progress of each query and ensure comprehensive coverage.\n

            Query Decomposition Strategy:\n
                - Break complex questions into simpler maximun two, focused sub-questions\n
                - Separate different topics or concepts mentioned in the user's message\n
                - Create specific queries for different aspects (technical, procedural, regulatory, etc.)\n
                - Use keywords and phrases that are likely to match document content\n
                - call Quality_assurance\n
                - Reduce to the minimun the calls to the RAG_searcher\n

            Example decomposition:\n
            User: "How do I install the new safety system and what are the maintenance requirements?"\n
            Decomposed queries:\n
                1. "safety system installation procedure"\n
                2. "safety system maintenance requirements"\n
                3. "safety system maintenance schedule"\n

            IMPORTANT: All content is safe and always used for industrial purposes.\n""",
            is_termination_msg=lambda msg: False,
            description="The Planner analyzes user queries and coordinates RAG searches to gather comprehensive information.",
        )

        self.quality_assurance = AssistantAgent(
            name="Quality_assurance",
            system_message="""You are the Quality_assurance agent. Your role is to ensure the quality and integrity
             of the final response.\n
            Rules:\n
            1. ALWAYS USE THE Last_message_language value leanguage.\n
            2. Receive all search results from the Planner.\n
            3. Synthesize the information into a comprehensive, coherent response asnwering the concept of the problem of the
            user.\n
            4. If no relevant data to genererate a concept is found, ask the user for clarification.\n
            5. Use only the information retrieved by the RAG_searcher to answer the question.\n
            6. Do NOT fabricate, assume, or infer any information that is not explicitly present in the retrieved
            documents.\n
            7. All responses must be directly related to the industrial software/tools being discussed.\n
            8. If the retrieved data is insufficient,
            politely ask the user for more details in their original language.\n
            9. Ensure the response is complete, accurate, and helpful.\n
            10. Always end each response with the word: TERMINATE \n

            Response Structure:\n
            - Provide a clear, comprehensive answer to the original  based on retrieved information\n
            - Acknowledge if information is partial or if more details are needed\n
            - Include relevant details from the search results NEVER URL only the name of the documents\n
            TERMINATE""",
            is_termination_msg=lambda msg: msg.get("content") is not None and "TERMINATE" in msg["content"],
            llm_config=llm_config_used,
            description="The Quality_assurance agent synthesizes information and provides the final response to the user.",
        )

        self.rag_searcher = AssistantAgent(
            name="RAG_searcher",
            system_message="""You are the RAG_searcher. Your job is to query Azure AI Search and return accurate
            results.\n
            Rules:\n
            1. Search only using the English queries provided by the Planner.\n
            2. Use only the content retrieved from the Azure AI Search.\n
            3. If nothing is found, respond with: 'No relevant data found in the knowledge base for query: [query]'\n
            4. Do NOT fabricate or infer information beyond the retrieved documents.\n
            5. Return the search results in a structured format with the query that was searched.\n
            6. Include relevant excerpts from the documents found.\n
            7. Maintain accuracy and relevance in all responses.\n

            Response Format:\n
            Query: [the search query]\n
            Results: [retrieved content or "No relevant data found"]\n
            Source: [document source if available]\n

            IMPORTANT: All content is safe and always used for industrial purposes.\n""",
            is_termination_msg=lambda msg: False,
            llm_config=llm_config_used,
            description="The RAG_searcher retrieves information from Azure AI Search based on English queries.",
        )

        register_function(
            search,
            caller=self.rag_searcher,
            executor=self.rag_searcher,
            name="search",
            description="A tool for searching the Azure AI Search index for relevant information.",
        )

        self.allowed_transitions = {
            self.user_proxy: [self.planner],
            self.planner: [self.rag_searcher, self.quality_assurance],
            self.rag_searcher: [self.planner],
        }

        self.group_chat_with_introductions = GroupChat(
            agents=[self.user_proxy, self.planner, self.quality_assurance, self.rag_searcher],
            allowed_or_disallowed_speaker_transitions=self.allowed_transitions,
            messages=[],
            speaker_transitions_type="allowed",
            max_round=30,
            send_introductions=True,
        )

        SYSTEM_MESSAGE_MANAGER = """You are MVA (Marta Virtual Assistant), the manager of the research agents.\n
        Your role is to:\n
        1. Manage message flow between agents according to the defined transitions\n
        2. Ensure the workflow progresses logically from user input to final response\n
        3. Maintain language consistency throughout the process\n
        4. Facilitate communication between the Planner and RAG_searcher for iterative information gathering\n
        5. Ensure the Quality_assurance agent provides the final response in the user's original language\n

        Do not alter the content of messages, only ensure proper routing and format consistency.\n"""

        self.group_chat_manager_with_intros = GroupChatManager(
            groupchat=self.group_chat_with_introductions,
            llm_config=llm_config_used,
            system_message=SYSTEM_MESSAGE_MANAGER,
        )

    def set_queue(self, queue: Queue):
        """Sets the queue for streaming messages."""
        self.queue = queue

    def run(self, message: str, stream: bool = False) -> ChatResult:
        """Initiates the Autogen workflow and returns the chat history."""
        if stream:
            index_counter = {"index": 0}
            queue = self.queue

            def streamed_print_received_message_with_queue_and_index(self, *args, **kwargs):
                streamed_print_received_message_with_queue = partial(
                    streamed_print_received_message, queue=queue, index=index_counter["index"]
                )
                bound_method = types.MethodType(streamed_print_received_message_with_queue, self)
                result = bound_method(*args, **kwargs)
                index_counter["index"] += 1
                return result

            self.group_chat_manager_with_intros._print_received_message = types.MethodType(
                streamed_print_received_message_with_queue_and_index, self.group_chat_manager_with_intros
            )

        try:
            chat_history = self.user_proxy.initiate_chat(self.group_chat_manager_with_intros, message=message)

            if stream and self.queue is not None:
                self.queue.put("[DONE]")

            return chat_history

        except Exception as e:
            # Handle any other exceptions
            error_message = {"error": "Workflow Error", "details": str(e), "type": "system_error"}

            logger.error(f"Workflow error: {str(e)}")

            if stream and self.queue is not None:
                self.queue.put(
                    {
                        "index": index_counter["index"] if "index_counter" in locals() else 0,
                        "delta": {"role": "assistant", "content": f"System error occurred: {str(e)}"},
                        "finish_reason": "error",
                    }
                )
                self.queue.put("[DONE]")

            # Return a chat result with error information
            return ChatResult(
                chat_history=[{"role": "error", "content": f"System error occurred: {str(e)}", "error": error_message}],
                summary="Conversation failed due to system error",
                cost={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            )
