# Database Setup Guide

## Overview

The Interview Co-Pilot application uses PostgreSQL for persistent data storage. This guide covers database setup, configuration, and verification.

## Current Database Usage

### Default Configuration

By default, the application uses **file-based session storage** (`SESSION_STORAGE_TYPE=file`), which stores sessions in JSON files. PostgreSQL is available but not required for basic operation.

### When PostgreSQL is Used

PostgreSQL is used when:

1. **ADK DatabaseSessionService** is enabled (for ADK session management)
2. **SESSION_STORAGE_TYPE=database** is set in configuration
3. Future features that require relational database storage

## Database Configuration

### Docker Setup (Automatic)

When using Docker Compose, PostgreSQL is automatically configured:

```yaml
db:
  image: postgres:15-alpine
  environment:
    - POSTGRES_USER=postgres
    - POSTGRES_PASSWORD=postgres
    - POSTGRES_DB=interview_copilot
```

The database is created automatically when the container starts.

### Manual Setup

If setting up PostgreSQL manually:

```bash
# Create database
createdb interview_copilot

# Or using psql
psql -U postgres -c "CREATE DATABASE interview_copilot;"
```

## Connection String Format

The database connection string follows this format:

```
postgresql://username:password@host:port/database_name
```

Example:
```
postgresql://postgres:postgres@localhost:5432/interview_copilot
```

## Environment Variables

Configure database connection in `.env`:

```env
# Database Connection
DATABASE_URL=postgresql://postgres:postgres@db:5432/interview_copilot

# For Docker, use service name 'db' as host
# For local development, use 'localhost'

# Session Storage (optional - defaults to file)
SESSION_STORAGE_TYPE=file  # or "database" to use PostgreSQL
SESSION_STORAGE_PATH=./data/sessions  # or DATABASE_URL for database storage
```

## ADK DatabaseSessionService

### Automatic Schema Creation

ADK's `DatabaseSessionService` automatically creates the necessary tables when first used. No manual schema setup is required.

### Enabling Database Sessions

To use PostgreSQL for ADK session storage:

1. **Set environment variables:**
   ```env
   SESSION_STORAGE_TYPE=database
   SESSION_STORAGE_PATH=postgresql://postgres:postgres@db:5432/interview_copilot
   ```

2. **Or configure in code:**
   ```python
   from memory.adk.session_service import create_adk_session_service
   
   session_service = create_adk_session_service(
       use_database=True,
       db_url="postgresql://postgres:postgres@db:5432/interview_copilot"
   )
   ```

## Verification

### Using Verification Script

Run the database verification script:

```bash
python scripts/verify_database_setup.py
```

This script will:
- ✅ Test PostgreSQL connection
- ✅ Check if database exists
- ✅ Create database if needed
- ✅ Verify table structure
- ✅ Check session storage configuration

### Manual Verification

```bash
# Test connection
psql -U postgres -d interview_copilot -c "SELECT version();"

# List tables
psql -U postgres -d interview_copilot -c "\dt"

# Check database size
psql -U postgres -d interview_copilot -c "SELECT pg_size_pretty(pg_database_size('interview_copilot'));"
```

### From Docker Container

```bash
# Connect to database container
docker-compose exec db psql -U postgres -d interview_copilot

# Run verification from API container
docker-compose exec api python scripts/verify_database_setup.py
```

## Database Schema

### ADK DatabaseSessionService Tables

When ADK `DatabaseSessionService` is used, it creates tables automatically. The exact schema depends on the ADK version, but typically includes:

- Session storage tables
- Event storage tables
- Metadata tables

### Current Session Storage

Currently, the application uses file-based storage by default. The schema for file-based storage is:

```json
{
  "session_id": "string",
  "user_id": "string",
  "state": "string",
  "agent_states": {},
  "artifacts": [],
  "checkpoints": [],
  "metadata": {},
  "created_at": "ISO timestamp",
  "updated_at": "ISO timestamp",
  "completed_at": "ISO timestamp"
}
```

## Migration from File to Database

To migrate from file-based to database storage:

1. **Backup existing sessions:**
   ```bash
   cp -r data/sessions data/sessions.backup
   ```

2. **Update configuration:**
   ```env
   SESSION_STORAGE_TYPE=database
   SESSION_STORAGE_PATH=postgresql://postgres:postgres@db:5432/interview_copilot
   ```

3. **Restart application:**
   ```bash
   docker-compose restart api
   ```

4. **Verify migration:**
   ```bash
   python scripts/verify_database_setup.py
   ```

## Troubleshooting

### Connection Issues

**Error**: `could not connect to server`

**Solutions**:
1. Verify PostgreSQL is running:
   ```bash
   docker-compose ps db
   ```

2. Check connection string format
3. Verify network connectivity (for Docker, use service name 'db')

### Database Not Found

**Error**: `database "interview_copilot" does not exist`

**Solution**:
```bash
# Create database
docker-compose exec db psql -U postgres -c "CREATE DATABASE interview_copilot;"
```

### Permission Issues

**Error**: `permission denied`

**Solutions**:
1. Verify user has CREATE DATABASE privilege
2. Check PostgreSQL user configuration
3. Verify password in connection string

### ADK Tables Not Created

**Issue**: ADK DatabaseSessionService tables not appearing

**Solutions**:
1. Verify `use_database=True` is set
2. Check database connection is working
3. Look for errors in application logs
4. ADK creates tables on first session creation

## Best Practices

1. **Use Connection Pooling**: For production, configure connection pooling
2. **Regular Backups**: Set up automated database backups
3. **Monitor Performance**: Track query performance and optimize as needed
4. **Use Migrations**: For custom tables, use proper migration tools
5. **Secure Credentials**: Never commit database passwords to version control

## Backup and Restore

### Backup

```bash
# Backup database
docker-compose exec db pg_dump -U postgres interview_copilot > backup.sql

# Or using docker exec
docker exec interview-copilot-db pg_dump -U postgres interview_copilot > backup.sql
```

### Restore

```bash
# Restore from backup
docker-compose exec -T db psql -U postgres interview_copilot < backup.sql
```

## Production Considerations

1. **Use Managed Database**: Consider using managed PostgreSQL (AWS RDS, Google Cloud SQL, etc.)
2. **Enable SSL**: Use SSL connections for production
3. **Set Resource Limits**: Configure appropriate memory and CPU limits
4. **Monitor Connections**: Track active connections and connection pool usage
5. **Regular Maintenance**: Schedule VACUUM and ANALYZE operations

## Additional Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [ADK Session Service Documentation](https://google.github.io/adk-docs/sessions/)
- [Docker PostgreSQL Image](https://hub.docker.com/_/postgres)

