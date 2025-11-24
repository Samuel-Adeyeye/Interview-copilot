# Error Handling Documentation

## Overview

The Interview Co-Pilot now has a comprehensive, consistent error handling system with custom exceptions and centralized error handling middleware.

## Custom Exception Classes

All custom exceptions inherit from `InterviewCoPilotException` and provide:
- User-friendly error messages
- Error codes for programmatic handling
- Additional details dictionary
- Original error tracking
- Automatic logging

### Exception Hierarchy

```
InterviewCoPilotException (base)
├── AgentExecutionError
├── CodeExecutionError
├── SessionNotFoundError
├── SessionError
├── APIError
├── ValidationError
├── MemoryError
├── ConfigurationError
└── ServiceUnavailableError
```

### Exception Classes

#### `InterviewCoPilotException`
Base exception class for all custom exceptions.

**Attributes:**
- `message`: User-friendly error message
- `error_code`: Error code for programmatic handling
- `details`: Dictionary with additional error details
- `original_error`: Original exception that caused this error

**Methods:**
- `to_dict()`: Convert exception to dictionary for API responses

#### `AgentExecutionError`
Raised when an agent fails to execute properly.

**Usage:**
```python
raise AgentExecutionError(
    agent_name="research",
    message="Failed to fetch company information",
    details={"session_id": "abc123"},
    original_error=original_exception
)
```

#### `CodeExecutionError`
Raised when code execution fails (Judge0 API errors, syntax errors, etc.).

**Usage:**
```python
raise CodeExecutionError(
    message="Code execution timeout",
    language="python",
    code=user_code,
    details={"timeout_seconds": 10}
)
```

#### `SessionNotFoundError`
Raised when a requested session is not found.

**Usage:**
```python
raise SessionNotFoundError(session_id="abc123")
```

#### `SessionError`
Raised for general session-related errors.

**Usage:**
```python
raise SessionError(
    message="Session is in invalid state",
    session_id="abc123"
)
```

#### `APIError`
Raised when external API calls fail (OpenAI, Tavily, Judge0, etc.).

**Usage:**
```python
raise APIError(
    service_name="OpenAI",
    message="API quota exceeded",
    status_code=429,
    original_error=original_exception
)
```

#### `ValidationError`
Raised when input validation fails.

**Usage:**
```python
raise ValidationError(
    message="Invalid input format",
    field="user_id",
    value=provided_value
)
```

#### `MemoryError`
Raised when memory bank operations fail.

**Usage:**
```python
raise MemoryError(
    message="Failed to store session",
    operation="store_session",
    original_error=original_exception
)
```

#### `ConfigurationError`
Raised when configuration is invalid or missing.

**Usage:**
```python
raise ConfigurationError(
    message="Missing required API key",
    config_key="OPENAI_API_KEY"
)
```

#### `ServiceUnavailableError`
Raised when a required service is not available or not initialized.

**Usage:**
```python
raise ServiceUnavailableError(
    service_name="session_service",
    message="Service not initialized"
)
```

## Centralized Error Handler Middleware

The error handler middleware (`middleware/error_handler.py`) automatically:
- Catches all exceptions
- Converts custom exceptions to appropriate HTTP responses
- Handles FastAPI HTTP exceptions
- Handles Pydantic validation errors
- Provides user-friendly error messages
- Logs unexpected errors

### HTTP Status Code Mapping

| Exception Type | HTTP Status Code |
|---------------|------------------|
| `SessionNotFoundError` | 404 Not Found |
| `ValidationError` | 400 Bad Request |
| `ServiceUnavailableError` | 503 Service Unavailable |
| `ConfigurationError` | 500 Internal Server Error |
| `AgentExecutionError` | 400/500 (based on details) |
| `CodeExecutionError` | 400/500 (based on details) |
| `APIError` | 400/500 (based on status_code) |
| `MemoryError` | 500 Internal Server Error |
| `SessionError` | 400/404 (based on message) |
| Other exceptions | 500 Internal Server Error |

### Error Response Format

All error responses follow this format:

```json
{
  "error": "User-friendly error message",
  "error_code": "ERROR_CODE",
  "details": {
    "additional": "information"
  }
}
```

## Usage in Code

### In API Endpoints

```python
from exceptions import SessionNotFoundError, SessionError

@app.get("/sessions/{session_id}")
async def get_session(session_id: str, session_service = Depends(get_session_service)):
    session = session_service.get_session(session_id)
    if not session:
        raise SessionNotFoundError(session_id=session_id)
    return session
```

### In Agents

Agents catch exceptions and return error results:

```python
from exceptions import AgentExecutionError, ValidationError

try:
    # Agent logic
    pass
except ValueError as ve:
    validation_error = ValidationError(
        message=str(ve),
        field="inputs",
        details={"session_id": context.session_id}
    )
    return self._create_result(
        success=False,
        output=None,
        error=validation_error.message
    )
except Exception as e:
    agent_error = AgentExecutionError(
        agent_name="research",
        message=str(e),
        details={"session_id": context.session_id},
        original_error=e
    )
    return self._create_result(
        success=False,
        output=None,
        error=agent_error.message
    )
```

### In Tools

Tools can raise custom exceptions:

```python
from exceptions import CodeExecutionError, APIError

try:
    result = await self._submit_to_judge0(code, language_id)
except httpx.TimeoutException as e:
    raise CodeExecutionError(
        message="Code execution timeout",
        language=language,
        code=code,
        original_error=e
    )
except httpx.HTTPStatusError as e:
    raise APIError(
        service_name="Judge0",
        message=f"API error: {e.response.status_code}",
        status_code=e.response.status_code,
        original_error=e
    )
```

## Best Practices

1. **Use Specific Exceptions**: Use the most specific exception type for the error
2. **Provide Context**: Always include relevant details (session_id, user_id, etc.)
3. **Preserve Original Errors**: Pass `original_error` when wrapping exceptions
4. **User-Friendly Messages**: Write error messages that are helpful to end users
5. **Log Appropriately**: Exceptions automatically log, but add context when needed
6. **Don't Catch Everything**: Let the middleware handle unexpected errors
7. **Validate Early**: Raise `ValidationError` as early as possible

## Error Logging

All exceptions automatically log:
- Exception type and message
- Error code
- Details dictionary
- Full traceback (for original_error)

Logs are structured and include:
- Timestamp
- Exception class name
- Error message
- Stack trace (for debugging)

## Testing Error Handling

### Test Custom Exceptions

```python
from exceptions import SessionNotFoundError

def test_session_not_found():
    error = SessionNotFoundError(session_id="test123")
    assert error.session_id == "test123"
    assert error.error_code == "SESSION_NOT_FOUND"
    assert "test123" in error.message
```

### Test Error Responses

```python
from fastapi.testclient import TestClient
from exceptions import SessionNotFoundError

def test_api_error_response(client: TestClient):
    response = client.get("/sessions/invalid-id")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert "error_code" in data
    assert data["error_code"] == "SESSION_NOT_FOUND"
```

## Migration Guide

### Before (Old Error Handling)

```python
try:
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
except Exception as e:
    logger.error(f"Error: {e}")
    raise HTTPException(status_code=500, detail=str(e))
```

### After (New Error Handling)

```python
session = session_service.get_session(session_id)
if not session:
    raise SessionNotFoundError(session_id=session_id)
# Middleware handles the rest automatically
```

## Future Enhancements

Potential improvements:
- Retry logic with exponential backoff
- Error rate limiting
- Error aggregation and reporting
- Custom error pages for web UI
- Error analytics dashboard

