"""
Tests for ADK Session and Memory Services
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from typing import Dict, Any


@pytest.mark.unit
@pytest.mark.api
class TestADKSessionService:
    """Tests for ADK Session Service"""
    
    @patch('memory.adk.session_service.InMemorySessionService')
    def test_create_adk_session_service_in_memory(self, mock_service):
        """Test creating in-memory session service"""
        from memory.adk.session_service import create_adk_session_service
        
        service = create_adk_session_service(use_database=False)
        assert service is not None
        assert service.service is not None
    
    @patch('memory.adk.session_service.DatabaseSessionService')
    def test_create_adk_session_service_database(self, mock_service):
        """Test creating database session service"""
        from memory.adk.session_service import create_adk_session_service
        
        service = create_adk_session_service(
            use_database=True,
            db_url="sqlite:///test.db"
        )
        assert service is not None
    
    @patch('memory.adk.session_service.InMemorySessionService')
    @pytest.mark.asyncio
    async def test_create_session(self, mock_service):
        """Test creating a session"""
        from memory.adk.session_service import create_adk_session_service
        
        # Mock ADK session service
        mock_adk_service = Mock()
        mock_session = Mock()
        mock_session.state = {}
        mock_adk_service.create_session = Mock(return_value=mock_session)
        mock_service.return_value = mock_adk_service
        
        service = create_adk_session_service(use_database=False)
        service.service = mock_adk_service
        
        session = service.create_session(
            session_id="test_session",
            user_id="test_user",
            metadata={"test": True}
        )
        
        assert session is not None
        assert session["session_id"] == "test_session"
    
    @patch('memory.adk.session_service.InMemorySessionService')
    @pytest.mark.asyncio
    async def test_get_session(self, mock_service):
        """Test getting a session"""
        from memory.adk.session_service import create_adk_session_service
        
        # Mock ADK session service
        mock_adk_service = Mock()
        mock_session = Mock()
        mock_session.state = {"metadata": {}}
        mock_session.user_id = "test_user"
        mock_adk_service.get_session = Mock(return_value=mock_session)
        mock_service.return_value = mock_adk_service
        
        service = create_adk_session_service(use_database=False)
        service.service = mock_adk_service
        
        session = service.get_session("test_session")
        
        assert session is not None


@pytest.mark.unit
@pytest.mark.api
class TestADKMemoryService:
    """Tests for ADK Memory Service"""
    
    @patch('memory.adk.memory_service.InMemoryMemoryService')
    def test_create_adk_memory_service_in_memory(self, mock_service):
        """Test creating in-memory memory service"""
        from memory.adk.memory_service import create_adk_memory_service
        
        service = create_adk_memory_service(use_vertex_ai=False)
        assert service is not None
    
    @patch('memory.adk.memory_service.VertexAIMemoryBank')
    def test_create_adk_memory_service_vertex_ai(self, mock_service):
        """Test creating Vertex AI memory service"""
        from memory.adk.memory_service import create_adk_memory_service
        
        service = create_adk_memory_service(
            use_vertex_ai=True,
            project_id="test-project",
            location="us-central1",
            memory_bank_id="test-bank"
        )
        assert service is not None
    
    @pytest.mark.asyncio
    async def test_store_research(self):
        """Test storing research"""
        from memory.adk.memory_service import create_adk_memory_service
        
        service = create_adk_memory_service(use_vertex_ai=False)
        
        # Should not raise exception (uses fallback storage)
        await service.store_research(
            session_id="test_session",
            company="TestCorp",
            research_data={"overview": "Test"}
        )
    
    @pytest.mark.asyncio
    async def test_get_user_history(self):
        """Test getting user history"""
        from memory.adk.memory_service import create_adk_memory_service
        
        service = create_adk_memory_service(use_vertex_ai=False)
        
        history = await service.get_user_history("test_user", limit=10)
        assert isinstance(history, list)


@pytest.mark.integration
@pytest.mark.api
class TestADKSessionMemoryIntegration:
    """Integration tests for session and memory services"""
    
    def test_service_imports(self):
        """Test that services can be imported"""
        from memory.adk import (
            create_adk_session_service,
            create_adk_memory_service
        )
        
        assert create_adk_session_service is not None
        assert create_adk_memory_service is not None

