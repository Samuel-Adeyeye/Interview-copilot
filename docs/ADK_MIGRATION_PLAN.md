# Google ADK Migration Action Plan
## Interview Co-Pilot: From LangChain/LangGraph to Google's Agent Development Kit

**Document Version:** 1.0  
**Date:** 2025-01-20  
**Status:** Planning Phase

---

## 📋 Executive Summary

This document outlines a comprehensive migration plan to transition the Interview Co-Pilot application from the current LangChain/LangGraph-based architecture to Google's Agent Development Kit (ADK). The migration will modernize the agent framework, improve maintainability, leverage Google's Gemini models, and align with industry best practices.

### Key Benefits of Migration

- ✅ **Modern Framework**: ADK is Google's latest agent development framework with active support
- ✅ **Gemini Integration**: Native support for Google's Gemini models with optimized performance
- ✅ **Built-in Tools**: Rich ecosystem of built-in tools (Google Search, Code Execution, etc.)
- ✅ **Better Session Management**: Robust session and memory management out of the box
- ✅ **Workflow Patterns**: Native support for Sequential, Parallel, and Loop workflows
- ✅ **A2A Protocol**: Standard protocol for agent-to-agent communication
- ✅ **Context Engineering**: Built-in context compaction and caching
- ✅ **Production Ready**: Enterprise-grade features for scaling

---

## 🎯 Migration Goals

1. **Preserve Functionality**: Maintain all existing features during migration
2. **Improve Architecture**: Leverage ADK's workflow patterns for better code organization
3. **Enhance Performance**: Utilize Gemini models and ADK optimizations
4. **Simplify Codebase**: Reduce complexity by using ADK's built-in features
5. **Future-Proof**: Align with Google's agent development roadmap

---

## 📊 Current Architecture Analysis

### Current Stack

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Backend                       │
├─────────────────────────────────────────────────────────┤
│  Orchestrator (LangGraph StateGraph)                    │
│    ├── ResearchAgent (LangChain + Tavily)               │
│    ├── TechnicalAgent (LangChain + Judge0)             │
│    └── CompanionAgent (LangChain)                       │
├─────────────────────────────────────────────────────────┤
│  Services                                                │
│    ├── MemoryBank (ChromaDB)                            │
│    ├── SessionService (InMemory/Persistent)              │
│    └── ObservabilityService                             │
├─────────────────────────────────────────────────────────┤
│  Tools                                                   │
│    ├── SearchTool (Tavily)                              │
│    ├── CodeExecutionTool (Judge0)                       │
│    ├── QuestionBank                                     │
│    └── JDParserTool                                     │
└─────────────────────────────────────────────────────────┘
```

### Key Components to Migrate

1. **Agents** (3 agents)
   - ResearchAgent → ADK LlmAgent with google_search tool
   - TechnicalAgent → ADK LlmAgent with code execution
   - CompanionAgent → ADK LlmAgent

2. **Orchestrator** (LangGraph → ADK Workflows)
   - Current: LangGraph StateGraph with conditional edges
   - Target: ADK SequentialAgent or custom workflow

3. **Session Management**
   - Current: Custom InMemorySessionService / PersistentSessionService
   - Target: ADK InMemorySessionService / DatabaseSessionService

4. **Memory System**
   - Current: ChromaDB-based MemoryBank
   - Target: ADK MemoryService (InMemoryMemoryService or Vertex AI Memory Bank)

5. **Tools**
   - SearchTool → ADK google_search (built-in)
   - CodeExecutionTool → ADK BuiltInCodeExecutor or FunctionTool
   - QuestionBank → FunctionTool
   - JDParserTool → FunctionTool

---

## 🗺️ Migration Strategy

### Phase 1: Foundation Setup (Week 1)
**Goal**: Set up ADK infrastructure and dependencies

#### Tasks:
1. **Update Dependencies**
   - [ ] Add `google-adk` to requirements.txt
   - [ ] Add `google-genai` for Gemini API
   - [ ] Remove/update LangChain dependencies (keep only if needed for transition)
   - [ ] Update environment variables for Google API keys

2. **Configuration Updates**
   - [ ] Create ADK-specific configuration in `config/settings.py`
   - [ ] Add Google API key management
   - [ ] Configure retry options and model settings

3. **Project Structure**
   - [ ] Create `agents/adk/` directory for new ADK agents
   - [ ] Create `tools/adk/` directory for ADK tools
   - [ ] Set up migration branch in git

#### Deliverables:
- Updated requirements.txt
- ADK configuration module
- Project structure for ADK components

---

### Phase 2: Tool Migration (Week 1-2)
**Goal**: Migrate all tools to ADK equivalents

#### 2.1 Search Tool Migration
**Current**: Custom Tavily integration  
**Target**: ADK `google_search` (built-in)

**Tasks**:
- [ ] Replace TavilySearchResults with ADK google_search
- [ ] Update tool usage in ResearchAgent
- [ ] Test search functionality
- [ ] Remove Tavily dependency if not needed elsewhere

**Code Changes**:
```python
# Before (LangChain)
from langchain_community.tools.tavily_search import TavilySearchResults
search_tool = TavilySearchResults(api_key=TAVILY_API_KEY)

