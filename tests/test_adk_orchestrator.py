"""
Tests for ADK Orchestrator
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from typing import Dict, Any


@pytest.mark.unit
@pytest.mark.agents
class TestADKOrchestrator:
    """Tests for ADK Orchestrator"""
    
    @patch('agents.adk.orchestrator.create_research_agent')
    @patch('agents.adk.orchestrator.create_technical_agent')
    @patch('agents.adk.orchestrator.create_companion_agent')
    @patch('agents.adk.orchestrator.SequentialAgent')
    @patch('agents.adk.orchestrator.InMemoryRunner')
    def test_create_adk_orchestrator_sequential(
        self, mock_runner, mock_sequential, mock_companion, mock_technical, mock_research
    ):
        """Test creating ADK orchestrator with SequentialAgent"""
        from agents.adk.orchestrator import create_adk_orchestrator
        
        orchestrator = create_adk_orchestrator(use_sequential=True)
        assert orchestrator is not None
        assert orchestrator.workflow is not None
        assert orchestrator.runner is not None
    
    @patch('agents.adk.orchestrator.create_research_agent')
    @patch('agents.adk.orchestrator.create_technical_agent')
    @patch('agents.adk.orchestrator.create_companion_agent')
    @patch('agents.adk.orchestrator.AgentTool')
    @patch('agents.adk.orchestrator.LlmAgent')
    @patch('agents.adk.orchestrator.InMemoryRunner')
    def test_create_adk_orchestrator_llm(
        self, mock_runner, mock_llm_agent, mock_agent_tool, mock_companion, mock_technical, mock_research
    ):
        """Test creating ADK orchestrator with LLM-based routing"""
        from agents.adk.orchestrator import create_adk_orchestrator
        
        orchestrator = create_adk_orchestrator(use_sequential=False)
        assert orchestrator is not None
    
    @patch('agents.adk.orchestrator.create_research_agent')
    @patch('agents.adk.orchestrator.create_technical_agent')
    @patch('agents.adk.orchestrator.create_companion_agent')
    @patch('agents.adk.orchestrator.SequentialAgent')
    @patch('agents.adk.orchestrator.InMemoryRunner')
    @pytest.mark.asyncio
    async def test_execute_research(
        self, mock_runner, mock_sequential, mock_companion, mock_technical, mock_research
    ):
        """Test executing research via orchestrator"""
        from agents.adk.orchestrator import create_adk_orchestrator
        
        # Mock runner events
        mock_event = Mock()
        mock_event.content = Mock()
        mock_event.content.parts = [Mock(text="Research results")]
        
        mock_runner_instance = Mock()
        mock_runner_instance.run_async = AsyncMock(return_value=[mock_event])
        mock_runner.return_value = mock_runner_instance
        
        orchestrator = create_adk_orchestrator(use_sequential=True)
        
        result = await orchestrator.execute_research(
            session_id="test_session",
            user_id="test_user",
            job_description="Test JD",
            company_name="TestCorp"
        )
        
        assert result is not None
        assert "success" in result or "output" in result
    
    @patch('agents.adk.orchestrator.create_research_agent')
    @patch('agents.adk.orchestrator.create_technical_agent')
    @patch('agents.adk.orchestrator.create_companion_agent')
    @patch('agents.adk.orchestrator.SequentialAgent')
    @patch('agents.adk.orchestrator.InMemoryRunner')
    @pytest.mark.asyncio
    async def test_execute_technical(
        self, mock_runner, mock_sequential, mock_companion, mock_technical, mock_research
    ):
        """Test executing technical agent via orchestrator"""
        from agents.adk.orchestrator import create_adk_orchestrator
        
        # Mock runner events
        mock_event = Mock()
        mock_event.content = Mock()
        mock_event.content.parts = [Mock(text="Technical results")]
        
        mock_runner_instance = Mock()
        mock_runner_instance.run_async = AsyncMock(return_value=[mock_event])
        mock_runner.return_value = mock_runner_instance
        
        orchestrator = create_adk_orchestrator(use_sequential=True)
        
        result = await orchestrator.execute_technical(
            session_id="test_session",
            user_id="test_user",
            mode="select_questions",
            difficulty="medium",
            num_questions=3
        )
        
        assert result is not None


@pytest.mark.integration
@pytest.mark.agents
class TestADKOrchestratorIntegration:
    """Integration tests for ADK orchestrator"""
    
    def test_orchestrator_imports(self):
        """Test that orchestrator can be imported"""
        from agents.adk.orchestrator import (
            ADKOrchestrator,
            create_adk_orchestrator
        )
        
        assert ADKOrchestrator is not None
        assert create_adk_orchestrator is not None

