import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from starlette.responses import RedirectResponse

from autogen_server import serve_autogen
from data_model import Input, ModelInformation

from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

import logging

# Load environment variables
load_dotenv()

# Get OpenTelemetry endpoint from environment variables
otel_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "otel-collector:4317")

# Set up OpenTelemetry resources and tracer
resource = Resource(attributes={"service.name": "Autogen-fastapi-service"})
tracer_provider = TracerProvider(resource=resource)
trace.set_tracer_provider(tracer_provider)

# Configure OTLP exporter
otlp_exporter = OTLPSpanExporter(endpoint=otel_endpoint)
span_processor = BatchSpanProcessor(otlp_exporter)
tracer_provider.add_span_processor(span_processor)

# Set up logging
logging.basicConfig(
    filename="app.log",
    filemode="a",
    format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
    level=logging.DEBUG,
)
logger = logging.getLogger(__name__)

# Add a tracer to logger manually
logger_tracer = trace.get_tracer_provider().get_tracer(__name__)


def log_with_trace(message: str, level: str = "info"):
    with logger_tracer.start_as_current_span("log"):
        if level == "info":
            logger.info(message)
        elif level == "error":
            logger.error(message)
        elif level == "debug":
            logger.debug(message)
        elif level == "warning":
            logger.warning(message)
        else:
            logger.log(level, message)


# Application base paths
base = "/autogen/"
prefix = base + "api/v1"
openapi_url = prefix + "/openapi.json"
docs_url = prefix + "/docs"

# Create FastAPI app
app = FastAPI(
    title="Autogen FastAPI Backend",
    openapi_url=openapi_url,
    docs_url=docs_url,
    redoc_url=None,
)

# Instrument FastAPI with OpenTelemetry
FastAPIInstrumentor.instrument_app(app)

# Model information
model_info = ModelInformation(
    id="internal-gpt4_v0.1",
    name="internal-gpt",
    description="This is a state-of-the-art model.",
    pricing={
        "prompt": "0.00",
        "completion": "0.00",
        "image": "0.00",
        "request": "0.00",
    },
    context_length=1024 * 1000,
    architecture={
        "modality": "text",
        "tokenizer": "text2vec-openai",
        "instruct_type": "InstructGPT",
    },
    top_provider={"max_completion_tokens": None, "is_moderated": False},
    per_request_limits=None,
)

# Define endpoints
@app.get(path=base, include_in_schema=False)
async def docs_redirect():
    return RedirectResponse(url=docs_url)


@app.get(prefix + "/models")
async def get_models():
    log_with_trace("Get models endpoint accessed")
    return {"data": {"data": model_info.dict()}}


@app.post(prefix + "/chat/completions")
async def route_query(model_input: Input):
    log_with_trace("Chat completion endpoint accessed")
    model_services = {
        model_info.name: serve_autogen,
    }

    service = model_services.get(model_input.model)
    if not service:
        raise HTTPException(status_code=404, detail="Model not found")
    return service(model_input)
