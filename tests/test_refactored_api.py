import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import Mock, patch, AsyncMock
import os

# Set test environment variables
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("TAVILY_API_KEY", "test-tavily-key")
os.environ.setdefault("JUDGE0_API_KEY", "test-judge0-key")
os.environ.setdefault("SESSION_PERSISTENCE_ENABLED", "false")
os.environ.setdefault("VECTOR_DB_PATH", "./data/vectordb_test")

@pytest.fixture
async def client():
    """Fixture for test client with mocked dependencies"""
    from api.main import app
    from api.dependencies import get_session_service, get_memory_bank, get_orchestrator
    
    # Setup mocks
    mock_session_service = Mock()
    mock_session_service.create_session.return_value = {
        "session_id": "test_session_123",
        "user_id": "test_user",
        "state": "created",
        "created_at": "2023-01-01T00:00:00",
        "metadata": {}
    }
    mock_session_service.get_session.return_value = {
        "session_id": "test_session_123",
        "user_id": "test_user",
        "state": "created",
        "created_at": "2023-01-01T00:00:00",
        "metadata": {}
    }
    mock_session_service.pause_session.return_value = True
    mock_session_service.resume_session.return_value = True
    
    mock_memory_bank = Mock()
    
    mock_orchestrator = Mock()
    mock_orchestrator.execute_research = AsyncMock(return_value={
        "success": True,
        "output": {
            "preparation_tips": ["Insight 1"],
            "company_overview": "Test Company"
        },
        "execution_time_ms": 100.0
    })
    
    mock_orchestrator.execute_technical = AsyncMock(return_value={
        "success": True,
        "output": {
            "result": [{"id": "q1", "title": "Test Q"}]
        },
        "execution_time_ms": 100.0
    })
    
    # Override dependencies
    app.dependency_overrides[get_session_service] = lambda: mock_session_service
    app.dependency_overrides[get_memory_bank] = lambda: mock_memory_bank
    app.dependency_overrides[get_orchestrator] = lambda: mock_orchestrator
    
    # Create test client
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    # Clean up overrides
    app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_health_check(client):
    """Test health check endpoint"""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

@pytest.mark.asyncio
async def test_create_session(client):
    """Test session creation"""
    response = await client.post(
        "/sessions/create",
        json={"user_id": "test_user"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data

@pytest.mark.asyncio
async def test_get_session(client):
    """Test getting session details"""
    response = await client.get("/sessions/test_session_123")
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "test_session_123"

@pytest.mark.asyncio
async def test_run_research(client):
    """Test running research"""
    response = await client.post(
        "/research/run",
        json={
            "session_id": "test_session_123",
            "job_description": "Test JD",
            "company_name": "TestCorp"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "research_packet" in data

@pytest.mark.asyncio
async def test_start_interview(client):
    """Test starting a mock interview"""
    response = await client.post(
        "/interview/start",
        json={
            "session_id": "test_session_123",
            "difficulty": "hard",
            "num_questions": 1
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "test_session_123"
    assert data["status"] == "started"
    assert len(data["questions"]) == 1


@pytest.mark.asyncio
async def test_get_user_progress(client):
    """Test getting user progress"""
    response = await client.get("/users/test_user/progress")
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "test_user"
    assert "completed_sessions" in data
