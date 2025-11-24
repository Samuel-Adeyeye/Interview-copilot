#!/bin/bash

# Docker Health Check Script
# Checks the health of all running containers

set -e

echo "🏥 Checking Docker Container Health..."
echo ""

# Determine compose command
if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
else
    echo "❌ Docker Compose not found"
    exit 1
fi

# Check if containers are running
if ! $COMPOSE_CMD ps | grep -q "Up"; then
    echo "⚠️  No containers are running"
    echo "   Start containers with: $COMPOSE_CMD up -d"
    exit 1
fi

# Check each service
services=("api" "db" "redis" "ui")
all_healthy=true

for service in "${services[@]}"; do
    if $COMPOSE_CMD ps | grep -q "$service.*Up"; then
        # Get health status
        health=$(docker inspect $($COMPOSE_CMD ps -q $service) 2>/dev/null | grep -o '"Health".*"Status":"[^"]*"' | grep -o 'Status":"[^"]*' | cut -d'"' -f3 || echo "no-healthcheck")
        
        if [ "$health" = "healthy" ]; then
            echo "✅ $service: healthy"
        elif [ "$health" = "no-healthcheck" ]; then
            echo "⚠️  $service: running (no health check)"
        else
            echo "❌ $service: $health"
            all_healthy=false
        fi
    else
        echo "⚠️  $service: not running"
        all_healthy=false
    fi
done

echo ""

# Test API health endpoint
if $COMPOSE_CMD ps | grep -q "api.*Up"; then
    echo "🔍 Testing API health endpoint..."
    if curl -f -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ API health endpoint is responding"
        curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null || curl -s http://localhost:8000/health
    else
        echo "❌ API health endpoint is not responding"
        all_healthy=false
    fi
    echo ""
fi

# Test UI health endpoint
if $COMPOSE_CMD ps | grep -q "ui.*Up"; then
    echo "🔍 Testing UI health endpoint..."
    if curl -f -s http://localhost:8501/_stcore/health > /dev/null 2>&1; then
        echo "✅ UI health endpoint is responding"
    else
        echo "⚠️  UI health endpoint is not responding (may be starting up)"
    fi
    echo ""
fi

# Summary
if [ "$all_healthy" = true ]; then
    echo "✅ All services are healthy!"
    exit 0
else
    echo "⚠️  Some services have issues. Check logs with: $COMPOSE_CMD logs"
    exit 1
fi

