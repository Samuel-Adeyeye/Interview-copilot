"""
Pytest configuration and shared fixtures for Interview Co-Pilot tests
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock
from typing import Dict, Any
import os
from datetime import datetime
from fastapi.testclient import TestClient

# Mock external API keys for testing
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("TAVILY_API_KEY", "test-tavily-key")
os.environ.setdefault("JUDGE0_API_KEY", "test-judge0-key")
os.environ.setdefault("GOOGLE_API_KEY", "test-google-key")  # For ADK
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("TESTING", "true")


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def app():
    """Create FastAPI app instance for testing"""
    from api.main import app
    return app


@pytest.fixture
def client(app):
    """Create TestClient that doesn't require running server.
    This is the preferred way to test FastAPI endpoints without needing
    a live server running on a specific port."""
    return TestClient(app)


@pytest.fixture
def mock_llm():
    """Mock ChatOpenAI LLM for testing"""
    llm = Mock()
    llm.model_name = "gpt-4o-mini"
    llm.temperature = 0.7
    
    # Mock async invoke
    async def mock_invoke(messages, **kwargs):
        return Mock(content="Mocked LLM response")
    llm.ainvoke = AsyncMock(side_effect=mock_invoke)
    
    # Mock with_structured_output
    structured_llm = Mock()
    async def mock_structured_invoke(messages, **kwargs):
        return {
            "company_overview": "Mock company overview",
            "interview_process": "Mock interview process",
            "tech_stack": ["Python", "FastAPI"],
            "recent_news": ["News 1", "News 2"],
            "preparation_tips": ["Tip 1", "Tip 2"]
        }
    structured_llm.ainvoke = AsyncMock(side_effect=mock_structured_invoke)
    llm.with_structured_output = Mock(return_value=structured_llm)
    
    return llm


@pytest.fixture
def mock_gemini_model():
    """Mock Gemini model for ADK testing"""
    model = Mock()
    model.model = "gemini-2.5-flash-lite"
    model.temperature = 0.7
    return model


@pytest.fixture
def mock_adk_agent():
    """Mock ADK agent for testing"""
    mock = AsyncMock()
    mock.run.return_value = {
        "status": "success",
        "result": "Test result",
        "data": {
            "company_overview": "Mock overview",
            "tech_stack": ["Python", "FastAPI"]
        }
    }
    return mock


@pytest.fixture
def mock_memory_bank():
    """Mock MemoryBank for testing"""
    memory_bank = Mock()
    memory_bank.store_research = AsyncMock(return_value="research_id_123")
    memory_bank.get_research_by_company = AsyncMock(return_value={
        "company_name": "TestCorp",
        "research_data": {"overview": "Test overview"}
    })
    memory_bank.get_user_progress = AsyncMock(return_value={
        "total_sessions": 5,
        "questions_attempted": 20,
        "success_rate": 0.75
    })
    memory_bank.get_user_history = AsyncMock(return_value=[])
    memory_bank.search_similar_sessions = AsyncMock(return_value=[])
    memory_bank.store_user_progress = AsyncMock()
    memory_bank.update_session_score = AsyncMock()
    return memory_bank


@pytest.fixture
def mock_session_service():
    """Mock SessionService for testing"""
    session_service = Mock()
    session_service.create_session = Mock(return_value="session_123")
    session_service.get_session = Mock(return_value={
        "session_id": "session_123",
        "user_id": "user_123",
        "state": "running",
        "created_at": datetime.utcnow().isoformat()
    })
    session_service.pause_session = Mock(return_value={"status": "paused"})
    session_service.resume_session = Mock(return_value={"status": "running"})
    session_service.update_session_metadata = Mock()
    return session_service


@pytest.fixture
def mock_adk_session_service():
    """Mock ADK Session Service for testing"""
    service = Mock()
    service.create_session = AsyncMock(return_value={
        "session_id": "test-session-id",
        "created_at": datetime.utcnow().isoformat()
    })
    service.get_session = AsyncMock(return_value={
        "session_id": "test-session-id",
        "user_id": "test-user",
        "state": {}
    })
    service.save_session = AsyncMock()
    service.delete_session = AsyncMock()
    return service


@pytest.fixture
def mock_adk_memory_service():
    """Mock ADK MemoryService for testing"""
    service = Mock()
    service.store = AsyncMock(return_value=True)
    service.retrieve = AsyncMock(return_value=[])
    service.search = AsyncMock(return_value=[])
    return service


@pytest.fixture
def mock_search_tool():
    """Mock search tool for testing"""
    search_tool = Mock()
    search_tool.name = "web_search"
    search_tool.description = "Search the web"
    
    def mock_search_func(query: str) -> str:
        return f"Mock search results for: {query}"
    
    search_tool.run = Mock(side_effect=mock_search_func)
    return search_tool


@pytest.fixture
def mock_code_exec_tool():
    """Mock CodeExecutionTool for testing"""
    code_exec_tool = Mock()
    code_exec_tool.name = "code_execution"
    
    async def mock_execute(code: str, language: str, test_cases: list) -> Dict[str, Any]:
        return {
            "success": True,
            "tests_passed": len(test_cases),
            "total_tests": len(test_cases),
            "output": "All tests passed",
            "execution_time_ms": 100.0,
            "results": [
                {"test_case": tc, "passed": True, "output": "OK"}
                for tc in test_cases
            ]
        }
    
    code_exec_tool.execute_code = AsyncMock(side_effect=mock_execute)
    return code_exec_tool


@pytest.fixture
def mock_question_bank():
    """Mock QuestionBank for testing"""
    question_bank = Mock()
    question_bank.get_question_count = Mock(return_value=5)
    question_bank.get_questions_by_difficulty = Mock(return_value=[
        {"id": "q1", "title": "Two Sum", "difficulty": "easy"},
        {"id": "q2", "title": "Valid Parentheses", "difficulty": "easy"}
    ])
    question_bank.get_question_by_id = Mock(return_value={
        "id": "q1",
        "title": "Two Sum",
        "difficulty": "easy",
        "description": "Find two numbers that sum to target",
        "test_cases": [
            {"input": "[2,7,11,15]\n9", "expected_output": "[0, 1]"}
        ]
    })
    question_bank.filter_by_tags = Mock(return_value=[])
    return question_bank


@pytest.fixture
def sample_agent_context():
    """Sample AgentContext for testing"""
    from agents.base_agent import AgentContext
    return AgentContext(
        session_id="test_session_123",
        user_id="test_user_123",
        inputs={"query": "test query"},
        metadata={"test": True}
    )


@pytest.fixture
def sample_job_description():
    """Sample job description for testing"""
    return {
        "job_title": "Senior Software Engineer",
        "company_name": "TechCorp",
        "jd_text": """
        We are looking for a Senior Software Engineer to join our team.
        
        Requirements:
        - 5+ years of Python experience
        - Strong algorithms and data structures knowledge
        - Experience with distributed systems
        - Cloud platforms (AWS/GCP)
        
        Responsibilities:
        - Design and implement scalable backend services
        - Lead technical interviews
        - Mentor junior engineers
        """
    }


@pytest.fixture
def sample_code_submission():
    """Sample code submission for testing"""
    return {
        "question_id": "q1",
        "code": """
