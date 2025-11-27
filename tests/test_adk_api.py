"""
Tests for ADK API Endpoints
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from typing import Dict, Any
import json


@pytest.mark.api
class TestADKAPIEndpoints:
    """Tests for ADK API endpoints"""
    
    @pytest.fixture
    def mock_adk_app(self):
        """Mock ADK application"""
        app = Mock()
        
        # Mock run_research
        async def mock_run_research(*args, **kwargs):
            mock_event = Mock()
            mock_event.content = Mock()
            mock_event.content.parts = [Mock(text="Research results")]
            yield mock_event
        
        app.run_research = AsyncMock(side_effect=mock_run_research)
        
        # Mock run_technical
        async def mock_run_technical(*args, **kwargs):
            mock_event = Mock()
            mock_event.content = Mock()
            mock_event.content.parts = [Mock(text="Technical results")]
            yield mock_event
        
        app.run_technical = AsyncMock(side_effect=mock_run_technical)
        
        # Mock run_workflow
        async def mock_run_workflow(*args, **kwargs):
            mock_event = Mock()
            mock_event.content = Mock()
            mock_event.content.parts = [Mock(text="Workflow results")]
            yield mock_event
        
        app.run_workflow = AsyncMock(side_effect=mock_run_workflow)
        
        return app
    
    @pytest.fixture
    def client(self, mock_adk_app):
        """Create test client with mocked ADK app"""
        from fastapi import FastAPI
        from api.adk_endpoints import router
        from api.adk_app import get_adk_app
        
        app = FastAPI()
        app.include_router(router)
        
        # Override get_adk_app dependency
        app.dependency_overrides[get_adk_app] = lambda: mock_adk_app
        
        return TestClient(app)
    
    def test_research_endpoint(self, client, mock_adk_app):
        """Test research endpoint"""
        response = client.post(
            "/api/v2/adk/research",
            json={
                "session_id": "test_session",
                "user_id": "test_user",
                "company_name": "Google",
                "job_description": "Software Engineer..."
            }
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
    
    def test_technical_endpoint_select_questions(self, client, mock_adk_app):
        """Test technical endpoint for question selection"""
        response = client.post(
            "/api/v2/adk/technical",
            json={
                "session_id": "test_session",
                "user_id": "test_user",
                "mode": "select_questions",
                "difficulty": "medium",
                "num_questions": 3
            }
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
    
    def test_technical_endpoint_evaluate_code(self, client, mock_adk_app):
        """Test technical endpoint for code evaluation"""
        response = client.post(
            "/api/v2/adk/technical",
            json={
                "session_id": "test_session",
                "user_id": "test_user",
                "mode": "evaluate_code",
                "question_id": "q1",
                "code": "def solution(): pass",
                "language": "python"
            }
        )
        
        assert response.status_code == 200
    
    def test_technical_endpoint_validation_error(self, client, mock_adk_app):
        """Test technical endpoint validation"""
        response = client.post(
            "/api/v2/adk/technical",
            json={
                "session_id": "test_session",
                "user_id": "test_user",
                "mode": "select_questions"
                # Missing required fields
            }
        )
        
        # Should return validation error
        assert response.status_code in [400, 422]
    
    def test_workflow_endpoint(self, client, mock_adk_app):
        """Test workflow endpoint"""
        response = client.post(
            "/api/v2/adk/workflow",
            json={
                "session_id": "test_session",
                "user_id": "test_user",
                "company_name": "Google",
                "job_description": "Software Engineer...",
                "mode": "select_questions",
                "difficulty": "medium",
                "num_questions": 3
            }
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
    
    def test_health_endpoint(self, client, mock_adk_app):
        """Test health check endpoint"""
        response = client.get("/api/v2/adk/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


@pytest.mark.integration
@pytest.mark.api
class TestADKAPIIntegration:
    """Integration tests for ADK API"""
    
    @patch('api.adk_app.ADKApplication')
    def test_adk_app_initialization(self, mock_adk_app_class):
        """Test ADK app can be initialized"""
        from api.adk_app import initialize_adk_app
        
        app = initialize_adk_app()
        assert app is not None
    
    def test_endpoint_routes_exist(self):
        """Test that all endpoint routes are defined"""
        from api.adk_endpoints import router
        
        routes = [route.path for route in router.routes]
        
        assert "/research" in routes or any("/research" in r for r in routes)
        assert "/technical" in routes or any("/technical" in r for r in routes)
        assert "/workflow" in routes or any("/workflow" in r for r in routes)
        assert "/health" in routes or any("/health" in r for r in routes)

