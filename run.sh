#!/bin/bash

# enable conda for this shell
. /opt/conda/etc/profile.d/conda.sh
# init conda
conda init
# activate the environment
conda activate autogen_env

echo "Starting backend with OpenTelemetry instrumentation..."
uvicorn src.fastapi_autogen_team.main:app --host $BE_HOST --port $BE_PORT --workers 1 --proxy-headers
