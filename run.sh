#!/bin/bash

# enable conda for this shell
. /opt/conda/etc/profile.d/conda.sh
# init conda
conda init
# activate the environment
conda activate autogen_env

# Set environment variables for OpenTelemetry
# export OTEL_EXPORTER_OTLP_ENDPOINT="http://otel_collector:4317"  # Adjust if using a different endpoint
# export OTEL_EXPORTER_OTLP_PROTOCOL="http/protobuf"
# export OTEL_LOG_LEVEL="info"

echo "Starting backend with OpenTelemetry instrumentation..."
opentelemetry-instrument uvicorn app.main:app --host $BE_HOST --port $BE_PORT --workers 1 --proxy-headers
