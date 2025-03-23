import json
import logging
import uuid
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


def serve_autogen(inp: Input) -> StreamingResponse | dict:
    """Serves the autogen workflow based on the input (streaming or non-streaming)."""
    try:
        model_dump = inp.model_dump()
        model_messages = model_dump["messages"]
        workflow = AutogenWorkflow()
        last_message = model_messages[-1]

        if inp.stream:
            queue: Queue = Queue()
            workflow.set_queue(queue)
            Thread(target=workflow.run, args=(last_message, inp.stream)).start()
            return StreamingResponse(generate_streaming_response(inp, queue), media_type="text/event-stream")
        else:
            chat_results = workflow.run(message=str(last_message), stream=inp.stream)
            return create_non_streaming_response(chat_results, inp.model)

    except Exception as e:
        logger.error(f"Error processing Autogen request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Autogen processing error: {e}") from e


def generate_streaming_response(inp: Input, queue: Queue):
    """Generates a streaming response from the message queue."""
    try:
        while True:
            message = queue.get()
            if message == "[DONE]":
                yield " [DONE]\n\n"
                break

            chunk = Output(
                id=str(uuid.uuid4()),
                object="chat.completion.chunk",
                choices=[message],
                usage=EMPTY_USAGE,
                model=inp.model,
            )
            yield f" {json.dumps(handle_response(chunk))}\n\n"
            queue.task_done()
    except Exception as e:
        logger.error(f"Streaming response failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Streaming error: {e}") from e


def create_non_streaming_response(chat_results, model: str) -> dict:
    """Creates a non-streaming response from the chat results."""
    try:
        if chat_results:
            choices = [
                {"index": i, "message": msg, "finish_reason": "stop"} for i, msg in enumerate(chat_results.chat_history)
            ]
            output = Output(id=str(chat_results.chat_id), choices=choices, usage=chat_results.cost, model=model)
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
            output = Output(id="None", choices=choices, usage=EMPTY_USAGE, model=model)

        return handle_response(output)
    except Exception as e:
        logger.error(f"Failed to create non-streaming response: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Response creation error: {e}") from e
