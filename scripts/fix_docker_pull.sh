#!/bin/bash
# Fix Docker image pull issues

set -e

echo "🔧 Fixing Docker Image Pull Issues"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Attempting to fix Docker image pull timeout...${NC}"
echo ""

# Method 1: Retry with increased timeout
echo "Method 1: Retrying with increased timeout..."
docker-compose pull --timeout 300 || {
    echo -e "${YELLOW}Method 1 failed, trying Method 2...${NC}"
    
    # Method 2: Pull images individually with retries
    echo "Method 2: Pulling images individually..."
    
    echo "Pulling postgres:15-alpine..."
    for i in {1..3}; do
        if docker pull postgres:15-alpine; then
            echo -e "${GREEN}✅ Successfully pulled postgres:15-alpine${NC}"
            break
        else
            echo -e "${YELLOW}Attempt $i failed, retrying...${NC}"
            sleep 5
        fi
    done
    
    echo "Pulling redis:7-alpine..."
    for i in {1..3}; do
        if docker pull redis:7-alpine; then
            echo -e "${GREEN}✅ Successfully pulled redis:7-alpine${NC}"
            break
        else
            echo -e "${YELLOW}Attempt $i failed, retrying...${NC}"
            sleep 5
        fi
    done
}

echo ""
echo -e "${GREEN}✅ Image pull process completed${NC}"
echo ""
echo "Next steps:"
echo "1. Try building again: docker-compose build"
echo "2. Or start services: docker-compose up -d"

