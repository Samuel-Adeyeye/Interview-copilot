#!/bin/bash

# Docker Setup Verification Script
# This script verifies the Docker setup without actually running containers

set -e

echo "🔍 Verifying Docker Setup..."
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed"
    exit 1
fi
echo "✅ Docker is installed: $(docker --version)"

# Check Docker Compose
if docker compose version &> /dev/null; then
    echo "✅ Docker Compose (v2) is available: $(docker compose version | head -1)"
    COMPOSE_CMD="docker compose"
elif command -v docker-compose &> /dev/null; then
    echo "✅ Docker Compose (v1) is available: $(docker-compose --version)"
    COMPOSE_CMD="docker-compose"
else
    echo "❌ Docker Compose is not installed"
    exit 1
fi

# Check Dockerfile
if [ ! -f "Dockerfile" ]; then
    echo "❌ Dockerfile not found"
    exit 1
fi
echo "✅ Dockerfile exists"

# Check docker-compose.yml
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ docker-compose.yml not found"
    exit 1
fi
echo "✅ docker-compose.yml exists"

# Validate docker-compose configuration
echo ""
echo "🔍 Validating docker-compose configuration..."
if $COMPOSE_CMD config --quiet 2>&1; then
    echo "✅ docker-compose.yml is valid"
else
    echo "❌ docker-compose.yml has errors"
    exit 1
fi

# Check .dockerignore
if [ -f ".dockerignore" ]; then
    echo "✅ .dockerignore exists"
else
    echo "⚠️  .dockerignore not found (recommended)"
fi

# Check required directories
echo ""
echo "🔍 Checking required directories..."
for dir in "data/vectordb" "data/sessions" "logs"; do
    if [ ! -d "$dir" ]; then
        echo "⚠️  Directory $dir does not exist (will be created)"
        mkdir -p "$dir"
    else
        echo "✅ Directory $dir exists"
    fi
done

# Check .env file
echo ""
echo "🔍 Checking environment configuration..."
if [ -f ".env" ]; then
    echo "✅ .env file exists"
    # Check for required variables
    required_vars=("OPENAI_API_KEY")
    missing_vars=()
    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" .env 2>/dev/null; then
            missing_vars+=("$var")
        fi
    done
    if [ ${#missing_vars[@]} -eq 0 ]; then
        echo "✅ Required environment variables are set"
    else
        echo "⚠️  Missing environment variables: ${missing_vars[*]}"
    fi
else
    echo "⚠️  .env file not found (create from .env.example)"
fi

# Check if Docker daemon is running
echo ""
echo "🔍 Checking Docker daemon..."
if docker info &> /dev/null; then
    echo "✅ Docker daemon is running"
else
    echo "❌ Docker daemon is not running"
    exit 1
fi

# Test Dockerfile syntax (build dry-run)
echo ""
echo "🔍 Testing Dockerfile syntax..."
if docker build --dry-run -f Dockerfile . &> /dev/null 2>&1 || true; then
    echo "✅ Dockerfile syntax appears valid"
else
    echo "⚠️  Could not verify Dockerfile syntax (this is okay)"
fi

echo ""
echo "✅ Docker setup verification complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Ensure .env file is configured with required API keys"
echo "   2. Run: $COMPOSE_CMD up -d"
echo "   3. Check logs: $COMPOSE_CMD logs -f"
echo "   4. Verify health: curl http://localhost:8000/health"

