# Docker Setup Guide

## Overview

The Interview Co-Pilot can be run using Docker and Docker Compose. This guide covers setup, configuration, and deployment.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- At least 4GB RAM available
- 10GB free disk space

## Quick Start

### Development

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Production

```bash
# Build and start with production settings
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Services

### API Service

- **Port**: 8000
- **Health Check**: `http://localhost:8000/health`
- **Dependencies**: PostgreSQL, Redis
- **Volumes**: 
  - `./data` → `/app/data` (persistent data)
  - `./logs` → `/app/logs` (application logs)

### Database (PostgreSQL)

- **Port**: 5432
- **Image**: `postgres:15-alpine`
- **Data Volume**: `postgres_data`
- **Health Check**: PostgreSQL readiness check

### Redis

- **Port**: 6379
- **Image**: `redis:7-alpine`
- **Data Volume**: `redis_data`
- **Health Check**: Redis ping

### UI Service (Streamlit)

- **Port**: 8501
- **Health Check**: `http://localhost:8501/_stcore/health`
- **Dependencies**: API service

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# API Keys (Required)
OPENAI_API_KEY=your_openai_key
TAVILY_API_KEY=your_tavily_key
JUDGE0_API_KEY=your_judge0_key

# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=interview_copilot
DATABASE_URL=postgresql://postgres:postgres@db:5432/interview_copilot

# Redis
REDIS_URL=redis://redis:6379

# Vector Database
VECTOR_DB_PATH=/app/data/vectordb

# Session Persistence
SESSION_PERSISTENCE_ENABLED=true
SESSION_STORAGE_TYPE=file
SESSION_STORAGE_PATH=/app/data/sessions
SESSION_EXPIRATION_HOURS=168

# LLM Settings
LLM_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.7

# Observability
LOG_LEVEL=INFO
METRICS_PORT=8001

# API URL for UI
API_URL=http://api:8000
```

### Volume Mounts

The following directories are mounted as volumes:

- `./data` → `/app/data` - Persistent data (vector DB, sessions)
- `./logs` → `/app/logs` - Application logs

**Important**: Ensure these directories exist and have proper permissions:

```bash
mkdir -p data/vectordb data/sessions logs
chmod -R 755 data logs
```

## Health Checks

All services include health checks:

- **API**: Checks `/health` endpoint every 30s
- **Database**: PostgreSQL readiness check every 10s
- **Redis**: Redis ping every 10s
- **UI**: Streamlit health check every 30s

View health status:

```bash
docker-compose ps
```

## Building Images

### Build API Image

```bash
docker build -t interview-copilot-api .
```

### Build UI Image

```bash
docker build -f Dockerfile.ui -t interview-copilot-ui .
```

### Build All Services

```bash
docker-compose build
```

## Development Workflow

### Using Development Override

```bash
# Start with development settings (hot reload, debug logging)
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

Development settings:
- Source code mounted for hot reload
- Debug logging enabled
- API runs with `--reload` flag

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f ui
docker-compose logs -f db
```

### Accessing Services

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **UI**: http://localhost:8501
- **Database**: localhost:5432
- **Redis**: localhost:6379

### Executing Commands

```bash
# Run command in API container
docker-compose exec api python -m pytest

# Access database
docker-compose exec db psql -U postgres -d interview_copilot

# Access Redis CLI
docker-compose exec redis redis-cli
```

## Production Deployment

### Using Production Override

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

Production settings:
- Multiple API workers (4 workers)
- Resource limits configured
- Optimized logging (INFO level)
- Always restart policy

### Resource Limits

Production configuration includes resource limits:

- **API**: 2 CPU, 2GB RAM
- **Database**: 1 CPU, 1GB RAM
- **Redis**: 0.5 CPU, 512MB RAM
- **UI**: 1 CPU, 1GB RAM

### Scaling

Scale API service:

```bash
docker-compose up -d --scale api=3
```

## Data Persistence

### Volumes

Named volumes for persistent data:

- `postgres_data`: PostgreSQL database files
- `redis_data`: Redis persistence files

### Backup

Backup PostgreSQL:

```bash
# Create backup
docker-compose exec db pg_dump -U postgres interview_copilot > backup.sql

# Restore backup
docker-compose exec -T db psql -U postgres interview_copilot < backup.sql
```

Backup application data:

```bash
# Backup data directory
tar -czf data-backup.tar.gz data/

# Restore data directory
tar -xzf data-backup.tar.gz
```

## Troubleshooting

### Services Not Starting

1. Check logs:
   ```bash
   docker-compose logs
   ```

2. Check health status:
   ```bash
   docker-compose ps
   ```

3. Verify environment variables:
   ```bash
   docker-compose config
   ```

### Port Conflicts

If ports are already in use:

1. Edit `docker-compose.yml` to change port mappings
2. Or stop conflicting services

### Permission Issues

If you see permission errors:

```bash
# Fix data directory permissions
sudo chown -R $USER:$USER data/ logs/
chmod -R 755 data/ logs/
```

### Database Connection Issues

1. Verify database is healthy:
   ```bash
   docker-compose ps db
   ```

2. Check database logs:
   ```bash
   docker-compose logs db
   ```

3. Test connection:
   ```bash
   docker-compose exec api python -c "import psycopg2; psycopg2.connect('postgresql://postgres:postgres@db:5432/interview_copilot')"
   ```

### Out of Memory

If containers are killed due to memory:

1. Increase Docker memory limit
2. Reduce resource limits in `docker-compose.prod.yml`
3. Scale down services

## Security Considerations

### Production Checklist

- [ ] Change default database passwords
- [ ] Use secrets management (Docker secrets, AWS Secrets Manager, etc.)
- [ ] Enable SSL/TLS for database connections
- [ ] Configure firewall rules
- [ ] Use non-root user (already configured)
- [ ] Regularly update base images
- [ ] Scan images for vulnerabilities
- [ ] Use `.dockerignore` to exclude sensitive files

### Secrets Management

For production, use Docker secrets or environment variable management:

```yaml
# docker-compose.prod.yml
services:
  api:
    secrets:
      - openai_api_key
      - database_password
secrets:
  openai_api_key:
    external: true
  database_password:
    external: true
```

## Monitoring

### Health Checks

Monitor service health:

```bash
# Check all services
docker-compose ps

# Check specific service
docker inspect interview-copilot-api | jq '.[0].State.Health'
```

### Logs

Centralized logging options:

1. **Docker logging driver**:
   ```yaml
   logging:
     driver: "json-file"
     options:
       max-size: "10m"
       max-file: "3"
   ```

2. **External logging** (ELK, Loki, etc.):
   ```yaml
   logging:
     driver: "gelf"
     options:
       gelf-address: "udp://localhost:12201"
   ```

## Cleanup

### Stop and Remove Containers

```bash
# Stop services
docker-compose down

# Remove volumes (WARNING: deletes data)
docker-compose down -v
```

### Remove Images

```bash
# Remove all images
docker-compose down --rmi all
```

### Clean Build

```bash
# Rebuild without cache
docker-compose build --no-cache
```

## Best Practices

1. **Always use `.env` file** for configuration
2. **Never commit `.env`** to version control
3. **Use named volumes** for persistent data
4. **Set resource limits** in production
5. **Enable health checks** for all services
6. **Use multi-stage builds** for smaller images (future)
7. **Regularly update** base images
8. **Monitor resource usage**
9. **Backup data regularly**
10. **Use production override** for production deployments

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Streamlit Deployment](https://docs.streamlit.io/deploy)

