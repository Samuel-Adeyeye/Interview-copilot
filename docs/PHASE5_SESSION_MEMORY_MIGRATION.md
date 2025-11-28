# Phase 5: Session & Memory Migration - Implementation Guide

## Overview

Phase 5 migrates custom session and memory services to ADK equivalents. This document describes the migration strategy and implementation details.

## Migration Status

| Component | Current | ADK Equivalent | Status |
|-----------|---------|----------------|--------|
| Session Service | Custom InMemorySessionService | ADK InMemorySessionService | ✅ Complete |
| Session Service | PersistentSessionService | ADK DatabaseSessionService | ✅ Complete |
| Memory Service | MemoryBank (ChromaDB) | ADK InMemoryMemoryService | ✅ Complete |
| Memory Service | MemoryBank (ChromaDB) | ADK VertexAIMemoryBank | ✅ Complete |

## Service Implementations

### 1. ADK Session Service (`memory/adk/session_service.py`)

**Migration**: Custom Session Service → ADK Session Service

**Key Features**:
- Wraps ADK `InMemorySessionService` or `DatabaseSessionService`
- Maintains backward compatibility with custom API
- Provides same methods as custom service
- Handles state conversion between formats

**Usage**:
```python
from memory.adk.session_service import create_adk_session_service

# Option 1: In-memory (development)
session_service = create_adk_session_service(use_database=False)

# Option 2: Database (production)
session_service = create_adk_session_service(
    use_database=True,
    db_url="sqlite:///sessions.db"
)
```

**Methods Preserved**:
- ✅ `create_session()` - Create new session
- ✅ `get_session()` - Retrieve session
- ✅ `update_agent_state()` - Update agent state
- ✅ `add_artifact()` - Add artifact
- ✅ `create_checkpoint()` - Create checkpoint
- ✅ `pause_session()` - Pause session
- ✅ `resume_session()` - Resume session
- ✅ `complete_session()` - Complete session
- ✅ `delete_session()` - Delete session
- ✅ `update_session_metadata()` - Update metadata

---

### 2. ADK Memory Service (`memory/adk/memory_service.py`)

**Migration**: Custom MemoryBank (ChromaDB) → ADK Memory Service

**Key Features**:
- Wraps ADK `InMemoryMemoryService` or `VertexAIMemoryBank`
- Maintains backward compatibility with MemoryBank API
- Provides fallback in-memory storage if ADK not available
- Handles semantic search and retrieval

**Usage**:
```python
from memory.adk.memory_service import create_adk_memory_service

# Option 1: In-memory (development)
memory_service = create_adk_memory_service(use_vertex_ai=False)

# Option 2: Vertex AI (production)
memory_service = create_adk_memory_service(
    use_vertex_ai=True,
    project_id="your-project",
    location="us-central1",
    memory_bank_id="interview-copilot-memory"
)
```

**Methods Preserved**:
- ✅ `store_research()` - Store research findings
- ✅ `store_session()` - Store session summary
- ✅ `get_user_history()` - Get user session history
- ✅ `search_similar_sessions()` - Semantic search
- ✅ `get_research_by_company()` - Get research by company
- ✅ `get_user_progress()` - Get user progress
- ✅ `store_user_progress()` - Store user progress
- ✅ `update_session_score()` - Update session score

---

## Migration Patterns

### Pattern 1: Session Service Creation

**Before (Custom)**:
```python
from memory.session_service import InMemorySessionService
session_service = InMemorySessionService()
```

**After (ADK)**:
```python
from memory.adk.session_service import create_adk_session_service
session_service = create_adk_session_service(use_database=False)
```

### Pattern 2: Memory Service Creation

**Before (Custom)**:
```python
from memory.memory_bank import MemoryBank
memory_bank = MemoryBank(persist_directory="./data/vectordb")
```

**After (ADK - In-Memory)**:
```python
from memory.adk.memory_service import create_adk_memory_service
memory_service = create_adk_memory_service(use_vertex_ai=False)
```

**After (ADK - Vertex AI)**:
```python
from memory.adk.memory_service import create_adk_memory_service
memory_service = create_adk_memory_service(
    use_vertex_ai=True,
    project_id="your-project",
    location="us-central1",
    memory_bank_id="interview-copilot-memory"
)
```

