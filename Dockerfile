# Use the official Miniconda3 image with alpine
FROM continuumio/miniconda3:4.10.3-alpine

# Environment variables
ENV \
    PORT=8080 \
    PYTHONPATH=/autogen/src/fastapi_autogen_team

# Set working directory where the Docker container will run
WORKDIR /autogen

# Copy conda environment file
COPY Settings/autogen_env.yaml ./

# Install system dependencies
RUN apk add --no-cache libstdc++

# Create the conda environment
RUN conda env create -f autogen_env.yaml && \
    conda clean -afy

# Copy the rest of the application code
COPY . .

# Command to run the application
COPY ./run.sh ./run.sh
RUN chmod +x ./run.sh

ENTRYPOINT ["./run.sh"]