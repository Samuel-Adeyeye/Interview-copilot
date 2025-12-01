# Session Persistence Documentation

## Overview

The Interview Co-Pilot now supports persistent session storage, allowing sessions to survive server restarts. This is critical for production use where session data should not be lost.

## Features

- **File-based persistence**: JSON file storage (default, simple, no dependencies)
- **SQLite persistence**: Database storage for better performance and querying
- **Automatic loading**: Sessions are loaded on server startup
- **Auto-save**: Sessions are automatically saved on every update
- **Session expiration**: Automatic cleanup of expired sessions
- **Background cleanup**: Periodic task runs every hour to remove expired sessions
- **Graceful shutdown**: Sessions are saved before server shutdown

## Configuration

Add these settings to your `.env` file:

```env
# Session Persistence Settings
SESSION_PERSISTENCE_ENABLED=true
SESSION_STORAGE_TYPE=file  # Options: "file" or "sqlite"
SESSION_STORAGE_PATH=./data/sessions
SESSION_EXPIRATION_HOURS=168  # 7 days default
```

### Settings Explained

- **SESSION_PERSISTENCE_ENABLED**: Enable/disable persistence (default: `true`)
  - `true`: Use `PersistentSessionService` with file or SQLite storage
  - `false`: Use `InMemorySessionService` (data lost on restart)

- **SESSION_STORAGE_TYPE**: Storage backend type
  - `file`: JSON file storage (simple, no dependencies)
  - `sqlite`: SQLite database (better performance, supports queries)

- **SESSION_STORAGE_PATH**: Path to storage location
  - For `file`: Directory where `sessions.json` will be stored
  - For `sqlite`: Path to SQLite database file (e.g., `./data/sessions.db`)

- **SESSION_EXPIRATION_HOURS**: Hours before sessions expire (default: 168 = 7 days)

## Storage Types

### File-based Storage

- **Location**: `{SESSION_STORAGE_PATH}/sessions.json`
- **Backup**: Automatic backup created before each save (`.json.bak`)
- **Format**: JSON with atomic writes (uses temporary file + rename)
- **Pros**: Simple, no dependencies, human-readable
- **Cons**: Slower for large datasets, no querying

### SQLite Storage

- **Location**: `{SESSION_STORAGE_PATH}` (if ends with `.db`) or `{SESSION_STORAGE_PATH}/sessions.db`
- **Schema**: Automatic table creation with indexes
- **Pros**: Fast, supports queries, ACID transactions
- **Cons**: Requires SQLite (usually included with Python)

## Usage

### Automatic

The persistent session service is automatically used when `SESSION_PERSISTENCE_ENABLED=true`. No code changes needed!

### Manual Save

You can manually trigger a save:

```python
# In API code
if isinstance(session_service, PersistentSessionService):
    session_service.force_save()
```

### Storage Statistics

Get storage statistics via API endpoint:

```bash
GET /sessions/storage/stats
```

Response:
```json
{
  "storage_type": "file",
  "storage_path": "./data/sessions",
  "total_sessions": 42,
  "active_sessions": 5,
  "expiration_hours": 168,
  "auto_save": true,
  "file_size_bytes": 123456
}
```

## Session Lifecycle

1. **Creation**: Session created → Saved to storage
2. **Updates**: Any state change → Auto-saved
3. **Expiration**: Sessions older than `SESSION_EXPIRATION_HOURS` are cleaned up
4. **Shutdown**: All sessions saved before server stops

## Background Cleanup

A background task runs every hour to:
- Find sessions older than expiration time
- Remove expired sessions
- Log cleanup statistics

The cleanup task is automatically cancelled on server shutdown.

## Migration

### From In-Memory to Persistent

1. Set `SESSION_PERSISTENCE_ENABLED=true` in `.env`
2. Restart server
3. Existing in-memory sessions will be lost (expected)
4. New sessions will be persisted

### Switching Storage Types

1. Stop server
2. If switching from file to SQLite:
   - Sessions in JSON file won't be automatically migrated
   - Consider exporting/importing if needed
3. Update `SESSION_STORAGE_TYPE` in `.env`
4. Restart server

## Troubleshooting

### Sessions Not Persisting

1. Check `SESSION_PERSISTENCE_ENABLED=true` in `.env`
2. Verify storage path is writable
3. Check server logs for errors
4. Verify disk space available

### Corrupted Sessions File

- Backup file (`.json.bak`) is created before each save
- Restore from backup if needed
- SQLite has automatic recovery

### Performance Issues

- For large numbers of sessions, use SQLite instead of file storage
- Adjust `SESSION_EXPIRATION_HOURS` to clean up old sessions more aggressively
- Monitor storage size via `/sessions/storage/stats` endpoint

## API Endpoints

### Get Storage Statistics

```http
GET /sessions/storage/stats
```

Returns storage statistics including:
- Storage type and path
- Total and active sessions
- Storage size
- Configuration settings

## Code Examples

### Check if Persistence is Enabled

```python
from memory.persistent_session_service import PersistentSessionService

if isinstance(session_service, PersistentSessionService):
    print("Persistence is enabled")
    stats = session_service.get_storage_stats()
    print(f"Total sessions: {stats['total_sessions']}")
```

### Manual Cleanup

```python
if isinstance(session_service, PersistentSessionService):
    deleted = session_service.cleanup_expired_sessions(max_age_hours=24)
    print(f"Deleted {deleted} expired sessions")
```

## Best Practices

1. **Production**: Always enable persistence (`SESSION_PERSISTENCE_ENABLED=true`)
2. **Storage Type**: Use SQLite for production, file for development
3. **Expiration**: Set reasonable expiration based on your use case
4. **Backups**: Regularly backup the storage directory
5. **Monitoring**: Monitor storage size and session counts

## Future Enhancements

Potential future improvements:
- Redis integration for distributed systems
- PostgreSQL support for larger deployments
- Session migration tools
- Compression for old sessions
- Session archiving

