#!/bin/bash

# Ensure environment variables are loaded if .env exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Run the Rust service in release mode
echo "Starting Rust-Agent-team Service..."
cargo run --release
