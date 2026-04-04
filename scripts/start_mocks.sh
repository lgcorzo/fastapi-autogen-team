#!/bin/bash

# Kill any existing mock server on port 8081
fuser -k 8081/tcp 2>/dev/null

echo "Starting Mock Services (R2R and Jira) on port 8081..."
cargo run --bin mock-services &
MOCK_PID=$!

# Wait for mock server to be ready
echo "Waiting for mock server to start..."
while ! curl -s http://localhost:8081 > /dev/null; do
  sleep 1
done

echo "Mock Services are READY!"
echo ""
echo "To run the main application using these mocks, use:"
echo "export R2R_URL=http://localhost:8081"
echo "export JIRA_INSTANCE_URL=http://localhost:8081"
echo "export R2R_USER=test"
echo "export R2R_PWD=test"
echo "export JIRA_USERNAME=test"
echo "export JIRA_API_TOKEN=test"
echo "cargo run"
echo ""
echo "Press Ctrl+C to stop the mock server."

trap "kill $MOCK_PID" EXIT
wait $MOCK_PID
