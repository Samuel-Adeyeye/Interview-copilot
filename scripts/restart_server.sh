#!/bin/bash
# Script to restart the API server

echo "🛑 Stopping existing server..."
pkill -f "uvicorn api.main:app" || true
sleep 2

echo "🚀 Starting server..."
cd "$(dirname "$0")/.."
source venv/bin/activate
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload &

echo "⏳ Waiting for server to start..."
sleep 5

echo "✅ Checking server health..."
curl -s http://localhost:8000/health | python -m json.tool || echo "❌ Server not responding"

echo ""
echo "✅ Server restarted. Check http://localhost:8000/docs for API documentation"

