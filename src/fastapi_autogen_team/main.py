import os
import logging

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.routing import APIRoute
from starlette.responses import RedirectResponse
from apscheduler.schedulers.background import BackgroundScheduler
from opentelemetry import metrics, trace
from opentelemetry._logs import set_logger_provider

from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.sdk.resources import Resource


import uvicorn

from fastapi_autogen_team.autogen_server import serve_autogen
from fastapi_autogen_team.data_model import Input, ModelInformation

# Configuration
APP_NAME = "Autogen-fastapi-service"
DEFAULT_OTEL_ENDPOINT = "http://otel-collector:4318/v1"
OTEL_TRACES_ENDPOINT_ENV = "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"
OTEL_METRICS_ENDPOINT_ENV = "OTEL_EXPORTER_OTLP_METRICS_ENDPOINT"
LOG_FILE = "app.log"
HEARTBEAT_INTERVAL = 60  # seconds
METRICS_EXPORT_INTERVAL = 30000  # milliseconds
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 4100

# Initialize
load_dotenv()
TRACES_ENDPOINT = os.getenv(OTEL_TRACES_ENDPOINT_ENV, f"{DEFAULT_OTEL_ENDPOINT}/traces")
METRICS_ENDPOINT = os.getenv(OTEL_METRICS_ENDPOINT_ENV, f"{DEFAULT_OTEL_ENDPOINT}/metrics")


# OpenTelemetry Setup
resource = Resource.create(attributes={"service.name": APP_NAME})

# Tracer Provider
tracer_provider = TracerProvider(resource=resource)
trace.set_tracer_provider(tracer_provider)
otlp_exporter = OTLPSpanExporter(endpoint=TRACES_ENDPOINT)
span_processor = BatchSpanProcessor(otlp_exporter)
tracer_provider.add_span_processor(span_processor)
logger_tracer = trace.get_tracer_provider().get_tracer(__name__)

# Meter Provider
otlp_metric_exporter = OTLPMetricExporter(endpoint=METRICS_ENDPOINT)
metric_reader = PeriodicExportingMetricReader(
    otlp_metric_exporter, export_interval_millis=METRICS_EXPORT_INTERVAL
)
meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
metrics.set_meter_provider(meter_provider)
meter = metrics.get_meter(__name__)

# Logging setup
logger_provider = LoggerProvider(resource=resource)
set_logger_provider(logger_provider)
otlp_log_exporter = OTLPLogExporter()
logger_provider.add_log_record_processor(BatchLogRecordProcessor(otlp_log_exporter))

# Attach OpenTelemetry handler to Python's logging
otel_handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
logging.getLogger().addHandler(otel_handler)

# Root logger configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

logger.info("Logging started")

# Heartbeat Metric
heartbeat_counter = meter.create_counter(
    name="autogen_service.heartbeat",
    description="Counts the number of heartbeat signals",
    unit="1",
)

def log_with_trace(message: str, level: str = "info") -> None:
    """Logs messages with OpenTelemetry tracing support."""
    with logger_tracer.start_as_current_span("log"):
        log_method = getattr(logger, level, None)
        if callable(log_method):
            log_method(message)
        else:
            logger.error(f"Unsupported log level: {level}. Message: {message}")

def record_heartbeat() -> None:
    """Increments the heartbeat counter and logs the event."""
    heartbeat_counter.add(1, {"service": APP_NAME})
    log_with_trace("Heartbeat recorded", level="debug")

# Model Information
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

# FastAPI App Setup
BASE_PATH = "/autogen"
API_PREFIX = BASE_PATH + "/api/v1beta"
OPENAPI_URL = API_PREFIX + "/openapi.json"
DOCS_URL = API_PREFIX + "/docs"

app = FastAPI(
    title="Autogen FastAPI Backend",
    openapi_url=OPENAPI_URL,
    docs_url=DOCS_URL,
    redoc_url=None,
)

FastAPIInstrumentor.instrument_app(app)

# Routes
@app.get(path=BASE_PATH, include_in_schema=False)
async def docs_redirect() -> RedirectResponse:
    """Redirects to API documentation."""
    return RedirectResponse(url=DOCS_URL)

@app.get(API_PREFIX + "/models")
async def get_models() -> dict:
    """Returns available model information."""
    log_with_trace("Get models endpoint accessed")
    return {"data": {"data": model_info.dict()}}

@app.post(API_PREFIX + "/chat/completions")
async def route_query(model_input: Input) -> dict:
    """Handles chat completion requests."""
    log_with_trace(f"Chat completion request for model: {model_input.model}")
    model_services = {model_info.name: serve_autogen}
    service = model_services.get(model_input.model)

    if not service:
        raise HTTPException(status_code=404, detail="Model not found")

    return service(model_input)

# Heartbeat Scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(record_heartbeat, "interval", seconds=HEARTBEAT_INTERVAL)
scheduler.start()

if __name__ == "__main__":
    uvicorn.run(app, host=DEFAULT_HOST, port=DEFAULT_PORT)