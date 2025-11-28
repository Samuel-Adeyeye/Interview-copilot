# Phase 4: Orchestrator Migration - Implementation Guide

## Overview

Phase 4 migrates the LangGraph-based orchestrator to ADK workflow patterns. This document describes the migration strategy and implementation details.

## Migration Status

| Component | Current | ADK Equivalent | Status |
|-----------|---------|----------------|--------|
| Orchestrator | LangGraph StateGraph | SequentialAgent / LLM Orchestrator | ✅ Complete |
| State Management | TypedDict State | ADK Session State | ✅ Complete |
| Conditional Routing | Custom edges | SequentialAgent / LLM routing | ✅ Complete |

## Orchestrator Implementation

### 1. ADK Orchestrator (`agents/adk/orchestrator.py`)

**Migration**: LangGraph Orchestrator → ADK Orchestrator

**Key Changes**:
- Uses `SequentialAgent` for fixed workflow
- Alternative: LLM-based orchestrator for dynamic routing
- State managed via ADK session state
- Same API maintained for backward compatibility

**Two Strategies**:

#### Strategy 1: SequentialAgent (Recommended)
```python
workflow = SequentialAgent(
    name="InterviewOrchestrator",
    sub_agents=[
        research_agent,
        technical_agent,
        companion_agent
    ]
)
```

**Pros**:
- ✅ Simple and predictable
- ✅ Fast execution
- ✅ Guaranteed order

**Cons**:
- ❌ Fixed order (can't skip agents dynamically)
- ❌ Less flexible

#### Strategy 2: LLM-Based Orchestrator
```python
orchestrator = LlmAgent(
    name="Orchestrator",
    instruction="Coordinate workflow...",
    tools=[
        AgentTool(research_agent),
        AgentTool(technical_agent),
        AgentTool(companion_agent)
    ]
)
```

**Pros**:
- ✅ Dynamic routing
- ✅ Can skip agents intelligently
- ✅ More flexible

**Cons**:
- ❌ Slower (LLM decides routing)
- ❌ Less predictable
- ❌ Higher cost

---

## Usage Examples

### Example 1: Create Orchestrator

```python
from agents.adk.orchestrator import create_adk_orchestrator

# Option 1: Sequential workflow (default)
orchestrator = create_adk_orchestrator(
    use_sequential=True,
    use_builtin_code_executor=True
)

# Option 2: LLM-based orchestrator
orchestrator = create_adk_orchestrator(
    use_sequential=False,
    use_builtin_code_executor=True
)
```

### Example 2: Execute Full Workflow

```python
result = await orchestrator.execute(
    session_id="session_123",
    user_id="user_456",
    inputs={
        "company_name": "Google",
        "job_description": "Software Engineer...",
        "mode": "select_questions",
        "difficulty": "medium",
        "num_questions": 3
    }
)

print(result)
# {
#     "success": True,
#     "research": {...},
#     "technical": {...},
#     "companion": {...}
# }
```

### Example 3: Execute Individual Agents

```python
# Research only
research_result = await orchestrator.execute_research(
    session_id="session_123",
    user_id="user_456",
    job_description="...",
    company_name="Google"
)

# Technical only
technical_result = await orchestrator.execute_technical(
    session_id="session_123",
    user_id="user_456",
    mode="evaluate_code",
    question_id="q1",
    code="def solution(): ...",
    language="python"
)
```

---

## Migration Patterns

### Pattern 1: Workflow Creation

**Before (LangGraph)**:
```python
workflow = StateGraph(OrchestratorState)
workflow.add_node("research", self._run_research)
workflow.add_node("technical", self._run_technical)
workflow.add_edge("research", "technical")
workflow.set_entry_point("research")
compiled = workflow.compile()
```

**After (ADK - Sequential)**:
```python
workflow = SequentialAgent(
    name="InterviewOrchestrator",
    sub_agents=[research_agent, technical_agent, companion_agent]
)
```

**After (ADK - LLM)**:
```python
orchestrator = LlmAgent(
    name="Orchestrator",
    instruction="Coordinate workflow...",
    tools=[
        AgentTool(research_agent),
        AgentTool(technical_agent),
        AgentTool(companion_agent)
    ]
)
```

### Pattern 2: State Management

**Before (LangGraph)**:
```python
class OrchestratorState(TypedDict):
    research_result: Optional[Dict]
    technical_result: Optional[Dict]
    # ...

state["research_result"] = result
```

**After (ADK)**:
```python
# State managed via session.state
# Access via output_key
research_agent = LlmAgent(..., output_key="research_packet")
# Result stored in session.state["research_packet"]
```

### Pattern 3: Conditional Routing

**Before (LangGraph)**:
```python
workflow.add_conditional_edges(
    "research",
    self._should_skip_technical,
    {"skip": "companion", "continue": "technical"}
)
```

**After (ADK - Sequential)**:
```python
# Fixed order - always executes all agents
# Can't skip dynamically
```

**After (ADK - LLM)**:
```python
# LLM decides which agents to call
# Can skip agents based on context
```

---

## API Compatibility

The ADK orchestrator maintains the same API as the LangGraph version:

### Methods Preserved:
- ✅ `execute()` - Full workflow execution
- ✅ `execute_research()` - Research only
- ✅ `execute_technical()` - Technical only

### State Structure:
- ✅ Same result dictionary format
- ✅ Same error handling
- ✅ Same execution time tracking

---

## Integration with Runner

The orchestrator uses `InMemoryRunner` for execution:

```python
from google.adk.runners import InMemoryRunner

runner = InMemoryRunner(agent=orchestrator.workflow)

async for event in runner.run_async(
    user_id=user_id,
    session_id=session_id,
    new_message=query
):
    # Process events
    pass
```

---

## State Access

In ADK, agent results are stored in session state via `output_key`:

```python
# Research agent stores result
research_agent = LlmAgent(..., output_key="research_packet")
# Access: session.state["research_packet"]

# Technical agent stores result
technical_agent = LlmAgent(..., output_key="technical_result")
# Access: session.state["technical_result"]

# Companion agent stores result
companion_agent = LlmAgent(..., output_key="companion_output")
# Access: session.state["companion_output"]
```

---

## Next Steps

1. ✅ **Phase 4 Complete**: Orchestrator migrated to ADK
2. **Phase 5**: Migrate session and memory services
3. **Phase 6**: Integrate with Runner and App
4. **Testing**: Comprehensive workflow testing

---

## Notes

- The ADK orchestrator maintains backward compatibility with the existing API
- Two strategies available: SequentialAgent (fast, fixed) or LLM orchestrator (flexible, dynamic)
- State management handled by ADK session service
- Results accessible via session.state[output_key]

---

**Last Updated**: 2025-01-20  
**Status**: Phase 4 Complete ✅

