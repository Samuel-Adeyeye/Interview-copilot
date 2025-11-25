# Docker Quick Start Guide

## 🚀 Quick Start (5 minutes)

### 1. Prerequisites

- Docker and Docker Compose installed
- Google API Key ([Get one here](https://makersuite.google.com/app/apikey))

### 2. Setup

```bash
# Clone the repository (if not already done)
git clone <repository-url>
cd Interview-copilot

# Create .env file
cat > .env << EOF
# Required: Google API Key for ADK
GOOGLE_API_KEY=your_google_api_key_here

# Database (defaults work for development)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=interview_copilot
DATABASE_URL=postgresql://postgres:postgres@db:5432/interview_copilot

# Optional: Legacy API Keys (for backward compatibility)
OPENAI_API_KEY=your_openai_key
TAVILY_API_KEY=your_tavily_key
JUDGE0_API_KEY=your_judge0_key
EOF

# Create data directories
mkdir -p data/vectordb data/sessions logs
chmod -R 755 data logs
```

### 3. Start Services

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

### 4. Verify Installation

```bash
# Check API health
curl http://localhost:8000/health

# Check ADK health
curl http://localhost:8000/api/v2/adk/health

# Check UI
open http://localhost:8501
```

### 5. Access Services

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **ADK Endpoints**: http://localhost:8000/api/v2/adk/*
- **UI**: http://localhost:8501

## 🛠️ Common Commands

```bash
# Stop services
docker-compose down

# Restart services
docker-compose restart

# View logs
docker-compose logs -f api

# Rebuild after code changes
docker-compose build --no-cache
docker-compose up -d

# Access API container shell
docker-compose exec api bash

# Run tests in container
docker-compose exec api pytest
```

## 🔧 Troubleshooting

### Services won't start

```bash
# Check logs
docker-compose logs

# Check if ports are in use
lsof -i :8000
lsof -i :8501
lsof -i :5432
```

### ADK not working

```bash
# Verify API key is set
docker-compose exec api env | grep GOOGLE_API_KEY

# Check ADK health
curl http://localhost:8000/api/v2/adk/health
```

### Database connection issues

```bash
# Check database is running
docker-compose ps db

# Test connection
docker-compose exec api python -c "import psycopg2; psycopg2.connect('postgresql://postgres:postgres@db:5432/interview_copilot')"
```

## 📚 Next Steps

- Read [DOCKER_SETUP.md](docs/DOCKER_SETUP.md) for detailed documentation
- Read [ADK_SETUP_GUIDE.md](docs/ADK_SETUP_GUIDE.md) for ADK configuration
- Check [DOCKER_TROUBLESHOOTING.md](docs/DOCKER_TROUBLESHOOTING.md) for more help

