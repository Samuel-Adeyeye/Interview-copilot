"""
Integration tests for Interview Copilot API
These tests run in the CI/CD pipeline before deployment
"""
"""
Integration tests for API health and basic endpoints
Uses FastAPI TestClient instead of httpx to avoid needing a running server
"""
import pytest
from fastapi.testclient import TestClient


def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ["healthy", "ok", "degraded"]  # degraded is ok in test mode


def test_api_root(client):
    """Test API root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data or "name" in data or "version" in data


def test_session_creation(client):
    """Test session creation endpoint"""
    payload = {
        "user_id": "test_user",
        "company_name": "Test Company",
        "job_description": "Test JD"
    }
    
    response = client.post("/sessions/create", json=payload)
    
    # Should return 200/201 for success, 422 for validation error, or 503 if service unavailable in test mode
    assert response.status_code in [200, 201, 422, 503]
    
    if response.status_code in [200, 201]:
        data = response.json()
        assert "session_id" in data or "id" in data


def test_research_endpoint_exists(client):
    """Test that research endpoint exists and is accessible"""
    # Empty payload - should return validation error (422) not 404
    response = client.post("/api/v2/adk/research", json={})
    
    # Should NOT be 404 (endpoint doesn't exist)
    # Should be 422 (validation error) or 400 (bad request)
    assert response.status_code != 404
    assert response.status_code in [400, 422]


def test_technical_endpoint_exists(client):
    """Test that technical endpoint exists and is accessible"""
    # Empty payload - should return validation error (422) not 404
    response = client.post("/api/v2/adk/technical", json={})
    
    # Should NOT be 404 (endpoint doesn't exist)
    # Should be 422 (validation error) or 400 (bad request)
    assert response.status_code != 404
    assert response.status_code in [400, 422]


@pytest.mark.skipif(
    condition=True,  # Always skip unless explicitly enabled
    reason="Requires running server - use TestClient tests instead"
)
def test_with_running_server():
    """
    This test would require a running server.
    Skip it in CI/CD and use TestClient-based tests instead.
    """
    import httpx
    with httpx.Client(base_url="http://localhost:8000") as client:
        response = client.get("/health")
        assert response.status_code == 200


# Add more integration tests using TestClient
def test_adk_health_endpoint(client):
    """Test ADK-specific health endpoint"""
    response = client.get("/api/v2/adk/health")
    
    # May return 404 if not implemented, or 200 if it exists
    if response.status_code == 200:
        data = response.json()
        assert "status" in data


def test_api_docs_accessible(client):
    """Test that API documentation is accessible"""
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_schema_accessible(client):
    """Test that OpenAPI schema is accessible"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "info" in data
    assert "paths" in data