from __future__ import annotations

import os
import types
from functools import partial
from queue import Queue
from typing import Union, Dict

from autogen.agentchat import AssistantAgent
from autogen import ChatResult, GroupChat, Agent, OpenAIWrapper, UserProxyAgent, GroupChatManager
from autogen.code_utils import content_str
from autogen.io import IOStream
from termcolor import colored

system_message_manager = "You are the manager of a research group your role is to manage the team and make sure the project is completed successfully."


def streamed_print_received_message(
        self,
        message: Union[Dict, str],
        sender: Agent,
        queue: Queue,
        index: int,
        *args,
        **kwargs,
):
    streaming_message = ""
    iostream = IOStream.get_default()
    # print the message received
    iostream.print(
        colored(sender.name, "yellow"), "(to", f"{self.name}):\n", flush=True
    )
    streaming_message += f"{sender.name} (to {self.name}):\n"
    message = self._message_to_dict(message)

    if message.get("tool_responses"):  # Handle tool multi-call responses
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
            return  # If role is tool, then content is just a concatenation of all tool_responses

    if message.get("role") in ["function", "tool"]:
        if message["role"] == "function":
            id_key = "name"
        else:
            id_key = "tool_call_id"
        id = message.get(id_key, "No id found")
        func_print = f"***** Response from calling {message['role']} ({id}) *****"
        iostream.print(colored(func_print, "green"), flush=True)
        streaming_message += f"{func_print}\n"
        iostream.print(message["content"], flush=True)
        streaming_message += f"{message['content']}\n"
        iostream.print(colored("*" * len(func_print), "green"), flush=True)
        streaming_message += f"{'*' * len(func_print)}\n"
    else:
        content = message.get("content")
        if content is not None:
            if "context" in message:
                content = OpenAIWrapper.instantiate(
                    content,
                    message["context"],
                    self.llm_config
                    and self.llm_config.get("allow_format_str_template", False),
                )
            iostream.print(content_str(content), flush=True)
            streaming_message += f"{content_str(content)}\n"
        if "function_call" in message and message["function_call"]:
            function_call = dict(message["function_call"])
            func_print = f"***** Suggested function call: {function_call.get('name', '(No function name found)')} *****"
            iostream.print(colored(func_print, "green"), flush=True)
            streaming_message += f"{func_print}\n"
            iostream.print(
                "Arguments: \n",
                function_call.get("arguments", "(No arguments found)"),
                flush=True,
                sep="",
            )
            streaming_message += f"Arguments: \n{function_call.get('arguments', '(No arguments found)')}\n"
            iostream.print(colored("*" * len(func_print), "green"), flush=True)
            streaming_message += f"{'*' * len(func_print)}\n"
        if "tool_calls" in message and message["tool_calls"]:
            for tool_call in message["tool_calls"]:
                id = tool_call.get("id", "No tool call id found")
                function_call = dict(tool_call.get("function", {}))
                func_print = f"***** Suggested tool call ({id}): {function_call.get('name', '(No function name found)')} *****"
                iostream.print(colored(func_print, "green"), flush=True)
                streaming_message += f"{func_print}\n"
                iostream.print(
                    "Arguments: \n",
                    function_call.get("arguments", "(No arguments found)"),
                    flush=True,
                    sep="",
                )
                streaming_message += f"Arguments: \n{function_call.get('arguments', '(No arguments found)')}\n"
                iostream.print(
                    colored("*" * len(func_print), "green"), flush=True)
                streaming_message += f"{'*' * len(func_print)}\n"

    iostream.print("\n", "-" * 80, flush=True, sep="")
    streaming_message += f"\n{'-' * 80}\n"
    queue.put(
        {
            "index": index,
            "delta": {"role": "assistant", "content": streaming_message},
            "finish_reason": "stop",
        }
    )


config_list_gpt4 = [
    {
        "model": "azure-gpt",
        "api_key": "sk-12345",
        "base_url": "http://litellm:4000",  # Your LiteLLM URL
    },
]

llm_config = {
    "cache_seed": 42,  # change the cache_seed for different trials
    "temperature": 0,
    "config_list": config_list_gpt4,
    "timeout": 240,
}


