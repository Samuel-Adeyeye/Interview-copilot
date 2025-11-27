#!/bin/bash
# Start API server and run full flow test

set -e

echo "🚀 Starting Interview Co-Pilot Full Flow Test"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Activate venv
cd "$(dirname "$0")/.."
source venv/bin/activate

# Check if server is already running
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Server already running on port 8000${NC}"
    SERVER_RUNNING=true
else
    echo "Starting API server..."
    uvicorn api.main:app --host 0.0.0.0 --port 8000 > /tmp/api_test.log 2>&1 &
    SERVER_PID=$!
    SERVER_RUNNING=false
    
    # Wait for server to start
    echo "Waiting for server to start..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Server started${NC}"
            SERVER_RUNNING=true
            break
        fi
        sleep 1
    done
    
    if [ "$SERVER_RUNNING" = false ]; then
        echo -e "${RED}❌ Server failed to start${NC}"
        echo "Check logs: tail -f /tmp/api_test.log"
        exit 1
    fi
fi

# Run test
echo ""
echo "Running full flow test..."
python scripts/test_full_flow.py

TEST_EXIT_CODE=$?

# Cleanup
if [ "$SERVER_RUNNING" = false ] && [ ! -z "$SERVER_PID" ]; then
    echo ""
    echo "Stopping server..."
    kill $SERVER_PID 2>/dev/null || true
    wait $SERVER_PID 2>/dev/null || true
fi

exit $TEST_EXIT_CODE