def two_sum(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []
""",
        "language": "python"
    }


@pytest.fixture
def sample_research_packet():
    """Sample ResearchPacket for testing"""
    from agents.research_agent import ResearchPacket
    return ResearchPacket(
        company_overview="Test company overview",
        interview_process="Test interview process",
        tech_stack=["Python", "FastAPI", "PostgreSQL"],
        recent_news=["News 1", "News 2"],
        preparation_tips=["Tip 1", "Tip 2"]
    )


@pytest.fixture
def mock_judge0_response():
    """Mock Judge0 API response"""
    return {
        "token": "test_token_123",
        "status": {
            "id": 3,  # Accepted
            "description": "Accepted"
        },
        "stdout": "[0, 1]",
        "stderr": "",
        "compile_output": "",
        "message": "",
        "time": "0.1",
        "memory": 1000
    }


@pytest.fixture(autouse=True)
def mock_external_services(monkeypatch):
    """Automatically mock external services for all tests to prevent
    real API calls during testing"""
    # Ensure test environment
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("TESTING", "true")
    
    # Mock API keys are already set above, but ensure they're in place
    if not os.getenv("GOOGLE_API_KEY"):
        monkeypatch.setenv("GOOGLE_API_KEY", "test-google-key")
    if not os.getenv("OPENAI_API_KEY"):
        monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    if not os.getenv("TAVILY_API_KEY"):
        monkeypatch.setenv("TAVILY_API_KEY", "test-tavily-key")
    if not os.getenv("JUDGE0_API_KEY"):
        monkeypatch.setenv("JUDGE0_API_KEY", "test-judge0-key")