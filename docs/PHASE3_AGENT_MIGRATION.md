# Phase 3: Agent Migration - Implementation Guide

## Overview

Phase 3 migrates all Interview Co-Pilot agents from LangChain to Google ADK LlmAgent. This document describes the migration strategy and implementation details.

## Migration Status

| Agent | Current | ADK Equivalent | Status |
|-------|---------|----------------|--------|
| ResearchAgent | LangChain + Tavily | ADK LlmAgent + google_search | ✅ Complete |
| TechnicalAgent | LangChain + Judge0 | ADK LlmAgent + code execution | ✅ Complete |
| CompanionAgent | LangChain | ADK LlmAgent | ✅ Complete |

## Agent Implementations

### 1. Research Agent (`agents/adk/research_agent.py`)

**Migration**: LangChain ResearchAgentStructured → ADK LlmAgent

**Key Changes**:
- Uses ADK `google_search` instead of Tavily
- Leverages Gemini's structured output capability
- Simpler implementation (no ReAct agent wrapper needed)
- Uses `output_key` for session state storage

**Usage**:
```python
from agents.adk.research_agent import create_research_agent

# Create agent
research_agent = create_research_agent()

# Use with Runner (Phase 6)
# The agent will automatically use google_search and structure output
```

**Features**:
- ✅ Automatic search tool integration
- ✅ Structured output via Gemini
- ✅ Error handling built-in
- ✅ Memory bank integration ready

**Instruction Strategy**:
The agent's instruction tells it to:
1. Use google_search to find company information
2. Structure findings into ResearchPacket format
3. Provide comprehensive, actionable information

---

### 2. Technical Agent (`agents/adk/technical_agent.py`)

**Migration**: LangChain TechnicalAgent → ADK LlmAgent

**Key Changes**:
- Uses ADK FunctionTools for question bank operations
- Supports both BuiltInCodeExecutor and Judge0
- Two modes: question selection and code evaluation
- Better tool integration

**Usage**:
```python
from agents.adk.technical_agent import create_technical_agent

# Option 1: Use built-in code executor (Python only)
agent = create_technical_agent(use_builtin_code_executor=True)

# Option 2: Use Judge0 (multi-language)
agent = create_technical_agent(
    use_builtin_code_executor=False,
    judge0_api_key="your_key"
)
```

**Specialized Variants**:
- `create_question_selection_agent()` - Focused on question selection
- `create_code_evaluation_agent()` - Focused on code evaluation

**Features**:
- ✅ Question bank tools integrated
- ✅ Code execution (BuiltIn or Judge0)
- ✅ Comprehensive feedback generation
- ✅ Two operational modes

---

### 3. Companion Agent (`agents/adk/companion_agent.py`)

**Migration**: LangChain CompanionAgent → ADK LlmAgent

**Key Changes**:
- Simpler implementation (no tools needed)
- Uses Gemini's conversational capabilities
- Can be specialized for different tasks

**Usage**:
```python
from agents.adk.companion_agent import create_companion_agent

# Create general companion agent
agent = create_companion_agent()

# Or create specialized agents
from agents.adk.companion_agent import (
    create_encouragement_agent,
    create_tips_agent,
    create_summary_agent
)
```

**Specialized Variants**:
- `create_encouragement_agent()` - Only encouragement
- `create_tips_agent()` - Only tips
- `create_summary_agent()` - Only summaries

**Features**:
- ✅ Personalized support generation
- ✅ Performance-based customization
- ✅ Multiple output modes
- ✅ Memory-aware (via session state)

---

## Migration Patterns

### Pattern 1: Agent Creation

**Before (LangChain)**:
```python
class ResearchAgent(BaseAgent):
    def __init__(self, llm, memory_bank):
        # Complex setup
        self.research_agent = create_react_agent(...)
    
    async def run(self, context):
        # Custom execution logic
        pass
```

