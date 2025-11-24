#!/bin/bash
# Script to run tests for Interview Co-Pilot

set -e

echo "🧪 Running Interview Co-Pilot Tests"
echo "===================================="

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest is not installed. Installing dependencies..."
    pip install -r requirements.txt
fi

# Set test environment variables
export OPENAI_API_KEY=${OPENAI_API_KEY:-"test-openai-key"}
export TAVILY_API_KEY=${TAVILY_API_KEY:-"test-tavily-key"}
export JUDGE0_API_KEY=${JUDGE0_API_KEY:-"test-judge0-key"}
export SESSION_PERSISTENCE_ENABLED=${SESSION_PERSISTENCE_ENABLED:-"false"}
export VECTOR_DB_PATH=${VECTOR_DB_PATH:-"./data/vectordb_test"}

# Create test directories
mkdir -p data/vectordb_test data/sessions_test logs

# Run tests
echo ""
echo "📋 Running all tests..."
pytest tests/ -v --tb=short

# Optionally run with coverage
if command -v pytest-cov &> /dev/null; then
    echo ""
    echo "📊 Running tests with coverage..."
    pytest tests/ --cov=. --cov-report=term-missing --cov-report=html
    echo ""
    echo "✅ Coverage report generated in htmlcov/index.html"
fi

echo ""
echo "✅ Tests completed!"