# After (ADK)
from google.adk.tools import google_search
# google_search is ready to use - no setup needed!
```

#### 2.2 Code Execution Tool Migration
**Current**: Custom Judge0 integration  
**Target**: ADK `BuiltInCodeExecutor` or custom FunctionTool

**Tasks**:
- [ ] Evaluate BuiltInCodeExecutor vs custom FunctionTool
- [ ] Migrate code execution logic
- [ ] Update TechnicalAgent to use new tool
- [ ] Test code execution with various languages

**Code Changes**:
```python
# Option 1: Use BuiltInCodeExecutor (Gemini's built-in)
from google.adk.code_executors import BuiltInCodeExecutor
code_executor = BuiltInCodeExecutor()

# Option 2: Keep Judge0 as FunctionTool
from google.adk.tools import FunctionTool
code_exec_tool = FunctionTool(judge0_execute_code)
```

#### 2.3 Question Bank Tool Migration
**Current**: Custom QuestionBank class  
**Target**: ADK FunctionTool

**Tasks**:
- [ ] Wrap QuestionBank methods as FunctionTool
- [ ] Update function signatures for ADK compatibility
- [ ] Test question retrieval and filtering

**Code Changes**:
```python
# Wrap existing QuestionBank as FunctionTool
from google.adk.tools import FunctionTool
from tools.question_bank import QuestionBank

qb = QuestionBank()

def get_questions_by_difficulty(difficulty: str) -> dict:
    """Get questions filtered by difficulty level."""
    questions = qb.get_questions_by_difficulty(difficulty)
    return {"status": "success", "questions": questions}

question_tool = FunctionTool(get_questions_by_difficulty)
```

#### 2.4 JD Parser Tool Migration
**Current**: Custom JDParserTool  
**Target**: ADK FunctionTool

**Tasks**:
- [ ] Convert JD parser to FunctionTool
- [ ] Update parsing logic if needed
- [ ] Test with various job descriptions

#### Deliverables:
- All tools migrated to ADK
- Tool tests updated
- Documentation updated

---

### Phase 3: Agent Migration (Week 2-3)
**Goal**: Migrate all agents to ADK LlmAgent

#### 3.1 Research Agent Migration
**Current**: ResearchAgentStructured (LangChain + Pydantic)  
**Target**: ADK LlmAgent with structured output

**Tasks**:
- [ ] Create ADK LlmAgent for research
- [ ] Configure Gemini model with structured output
- [ ] Integrate google_search tool
- [ ] Implement ResearchPacket extraction
- [ ] Update memory bank integration
- [ ] Test research workflow

**Code Structure**:
```python
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools import google_search
from google.genai import types

