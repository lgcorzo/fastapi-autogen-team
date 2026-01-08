import json
import logging
import uuid
import time
from queue import Queue
from threading import Thread

from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from fastapi_autogen_team.autogen_workflow_team import AutogenWorkflow
from fastapi_autogen_team.data_model import Input, Output

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

EMPTY_USAGE = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}


def handle_response(response: Output) -> dict:
    """Validates and processes the response object."""
    if isinstance(response, str):
        raise HTTPException(status_code=500, detail=f"Unexpected string response: {response}")

    if not hasattr(response, "model_dump"):
        raise HTTPException(status_code=500, detail=f"Response object missing 'model_dump' method: {type(response)}")

    try:
        return response.model_dump()
    except Exception as e:
        logger.error(f"Failed to serialize response: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Serialization error: {e}") from e


def normalize_input_messages(inp: Input) -> str:
    """Normalizes the input messages."""
    model_dump = inp.model_dump()
    model_messages = model_dump["messages"]

    # Normalizamos los mensajes en bloques de texto plano
    normalized_messages = []
    for m in model_messages:
        if m["role"] not in ("user", "assistant", "system"):
            continue
        if isinstance(m["content"], list):
            content_blocks = m["content"]
        elif isinstance(m["content"], str):
            content_blocks = [{"type": "text", "text": m["content"]}]
        else:
            content_blocks = [m["content"]]

        for c in content_blocks:
            if c.get("type") == "text":
                normalized_messages.append({"role": m["role"].capitalize(), "text": c["text"]})

    # Extraer mensajes según rol
    system_messages = [m for m in normalized_messages if m["role"] == "System"]
    user_messages = [m for m in normalized_messages if m["role"] == "User"]

    if not user_messages:
        full_prompt = (
            "'SHORT_MEMORY':{\n NO user message detected, finish the workflow  \n},\n'REQUEST':{\n TERMINATE \n}"
        )

        return full_prompt

    last_user_index = max(i for i, m in enumerate(normalized_messages) if m["role"] == "User")
    last_message = normalized_messages[last_user_index]
    historic_messages = normalized_messages[:last_user_index]

    # Construcción del prompt final
    short_memory = "\n".join(f"{m['role']}: {m['text']}" for m in historic_messages if m["role"] != "System")

    system_message = "\n".join(f"{m['role']}: {m['text']}" for m in system_messages if m["role"] != "System")
    request = f"{last_message['role']}: {last_message['text']}"

    full_prompt = (
        "'SYSTEM_INFO':{\n" + system_message + "\n},\n"
        "'SHORT_MEMORY':{\n" + short_memory + "\n},\n"
        "'REQUEST':{\n" + request + "\n}"
    )

    return full_prompt


def serve_autogen(inp: Input) -> StreamingResponse | dict:
    """Serves the autogen workflow based on the input (streaming or non-streaming)."""
    try:
        user_id = str(inp.user)
        workflow = AutogenWorkflow(user=user_id)
        norm_message = normalize_input_messages(inp)

        if inp.stream:
            queue: Queue = Queue()
            workflow.set_queue(queue)
            Thread(target=workflow.run, args=(norm_message, inp.stream)).start()
            return StreamingResponse(generate_streaming_response(inp, queue), media_type="text/event-stream")
        else:
            result = workflow.run(message=str(norm_message), stream=False)
            # handle generator output
            if hasattr(result, "__next__"):
                result = next(result)

            response_data = create_non_streaming_response(result, inp.model)
            return response_data

    except Exception as e:
        logger.error(f"Error processing Autogen request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Autogen processing error: {e}") from e


def generate_streaming_response(inp: Input, queue: Queue):
    """Generates a streaming response from the message queue."""
    try:
        while True:
            message = queue.get()
            if message == "[DONE]":
                yield "data: [DONE]\n\n"
                break

            chunk = Output(
                id=str(uuid.uuid4()),
                object="chat.completion.chunk",
                choices=[message],
                usage=EMPTY_USAGE,
                model=inp.model,
            )
            yield f"data: {json.dumps(handle_response(chunk))}\n\n"
            queue.task_done()
    except Exception as e:
        logger.error(f"Streaming response failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Streaming error: {e}") from e


def create_non_streaming_response(chat_results, model: str):
    """Creates a non-streaming response from the chat results."""
    try:
        if chat_results:
            choices = [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": chat_results.summary,
                    },
                    "finish_reason": "stop",
                }
            ]
            output = Output(
                id=str(uuid.uuid4()),
                choices=choices,
                created=int(time.time()),
                usage=getattr(chat_results, "cost", None) or EMPTY_USAGE,
                object="chat.completion",
                model=model,
            )
        else:
            choices = [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Sorry, I am unable to assist with that request at this time.",
                    },
                    "finish_reason": "stop",
                    "logprobs": None,
                }
            ]
            output = Output(
                id=str(uuid.uuid4()),
                choices=choices,
                created=int(time.time()),
                usage=EMPTY_USAGE,
                object="chat.completion",
                model=model,
            )

        return handle_response(output)
    except Exception as e:
        logger.error(f"Failed to create non-streaming response: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Response creation error: {e}") from e