class AutogenWorkflow:
    def __init__(self):
        self.queue: Queue | None = None
        self.user_proxy = UserProxyAgent(
            name="UserProxy",
            system_message="You are the UserProxy. You are the user in this conversation.",
            human_input_mode="NEVER",
            code_execution_config=False,
            llm_config=llm_config,
            description="The UserProxy is the user in this conversation. They will be interacting with the other agents in the group chat.",
        )
        self.developer = AssistantAgent(
            name="Developer",
            max_consecutive_auto_reply=3,
            human_input_mode="NEVER",
            code_execution_config=False,
            llm_config=llm_config,
            system_message="""You are an AI developer. You follow an approved plan, follow these guidelines: 
            1. You write python/shell code to solve tasks. 
            2. Wrap the code in a code block that specifies the script type.   
            3. The user can't modify your code. So do not suggest incomplete code which requires others to modify.   
            4. You should print the specific code you would like the executor to run.
            5. Don't include multiple code blocks in one response.   
            6. If you need to import libraries, use ```bash pip install module_name```, please send a code block that installs these libraries and then send the script with the full implementation code 
            7. Check the execution result returned by the executor,  If the result indicates there is an error, fix the error and output the code again  
            8. Do not show appreciation in your responses, say only what is necessary.    
            9. If the error can't be fixed or if the task is not solved even after the code is executed successfully, analyze the problem, revisit your assumption, collect additional info you need, and think of a different approach to try.
            """,
            description="""Call this Agent if:   
            You need to write code.                  
            DO NOT CALL THIS AGENT IF:  
            You need to execute the code.""",

        )
        self.planner = AssistantAgent(
            name="Planner",
            max_consecutive_auto_reply=3,
            human_input_mode="NEVER",
            code_execution_config=False,
            llm_config=llm_config,
            system_message="""You are an AI Planner,  follow these guidelines: 
            1. Your plan should include 5 steps, you should provide a detailed plan to solve the task.
            2. Post project review isn't needed. 
            3. Revise the plan based on feedback from admin and quality_assurance.   
            4. The plan should include the various team members,  explain which step is performed by whom, for instance: the Developer should write code, the Executor should execute code, important do not include the admin in the tasks e.g ask the admin to research.  
            5. Do not show appreciation in your responses, say only what is necessary.  
            6. The final message should include an accurate answer to the user request
            """,
            description="""Call this Agent if:   
            You need to build a plan.               
            DO NOT CALL THIS AGENT IF:  
            You need to execute the code.""",
        )

        # User Proxy Agent - Executor
        self.executor = UserProxyAgent(
            name="Executor",
            system_message="1. You are the code executer. 2. Execute the code written by the developer and report the result.3. you should read the developer request and execute the required code",
            human_input_mode="NEVER",
            code_execution_config={
                "last_n_messages": 20,
                "work_dir": "dream",
                "use_docker": True,
            },
            description="""Call this Agent if:   
                You need to execute the code written by the developer.  
                You need to execute the last script.  
                You have an import issue.  
                DO NOT CALL THIS AGENT IF:  
                You need to modify code""",
        )
        self.quality_assurance = AssistantAgent(
            name="Quality_assurance",
            system_message="""You are an AI Quality Assurance. Follow these instructions:
            1. Double check the plan, 
            2. if there's a bug or error suggest a resolution
            3. If the task is not solved, analyze the problem, revisit your assumption, collect additional info you need, and think of a different approach.""",
            llm_config=llm_config,
        )

        self.allowed_transitions = {
            self.user_proxy: [self.planner, self.quality_assurance],
            self.planner: [self.user_proxy, self.developer, self.quality_assurance],
            self.developer: [self.executor, self.quality_assurance, self.user_proxy],
            self.executor: [self.developer],
            self.quality_assurance: [self.planner, self.developer, self.executor, self.user_proxy],
        }

        self.group_chat_with_introductions = GroupChat(
            agents=[
                self.user_proxy,
                self.developer,
                self.planner,
                self.executor,
                self.quality_assurance
            ],
            allowed_or_disallowed_speaker_transitions=self.allowed_transitions,
            messages=[],
            speaker_transitions_type="allowed",
            max_round=10,
            send_introductions=True,
        )
        self.group_chat_manager_with_intros = GroupChatManager(
            groupchat=self.group_chat_with_introductions,
            llm_config=llm_config,
            system_message=system_message_manager)

    def set_queue(self, queue: Queue):
        self.queue = queue

    def run(
            self,
            message: str,
            stream: bool = False,
    ) -> ChatResult:

        if stream:
            # currently this streams the entire chat history, but you may want to return only the last message or a
            # summary
            index_counter = {"index": 0}
            queue = self.queue

            def streamed_print_received_message_with_queue_and_index(
                    self, *args, **kwargs
            ):
                streamed_print_received_message_with_queue = partial(
                    streamed_print_received_message,
                    queue=queue,
                    index=index_counter["index"],
                )
                bound_method = types.MethodType(
                    streamed_print_received_message_with_queue, self
                )
                result = bound_method(*args, **kwargs)
                index_counter["index"] += 1
                return result

            self.group_chat_manager_with_intros._print_received_message = types.MethodType(
                streamed_print_received_message_with_queue_and_index,
                self.group_chat_manager_with_intros,
            )

        chat_history = self.user_proxy.initiate_chat(
            self.group_chat_manager_with_intros, message=message,
        )
        if stream:
            self.queue.put("[DONE]")
        # currently this returns the entire chat history, but you may want to return only the last message or a summary
        return chat_history
