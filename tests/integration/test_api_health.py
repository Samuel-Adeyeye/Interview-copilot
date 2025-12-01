"""
Integration tests for Interview Copilot API
These tests run in the CI/CD pipeline before deployment
"""

import pytest
import httpx
import os
from typing import Generator

# Base URL for testing (will be set by environment)
BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


@pytest.fixture
def client() -> Generator[httpx.Client, None, None]:
    """Create HTTP client for testing"""
    with httpx.Client(base_url=BASE_URL, timeout=30.0) as client:
        yield client


def test_health_check(client: httpx.Client):
    """Test API health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_api_root(client: httpx.Client):
    """Test API root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "Interview Co-Pilot" in data["message"]


def test_session_creation(client: httpx.Client):
    """Test session creation endpoint"""
    response = client.post(
        "/sessions/create",
        json={
            "user_id": "test_user_ci",
            "metadata": {"test": True}
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["user_id"] == "test_user_ci"


def test_research_endpoint_exists(client: httpx.Client):
    """Test that research endpoint exists (doesn't test full functionality)"""
    # This should return 422 (validation error) not 404 (not found)
    response = client.post("/api/v2/adk/research", json={})
    assert response.status_code in [422, 400]  # Validation error, not not-found


def test_technical_endpoint_exists(client: httpx.Client):
    """Test that technical endpoint exists (doesn't test full functionality)"""
    # This should return 422 (validation error) not 404 (not found)
    response = client.post("/api/v2/adk/technical", json={})
    assert response.status_code in [422, 400]  # Validation error, not not-found


def test_metrics_endpoint(client: httpx.Client):
    """Test metrics endpoint"""
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "total_sessions" in data or "status" in data





if __name__ == "__main__":
    pytest.main([__file__, "-v"])
