import json
import traceback
import uuid
from queue import Queue
from threading import Thread

from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from fastapi_autogen_team.autogen_workflow_team import AutogenWorkflow
from fastapi_autogen_team.data_model import Input, Output

empty_usage = {
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "total_tokens": 0,
}

def handle_response(response):
    """
    Validates and processes the response object, ensuring it's of the expected type and has the required attributes.
    """
    try:
        # Validate that response is not a string
        if isinstance(response, str):
            raise ValueError(
                f"Unexpected error: Received a string instead of a valid object. Response: {response}"
            )
        
        # Validate that the object has the `model_dump` method
        if not hasattr(response, "model_dump"):
            raise AttributeError(
                f"Received object does not have the 'model_dump' method. Type: {type(response)}"
            )
        
        # Call `model_dump` if all validations pass
        return response.model_dump()
    except Exception as e:
        # Log the error and raise an HTTP exception
        print(f"Error while processing response: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


def serve_autogen(inp: Input):
    """
    Serves the autogen workflow based on the input, either streaming or non-streaming.
    """
    try:
        model_dump = inp.model_dump()
        model_messages = model_dump["messages"]
        workflow = AutogenWorkflow()

        if inp.stream:
            queue = Queue()
            workflow.set_queue(queue)
            Thread(
                target=workflow.run,
                args=(
                    model_messages[-1],
                    inp.stream,
                ),
            ).start()
            return StreamingResponse(
                return_streaming_response(inp, queue),
                media_type="text/event-stream",
            )
        else:
            chat_results = workflow.run(
                message=model_messages[-1],
                stream=inp.stream,
            )
            return return_non_streaming_response(
                chat_results, inp.model
            )
    except Exception as e:
        print(f"Error in serve_autogen: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


def return_streaming_response(inp: Input, queue: Queue):
    """
    Generates a streaming response for the workflow.
    """
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
                usage=empty_usage,
                model=inp.model,
            )
            yield f"data: {json.dumps(handle_response(chunk))}\n\n"
            queue.task_done()
    except Exception as e:
        print(f"Error in return_streaming_response: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


def return_non_streaming_response(chat_results, model):
    """
    Returns a non-streaming response for the workflow.
    """
    try:
        if chat_results:
            return handle_response(Output(
                id=str(chat_results.chat_id),
                choices=[
                    {"index": i, "message": msg, "finish_reason": "stop"}
                    for i, msg in enumerate(chat_results.chat_history)
                ],
                usage=chat_results.cost,
                model=model,
            ))
        else:
            return handle_response(Output(
                id="None",
                choices=[
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": "Sorry, I am unable to assist with that request at this time.",
                        },
                        "finish_reason": "stop",
                        "logprobs": None,
                    }
                ],
                usage=empty_usage,
                model=model,
            ))
    except Exception as e:
        print(f"Error in return_non_streaming_response: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
