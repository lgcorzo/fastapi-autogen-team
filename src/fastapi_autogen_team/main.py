import os
import logging

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from starlette.responses import RedirectResponse
from apscheduler.schedulers.background import BackgroundScheduler

from fastapi_autogen_team.autogen_server import serve_autogen
from fastapi_autogen_team.data_model import Input, ModelInformation

from opentelemetry import trace, metrics
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.metrics.export import (
    ConsoleMetricExporter,
    PeriodicExportingMetricReader,
)
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter


# Load environment variables
load_dotenv()

# Get OpenTelemetry endpoint from environment variables
otel_traces_endpoint = os.getenv(
    "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", "http://otel-collector:4318/v1/traces"
)  # Default OTLP/HTTP port

# Get OpenTelemetry endpoint from environment variables
otel_metrics_endpoint = os.getenv(
    "OTEL_EXPORTER_OTLP_METRICS_ENDPOINT", "http://otel-collector:4318/v1/metrics"
)  # Default OTLP/HTTP port

# Set up OpenTelemetry resources and tracer
resource = Resource.create(attributes={"service.name": "Autogen-fastapi-service"})

# Tracer setup
tracer_provider = TracerProvider(resource=resource)
trace.set_tracer_provider(tracer_provider)
otlp_exporter = OTLPSpanExporter(endpoint=otel_traces_endpoint)
span_processor = BatchSpanProcessor(otlp_exporter)
tracer_provider.add_span_processor(span_processor)

# Meter setup with correct initialization
# exporter = ConsoleMetricExporter() ## only for debuging
otlp_metric_exporter = OTLPMetricExporter(endpoint=otel_metrics_endpoint)
metric_reader = PeriodicExportingMetricReader(otlp_metric_exporter, export_interval_millis=30000)
meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
metrics.set_meter_provider(meter_provider)
meter = metrics.get_meter(__name__)

# Create heartbeat metric
heartbeat_counter = meter.create_counter(
    name="autogen_service.heartbeat",
    description="Counts the number of heartbeat signals",
    unit="1",
)

# Set up logging
logging.basicConfig(
    filename="app.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)
logger_tracer = trace.get_tracer_provider().get_tracer(__name__)


def log_with_trace(message: str, level: str = "info"):
    """Logs messages with OpenTelemetry tracing support."""
    with logger_tracer.start_as_current_span("log"):
        log_method = getattr(logger, level, None)
        if callable(log_method):
            log_method(message)
        else:
            logger.error(f"Unsupported log level: {level}. Message: {message}")


# Function to record heartbeat
def record_heartbeat():
    """Increments the heartbeat counter and logs the event."""
    heartbeat_counter.add(1, {"service": "Autogen-fastapi-service"})
    log_with_trace("Heartbeat recorded", level="debug")


# Initialize scheduler for heartbeat
scheduler = BackgroundScheduler()
scheduler.add_job(record_heartbeat, "interval", seconds=10)
scheduler.start()

# Application base paths
base = "/autogen"
prefix = base + "/api/v1beta"
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
    """Redirects to API documentation."""
    return RedirectResponse(url=docs_url)


@app.get(prefix + "/models")
async def get_models():
    """Returns available model information."""
    log_with_trace("Get models endpoint accessed")
    return {"data": {"data": model_info.dict()}}


@app.post(prefix + "/chat/completions")
async def route_query(model_input: Input):
    """Handles chat completion requests."""
    log_with_trace(f"Chat completion request for model: {model_input.model}")
    model_services = {
        model_info.name: serve_autogen,
    }

    service = model_services.get(model_input.model)
    if not service:
        raise HTTPException(status_code=404, detail="Model not found")
    return service(model_input)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(4100))
