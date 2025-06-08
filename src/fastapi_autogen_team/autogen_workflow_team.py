from __future__ import annotations

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
    UserProxyAgent,
    register_function
)
from autogen.code_utils import content_str
from autogen.io import IOStream
from termcolor import colored

from fastapi_autogen_team.tool import search

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


SYSTEM_MESSAGE_MANAGER = """
        You are KAI (Lantek Virtual Assistant), the manager of the research agents.
        Your role is to manage message flow and ensure the final response to the user
        is in the same language as the user's original query.
        Do not alter messages — only ensure correct format and language consistency.
        """

def create_llm_config(config_list: list[dict] | None = None, temperature: int = 0, timeout: int = 240) -> dict:
    """Creates a llm configuration for autogen agents."""
    config_list_used = (
        config_list
        if config_list is not None
        else [
            {
                "model": "azure-gpt",
                "api_key": "sk-12345",
                "base_url": "http://litellm:4000",  # Your LiteLLM URL
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

    def __init__(self, llm_config: dict | None = None):
        """Initializes the AutogenWorkflow with default agents and configurations."""
        llm_config_used = llm_config if llm_config is not None else create_llm_config()
        self.queue: Queue | None = None

        self.user_proxy = UserProxyAgent(
            name="UserProxy",
            system_message="You are the UserProxy. You are the user in this conversation.",
            human_input_mode="NEVER",
            code_execution_config=False,
            llm_config=llm_config_used,
            description="The UserProxy interacts with other agents in the group chat as the user.",
            is_termination_msg=lambda msg: msg.get("content") is not None
            and "TERMINATE" in msg["content"],
        )

        
        self.planner = AssistantAgent(
            name="Planner",
            max_consecutive_auto_reply=3,
            human_input_mode="NEVER",
            code_execution_config=False,
            llm_config=llm_config_used,
            system_message="""
            You are the Admin. You manage the workflow and coordinate between the user and the RAG_searcher.
            Rules:
            1. The user may speak any language. You must detect the language of the user query.
            2. You must translate the user message to English before sending it to RAG_searcher.
            3. ALL messages exchanged between you and RAG_searcher MUST be in English.
            4. The RAG_searcher can only respond based on retrieved content. It cannot fabricate information.
            5. If relevant data is found, summarize it and translate your final response back into the user’s original
            language before replying to the user.
            6. If no relevant data is found, ask the user for clarification in their original language.
            DO NOT speak to the user until you have processed results or need clarification.
            """,
            is_termination_msg=lambda msg: False,
            description="You are the planner prepare the  task to  get the usefull information.",
        )

        self.quality_assurance = AssistantAgent(
            name="Quality_assurance",
            system_message="You are an AI Quality Assurance. Follow these instructions:\n"
            "1. Make a summary of all the content and make easy to understant .\n"
            "2. Suggest resolutions for errors.\n"
            "3. Always end your final message with 'TERMINATE'.",
            is_termination_msg=lambda msg: msg.get("content") is not None
            and "TERMINATE" in msg["content"],
            llm_config=llm_config_used,
        )
        
        self.rag_assurance = AssistantAgent(
            name="rag_assurance",
            system_message="""
            You are the content controller. Your job is to query Azure AI Search and return results.
            Rules:
            1. Search only using the translated English query from user.
            2. Use only the content retrieved from the Azure AI Search.
            3. If nothing is found, respond with: 'No relevant data found in the knowledge base'
            4. Do NOT fabricate or infer information beyond the retrieved documents.
            5. Always end your final message with 'TERMINATE'.
            """,
           is_termination_msg=lambda msg: False,
            llm_config=llm_config_used,
        )
        
        register_function(
            search,
            caller=self.rag_assurance,
            executor=self.user_proxy,
            name="search",
            description="A tool for searching the Azure AI search.",
        )

        self.allowed_transitions = {
            self.user_proxy: [self.planner],
            self.planner: [self.rag_assurance],
            self.rag_assurance: [self.quality_assurance],
            self.quality_assurance: [self.user_proxy],
        }

        self.group_chat_with_introductions = GroupChat(
            agents=[self.user_proxy, self.planner, self.quality_assurance, self.rag_assurance],
            allowed_or_disallowed_speaker_transitions=self.allowed_transitions,
            messages=[],
            speaker_transitions_type="allowed",
            max_round=20,
            send_introductions=True,
        )

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
                        "finish_reason": "error"
                    }
                )
                self.queue.put("[DONE]")

            # Return a chat result with error information
            return ChatResult(
                chat_history=[{"role": "error", "content": f"System error occurred: {str(e)}", "error": error_message}],
                summary="Conversation failed due to system error"
            )