research_agent = LlmAgent(
    name="ResearchAgent",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config
    ),
    instruction="""You are a research specialist. Use google_search to find 
    information about companies and their interview processes. Extract and 
    structure the information into: company_overview, interview_process, 
    tech_stack, recent_news, preparation_tips.""",
    tools=[google_search],
    output_key="research_packet"
)
```

#### 3.2 Technical Agent Migration
**Current**: TechnicalAgent (LangChain + Judge0)  
**Target**: ADK LlmAgent with code execution

**Tasks**:
- [ ] Create ADK LlmAgent for technical interviews
- [ ] Integrate code execution tool (BuiltInCodeExecutor or FunctionTool)
- [ ] Integrate question bank tool
- [ ] Implement question selection mode
- [ ] Implement code evaluation mode
- [ ] Test both modes

**Code Structure**:
```python
technical_agent = LlmAgent(
    name="TechnicalAgent",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config
    ),
    instruction="""You are a technical interview assistant. You can:
    1. Select coding questions based on difficulty
    2. Evaluate submitted code solutions
    Use the available tools to accomplish these tasks.""",
    tools=[code_exec_tool, question_tool],
    code_executor=BuiltInCodeExecutor()  # Optional: for calculations
)
```

#### 3.3 Companion Agent Migration
**Current**: CompanionAgent (LangChain)  
**Target**: ADK LlmAgent

**Tasks**:
- [ ] Create ADK LlmAgent for companion features
- [ ] Implement encouragement generation
- [ ] Implement tips generation
- [ ] Implement session summary
- [ ] Integrate with memory service
- [ ] Test companion features

**Code Structure**:
```python
companion_agent = LlmAgent(
    name="CompanionAgent",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config
    ),
    instruction="""You are a supportive interview companion. Provide 
    encouragement, tips, and session summaries to help users prepare 
    for interviews.""",
    tools=[memory_tool]  # For accessing user history
)
```

#### Deliverables:
- All three agents migrated to ADK
- Agent functionality preserved
- Updated agent tests

---

### Phase 4: Orchestrator Migration (Week 3-4)
**Goal**: Replace LangGraph orchestrator with ADK workflow patterns

#### Current Orchestrator Analysis
- Uses LangGraph StateGraph
- Has conditional routing (skip technical if needed)
- Sequential flow: Research → Technical → Companion
- State management via TypedDict

#### ADK Orchestration Options

**Option A: SequentialAgent (Recommended)**
- Simple, deterministic workflow
- Research → Technical → Companion
- Use conditional logic within agents

**Option B: LLM-based Orchestrator**
- Root agent with sub-agents as AgentTool
- More flexible, LLM decides routing
- Better for dynamic workflows

**Option C: Hybrid Approach**
- SequentialAgent for main flow
- ParallelAgent for independent tasks
- LoopAgent for refinement cycles

#### Recommended: SequentialAgent with Conditional Logic

**Tasks**:
- [ ] Create SequentialAgent with sub-agents
- [ ] Implement conditional logic for skipping technical
- [ ] Migrate state management to ADK session state
- [ ] Update orchestrator API methods
- [ ] Test full workflow

**Code Structure**:
```python
from google.adk.agents import SequentialAgent, Agent

# Create root orchestrator
root_orchestrator = SequentialAgent(
    name="InterviewOrchestrator",
    sub_agents=[
        research_agent,
        technical_agent,  # Can be conditionally skipped
        companion_agent
    ]
)

# Or use LLM-based orchestrator for flexibility
orchestrator_agent = Agent(
    name="Orchestrator",
    model=Gemini(model="gemini-2.5-flash-lite"),
    instruction="""Coordinate interview preparation workflow:
    1. Call ResearchAgent for company research
    2. Call TechnicalAgent for coding questions (if needed)
    3. Call CompanionAgent for support""",
    tools=[
        AgentTool(research_agent),
        AgentTool(technical_agent),
        AgentTool(companion_agent)
    ]
)
```

#### Deliverables:
- New orchestrator using ADK patterns
- Workflow tests passing
- API compatibility maintained

---

### Phase 5: Session & Memory Migration (Week 4-5)
**Goal**: Migrate to ADK session and memory services

#### 5.1 Session Service Migration
**Current**: Custom InMemorySessionService / PersistentSessionService  
**Target**: ADK InMemorySessionService / DatabaseSessionService

**Tasks**:
- [ ] Replace custom session service with ADK equivalents
- [ ] Migrate session data structure
- [ ] Update session API endpoints
- [ ] Test session persistence
- [ ] Implement session cleanup

**Code Changes**:
```python
# Before
from memory.session_service import InMemorySessionService
session_service = InMemorySessionService()

# After
from google.adk.sessions import InMemorySessionService, DatabaseSessionService
session_service = DatabaseSessionService(db_url="sqlite:///sessions.db")
```

#### 5.2 Memory System Migration
**Current**: ChromaDB-based MemoryBank  
**Target**: ADK MemoryService

**Options**:
1. **InMemoryMemoryService**: For development/testing
2. **Vertex AI Memory Bank**: For production (requires GCP)

**Tasks**:
- [ ] Evaluate memory service options
- [ ] Migrate memory storage logic
- [ ] Update memory retrieval methods
- [ ] Test memory persistence
- [ ] Implement memory consolidation (if using Vertex AI)

**Code Changes**:
```python
# Option 1: InMemory (development)
from google.adk.memory import InMemoryMemoryService
memory_service = InMemoryMemoryService()

