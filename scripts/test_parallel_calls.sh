#!/bin/bash

# Port forward the NGINX proxy (the main rust-agent-team service) to test parallel calls
echo "Setting up port forward to the rust-agent-team service..."
kubectl port-forward svc/rust-agent-team -n llm-apps 4100:4100 &
PF_PID=$!

# Wait for port forward to be ready
sleep 3

echo "Starting 10 parallel requests..."

for i in {1..10}; do
    # Assuming there's a simple health or root endpoint. Modify as needed for the specific API.
    curl -s http://localhost:4100/health > /dev/null && echo "Request $i completed" &
done

wait

echo "All requests completed."
kill $PF_PID
