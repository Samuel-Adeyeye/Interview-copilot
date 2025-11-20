import pytest
from httpx import AsyncClient
from api.main import app

@pytest.fixture
async def client():
    """Fixture for test client"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

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
    """Sample code for testing"""
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


# ===== Test Cases =====

@pytest.mark.asyncio
async def test_health_check(client):
    """Test health check endpoint"""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_create_session(client):
    """Test session creation"""
    response = await client.post(
        "/sessions/create",
        json={"user_id": "test_user_123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["user_id"] == "test_user_123"
    assert data["state"] in ["created", "running"]


@pytest.mark.asyncio
async def test_session_lifecycle(client):
    """Test full session lifecycle: create -> pause -> resume"""
    # Create session
    create_response = await client.post(
        "/sessions/create",
        json={"user_id": "test_user_123"}
    )
    session_id = create_response.json()["session_id"]
    
    # Pause session
    pause_response = await client.post(f"/sessions/{session_id}/pause")
    assert pause_response.status_code == 200
    assert pause_response.json()["status"] == "paused"
    
    # Resume session
    resume_response = await client.post(f"/sessions/{session_id}/resume")
    assert resume_response.status_code == 200
    assert resume_response.json()["status"] == "running"


@pytest.mark.asyncio
async def test_upload_job_description(client, sample_job_description):
    """Test job description upload"""
    response = await client.post(
        "/job-descriptions/upload",
        json=sample_job_description
    )
    assert response.status_code == 200
    data = response.json()
    assert "jd_id" in data
    assert data["company_name"] == sample_job_description["company_name"]


@pytest.mark.asyncio
async def test_research_agent(client, sample_job_description):
    """Test research agent execution"""
    # Create session
    session_response = await client.post(
        "/sessions/create",
        json={"user_id": "test_user_123"}
    )
    session_id = session_response.json()["session_id"]
    
    # Run research
    research_response = await client.post(
        "/research/run",
        json={
            "session_id": session_id,
            "job_description": sample_job_description["jd_text"],
            "company_name": sample_job_description["company_name"]
        }
    )
    assert research_response.status_code == 200
    data = research_response.json()
    assert "research_packet" in data
    assert "insights" in data
    assert isinstance(data["insights"], list)


@pytest.mark.asyncio
async def test_start_mock_interview(client):
    """Test starting mock interview"""
    # Create session
    session_response = await client.post(
        "/sessions/create",
        json={"user_id": "test_user_123"}
    )
    session_id = session_response.json()["session_id"]
    
    # Start interview
    interview_response = await client.post(
        "/interview/start",
        json={
            "session_id": session_id,
            "difficulty": "medium",
            "num_questions": 3
        }
    )
    assert interview_response.status_code == 200
    data = interview_response.json()
    assert data["status"] == "started"
    assert "questions" in data
    assert len(data["questions"]) == 3


@pytest.mark.asyncio
async def test_code_submission(client, sample_code_submission):
    """Test code submission and evaluation"""
    # Create session and start interview
    session_response = await client.post(
        "/sessions/create",
        json={"user_id": "test_user_123"}
    )
    session_id = session_response.json()["session_id"]
    
    # Submit code
    submission_response = await client.post(
        "/interview/submit-code",
        json={
            "session_id": session_id,
            **sample_code_submission
        }
    )
    assert submission_response.status_code == 200
    data = submission_response.json()
    assert "status" in data
    assert "tests_passed" in data
    assert "feedback" in data


@pytest.mark.asyncio
async def test_get_user_progress(client):
    """Test retrieving user progress"""
    user_id = "test_user_123"
    response = await client.get(f"/users/{user_id}/progress")
    assert response.status_code == 200
    data = response.json()
    assert "total_sessions" in data
    assert "questions_attempted" in data
    assert "success_rate" in data


@pytest.mark.asyncio
async def test_get_metrics(client):
    """Test metrics endpoint"""
    response = await client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "system" in data
    assert "agents" in data
    assert "tools" in data


@pytest.mark.asyncio
async def test_session_not_found(client):
    """Test 404 for non-existent session"""
    response = await client.get("/sessions/nonexistent_session_id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_invalid_difficulty(client):
    """Test validation for invalid difficulty"""
    session_response = await client.post(
        "/sessions/create",
        json={"user_id": "test_user_123"}
    )
    session_id = session_response.json()["session_id"]
    
    response = await client.post(
        "/interview/start",
        json={
            "session_id": session_id,
            "difficulty": "invalid_difficulty",  # Should fail validation
            "num_questions": 3
        }
    )
    assert response.status_code == 422  # Validation error


# ===== Integration Test Example =====

@pytest.mark.asyncio
async def test_full_interview_flow(client, sample_job_description, sample_code_submission):
    """
    Test complete interview flow:
    1. Create session
    2. Upload JD
    3. Run research
    4. Start mock interview
    5. Submit code
    6. Get session summary
    """
    # 1. Create session
    session_response = await client.post(
        "/sessions/create",
        json={"user_id": "test_user_integration"}
    )
    assert session_response.status_code == 200
    session_id = session_response.json()["session_id"]
    
    # 2. Upload JD
    jd_response = await client.post(
        "/job-descriptions/upload",
        json=sample_job_description
    )
    assert jd_response.status_code == 200
    
    # 3. Run research
    research_response = await client.post(
        "/research/run",
        json={
            "session_id": session_id,
            "job_description": sample_job_description["jd_text"],
            "company_name": sample_job_description["company_name"]
        }
    )
    assert research_response.status_code == 200
    
    # 4. Start mock interview
    interview_response = await client.post(
        "/interview/start",
        json={
            "session_id": session_id,
            "difficulty": "medium",
            "num_questions": 2
        }
    )
    assert interview_response.status_code == 200
    questions = interview_response.json()["questions"]
    
    # 5. Submit code for first question
    submission_response = await client.post(
        "/interview/submit-code",
        json={
            "session_id": session_id,
            "question_id": questions[0]["id"],
            "code": sample_code_submission["code"],
            "language": "python"
        }
    )
    assert submission_response.status_code == 200
    evaluation = submission_response.json()
    assert "feedback" in evaluation
    
    # 6. Get session summary
    summary_response = await client.get(f"/sessions/{session_id}/summary")
    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert summary["session_id"] == session_id
    assert len(summary["artifacts"]) > 0


# ===== Run Tests =====

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])