# Option 2: Vertex AI (production)
from google.adk.memory import VertexAIMemoryBank
memory_service = VertexAIMemoryBank(
    project_id="your-project",
    location="us-central1"
)
```

#### Deliverables:
- Session service migrated
- Memory service migrated
- Data migration scripts
- Tests updated

---

### Phase 6: Runner & App Integration (Week 5)
**Goal**: Integrate ADK Runner and App

#### 6.1 Runner Setup
**Tasks**:
- [ ] Create Runner instance with agents
- [ ] Configure session service
- [ ] Set up memory service
- [ ] Implement context compaction
- [ ] Test runner functionality

**Code Structure**:
```python
from google.adk.runners import Runner
from google.adk.apps.app import App, EventsCompactionConfig

# Create App with compaction
app = App(
    name="interview_copilot",
    root_agent=root_orchestrator,
    events_compaction_config=EventsCompactionConfig(
        compaction_interval=5,
        overlap_size=2
    )
)

# Create Runner
runner = Runner(
    app=app,
    session_service=session_service,
    memory_service=memory_service
)
```

#### 6.2 API Integration
**Tasks**:
- [ ] Update FastAPI endpoints to use Runner
- [ ] Migrate session management endpoints
- [ ] Update agent execution endpoints
- [ ] Implement async message handling
- [ ] Update response formats

**Code Changes**:
```python
# Before
result = await orchestrator.execute_research(...)

# After
from google.genai import types
query = types.Content(role="user", parts=[types.Part(text=user_query)])
async for event in runner.run_async(
    user_id=user_id,
    session_id=session_id,
    new_message=query
):
    # Handle events
    pass
```

#### Deliverables:
- Runner integrated
- API endpoints updated
- Async event handling
- Documentation updated

---

### Phase 7: Testing & Validation (Week 6)
**Goal**: Ensure all functionality works correctly

#### 7.1 Unit Tests
**Tasks**:
- [ ] Update agent unit tests for ADK
- [ ] Update tool unit tests
- [ ] Update orchestrator tests
- [ ] Fix failing tests
- [ ] Achieve >80% coverage

#### 7.2 Integration Tests
**Tasks**:
- [ ] Test full interview workflow
- [ ] Test session persistence
- [ ] Test memory retrieval
- [ ] Test error handling
- [ ] Test concurrent sessions

#### 7.3 End-to-End Tests
**Tasks**:
- [ ] Test complete user journey
- [ ] Test API endpoints
- [ ] Test UI integration
- [ ] Performance testing
- [ ] Load testing

#### Deliverables:
- All tests passing
- Test coverage report
- Performance benchmarks
- Migration validation report

---

### Phase 8: Documentation & Cleanup (Week 6-7)
**Goal**: Complete migration and document changes

#### 8.1 Documentation
**Tasks**:
- [ ] Update README with ADK information
- [ ] Document new architecture
- [ ] Update API documentation
- [ ] Create migration guide
- [ ] Update deployment docs

#### 8.2 Code Cleanup
**Tasks**:
- [ ] Remove LangChain dependencies (if not needed)
- [ ] Remove old agent implementations
- [ ] Remove old orchestrator code
- [ ] Clean up unused imports
- [ ] Update .gitignore

#### 8.3 Deployment
**Tasks**:
- [ ] Update Docker configuration
- [ ] Update environment variables
- [ ] Test deployment process
- [ ] Update CI/CD pipelines
- [ ] Deploy to staging

#### Deliverables:
- Complete documentation
- Clean codebase
- Successful deployment
- Migration completion report

---

## 🔄 Migration Patterns & Best Practices

### Pattern 1: Agent Migration
```python
# LangChain Pattern
class ResearchAgent(BaseAgent):
    def __init__(self, llm, memory_bank):
        self.llm = llm
        self.memory_bank = memory_bank
        self.tools = [search_tool]
    
    async def run(self, context):
        # Custom logic
        pass

# ADK Pattern
research_agent = LlmAgent(
    name="ResearchAgent",
    model=Gemini(model="gemini-2.5-flash-lite"),
    instruction="...",
    tools=[google_search],
    output_key="research_packet"
)
```

### Pattern 2: Tool Migration
```python
# LangChain Pattern
from langchain_core.tools import Tool
tool = Tool(name="search", func=search_func)

# ADK Pattern
from google.adk.tools import FunctionTool
tool = FunctionTool(search_func)  # Auto-generates schema from function
```

### Pattern 3: Workflow Migration
```python
# LangGraph Pattern
workflow = StateGraph(State)
workflow.add_node("research", research_node)
workflow.add_node("technical", technical_node)
workflow.add_edge("research", "technical")

