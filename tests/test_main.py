import pytest
from unittest.mock import patch, MagicMock
from fastapi import FastAPI, HTTPException

from fastapi_autogen_team.data_model import Input
from fastapi_autogen_team.main import (
    get_models,
    record_heartbeat,
    route_query,
    log_with_trace,
)


@pytest.fixture
def mock_app():
    """Fixture to mock FastAPI app and dependencies."""
    with (
        patch("fastapi_autogen_team.main.FastAPI") as MockFastAPI,
        patch("fastapi_autogen_team.main.BackgroundScheduler") as MockBackgroundScheduler,
        patch("fastapi_autogen_team.main.FastAPIInstrumentor.instrument_app") as MockInstrumentApp,
        patch("fastapi_autogen_team.main.OTLPSpanExporter") as MockOTLPSpanExporter,
        patch("fastapi_autogen_team.main.BatchSpanProcessor") as MockBatchSpanProcessor,
        patch("fastapi_autogen_team.main.TracerProvider") as MockTracerProvider,
        patch("fastapi_autogen_team.main.PeriodicExportingMetricReader") as MockPeriodicExportingMetricReader,
        patch("fastapi_autogen_team.main.OTLPMetricExporter") as MockOTLPMetricExporter,
        patch("fastapi_autogen_team.main.MeterProvider") as MockMeterProvider,
        patch("fastapi_autogen_team.main.metrics.set_meter_provider") as MockSetMeterProvider,
        patch("fastapi_autogen_team.main.logging.basicConfig") as MockLoggingBasicConfig,
        patch("fastapi_autogen_team.main.trace.set_tracer_provider") as MockTraceSetTracerProvider,
        patch("fastapi_autogen_team.main.load_dotenv") as MockLoadDotenv,
        patch("fastapi_autogen_team.main.os.getenv") as MockGetEnv,
    ):
        mock_app = MagicMock(spec=FastAPI)
        mock_scheduler = MagicMock()
        MockFastAPI.return_value = mock_app
        MockBackgroundScheduler.return_value = mock_scheduler
        MockGetEnv.return_value = "mock_value"

        yield (
            mock_app,
            mock_scheduler,
            MockFastAPI,
            MockBackgroundScheduler,
            MockInstrumentApp,
            MockOTLPSpanExporter,
            MockBatchSpanProcessor,
            MockTracerProvider,
            MockPeriodicExportingMetricReader,
            MockOTLPMetricExporter,
            MockMeterProvider,
            MockSetMeterProvider,
            MockLoggingBasicConfig,
            MockTraceSetTracerProvider,
            MockLoadDotenv,
            MockGetEnv,
        )


@pytest.mark.asyncio
async def test_get_models(mock_app):
    """Test that the get_models function returns model information."""
    (
        mock_app,
        mock_scheduler,
        MockFastAPI,
        MockBackgroundScheduler,
        MockInstrumentApp,
        MockOTLPSpanExporter,
        MockBatchSpanProcessor,
        MockTracerProvider,
        MockPeriodicExportingMetricReader,
        MockOTLPMetricExporter,
        MockMeterProvider,
        MockSetMeterProvider,
        MockLoggingBasicConfig,
        MockTraceSetTracerProvider,
        MockLoadDotenv,
        MockGetEnv,
    ) = mock_app

    result = await get_models()
    assert "data" in result
    assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_route_query_valid_model(mock_app):
    """Test that the route_query function calls serve_autogen with a valid model."""
    (
        mock_app,
        mock_scheduler,
        MockFastAPI,
        MockBackgroundScheduler,
        MockInstrumentApp,
        MockOTLPSpanExporter,
        MockBatchSpanProcessor,
        MockTracerProvider,
        MockPeriodicExportingMetricReader,
        MockOTLPMetricExporter,
        MockMeterProvider,
        MockSetMeterProvider,
        MockLoggingBasicConfig,
        MockTraceSetTracerProvider,
        MockLoadDotenv,
        MockGetEnv,
    ) = mock_app

    with patch("fastapi_autogen_team.main.serve_autogen") as MockServeAutogen:
        test_input = Input(model="internal-gpt", messages=[{"role": "user", "content": "Hello"}])
        await route_query(test_input)
        MockServeAutogen.assert_called_once_with(test_input)


@pytest.mark.asyncio
async def test_route_query_invalid_model(mock_app):
    """Test that route_query raises an HTTPException when an invalid model is specified."""
    (
        mock_app,
        mock_scheduler,
        MockFastAPI,
        MockBackgroundScheduler,
        MockInstrumentApp,
        MockOTLPSpanExporter,
        MockBatchSpanProcessor,
        MockTracerProvider,
        MockPeriodicExportingMetricReader,
        MockOTLPMetricExporter,
        MockMeterProvider,
        MockSetMeterProvider,
        MockLoggingBasicConfig,
        MockTraceSetTracerProvider,
        MockLoadDotenv,
        MockGetEnv,
    ) = mock_app
    with pytest.raises(HTTPException) as exc_info:
        test_input = Input(model="invalid_model", messages=[{"role": "user", "content": "Hello"}])
        await route_query(test_input)
    assert exc_info.value.status_code == 404
    assert "Model not found" in exc_info.value.detail


def test_heartbeat_and_log(mock_app):
    """Test the log_with_trace and record_heartbeat functions"""
    (
        mock_app,
        mock_scheduler,
        MockFastAPI,
        MockBackgroundScheduler,
        MockInstrumentApp,
        MockOTLPSpanExporter,
        MockBatchSpanProcessor,
        MockTracerProvider,
        MockPeriodicExportingMetricReader,
        MockOTLPMetricExporter,
        MockMeterProvider,
        MockSetMeterProvider,
        MockLoggingBasicConfig,
        MockTraceSetTracerProvider,
        MockLoadDotenv,
        MockGetEnv,
    ) = mock_app

    with (
        patch("fastapi_autogen_team.main.logger.info") as mock_logger_info,
        patch("fastapi_autogen_team.main.heartbeat_counter.add") as mock_heartbeat_counter,
        patch("fastapi_autogen_team.main.logger_tracer.start_as_current_span"),
    ):
        log_with_trace("test message")
        mock_logger_info.assert_called_once_with("test message")

        record_heartbeat()
        mock_heartbeat_counter.assert_called_once()
