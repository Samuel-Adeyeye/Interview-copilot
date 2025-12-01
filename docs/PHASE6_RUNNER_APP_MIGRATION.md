# Phase 6: Runner & App Integration - Implementation Guide

## Overview

Phase 6 integrates ADK Runner and App with the FastAPI backend. This document describes the integration strategy and implementation details.

## Migration Status

| Component | Current | ADK Equivalent | Status |
|-----------|---------|----------------|--------|
| API Endpoints | Custom orchestrator calls | ADK Runner endpoints | ✅ Complete |
| App Setup | Manual service initialization | ADK App | ✅ Complete |
| Session Management | Custom session service | ADK Session Service | ✅ Complete |
| Streaming | Custom async generators | ADK Runner events | ✅ Complete |

## Implementation

### 1. ADK Application (`api/adk_app.py`)

**Purpose**: Manages ADK App and Runner instances

**Key Features**:
- Creates and configures ADK App with orchestrator
- Sets up Runner with session service
- Provides methods for running workflows
- Handles configuration from settings

**Usage**:
```python
from api.adk_app import get_adk_app, initialize_adk_app

# Initialize (in lifespan)
adk_app = initialize_adk_app(
    use_sequential_orchestrator=True,
    use_builtin_code_executor=True
)

# Use in endpoints
adk_app = get_adk_app()
async for event in adk_app.run_workflow(user_id, session_id, message):
    # Process events
    pass
```

---

### 2. ADK API Endpoints (`api/adk_endpoints.py`)

**Purpose**: FastAPI endpoints using ADK Runner

**Endpoints**:
- `POST /api/v2/adk/research` - Run research agent
- `POST /api/v2/adk/technical` - Run technical agent
- `POST /api/v2/adk/workflow` - Run full workflow
- `GET /api/v2/adk/health` - Health check

**Features**:
- Streaming responses (Server-Sent Events)
- Request validation
- Error handling
- Event-based responses

---

## Integration Steps

### Step 1: Initialize ADK App in Lifespan

```python
from api.adk_app import initialize_adk_app

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing ADK Application...")
    adk_app = initialize_adk_app(
        use_sequential_orchestrator=True,
        use_builtin_code_executor=True
    )
    app.state.adk_app = adk_app
    logger.info("✅ ADK Application initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down ADK Application...")
```

### Step 2: Include ADK Router

```python
from api.adk_endpoints import router as adk_router

app = FastAPI(...)
app.include_router(adk_router)
```

### Step 3: Use ADK Endpoints

```python
# Client can now call:
POST /api/v2/adk/research
POST /api/v2/adk/technical
POST /api/v2/adk/workflow
```

---

## API Comparison

### Research Endpoint

**Before (Custom)**:
```python
POST /api/v1/research
{
    "session_id": "...",
    "job_description": "...",
    "company_name": "..."
}
# Returns: JSON response
```

**After (ADK)**:
```python
POST /api/v2/adk/research
{
    "session_id": "...",
    "user_id": "...",
    "company_name": "...",
    "job_description": "..."
}
# Returns: Streaming SSE response
```

### Technical Endpoint

**Before (Custom)**:
```python
POST /api/v1/technical/select-questions
{
    "session_id": "...",
    "difficulty": "medium",
    "num_questions": 3
}
# Returns: JSON response
```

**After (ADK)**:
```python
POST /api/v2/adk/technical
{
    "session_id": "...",
    "user_id": "...",
    "mode": "select_questions",
    "difficulty": "medium",
    "num_questions": 3
}
# Returns: Streaming SSE response
```

---

## Streaming Responses

ADK endpoints use Server-Sent Events (SSE) for streaming:

```python
# Client receives:
data: {"text": "Researching...", "type": "chunk"}

data: {"text": " Found information...", "type": "chunk"}

data: {"text": "Complete response", "type": "complete"}
```

**Client Usage**:
```javascript
const eventSource = new EventSource('/api/v2/adk/research', {
    method: 'POST',
    body: JSON.stringify(request)
});

eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'chunk') {
        // Append to UI
    } else if (data.type === 'complete') {
        // Finalize
    }
};
```

---

## Configuration

### Environment Variables

```bash
# ADK Configuration
GOOGLE_API_KEY=your-api-key
ADK_LLM_MODEL=gemini-2.5-flash-lite
ADK_LLM_TEMPERATURE=0.7

# Session Service
SESSION_PERSISTENCE_ENABLED=true
SESSION_STORAGE_TYPE=database
SESSION_STORAGE_PATH=sqlite:///sessions.db

# Memory Service
MEMORY_SERVICE_TYPE=in_memory  # or "vertex_ai"
GCP_PROJECT_ID=your-project
GCP_LOCATION=us-central1
MEMORY_BANK_ID=interview-copilot-memory
```

### Code Configuration

```python
from api.adk_app import initialize_adk_app

adk_app = initialize_adk_app(
    use_database_session=True,
    db_url="sqlite:///sessions.db",
    use_vertex_ai_memory=False,  # Set to True for production
    use_sequential_orchestrator=True,
    use_builtin_code_executor=True
)
```

---

## Migration Strategy

### Option 1: Parallel APIs (Recommended)
- Keep existing `/api/v1/*` endpoints
- Add new `/api/v2/adk/*` endpoints
- Gradually migrate clients
- Remove old endpoints when migration complete

### Option 2: Direct Replacement
- Replace existing endpoints with ADK versions
- Update all clients immediately
- Higher risk but faster migration

### Option 3: Feature Flag
- Use feature flag to switch between implementations
- Test ADK endpoints in production
- Switch when ready

---

## Testing

### Test ADK Endpoints

```python
import pytest
from fastapi.testclient import TestClient
from api.adk_app import initialize_adk_app

def test_research_endpoint():
    # Initialize ADK app
    adk_app = initialize_adk_app()
    
    # Test endpoint
    client = TestClient(app)
    response = client.post("/api/v2/adk/research", json={
        "session_id": "test_session",
        "user_id": "test_user",
        "company_name": "Google",
        "job_description": "Software Engineer..."
    })
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream"
```

---

## Next Steps

1. ✅ **Phase 6 Complete**: Runner and App integrated
2. **Phase 7**: Comprehensive testing
3. **Phase 8**: Documentation and cleanup
4. **Deployment**: Deploy ADK endpoints to production

---

## Notes

- ADK endpoints use streaming responses (SSE)
- All endpoints require `user_id` in request
- Session management handled automatically by Runner
- Events are streamed in real-time
- Health check endpoint available for monitoring

---

**Last Updated**: 2025-01-20  
**Status**: Phase 6 Complete ✅