# ADK Pattern
workflow = SequentialAgent(
    sub_agents=[research_agent, technical_agent]
)
```

### Pattern 4: Session Management
```python
# Custom Pattern
session = session_service.create_session(user_id, session_id)
session.add_message(user_message)
session.add_message(agent_response)

# ADK Pattern
session = await session_service.create_session(
    app_name=app_name,
    user_id=user_id,
    session_id=session_id
)
# Runner automatically manages messages
```

---

## ⚠️ Risks & Mitigation

### Risk 1: API Compatibility
**Risk**: Breaking changes in API endpoints  
**Mitigation**: 
- Maintain API compatibility layer
- Version API endpoints
- Gradual migration with feature flags

### Risk 2: Data Migration
**Risk**: Loss of existing session/memory data  
**Mitigation**:
- Create data migration scripts
- Test migration on staging
- Backup existing data
- Rollback plan

### Risk 3: Performance Regression
**Risk**: Slower response times  
**Mitigation**:
- Performance benchmarking
- Load testing
- Optimize context compaction
- Use caching where appropriate

### Risk 4: Feature Gaps
**Risk**: Missing features in ADK  
**Mitigation**:
- Feature comparison matrix
- Identify workarounds
- Custom implementations where needed
- Engage with ADK community

### Risk 5: Learning Curve
**Risk**: Team unfamiliar with ADK  
**Mitigation**:
- Training sessions
- Pair programming
- Code reviews
- Documentation

---

## 📈 Success Metrics

### Technical Metrics
- [ ] All tests passing (>80% coverage)
- [ ] API response times < 2s (p95)
- [ ] Zero data loss during migration
- [ ] 100% feature parity

### Business Metrics
- [ ] No user-facing downtime
- [ ] Improved agent accuracy
- [ ] Reduced infrastructure costs
- [ ] Faster development velocity

---

## 🛠️ Tools & Resources

### Required Tools
- Google ADK: `pip install google-adk`
- Google GenAI: `pip install google-genai`
- Gemini API Key: [Google AI Studio](https://aistudio.google.com/app/api-keys)

### Documentation
- [ADK Documentation](https://google.github.io/adk-docs/)
- [ADK Quickstart](https://google.github.io/adk-docs/get-started/python/)
- [Gemini API Docs](https://ai.google.dev/gemini-api/docs)
- [ADK GitHub](https://github.com/google/adk)

### Training Resources
- Kaggle 5-Day Agents Course (notebooks in `/Notebooks`)
- ADK Tutorials
- Google Cloud Agent Development

---

## 📅 Timeline Summary

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| Phase 1: Foundation | Week 1 | ADK setup, configuration |
| Phase 2: Tools | Week 1-2 | All tools migrated |
| Phase 3: Agents | Week 2-3 | All agents migrated |
| Phase 4: Orchestrator | Week 3-4 | Workflow migration |
| Phase 5: Session/Memory | Week 4-5 | Data services migrated |
| Phase 6: Runner/App | Week 5 | Integration complete |
| Phase 7: Testing | Week 6 | All tests passing |
| Phase 8: Documentation | Week 6-7 | Migration complete |

**Total Estimated Duration**: 6-7 weeks

---

## 🚀 Next Steps

1. **Review & Approval**: Review this plan with the team
2. **Setup Environment**: Get Google API keys and set up ADK
3. **Create Migration Branch**: `git checkout -b feature/adk-migration`
4. **Start Phase 1**: Begin foundation setup
5. **Weekly Reviews**: Track progress and adjust as needed

---

## 📝 Notes & Considerations

### Key Decisions Needed
1. **Memory Service**: InMemory vs Vertex AI Memory Bank?
2. **Code Execution**: BuiltInCodeExecutor vs Judge0?
3. **Orchestration**: SequentialAgent vs LLM-based?
4. **Session Storage**: SQLite vs PostgreSQL?

### Open Questions
- Do we need to maintain LangChain compatibility during transition?
- Should we migrate UI components simultaneously?
- What's the rollback strategy if migration fails?
- How do we handle existing user sessions?

### Future Enhancements
- A2A Protocol for external agent integration
- Advanced context compaction strategies
- Multi-modal agent capabilities
- Real-time agent collaboration

---

**Document Owner**: Development Team  
**Last Updated**: 2025-01-20  
**Status**: Ready for Review

