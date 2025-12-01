#!/bin/bash
set -e

# Start the API server in the background
echo "Starting API server..."
uvicorn api.main:app --host 0.0.0.0 --port 8002 &
API_PID=$!

# Wait for the API to be ready
echo "Waiting for API to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8002/health > /dev/null; then
        echo "API is ready!"
        break
    fi
    echo "Waiting for API... ($i/30)"
    sleep 1
done

# Run the tests
echo "Running tests..."
pytest tests/integration/ -v

# Capture the exit code of pytest
TEST_EXIT_CODE=$?

# Kill the API server
echo "Stopping API server..."
kill $API_PID

# Exit with the test exit code
exit $TEST_EXIT_CODE
