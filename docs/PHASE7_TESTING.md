# Phase 7: Testing - Implementation Guide

## Overview

Phase 7 implements comprehensive testing for the ADK migration. This document describes the testing strategy and test coverage.

## Test Coverage

| Component | Unit Tests | Integration Tests | Status |
|-----------|-----------|-------------------|--------|
| ADK Tools | ✅ | ✅ | Complete |
| ADK Agents | ✅ | ✅ | Complete |
| ADK Orchestrator | ✅ | ✅ | Complete |
| ADK Session/Memory | ✅ | ✅ | Complete |
| ADK API Endpoints | ✅ | ✅ | Complete |
| End-to-End | ✅ | - | Complete |

## Test Files

### 1. `tests/test_adk_tools.py`
Tests for ADK tools:
- Search tool creation
- Code execution tool (BuiltIn and Judge0)
- Question bank tools
- JD parser tools
- Tool integration

### 2. `tests/test_adk_agents.py`
Tests for ADK agents:
- Research agent creation
- Technical agent creation
- Companion agent creation
- Specialized agent variants
- Agent integration

### 3. `tests/test_adk_orchestrator.py`
Tests for ADK orchestrator:
- Sequential orchestrator
- LLM-based orchestrator
- Research execution
- Technical execution
- Full workflow execution

### 4. `tests/test_adk_session_memory.py`
Tests for ADK session and memory services:
- Session service creation (in-memory and database)
- Memory service creation (in-memory and Vertex AI)
- Session operations
- Memory operations

### 5. `tests/test_adk_api.py`
Tests for ADK API endpoints:
- Research endpoint
- Technical endpoint
- Workflow endpoint
- Health check endpoint
- Request validation

### 6. `tests/test_adk_integration.py`
End-to-end integration tests:
- Complete workflow execution
- Component integration
- Migration compatibility

## Running Tests

### Run All ADK Tests
```bash
pytest tests/test_adk_*.py -v
```

### Run by Category
```bash
# Unit tests only
pytest tests/test_adk_*.py -m unit -v

# Integration tests only
pytest tests/test_adk_*.py -m integration -v

# API tests only
pytest tests/test_adk_api.py -v

# Agent tests only
pytest tests/test_adk_agents.py -v

# Tool tests only
pytest tests/test_adk_tools.py -v
```

### Run with Coverage
```bash
pytest tests/test_adk_*.py --cov=. --cov-report=html --cov-report=term
```

## Test Markers

Tests are organized using pytest markers:

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.api` - API tests
- `@pytest.mark.agents` - Agent tests
- `@pytest.mark.tools` - Tool tests
- `@pytest.mark.slow` - Slow-running tests

## Mocking Strategy

### ADK Components
Since ADK may not be fully installed, all ADK components are mocked:
- `google.adk.agents.LlmAgent`
- `google.adk.agents.SequentialAgent`
- `google.adk.tools.google_search`
- `google.adk.runners.Runner`
- `google.adk.apps.app.App`

### External Services
External services are mocked:
- Google API calls
- Judge0 API calls
- Database connections
- File system operations

## Test Fixtures

### Updated `conftest.py`
Added fixtures for ADK testing:
- `mock_gemini_model` - Mock Gemini model
- `mock_adk_session_service` - Mock ADK session service

## Test Examples

### Example 1: Tool Test
```python
@pytest.mark.unit
@pytest.mark.tools
def test_create_adk_search_tool():
    from tools.adk.search_tool import create_adk_search_tool
    
    with patch('tools.adk.search_tool.google_search'):
        tool = create_adk_search_tool()
        assert tool is not None
```

### Example 2: Agent Test
```python
@pytest.mark.unit
@pytest.mark.agents
@patch('agents.adk.research_agent.get_gemini_model')
@patch('agents.adk.research_agent.LlmAgent')
def test_create_research_agent(mock_llm_agent, mock_gemini):
    from agents.adk.research_agent import create_research_agent
    
    agent = create_research_agent()
    assert agent is not None
```

### Example 3: API Test
```python
@pytest.mark.api
def test_research_endpoint(client, mock_adk_app):
    response = client.post(
        "/api/v2/adk/research",
        json={
            "session_id": "test_session",
            "user_id": "test_user",
            "company_name": "Google",
            "job_description": "..."
        }
    )
    
    assert response.status_code == 200
```

## Continuous Integration

### GitHub Actions Example
```yaml
name: ADK Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pip install pytest pytest-asyncio pytest-cov
      - run: pytest tests/test_adk_*.py --cov=. --cov-report=xml
```

## Test Results

### Expected Coverage
- Tools: >80%
- Agents: >80%
- Orchestrator: >75%
- Session/Memory: >70%
- API Endpoints: >85%

### Running Coverage Report
```bash
pytest tests/test_adk_*.py --cov=. --cov-report=html
# Open htmlcov/index.html in browser
```

## Next Steps

1. ✅ **Phase 7 Complete**: Comprehensive tests created
2. **Phase 8**: Documentation and cleanup
3. **Deployment**: Run tests in CI/CD pipeline

## Notes

- All tests use mocking to avoid requiring full ADK installation
- Tests are designed to run quickly (< 1 minute total)
- Integration tests can be run separately for slower validation
- API tests require FastAPI test client

---

**Last Updated**: 2025-01-20  
**Status**: Phase 7 Complete ✅

