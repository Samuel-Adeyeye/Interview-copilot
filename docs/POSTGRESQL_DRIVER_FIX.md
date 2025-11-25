# PostgreSQL Driver Fix for ADK DatabaseSessionService

## Issue

ADK's `DatabaseSessionService` requires an **async PostgreSQL driver**, but the project currently has `psycopg2-binary` (synchronous driver) installed.

**Error**:
```
sqlalchemy.exc.InvalidRequestError: The asyncio extension requires an async driver to be used. 
The loaded 'psycopg2' is not async.
```

## Solution

Install the async PostgreSQL driver `psycopg` (version 3+):

```bash
pip install "psycopg[binary]>=3.1.0"
```

Or update `requirements.txt` and reinstall:

```bash
pip install -r requirements.txt
```

## Updated Requirements

The `requirements.txt` has been updated to include:

```txt
psycopg2-binary>=2.9.0  # For legacy/sync operations
psycopg[binary]>=3.1.0  # Async PostgreSQL driver for ADK DatabaseSessionService
```

## Why Both?

- **`psycopg2-binary`**: Used by legacy code and other parts of the application
- **`psycopg[binary]`**: Required by ADK's `DatabaseSessionService` for async operations

## Verification

After installing, verify the driver:

```bash
python -c "import psycopg; print('✅ psycopg (async) installed')"
python -c "import psycopg2; print('✅ psycopg2 (sync) installed')"
```

## Connection String

The connection string format remains the same:

```
postgresql://username:password@host:port/database
```

SQLAlchemy will automatically use the async driver (`psycopg`) when creating async engines.

## Next Steps

1. Install the async driver:
   ```bash
   pip install "psycopg[binary]>=3.1.0"
   ```

2. Restart your application:
   ```bash
   uvicorn api.main:app --reload
   ```

3. Verify PostgreSQL session service initializes:
   ```
   INFO:memory.adk.session_service:✅ Using ADK DatabaseSessionService: ...
   ```

## Troubleshooting

### Still Getting Driver Error

1. **Verify installation**:
   ```bash
   pip list | grep psycopg
   ```

2. **Reinstall if needed**:
   ```bash
   pip uninstall psycopg psycopg-binary
   pip install "psycopg[binary]>=3.1.0"
   ```

3. **Check virtual environment**:
   Make sure you're installing in the correct virtual environment:
   ```bash
   which python
   source venv/bin/activate  # If using venv
   ```

### Alternative: Use File Storage Temporarily

If you need to run the application immediately while fixing the driver issue:

```env
SESSION_STORAGE_TYPE=file
```

This will use file-based storage until the async driver is installed.

