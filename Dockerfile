FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*
    
COPY dist/*.whl .
RUN pip install *.whl
# Ejecuta la función main() del módulo controller.kafka_app
CMD ["python", "-m", "fastapi_autogen_team.main"]