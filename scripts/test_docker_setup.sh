#!/bin/bash
# Test Docker setup for Interview Co-Pilot

set -e

echo "🐳 Testing Docker Setup for Interview Co-Pilot"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker is running${NC}"

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ docker-compose not found. Please install docker-compose.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ docker-compose is available${NC}"

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating template...${NC}"
    cat > .env << EOF
# Required: Google API Key for ADK
GOOGLE_API_KEY=your_google_api_key_here

# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=interview_copilot
DATABASE_URL=postgresql://postgres:postgres@db:5432/interview_copilot

# Redis
REDIS_URL=redis://redis:6379
EOF
    echo -e "${YELLOW}⚠️  Please edit .env and add your GOOGLE_API_KEY${NC}"
fi

# Check if GOOGLE_API_KEY is set
if grep -q "GOOGLE_API_KEY=your_google_api_key_here" .env || ! grep -q "GOOGLE_API_KEY=" .env; then
    echo -e "${YELLOW}⚠️  GOOGLE_API_KEY not configured in .env${NC}"
    echo -e "${YELLOW}   ADK endpoints will not work without a valid API key${NC}"
fi

# Create data directories if they don't exist
mkdir -p data/vectordb data/sessions logs
chmod -R 755 data logs 2>/dev/null || true

echo -e "${GREEN}✅ Data directories ready${NC}"

# Test docker-compose configuration
echo ""
echo "Testing docker-compose configuration..."
if docker-compose config > /dev/null 2>&1; then
    echo -e "${GREEN}✅ docker-compose.yml is valid${NC}"
else
    echo -e "${RED}❌ docker-compose.yml has errors${NC}"
    docker-compose config
    exit 1
fi

# Check if services are already running
if docker-compose ps | grep -q "Up"; then
    echo -e "${YELLOW}⚠️  Some services are already running${NC}"
    echo "   Run 'docker-compose down' to stop them first"
fi

echo ""
echo -e "${GREEN}✅ Docker setup check complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your GOOGLE_API_KEY"
echo "2. Run: docker-compose up -d"
echo "3. Check logs: docker-compose logs -f"
echo "4. Test API: curl http://localhost:8000/health"
echo "5. Test ADK: curl http://localhost:8000/api/v2/adk/health"

