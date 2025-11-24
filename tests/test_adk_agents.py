"""
Tests for ADK Agents
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from typing import Dict, Any


@pytest.mark.unit
@pytest.mark.agents
class TestADKResearchAgent:
    """Tests for ADK Research Agent"""
    
    @patch('agents.adk.research_agent.get_gemini_model')
    @patch('agents.adk.research_agent.create_adk_search_tool')
    @patch('agents.adk.research_agent.LlmAgent')
    def test_create_research_agent(self, mock_llm_agent, mock_search_tool, mock_gemini):
        """Test creating research agent"""
        from agents.adk.research_agent import create_research_agent
        
        agent = create_research_agent()
        assert agent is not None
        # Should create LlmAgent
        mock_llm_agent.assert_called_once()
    
    def test_research_packet_model(self):
        """Test ResearchPacket Pydantic model"""
        from agents.adk.research_agent import ResearchPacket
        
        packet = ResearchPacket(
            company_overview="Test overview",
            interview_process="Test process",
            tech_stack=["Python", "FastAPI"],
            recent_news=["News 1"],
            preparation_tips=["Tip 1"]
        )
        
        assert packet.company_overview == "Test overview"
        assert len(packet.tech_stack) == 2
        assert isinstance(packet.recent_news, list)


@pytest.mark.unit
@pytest.mark.agents
class TestADKTechnicalAgent:
    """Tests for ADK Technical Agent"""
    
    @patch('agents.adk.technical_agent.get_gemini_model')
    @patch('agents.adk.technical_agent.create_question_bank_tools')
    @patch('agents.adk.technical_agent.create_builtin_code_executor')
    @patch('agents.adk.technical_agent.LlmAgent')
    def test_create_technical_agent(self, mock_llm_agent, mock_code_exec, mock_question_tools, mock_gemini):
        """Test creating technical agent"""
        from agents.adk.technical_agent import create_technical_agent
        
        agent = create_technical_agent(use_builtin_code_executor=True)
        assert agent is not None
        mock_llm_agent.assert_called_once()
    
    @patch('agents.adk.technical_agent.get_gemini_model')
    @patch('agents.adk.technical_agent.create_question_bank_tools')
    @patch('agents.adk.technical_agent.LlmAgent')
    def test_create_question_selection_agent(self, mock_llm_agent, mock_question_tools, mock_gemini):
        """Test creating question selection agent"""
        from agents.adk.technical_agent import create_question_selection_agent
        
        agent = create_question_selection_agent()
        assert agent is not None
    
    @patch('agents.adk.technical_agent.get_gemini_model')
    @patch('agents.adk.technical_agent.get_question_lookup_tool')
    @patch('agents.adk.technical_agent.create_builtin_code_executor')
    @patch('agents.adk.technical_agent.LlmAgent')
    def test_create_code_evaluation_agent(self, mock_llm_agent, mock_code_exec, mock_question_tool, mock_gemini):
        """Test creating code evaluation agent"""
        from agents.adk.technical_agent import create_code_evaluation_agent
        
        agent = create_code_evaluation_agent(use_builtin_code_executor=True)
        assert agent is not None


@pytest.mark.unit
@pytest.mark.agents
class TestADKCompanionAgent:
    """Tests for ADK Companion Agent"""
    
    @patch('agents.adk.companion_agent.get_gemini_model')
    @patch('agents.adk.companion_agent.LlmAgent')
    def test_create_companion_agent(self, mock_llm_agent, mock_gemini):
        """Test creating companion agent"""
        from agents.adk.companion_agent import create_companion_agent
        
        agent = create_companion_agent()
        assert agent is not None
        mock_llm_agent.assert_called_once()
    
    @patch('agents.adk.companion_agent.get_gemini_model')
    @patch('agents.adk.companion_agent.LlmAgent')
    def test_create_encouragement_agent(self, mock_llm_agent, mock_gemini):
        """Test creating encouragement agent"""
        from agents.adk.companion_agent import create_encouragement_agent
        
        agent = create_encouragement_agent()
        assert agent is not None
    
    @patch('agents.adk.companion_agent.get_gemini_model')
    @patch('agents.adk.companion_agent.LlmAgent')
    def test_create_tips_agent(self, mock_llm_agent, mock_gemini):
        """Test creating tips agent"""
        from agents.adk.companion_agent import create_tips_agent
        
        agent = create_tips_agent()
        assert agent is not None


@pytest.mark.integration
@pytest.mark.agents
class TestADKAgentsIntegration:
    """Integration tests for ADK agents"""
    
    def test_agent_imports(self):
        """Test that all ADK agents can be imported"""
        from agents.adk import (
            create_research_agent,
            create_technical_agent,
            create_companion_agent
        )
        
        assert create_research_agent is not None
        assert create_technical_agent is not None
        assert create_companion_agent is not None
    
    @patch('agents.adk.research_agent.get_gemini_model')
    @patch('agents.adk.research_agent.create_adk_search_tool')
    @patch('agents.adk.research_agent.LlmAgent')
    def test_agents_can_be_created(self, mock_llm_agent, mock_search, mock_gemini):
        """Test that agents can be created without errors"""
        from agents.adk import (
            create_research_agent,
            create_technical_agent,
            create_companion_agent
        )
        
        # Should not raise exceptions
        research = create_research_agent()
        technical = create_technical_agent()
        companion = create_companion_agent()
        
        assert research is not None
        assert technical is not None
        assert companion is not None

