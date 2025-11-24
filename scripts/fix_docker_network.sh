#!/bin/bash

# Fix Docker Network/Connectivity Issues
# Handles TLS handshake timeout and network issues

set -e

echo "🔧 Fixing Docker Network Issues..."
echo ""

# Check Docker connectivity
echo "1. Testing Docker Hub connectivity..."
if curl -s --max-time 5 https://registry-1.docker.io/v2/ > /dev/null 2>&1; then
    echo "✅ Can reach Docker Hub"
else
    echo "❌ Cannot reach Docker Hub - network issue"
    echo ""
    echo "Possible solutions:"
    echo "  - Check your internet connection"
    echo "  - Check firewall/proxy settings"
    echo "  - Try using a VPN if behind a corporate firewall"
    echo "  - Configure Docker proxy settings"
fi

echo ""

# Check Docker daemon
echo "2. Checking Docker daemon..."
if docker info > /dev/null 2>&1; then
    echo "✅ Docker daemon is running"
else
    echo "❌ Docker daemon is not running"
    echo "   Start Docker Desktop"
    exit 1
fi

echo ""

# Check DNS
echo "3. Testing DNS resolution..."
if nslookup registry-1.docker.io > /dev/null 2>&1; then
    echo "✅ DNS resolution works"
else
    echo "⚠️  DNS resolution may be slow"
    echo "   Try: sudo dscacheutil -flushcache (macOS)"
fi

echo ""

# Suggest solutions
echo "📝 Solutions to try:"
echo ""
echo "Solution 1: Increase Docker timeout"
echo "  Edit Docker Desktop → Settings → Docker Engine"
echo "  Add: { \"max-concurrent-downloads\": 1 }"
echo ""
echo "Solution 2: Use Docker mirror (if available)"
echo "  Configure in Docker Desktop → Settings → Docker Engine"
echo ""
echo "Solution 3: Retry with longer timeout"
echo "  DOCKER_BUILDKIT=0 docker compose build --progress=plain"
echo ""
echo "Solution 4: Pull image manually first"
echo "  docker pull python:3.11-slim"
echo ""
echo "Solution 5: Check proxy settings"
echo "  Docker Desktop → Settings → Resources → Proxies"
echo ""

# Try to pull the image manually
echo "🔍 Attempting to pull Python base image manually..."
if docker pull python:3.11-slim 2>&1 | head -10; then
    echo "✅ Successfully pulled Python image!"
else
    echo "⚠️  Failed to pull image - network issue persists"
    echo ""
    echo "Try these commands:"
    echo "  docker pull python:3.11-slim"
    echo "  docker compose build --no-cache"
fi

