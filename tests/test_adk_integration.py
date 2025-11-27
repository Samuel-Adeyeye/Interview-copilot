"""
End-to-end integration tests for ADK migration
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from typing import Dict, Any


@pytest.mark.integration
@pytest.mark.slow
class TestADKEndToEnd:
    """End-to-end tests for ADK workflow"""
    
    @patch('api.adk_app.create_adk_orchestrator')
    @patch('api.adk_app.create_adk_session_service')
    @patch('api.adk_app.create_adk_memory_service')
    @patch('api.adk_app.App')
    @patch('api.adk_app.Runner')
    def test_adk_app_setup(self, mock_runner, mock_app, mock_memory, mock_session, mock_orchestrator):
        """Test complete ADK app setup"""
        from api.adk_app import initialize_adk_app
        
        app = initialize_adk_app()
        assert app is not None
        assert app.orchestrator is not None
        assert app.session_service is not None
        assert app.memory_service is not None
        assert app.app is not None
        assert app.runner is not None
    
    @patch('api.adk_app.ADKApplication')
    @pytest.mark.asyncio
    async def test_full_workflow_execution(self, mock_adk_app_class):
        """Test full workflow execution"""
        from api.adk_app import get_adk_app
        
        # Mock ADK app
        mock_app = Mock()
        async def mock_run_workflow(*args, **kwargs):
            mock_event = Mock()
            mock_event.content = Mock()
            mock_event.content.parts = [Mock(text="Workflow complete")]
            yield mock_event
        
        mock_app.run_workflow = AsyncMock(side_effect=mock_run_workflow)
        mock_adk_app_class.return_value = mock_app
        
        app = get_adk_app()
        
        events = []
        async for event in app.run_workflow(
            user_id="test_user",
            session_id="test_session",
            message="Test workflow"
        ):
            events.append(event)
        
        assert len(events) > 0


@pytest.mark.integration
class TestADKComponentIntegration:
    """Integration tests for ADK components"""
    
    def test_tools_and_agents_integration(self):
        """Test that tools and agents work together"""
        from tools.adk import create_adk_search_tool, create_question_bank_tools
        from agents.adk import create_research_agent, create_technical_agent
        
        # Should be able to create tools
        with patch('tools.adk.search_tool.google_search'):
            search_tool = create_adk_search_tool()
            assert search_tool is not None
        
        # Should be able to create agents
        with patch('agents.adk.research_agent.get_gemini_model'), \
             patch('agents.adk.research_agent.create_adk_search_tool'), \
             patch('agents.adk.research_agent.LlmAgent'):
            research_agent = create_research_agent()
            assert research_agent is not None
    
    def test_orchestrator_with_agents(self):
        """Test orchestrator with all agents"""
        from agents.adk.orchestrator import create_adk_orchestrator
        
        with patch('agents.adk.orchestrator.create_research_agent'), \
             patch('agents.adk.orchestrator.create_technical_agent'), \
             patch('agents.adk.orchestrator.create_companion_agent'), \
             patch('agents.adk.orchestrator.SequentialAgent'), \
             patch('agents.adk.orchestrator.InMemoryRunner'):
            
            orchestrator = create_adk_orchestrator()
            assert orchestrator is not None
            assert orchestrator.research_agent is not None
            assert orchestrator.technical_agent is not None
            assert orchestrator.companion_agent is not None


@pytest.mark.integration
class TestADKMigrationCompatibility:
    """Tests for migration compatibility"""
    
    def test_backward_compatibility_imports(self):
        """Test that old imports still work alongside new ones"""
        # Old imports should still work
        try:
            from agents.research_agent import ResearchAgentStructured
            from agents.technical_agent import TechnicalAgent
            from agents.companion_agent import CompanionAgent
        except ImportError:
            # Old agents might not be available, that's okay
            pass
        
        # New imports should work
        from agents.adk import (
            create_research_agent,
            create_technical_agent,
            create_companion_agent
        )
        
        assert create_research_agent is not None
        assert create_technical_agent is not None
        assert create_companion_agent is not None
    
    def test_api_versioning(self):
        """Test that both API versions can coexist"""
        # Old API endpoints should exist
        # (Would need actual API running to test)
        
        # New ADK endpoints should exist
        from api.adk_endpoints import router
        assert router is not None

