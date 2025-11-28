# Phase 2: Tool Migration - Implementation Guide

## Overview

Phase 2 migrates all Interview Co-Pilot tools from LangChain to Google ADK equivalents. This document describes the migration strategy and implementation details.

## Migration Status

| Tool | Current | ADK Equivalent | Status |
|------|---------|----------------|--------|
| Search Tool | TavilySearchResults | `google_search` (built-in) | ✅ Complete |
| Code Execution | Custom Judge0 | `BuiltInCodeExecutor` or FunctionTool | ✅ Complete |
| Question Bank | Custom Class | FunctionTool wrapper | ✅ Complete |
| JD Parser | Custom Tool | FunctionTool wrapper | ✅ Complete |

## Tool Implementations

### 1. Search Tool (`tools/adk/search_tool.py`)

**Migration**: Tavily → ADK `google_search`

**Key Changes**:
- No API key required (uses Google's native search)
- Direct replacement - just use `google_search` from ADK
- No configuration needed

**Usage**:
```python
from tools.adk.search_tool import create_adk_search_tool

search_tool = create_adk_search_tool()
agent = LlmAgent(..., tools=[search_tool])
```

**Benefits**:
- ✅ No external API dependency
- ✅ Better integration with Gemini
- ✅ No API key management

---

### 2. Code Execution Tool (`tools/adk/code_exec_tool.py`)

**Migration**: Custom Judge0 → ADK `BuiltInCodeExecutor` or FunctionTool

**Two Options**:

#### Option A: BuiltInCodeExecutor (Recommended for Python)
- Uses Gemini's native code execution
- No external API needed
- Limited to Python code
- Better security (sandboxed by Google)

```python
from tools.adk.code_exec_tool import create_builtin_code_executor

code_executor = create_builtin_code_executor()
agent = LlmAgent(..., code_executor=code_executor)
```

#### Option B: Judge0 FunctionTool (For Multi-Language)
- Wraps existing Judge0 integration
- Supports multiple languages (Python, JavaScript, Java, C++)
- Requires Judge0 API key
- More flexible but external dependency

```python
from tools.adk.code_exec_tool import create_judge0_code_exec_tool

code_tool = create_judge0_code_exec_tool()
agent = LlmAgent(..., tools=[code_tool])
```

**Recommendation**: Use BuiltInCodeExecutor for most cases, Judge0 only if multi-language support is critical.

---

### 3. Question Bank Tool (`tools/adk/question_bank_tool.py`)

**Migration**: Custom Class → ADK FunctionTools

**Key Changes**:
- Wrapped existing QuestionBank methods as FunctionTools
- Each operation is a separate tool
- Maintains backward compatibility

**Available Tools**:
- `get_questions_by_difficulty(difficulty: str)` - Filter by difficulty
- `get_question_by_id(question_id: str)` - Get specific question
- `filter_questions_by_tags(tags: List[str])` - Filter by tags
- `search_questions(query: str)` - Text search
- `get_question_count()` - Get total count

**Usage**:
```python
from tools.adk.question_bank_tool import create_question_bank_tools

# Get all tools
question_tools = create_question_bank_tools()
agent = LlmAgent(..., tools=question_tools)

# Or get specific tools
from tools.adk.question_bank_tool import get_question_selection_tool
tool = get_question_selection_tool()
```

**Benefits**:
- ✅ ADK-compatible
- ✅ Better tool discovery by agents
- ✅ Structured error handling

---

### 4. JD Parser Tool (`tools/adk/jd_parser_tool.py`)

**Migration**: Custom Tool → ADK FunctionTool

**Key Changes**:
- Basic parsing as FunctionTool
- Advanced LLM parsing handled by agents (structured output)
- Maintains compatibility with existing code

**Usage**:
```python
from tools.adk.jd_parser_tool import get_jd_parser_tool

parser_tool = get_jd_parser_tool()
agent = LlmAgent(..., tools=[parser_tool])
```

**Note**: For advanced parsing with structured output, agents will use Gemini's structured output capability directly rather than a separate tool.

---

## Migration Strategy

### Step 1: Parallel Implementation
- ✅ Created ADK tools alongside existing tools
- ✅ No breaking changes to existing code
- ✅ Can test ADK tools independently

### Step 2: Gradual Migration
1. Test ADK tools in isolation
2. Update agents to use ADK tools
3. Remove legacy tool dependencies

### Step 3: Cleanup
- Remove Tavily dependency (if not used elsewhere)
- Keep Judge0 optional (for multi-language support)
- Update documentation

---

## Testing ADK Tools

### Test Search Tool
```python
from tools.adk.search_tool import create_adk_search_tool

search_tool = create_adk_search_tool()
# Tool is ready to use - no setup needed
```

### Test Code Execution
```python
from tools.adk.code_exec_tool import create_builtin_code_executor

executor = create_builtin_code_executor()
# Use in agent with code_executor parameter
```

### Test Question Bank
```python
from tools.adk.question_bank_tool import get_question_selection_tool

tool = get_question_selection_tool()
result = tool.func("easy")  # Test directly
print(result)
```

---

## Integration with Agents

ADK tools will be integrated in Phase 3 (Agent Migration). For now, the tools are ready to use:

```python
from google.adk.agents import LlmAgent
from tools.adk import (
    create_adk_search_tool,
    create_question_bank_tools,
    get_jd_parser_tool
)

# Create agent with ADK tools
agent = LlmAgent(
    name="InterviewAgent",
    model=Gemini(model="gemini-2.5-flash-lite"),
    instruction="...",
    tools=[
        create_adk_search_tool(),
        *create_question_bank_tools(),
        get_jd_parser_tool()
    ]
)
```

---

## Next Steps

1. ✅ **Phase 2 Complete**: All tools migrated to ADK
2. **Phase 3**: Migrate agents to use ADK tools
3. **Phase 4**: Update orchestrator to use ADK workflows
4. **Testing**: Comprehensive testing of all tools

---

## Notes

- All ADK tools follow ADK best practices:
  - Return structured dictionaries with `status` field
  - Include error handling
  - Have clear docstrings for LLM understanding
  - Use type hints for schema generation

- Backward compatibility is maintained:
  - Existing tools still work
  - ADK tools are in separate module
  - Gradual migration possible

---

**Last Updated**: 2025-01-20  
**Status**: Phase 2 Complete ✅

