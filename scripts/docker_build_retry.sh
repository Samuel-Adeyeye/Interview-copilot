#!/bin/bash

# Docker Build Retry Script
# Handles network issues and retries with different strategies

set -e

echo "🐳 Docker Build with Retry Logic..."
echo ""

# Strategy 1: Try with BuildKit disabled
echo "Strategy 1: Building with BuildKit disabled..."
if DOCKER_BUILDKIT=0 docker compose build 2>&1; then
    echo "✅ Build successful with BuildKit disabled!"
    exit 0
else
    echo "⚠️  BuildKit disabled attempt failed, trying next strategy..."
fi

echo ""

# Strategy 2: Pull base image first, then build
echo "Strategy 2: Pulling base images first..."
if docker pull python:3.11-slim 2>&1; then
    echo "✅ Base image pulled successfully"
    echo "Building with pre-pulled images..."
    if docker compose build 2>&1; then
        echo "✅ Build successful!"
        exit 0
    fi
else
    echo "⚠️  Failed to pull base image"
fi

echo ""

# Strategy 3: Build without cache
echo "Strategy 3: Building without cache..."
if docker compose build --no-cache 2>&1; then
    echo "✅ Build successful without cache!"
    exit 0
else
    echo "❌ All build strategies failed"
    echo ""
    echo "📝 Troubleshooting steps:"
    echo "   1. Check internet connection"
    echo "   2. Check Docker Desktop is running"
    echo "   3. Try: docker pull python:3.11-slim"
    echo "   4. Check firewall/proxy settings"
    echo "   5. Restart Docker Desktop"
    exit 1
fi

