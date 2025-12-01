# ADK Migration Quick Reference Guide

## 🔄 Component Mapping

### Agents

| Current (LangChain) | ADK Equivalent | Notes |
|---------------------|----------------|-------|
| `ResearchAgentStructured` | `LlmAgent` with `google_search` | Use structured output for ResearchPacket |
| `TechnicalAgent` | `LlmAgent` with code execution | Use `BuiltInCodeExecutor` or FunctionTool |
| `CompanionAgent` | `LlmAgent` | Simple conversational agent |

### Tools

| Current | ADK Equivalent | Migration Path |
|---------|----------------|----------------|
| `TavilySearchResults` | `google_search` | Direct replacement - built-in |
| `CodeExecutionTool` (Judge0) | `BuiltInCodeExecutor` or `FunctionTool` | Choose based on needs |
| `QuestionBank` | `FunctionTool` | Wrap existing class methods |
| `JDParserTool` | `FunctionTool` | Convert to function tool |

### Orchestration

| Current (LangGraph) | ADK Equivalent | When to Use |
|---------------------|----------------|-------------|
| `StateGraph` with conditional edges | `SequentialAgent` | Fixed order workflow |
| `StateGraph` with LLM routing | `Agent` with `AgentTool` | Dynamic routing |
| Parallel execution | `ParallelAgent` | Independent tasks |
| Loop/refinement | `LoopAgent` | Iterative improvement |

### Session & Memory

| Current | ADK Equivalent | Use Case |
|---------|----------------|----------|
| `InMemorySessionService` | `InMemorySessionService` | Development/testing |
| `PersistentSessionService` | `DatabaseSessionService` | Production |
| `MemoryBank` (ChromaDB) | `InMemoryMemoryService` | Development |
| `MemoryBank` (ChromaDB) | `VertexAIMemoryBank` | Production (GCP) |

---

## 📝 Code Snippets

### Creating an ADK Agent

```python
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools import google_search
from google.genai import types

retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504]
)

agent = LlmAgent(
    name="ResearchAgent",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config
    ),
    instruction="You are a research specialist...",
    tools=[google_search],
    output_key="research_packet"
)
```

### Creating a Function Tool

```python
from google.adk.tools import FunctionTool

def get_questions(difficulty: str) -> dict:
    """Get coding questions by difficulty level.
    
    Args:
        difficulty: One of 'easy', 'medium', 'hard'
    
    Returns:
        Dictionary with status and questions list
    """
    questions = question_bank.get_questions_by_difficulty(difficulty)
    return {
        "status": "success",
        "questions": questions
    }

question_tool = FunctionTool(get_questions)
```

### Creating a Sequential Workflow

```python
from google.adk.agents import SequentialAgent

workflow = SequentialAgent(
    name="InterviewWorkflow",
    sub_agents=[
        research_agent,
        technical_agent,
        companion_agent
    ]
)
```

### Setting Up Runner

```python
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService
from google.adk.apps.app import App, EventsCompactionConfig

# Create app with compaction
app = App(
    name="interview_copilot",
    root_agent=workflow,
    events_compaction_config=EventsCompactionConfig(
        compaction_interval=5,
        overlap_size=2
    )
)

# Create session service
session_service = DatabaseSessionService(
    db_url="sqlite:///sessions.db"
)

# Create runner
runner = Runner(
    app=app,
    session_service=session_service
)
```

### Running an Agent

```python
from google.genai import types

# Create user message
query = types.Content(
    role="user",
    parts=[types.Part(text="Research Google's interview process")]
)

# Run agent
async for event in runner.run_async(
    user_id="user_123",
    session_id="session_456",
    new_message=query
):
    if event.content and event.content.parts:
        text = event.content.parts[0].text
        print(f"Agent: {text}")
```

### Using Agent as Tool

```python
from google.adk.tools import AgentTool

# Wrap agent as tool
research_tool = AgentTool(research_agent)

# Use in another agent
orchestrator = LlmAgent(
    name="Orchestrator",
    model=Gemini(model="gemini-2.5-flash-lite"),
    instruction="Coordinate workflow...",
    tools=[research_tool, technical_tool, companion_tool]
)
```

---

## 🔑 Key Concepts

### 1. Output Keys
Use `output_key` to store agent results in session state:
```python
agent = LlmAgent(
    ...,
    output_key="research_results"  # Stored in session.state["research_results"]
)
```

### 2. State Placeholders
Reference state values in instructions:
```python
instruction="""Use this research: {research_results}
Create a summary based on: {research_results}"""
```

### 3. Tool Context
Access session state in tools:
```python
from google.adk.tools.tool_context import ToolContext

def my_tool(tool_context: ToolContext, param: str) -> dict:
    # Read state
    value = tool_context.state.get("key")
    
    # Write state
    tool_context.state["new_key"] = "value"
    
    return {"status": "success"}
```

### 4. Context Compaction
Automatically summarize old conversations:
```python
app = App(
    ...,
    events_compaction_config=EventsCompactionConfig(
        compaction_interval=5,  # Compact every 5 turns
        overlap_size=2  # Keep last 2 turns
    )
)
```

---

## 🎯 Decision Matrix

### When to Use SequentialAgent
- ✅ Fixed order of execution
- ✅ Each step depends on previous
- ✅ Predictable workflow
- ❌ Don't use if order is dynamic

### When to Use ParallelAgent
- ✅ Independent tasks
- ✅ Speed is important
- ✅ Tasks don't depend on each other
- ❌ Don't use if tasks share state

### When to Use LoopAgent
- ✅ Iterative refinement needed
- ✅ Quality improvement cycles
- ✅ Review and revise pattern
- ❌ Don't use for one-shot tasks

### When to Use AgentTool
- ✅ Delegation to specialist
- ✅ Agent needs to continue after tool
- ✅ Tool-like usage pattern
- ❌ Don't use for complete handoff

---

## ⚡ Performance Tips

1. **Use Context Compaction**: Reduces token usage and costs
2. **Choose Right Model**: `gemini-2.5-flash-lite` for speed, `gemini-2.0-flash-exp` for quality
3. **Parallel Independent Tasks**: Use `ParallelAgent` for speed
4. **Cache Tool Results**: Implement caching in FunctionTools
5. **Optimize Instructions**: Clear, concise instructions reduce tokens

---

## 🐛 Common Issues & Solutions

### Issue: Agent not using tools
**Solution**: Check tool descriptions in docstrings - LLM uses them to decide when to call tools

### Issue: State not persisting
**Solution**: Ensure using `DatabaseSessionService` and proper session management

### Issue: Context too long
**Solution**: Enable `EventsCompactionConfig` in App

### Issue: Tool errors not handled
**Solution**: Return structured error responses: `{"status": "error", "error_message": "..."}`

---

## 📚 Additional Resources

- [ADK Documentation](https://google.github.io/adk-docs/)
- [ADK Agents Guide](https://google.github.io/adk-docs/agents/)
- [ADK Tools Guide](https://google.github.io/adk-docs/tools/)
- [ADK Sessions Guide](https://google.github.io/adk-docs/sessions/)
- [Gemini API Reference](https://ai.google.dev/gemini-api/docs)

---

**Last Updated**: 2025-01-20