### Pattern 3: Session Operations

**Before (Custom)**:
```python
session = session_service.create_session(session_id, user_id, metadata)
session_service.update_agent_state(session_id, "research", state)
```

**After (ADK)**:
```python
session = await session_service.create_session(session_id, user_id, metadata)
await session_service.update_agent_state(session_id, "research", state)
# Note: ADK methods are async
```

### Pattern 4: Memory Operations

**Before (Custom)**:
```python
await memory_bank.store_research(session_id, company, research_data)
history = await memory_bank.get_user_history(user_id, limit=10)
```

**After (ADK)**:
```python
await memory_service.store_research(session_id, company, research_data)
history = await memory_service.get_user_history(user_id, limit=10)
# Same API, different implementation
```

---

## Integration with ADK Runner

ADK services integrate seamlessly with Runner:

```python
from google.adk.runners import Runner
from memory.adk.session_service import create_adk_session_service

# Create session service
session_service = create_adk_session_service(use_database=True, db_url="sqlite:///sessions.db")

# Create runner with session service
runner = Runner(
    app=app,
    session_service=session_service
)

# Runner automatically uses session service
async for event in runner.run_async(
    user_id=user_id,
    session_id=session_id,
    new_message=query
):
    # Session automatically managed
    pass
```

---

## State Management

### Session State Structure

**Custom Format**:
```python
{
    "session_id": "session_123",
    "user_id": "user_456",
    "state": "running",
    "agent_states": {...},
    "artifacts": [...],
    "metadata": {...}
}
```

**ADK Format**:
```python
session.state = {
    "custom_state": "running",
    "agent_states": {...},
    "artifacts": [...],
    "metadata": {...}
}
# Plus ADK-specific fields
```

The wrapper handles conversion between formats automatically.

---

## Fallback Behavior

If ADK services are not available, the wrappers provide fallback implementations:

- **Session Service**: Falls back to in-memory dictionary storage
- **Memory Service**: Falls back to in-memory dictionary storage with basic search

This ensures the application continues to work even if ADK is not fully installed.

---

## Configuration

### Environment Variables

```bash
# Session Service
SESSION_STORAGE_TYPE=in_memory  # or "database"
SESSION_STORAGE_PATH=./sessions.db  # for database

# Memory Service
MEMORY_SERVICE_TYPE=in_memory  # or "vertex_ai"
GCP_PROJECT_ID=your-project-id
GCP_LOCATION=us-central1
MEMORY_BANK_ID=interview-copilot-memory
```

### Code Configuration

```python
from config.settings import settings
from memory.adk.session_service import create_adk_session_service
from memory.adk.memory_service import create_adk_memory_service

# Session service
session_service = create_adk_session_service(
    use_database=(settings.SESSION_STORAGE_TYPE == "database"),
    db_url=settings.SESSION_STORAGE_PATH if settings.SESSION_STORAGE_TYPE == "database" else None
)

# Memory service
memory_service = create_adk_memory_service(
    use_vertex_ai=(settings.MEMORY_SERVICE_TYPE == "vertex_ai"),
    project_id=settings.GCP_PROJECT_ID if settings.MEMORY_SERVICE_TYPE == "vertex_ai" else None,
    location=settings.GCP_LOCATION if settings.MEMORY_SERVICE_TYPE == "vertex_ai" else None,
    memory_bank_id=settings.MEMORY_BANK_ID if settings.MEMORY_SERVICE_TYPE == "vertex_ai" else None
)
```

---

## Next Steps

1. ✅ **Phase 5 Complete**: Session and memory services migrated
2. **Phase 6**: Integrate with Runner and App
3. **Phase 7**: Comprehensive testing
4. **Phase 8**: Documentation and cleanup

---

## Notes

- All methods maintain backward compatibility
- ADK methods are async (custom methods were sync/async mix)
- Fallback implementations ensure functionality even without ADK
- State conversion handled automatically by wrappers

---

**Last Updated**: 2025-01-20  
**Status**: Phase 5 Complete ✅

