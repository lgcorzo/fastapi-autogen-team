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

SYSTEM_MESSAGE_MANAGER = "You are the manager of a research group; your role is to manage the team and ensure the project is completed successfully."


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
        )

        self.developer = AssistantAgent(
            name="Developer",
            max_consecutive_auto_reply=3,
            human_input_mode="NEVER",
            code_execution_config=False,
            llm_config=llm_config_used,
            system_message="You are an AI developer. Follow an approved plan and these guidelines:\n"
            "1. Write python/shell code to solve tasks. \n"
            "2. Wrap the code in a code block that specifies the script type. \n"
            "3. The user can't modify your code, so provide complete code.\n"
            "4. Print the specific code you want the executor to run.\n"
            "5. Don't include multiple code blocks in one response.\n"
            "6. Install libraries using: ```bash pip install module_name``` then send the full implementation code.\n"
            "7. Check the execution result and fix errors. \n"
            "8. Be concise; only state what is necessary.\n"
            "9. If you can't fix the error, analyze the problem, revisit assumptions, gather more info, and try a different approach.",
            description="Call this Agent to write code; don't call to execute code.",
        )

        self.planner = AssistantAgent(
            name="Planner",
            max_consecutive_auto_reply=3,
            human_input_mode="NEVER",
            code_execution_config=False,
            llm_config=llm_config_used,
            system_message="You are an AI Planner. Follow these guidelines:\n"
            "1. Create a 5-step plan to solve the task.\n"
            "2. Post-project review is not needed.\n"
            "3. Revise the plan based on feedback from admin and quality_assurance.\n"
            "4. Include team members for each step (e.g., Developer writes code, Executor executes code; exclude the admin).\n"
            "5. Be concise; only state what is necessary.\n"
            "6. Include an accurate answer to the user's request in the final message.",
            description="Call this Agent to build a plan; don't call to execute code.",
        )

        self.executor = UserProxyAgent(
            name="Executor",
            system_message="You are the code executor. Execute code and report the result. Read the developer's request and execute the required code.",
            human_input_mode="NEVER",
            code_execution_config={
                "last_n_messages": 20,
                "work_dir": "dream",
                "use_docker": True,
            },
            description="Call this Agent to execute code; don't call to modify code.",
        )

        self.quality_assurance = AssistantAgent(
            name="Quality_assurance",
            system_message="You are an AI Quality Assurance. Follow these instructions:\n"
            "1. Double-check the plan.\n"
            "2. Suggest resolutions for bugs or errors.\n"
            "3. If the task isn't solved, analyze the problem, revisit assumptions, gather more info, and suggest a different approach.",
            llm_config=llm_config_used,
        )
        
        self.rag_assurance = AssistantAgent(
            name="rag_assurance",
            system_message="You are an AI RAG assitant. Follow these instructions:\n"
            "1. Get information using the toll.\n"
            "2. summary the content of the reponse form the rag server.\n",
            llm_config=llm_config_used,
        )

        self.allowed_transitions = {
            self.user_proxy: [self.planner, self.quality_assurance, self.rag_assurance],
            self.rag_assurance: [self.planner, self.user_proxy],
            self.planner: [self.user_proxy, self.developer, self.quality_assurance],
            self.developer: [self.executor, self.quality_assurance, self.user_proxy],
            self.executor: [self.developer],
            self.quality_assurance: [self.planner, self.developer, self.executor, self.user_proxy],
        }

        self.group_chat_with_introductions = GroupChat(
            agents=[self.user_proxy, self.developer, self.planner, self.executor, self.quality_assurance, self.rag_assurance],
            allowed_or_disallowed_speaker_transitions=self.allowed_transitions,
            messages=[],
            speaker_transitions_type="allowed",
            max_round=10,
            send_introductions=True,
        )

        self.group_chat_manager_with_intros = GroupChatManager(
            groupchat=self.group_chat_with_introductions,
            llm_config=llm_config_used,
            system_message=SYSTEM_MESSAGE_MANAGER,
        )
        
        register_function(
        search,
        caller=self.rag_assurance,
        executor=self.user_proxy,
        name="search",
        description="A tool for searching the Azure AI search.",
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
                        "error": error_message,
                    }
                )
                self.queue.put("[DONE]")

            # Return a chat result with error information
            return ChatResult(
                chat_history=[{"role": "error", "content": f"System error occurred: {str(e)}", "error": error_message}],
                summary="Conversation failed due to system error",
                error=error_message,
            )