**After (ADK)**:
```python
def create_research_agent(model=None, memory_bank=None):
    agent = LlmAgent(
        name="ResearchAgent",
        model=model or get_gemini_model(),
        instruction="...",
        tools=[create_adk_search_tool()],
        output_key="research_packet"
    )
    return agent
```

### Pattern 2: Tool Integration

**Before (LangChain)**:
```python
search_tool = TavilySearchResults(...)
agent = Agent(tools=[search_tool])
```

**After (ADK)**:
```python
search_tool = create_adk_search_tool()
agent = LlmAgent(..., tools=[search_tool])
```

### Pattern 3: Structured Output

**Before (LangChain)**:
```python
structured_llm = llm.with_structured_output(ResearchPacket)
result = await structured_llm.ainvoke([...])
```

**After (ADK)**:
```python
# Option 1: Use Gemini's native structured output
# (Handled by model configuration)

# Option 2: Use output_key and parse in post-processing
agent = LlmAgent(..., output_key="research_packet")
# Result stored in session.state["research_packet"]
```

---

## Agent Configuration

### Model Selection

All agents use `get_gemini_model()` from `config/adk_config.py`:
- Default: `gemini-2.5-flash-lite` (fast, cost-effective)
- Configurable via `ADK_MODEL` setting
- Retry configuration included

### Tool Integration

Agents automatically integrate ADK tools:
- ResearchAgent: `google_search`
- TechnicalAgent: Question bank tools + code execution
- CompanionAgent: No tools (LLM-only)

### Output Keys

All agents use `output_key` to store results in session state:
- ResearchAgent: `"research_packet"`
- TechnicalAgent: `"technical_result"`
- CompanionAgent: `"companion_output"`

---

## Usage Examples

### Example 1: Research Agent

```python
from agents.adk.research_agent import create_research_agent
from google.adk.runners import InMemoryRunner
from google.genai import types

# Create agent
agent = create_research_agent()

# Create runner
runner = InMemoryRunner(agent=agent)

# Run research
query = types.Content(
    role="user",
    parts=[types.Part(text="Research Google's interview process for software engineers")]
)

response = await runner.run_debug(query)
# Research packet stored in session.state["research_packet"]
```

### Example 2: Technical Agent

```python
from agents.adk.technical_agent import create_technical_agent

# Create agent with built-in code executor
agent = create_technical_agent(use_builtin_code_executor=True)

# Agent can:
# 1. Select questions: "Get 3 medium difficulty questions"
# 2. Evaluate code: "Evaluate this Python code for question q1"
```

### Example 3: Companion Agent

```python
from agents.adk.companion_agent import create_companion_agent

agent = create_companion_agent()

# Agent can generate:
# - Encouragement based on performance
# - Tips for improvement
# - Session summaries
# - Recommendations
```

---

## Integration with Runner

Agents will be integrated with ADK Runner in Phase 6. For now, they can be used with `InMemoryRunner`:

```python
from google.adk.runners import InMemoryRunner
from agents.adk import create_research_agent

agent = create_research_agent()
runner = InMemoryRunner(agent=agent)

# Run agent
response = await runner.run_debug("Research Google's interview process")
```

---

## Backward Compatibility

All agents maintain backward compatibility:
- Same functionality preserved
- Similar output formats
- Can be used alongside legacy agents during migration

---

## Next Steps

1. ✅ **Phase 3 Complete**: All agents migrated to ADK
2. **Phase 4**: Create orchestrator using ADK workflows
3. **Phase 5**: Migrate session and memory services
4. **Phase 6**: Integrate with Runner and App
5. **Testing**: Comprehensive testing of all agents

---

## Notes

- All ADK agents follow ADK best practices:
  - Clear, specific instructions
  - Proper tool integration
  - Output key usage for state management
  - Error handling via structured responses

- Agents are ready to use but need:
  - ADK installation (pending)
  - Runner integration (Phase 6)
  - Session service integration (Phase 5)

---

**Last Updated**: 2025-01-20  
**Status**: Phase 3 Complete ✅

