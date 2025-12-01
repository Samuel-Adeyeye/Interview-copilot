# PostgreSQL Session Storage Setup

## Overview

The Interview Co-Pilot supports PostgreSQL for session storage using ADK's `DatabaseSessionService`. This provides persistent, scalable session management.

## Configuration

### Environment Variables

To enable PostgreSQL session storage, set in your `.env` file:

```env
# Enable session persistence
SESSION_PERSISTENCE_ENABLED=true

# Use PostgreSQL (via ADK DatabaseSessionService)
SESSION_STORAGE_TYPE=database

# PostgreSQL connection string
DATABASE_URL=postgresql://username:password@host:port/database_name

# Example for local PostgreSQL
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/interview_copilot

# Example for Docker
DATABASE_URL=postgresql://postgres:postgres@db:5432/interview_copilot
```

### Settings

The application will automatically:
1. Detect `SESSION_STORAGE_TYPE=database`
2. Use ADK's `DatabaseSessionService` with your `DATABASE_URL`
3. Create necessary tables automatically (no manual schema setup required)

## How It Works

### Automatic Schema Creation

ADK's `DatabaseSessionService` automatically creates the necessary database tables when first used. No manual migrations or schema setup is required.

### Session Service Selection

The application selects the session service based on `SESSION_STORAGE_TYPE`:

- `"file"` → `PersistentSessionService` (JSON files)
- `"sqlite"` → `PersistentSessionService` (SQLite database)
- `"database"` → `ADKSessionService` with `DatabaseSessionService` (PostgreSQL)

## Verification

### Check Configuration

```bash
python -c "from config.settings import settings; print(f'Storage Type: {settings.SESSION_STORAGE_TYPE}'); print(f'Database URL: {settings.DATABASE_URL}')"
```

### Test Database Connection

```bash
python scripts/verify_database_setup.py
```

### Check Application Logs

When the application starts, you should see:

```
INFO:api.main:Initializing persistent session service (type: database)...
INFO:memory.adk.session_service:✅ Using ADK DatabaseSessionService: postgresql://...
INFO:api.main:✅ ADK DatabaseSessionService initialized (PostgreSQL)
```

## Troubleshooting

### Error: "Unsupported storage_type: database"

**Cause**: The code was trying to use `PersistentSessionService` which doesn't support "database".

**Solution**: The code has been updated to use `ADKSessionService` when `SESSION_STORAGE_TYPE=database`. Make sure you're using the latest code.

### Error: "db_url is required when use_database=True"

**Cause**: `DATABASE_URL` is not set or is empty.

**Solution**: Set `DATABASE_URL` in your `.env` file:
```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/interview_copilot
```

### Error: "could not connect to server"

**Cause**: PostgreSQL is not running or connection string is incorrect.

**Solution**:
1. Verify PostgreSQL is running:
   ```bash
   # Local
   pg_isready
   
   # Docker
   docker-compose ps db
   ```

2. Check connection string format:
   ```
   postgresql://username:password@host:port/database
   ```

3. For Docker, use service name `db` as host:
   ```
   DATABASE_URL=postgresql://postgres:postgres@db:5432/interview_copilot
   ```

### Tables Not Created

**Cause**: ADK creates tables on first session creation.

**Solution**: This is normal. Tables will be created automatically when you create your first session. You can verify by:
1. Creating a session via the API
2. Checking tables in PostgreSQL:
   ```bash
   docker-compose exec db psql -U postgres -d interview_copilot -c "\dt"
   ```

## Migration from File to Database

To migrate existing sessions from file storage to PostgreSQL:

1. **Backup existing sessions**:
   ```bash
   cp -r data/sessions data/sessions.backup
   ```

2. **Update `.env`**:
   ```env
   SESSION_STORAGE_TYPE=database
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/interview_copilot
   ```

3. **Restart application**:
   ```bash
   # The application will start using PostgreSQL
   # New sessions will be stored in PostgreSQL
   # Old file-based sessions remain in data/sessions/
   ```

**Note**: File-based sessions are not automatically migrated. You would need to write a migration script if you want to transfer existing sessions.

## Benefits of PostgreSQL Session Storage

1. **Scalability**: Can handle many concurrent sessions
2. **Persistence**: Survives application restarts
3. **Querying**: Can query sessions using SQL
4. **Backup**: Standard PostgreSQL backup tools
5. **Performance**: Better performance for large numbers of sessions

## Comparison

| Feature | File Storage | SQLite | PostgreSQL (ADK) |
|---------|-------------|--------|-------------------|
| Setup | None | None | Requires PostgreSQL |
| Scalability | Limited | Limited | High |
| Querying | No | SQL | SQL |
| Backup | File copy | File copy | pg_dump |
| Performance | Good (small) | Good (medium) | Excellent (large) |

## Additional Resources

- [ADK Session Service Documentation](https://google.github.io/adk-docs/sessions/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Database Setup Guide](docs/DATABASE_SETUP.md)

