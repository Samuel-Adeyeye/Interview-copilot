# Tool Migration Comparison: LangChain → ADK

## Side-by-Side Comparison

### 1. Search Tool

| Aspect | LangChain (Tavily) | ADK (google_search) |
|--------|-------------------|---------------------|
| **Implementation** | `TavilySearchResults` | `google_search` (built-in) |
| **API Key Required** | ✅ Yes (TAVILY_API_KEY) | ❌ No |
| **Setup** | Custom wrapper needed | Direct import |
| **Code** | `create_search_tool()` | `create_adk_search_tool()` |
| **Dependencies** | `langchain-community` | `google-adk` |
| **Integration** | LangChain Tool | ADK Tool (native) |

**Before (LangChain)**:
```python
from tools.search_tool import create_search_tool
search_tool = create_search_tool()  # Requires TAVILY_API_KEY
```

**After (ADK)**:
```python
from tools.adk.search_tool import create_adk_search_tool
search_tool = create_adk_search_tool()  # No API key needed!
```

---

### 2. Code Execution Tool

| Aspect | LangChain (Judge0) | ADK Options |
|--------|-------------------|-------------|
| **Option 1** | Custom Judge0 wrapper | `BuiltInCodeExecutor` |
| **Option 2** | Custom Judge0 wrapper | Judge0 as FunctionTool |
| **API Key** | ✅ Yes (JUDGE0_API_KEY) | Option 1: ❌ No<br>Option 2: ✅ Yes |
| **Languages** | Python, JS, Java, C++ | Option 1: Python only<br>Option 2: All languages |
| **Security** | External service | Option 1: Google sandbox<br>Option 2: External |

**Before (LangChain)**:
```python
from tools.code_exec_tool import create_code_exec_tool
code_tool = create_code_exec_tool(judge0_api_key)  # Always requires API key
```

**After (ADK - Option 1: BuiltIn)**:
```python
from tools.adk.code_exec_tool import create_builtin_code_executor
executor = create_builtin_code_executor()  # No API key, Python only
agent = LlmAgent(..., code_executor=executor)
```

**After (ADK - Option 2: Judge0)**:
```python
from tools.adk.code_exec_tool import create_judge0_code_exec_tool
code_tool = create_judge0_code_exec_tool()  # Multi-language support
agent = LlmAgent(..., tools=[code_tool])
```

---

### 3. Question Bank Tool

| Aspect | LangChain | ADK |
|--------|-----------|-----|
| **Implementation** | Custom class | FunctionTool wrappers |
| **Access Pattern** | Class methods | Function tools |
| **Tool Discovery** | Manual | Automatic (ADK) |
| **Error Handling** | Custom | Structured responses |

**Before (LangChain)**:
```python
from tools.question_bank import QuestionBank
qb = QuestionBank()
questions = qb.get_questions_by_difficulty("easy")
```

**After (ADK)**:
```python
from tools.adk.question_bank_tool import get_question_selection_tool
tool = get_question_selection_tool()
result = tool.func("easy")  # Returns {"status": "success", "questions": [...]}
```

**In Agent**:
```python
from tools.adk.question_bank_tool import create_question_bank_tools
tools = create_question_bank_tools()
agent = LlmAgent(..., tools=tools)
# Agent can now call: get_questions_by_difficulty("easy")
```

---

### 4. JD Parser Tool

| Aspect | LangChain | ADK |
|--------|-----------|-----|
| **Basic Parsing** | Custom function | FunctionTool |
| **Advanced Parsing** | LLM-based tool | Agent structured output |
| **Integration** | Separate tool | Native agent capability |

**Before (LangChain)**:
```python
from tools.jd_parser_tool import parse_job_description_llm
parsed = await parse_job_description_llm(jd_text, llm)
```

**After (ADK - Basic)**:
```python
from tools.adk.jd_parser_tool import get_jd_parser_tool
tool = get_jd_parser_tool()
result = tool.func(jd_text)
```

**After (ADK - Advanced)**:
```python
# Use agent with structured output instead of separate tool
agent = LlmAgent(
    ...,
    # Agent uses Gemini's structured output for parsing
    # No separate tool needed!
)
```

---

## Key Differences

### 1. Tool Creation

**LangChain**:
- Tools are classes or function wrappers
- Manual tool registration
- Custom error handling

**ADK**:
- Tools are FunctionTools (automatic schema generation)
- Built-in tools available
- Structured error responses

### 2. Tool Usage

**LangChain**:
```python
tool = Tool(name="...", func=my_function)
agent = Agent(tools=[tool])
```

**ADK**:
```python
from google.adk.tools import FunctionTool
tool = FunctionTool(my_function)  # Auto-generates schema
agent = LlmAgent(..., tools=[tool])
```

### 3. Error Handling

**LangChain**:
- Custom exception handling
- Manual error propagation

**ADK**:
- Structured responses: `{"status": "success" | "error", ...}`
- LLM can handle errors gracefully
- Consistent error format

### 4. Built-in Tools

**LangChain**:
- Limited built-in tools
- Most tools require external APIs

**ADK**:
- Rich built-in tool ecosystem
- `google_search` - no API key
- `BuiltInCodeExecutor` - no external service
- MCP tools support

---

## Migration Benefits

### 1. Reduced Dependencies
- ❌ Remove: `langchain-community` (for Tavily)
- ✅ Use: ADK built-in `google_search`
- Result: Fewer dependencies, simpler setup

### 2. Better Integration
- Native Gemini integration
- Optimized for Google's infrastructure
- Better performance

### 3. Improved Developer Experience
- Automatic schema generation
- Better tool discovery
- Clearer error messages

### 4. Cost Savings
- No Tavily API costs
- BuiltInCodeExecutor (no Judge0 costs for Python)
- Reduced external API dependencies

---

## Migration Checklist

- [x] Search tool migrated to `google_search`
- [x] Code execution tool options created (BuiltIn + Judge0)
- [x] Question bank wrapped as FunctionTools
- [x] JD parser converted to FunctionTool
- [x] All tools follow ADK best practices
- [x] Error handling standardized
- [x] Documentation created
- [ ] Integration tests (Phase 7)
- [ ] Performance benchmarks
- [ ] Remove legacy dependencies (Phase 8)

---

## Testing Strategy

### Unit Tests
Test each tool independently:
```python
def test_adk_search_tool():
    tool = create_adk_search_tool()
    assert tool is not None

def test_question_bank_tool():
    tool = get_question_selection_tool()
    result = tool.func("easy")
    assert result["status"] == "success"
```

### Integration Tests
Test tools with agents:
```python
def test_agent_with_tools():
    agent = LlmAgent(
        ...,
        tools=[create_adk_search_tool(), *create_question_bank_tools()]
    )
    # Test agent can use tools
```

---

**Last Updated**: 2025-01-20

