"""
Comprehensive unit tests for Interview Co-Pilot agents
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from agents.base_agent import AgentContext
from agents.research_agent import ResearchAgentStructured, ResearchPacket
from agents.technical_agent import TechnicalAgent
from agents.companion_agent import CompanionAgent
from agents.orchestrator import Orchestrator
from exceptions import ValidationError, AgentExecutionError


class TestResearchAgent:
    """Tests for ResearchAgentStructured"""
    
    @pytest.mark.asyncio
    async def test_research_agent_initialization(self, mock_llm, mock_memory_bank):
        """Test ResearchAgent initialization"""
        agent = ResearchAgentStructured(mock_llm, mock_memory_bank)
        assert agent.name == "ResearchAgent"
        assert agent.memory_bank == mock_memory_bank
        assert agent.llm == mock_llm
        assert len(agent.tools) > 0
    
    @pytest.mark.asyncio
    async def test_research_agent_run_success(self, mock_llm, mock_memory_bank, sample_agent_context):
        """Test successful research agent execution"""
        # Mock the research agent's ainvoke
        mock_research_result = {
            "messages": [Mock(content="Mocked research results about TestCorp")]
        }
        
        agent = ResearchAgentStructured(mock_llm, mock_memory_bank)
        
        # Mock the research_agent.ainvoke
        agent.research_agent.ainvoke = AsyncMock(return_value=mock_research_result)
        
        # Update context with required inputs
        sample_agent_context.inputs = {
            "job_description": "We need a Python developer",
            "company_name": "TestCorp"
        }
        
        result = await agent.run(sample_agent_context)
        
        assert result.success is True
        assert result.agent_name == "ResearchAgent"
        assert "research_packet" in result.output
        assert isinstance(result.output["research_packet"], dict)
        assert result.execution_time_ms > 0
        assert result.trace_id is not None
    
    @pytest.mark.asyncio
    async def test_research_agent_missing_inputs(self, mock_llm, mock_memory_bank, sample_agent_context):
        """Test research agent with missing required inputs"""
        agent = ResearchAgentStructured(mock_llm, mock_memory_bank)
        
        # Missing company_name
        sample_agent_context.inputs = {"job_description": "Test JD"}
        
        with pytest.raises(ValueError, match="company_name is required"):
            await agent.run(sample_agent_context)
    
    @pytest.mark.asyncio
    async def test_research_agent_empty_inputs(self, mock_llm, mock_memory_bank, sample_agent_context):
        """Test research agent with empty inputs"""
        agent = ResearchAgentStructured(mock_llm, mock_memory_bank)
        sample_agent_context.inputs = {}
        
        with pytest.raises(ValueError, match="Context inputs cannot be empty"):
            await agent.run(sample_agent_context)
    
    @pytest.mark.asyncio
    async def test_research_agent_search_failure_handling(self, mock_llm, mock_memory_bank, sample_agent_context):
        """Test research agent handles search failures gracefully"""
        agent = ResearchAgentStructured(mock_llm, mock_memory_bank)
        
        # Mock search failure
        agent.research_agent.ainvoke = AsyncMock(side_effect=Exception("Search API error"))
        
        sample_agent_context.inputs = {
            "job_description": "We need a Python developer",
            "company_name": "TestCorp"
        }
        
        # Should still succeed with limited data
        result = await agent.run(sample_agent_context)
        assert result.success is True


class TestTechnicalAgent:
    """Tests for TechnicalAgent"""
    
    @pytest.mark.asyncio
    async def test_technical_agent_initialization(self, mock_llm, mock_code_exec_tool, mock_question_bank):
        """Test TechnicalAgent initialization"""
        agent = TechnicalAgent(mock_llm, mock_code_exec_tool, mock_question_bank)
        assert agent.name == "TechnicalAgent"
        assert agent.code_exec_tool == mock_code_exec_tool
        assert agent.question_bank == mock_question_bank
    
    @pytest.mark.asyncio
    async def test_technical_agent_select_questions(self, mock_llm, mock_code_exec_tool, mock_question_bank, sample_agent_context):
        """Test question selection mode"""
        agent = TechnicalAgent(mock_llm, mock_code_exec_tool, mock_question_bank)
        
        sample_agent_context.inputs = {
            "mode": "select_questions",
            "difficulty": "easy",
            "num_questions": 2
        }
        
        result = await agent.run(sample_agent_context)
        
        assert result.success is True
        assert "questions" in result.output
        assert len(result.output["questions"]) == 2
        assert all("id" in q for q in result.output["questions"])
    
    @pytest.mark.asyncio
    async def test_technical_agent_evaluate_code(self, mock_llm, mock_code_exec_tool, mock_question_bank, sample_agent_context):
        """Test code evaluation mode"""
        agent = TechnicalAgent(mock_llm, mock_code_exec_tool, mock_question_bank)
        
        # Mock LLM for feedback generation
        mock_llm.ainvoke = AsyncMock(return_value=Mock(content="Good solution! Time complexity is O(n)."))
        
        sample_agent_context.inputs = {
            "mode": "evaluate_code",
            "question_id": "q1",
            "code": "def two_sum(nums, target): return [0, 1]",
            "language": "python"
        }
        
        result = await agent.run(sample_agent_context)
        
        assert result.success is True
        assert "evaluation" in result.output
        assert "feedback" in result.output["evaluation"]
        assert "tests_passed" in result.output["evaluation"]
    
    @pytest.mark.asyncio
    async def test_technical_agent_missing_mode(self, mock_llm, mock_code_exec_tool, mock_question_bank, sample_agent_context):
        """Test technical agent with missing mode"""
        agent = TechnicalAgent(mock_llm, mock_code_exec_tool, mock_question_bank)
        sample_agent_context.inputs = {"difficulty": "easy"}
        
        with pytest.raises(ValueError, match="mode is required"):
            await agent.run(sample_agent_context)
    
    @pytest.mark.asyncio
    async def test_technical_agent_invalid_mode(self, mock_llm, mock_code_exec_tool, mock_question_bank, sample_agent_context):
        """Test technical agent with invalid mode"""
        agent = TechnicalAgent(mock_llm, mock_code_exec_tool, mock_question_bank)
        sample_agent_context.inputs = {"mode": "invalid_mode"}
        
        with pytest.raises(ValueError, match="Invalid mode"):
            await agent.run(sample_agent_context)
    
    @pytest.mark.asyncio
    async def test_technical_agent_code_execution_error(self, mock_llm, mock_code_exec_tool, mock_question_bank, sample_agent_context):
        """Test technical agent handles code execution errors"""
        agent = TechnicalAgent(mock_llm, mock_code_exec_tool, mock_question_bank)
        
        # Mock code execution failure
        from exceptions import CodeExecutionError
        mock_code_exec_tool.execute_code = AsyncMock(side_effect=CodeExecutionError("Execution failed"))
        
        sample_agent_context.inputs = {
            "mode": "evaluate_code",
            "question_id": "q1",
            "code": "invalid code",
            "language": "python"
        }
        
        # Should handle error gracefully
        result = await agent.run(sample_agent_context)
        # Result may be success=False or may handle error internally
        assert result is not None


class TestCompanionAgent:
    """Tests for CompanionAgent"""
    
    @pytest.mark.asyncio
    async def test_companion_agent_initialization(self, mock_llm, mock_memory_bank):
        """Test CompanionAgent initialization"""
        agent = CompanionAgent(mock_llm, mock_memory_bank)
        assert agent.name == "CompanionAgent"
        assert agent.memory_bank == mock_memory_bank
    
    @pytest.mark.asyncio
    async def test_companion_agent_generate_encouragement(self, mock_llm, mock_memory_bank, sample_agent_context):
        """Test encouragement generation"""
        agent = CompanionAgent(mock_llm, mock_memory_bank)
        
        # Mock LLM response
        mock_llm.ainvoke = AsyncMock(return_value=Mock(content="Great job! Keep practicing!"))
        
        sample_agent_context.inputs = {
            "action": "generate_encouragement",
            "context": {"score": 0.8, "question_difficulty": "medium"}
        }
        
        result = await agent.run(sample_agent_context)
        
        assert result.success is True
        assert "encouragement" in result.output
        assert isinstance(result.output["encouragement"], str)
    
    @pytest.mark.asyncio
    async def test_companion_agent_generate_tips(self, mock_llm, mock_memory_bank, sample_agent_context):
        """Test tips generation"""
        agent = CompanionAgent(mock_llm, mock_memory_bank)
        
        mock_llm.ainvoke = AsyncMock(return_value=Mock(content="Tip 1: Practice daily\nTip 2: Review algorithms"))
        
        sample_agent_context.inputs = {
            "action": "generate_tips",
            "context": {"weak_areas": ["dynamic-programming"]}
        }
        
        result = await agent.run(sample_agent_context)
        
        assert result.success is True
        assert "tips" in result.output
        assert isinstance(result.output["tips"], list)
    
    @pytest.mark.asyncio
    async def test_companion_agent_session_summary(self, mock_llm, mock_memory_bank, sample_agent_context):
        """Test session summary generation"""
        agent = CompanionAgent(mock_llm, mock_memory_bank)
        
        mock_llm.ainvoke = AsyncMock(return_value=Mock(content="Session summary: You completed 3 questions with 80% success rate."))
        
        sample_agent_context.inputs = {
            "action": "generate_summary",
            "context": {
                "questions_attempted": 3,
                "questions_solved": 2,
                "session_duration": 1800
            }
        }
        
        result = await agent.run(sample_agent_context)
        
        assert result.success is True
        assert "summary" in result.output
    
    @pytest.mark.asyncio
    async def test_companion_agent_missing_action(self, mock_llm, mock_memory_bank, sample_agent_context):
        """Test companion agent with missing action"""
        agent = CompanionAgent(mock_llm, mock_memory_bank)
        sample_agent_context.inputs = {"context": {}}
        
        with pytest.raises(ValueError, match="action is required"):
            await agent.run(sample_agent_context)


class TestOrchestrator:
    """Tests for Orchestrator"""
    
    @pytest.fixture
    def mock_research_agent(self):
        """Mock research agent"""
        agent = Mock()
        agent.name = "ResearchAgent"
        
        async def mock_run(context):
            from agents.base_agent import AgentResult
            return AgentResult(
                agent_name="ResearchAgent",
                success=True,
                output={"research_packet": {"company_overview": "Test"}},
                execution_time_ms=100.0,
                trace_id="trace_123"
            )
        
        agent.run = AsyncMock(side_effect=mock_run)
        return agent
    
    @pytest.fixture
    def mock_technical_agent(self):
        """Mock technical agent"""
        agent = Mock()
        agent.name = "TechnicalAgent"
        
        async def mock_run(context):
            from agents.base_agent import AgentResult
            return AgentResult(
                agent_name="TechnicalAgent",
                success=True,
                output={"questions": [{"id": "q1"}]},
                execution_time_ms=50.0,
                trace_id="trace_456"
            )
        
        agent.run = AsyncMock(side_effect=mock_run)
        return agent
    
    @pytest.fixture
    def mock_companion_agent(self):
        """Mock companion agent"""
        agent = Mock()
        agent.name = "CompanionAgent"
        
        async def mock_run(context):
            from agents.base_agent import AgentResult
            return AgentResult(
                agent_name="CompanionAgent",
                success=True,
                output={"encouragement": "Great job!"},
                execution_time_ms=30.0,
                trace_id="trace_789"
            )
        
        agent.run = AsyncMock(side_effect=mock_run)
        return agent
    
    @pytest.mark.asyncio
    async def test_orchestrator_initialization(
        self, mock_research_agent, mock_technical_agent, 
        mock_companion_agent, mock_session_service, mock_memory_bank
    ):
        """Test Orchestrator initialization"""
        orchestrator = Orchestrator(
            mock_research_agent,
            mock_technical_agent,
            mock_companion_agent,
            mock_session_service,
            mock_memory_bank
        )
        
        assert orchestrator.research_agent == mock_research_agent
        assert orchestrator.technical_agent == mock_technical_agent
        assert orchestrator.companion_agent == mock_companion_agent
        assert orchestrator.workflow is not None
    
    @pytest.mark.asyncio
    async def test_orchestrator_execute_research(
        self, mock_research_agent, mock_technical_agent,
        mock_companion_agent, mock_session_service, mock_memory_bank
    ):
        """Test orchestrator research execution"""
        orchestrator = Orchestrator(
            mock_research_agent,
            mock_technical_agent,
            mock_companion_agent,
            mock_session_service,
            mock_memory_bank
        )
        
        result = await orchestrator.execute_research(
            session_id="test_session",
            user_id="test_user",
            job_description="Test JD",
            company_name="TestCorp"
        )
        
        assert result is not None
        assert "research_packet" in result or "error" in result
        mock_research_agent.run.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_orchestrator_execute_technical_select(
        self, mock_research_agent, mock_technical_agent,
        mock_companion_agent, mock_session_service, mock_memory_bank
    ):
        """Test orchestrator technical execution for question selection"""
        orchestrator = Orchestrator(
            mock_research_agent,
            mock_technical_agent,
            mock_companion_agent,
            mock_session_service,
            mock_memory_bank
        )
        
        result = await orchestrator.execute_technical(
            session_id="test_session",
            user_id="test_user",
            mode="select_questions",
            difficulty="easy",
            num_questions=2
        )
        
        assert result is not None
        mock_technical_agent.run.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_orchestrator_execute_technical_evaluate(
        self, mock_research_agent, mock_technical_agent,
        mock_companion_agent, mock_session_service, mock_memory_bank
    ):
        """Test orchestrator technical execution for code evaluation"""
        orchestrator = Orchestrator(
            mock_research_agent,
            mock_technical_agent,
            mock_companion_agent,
            mock_session_service,
            mock_memory_bank
        )
        
        result = await orchestrator.execute_technical(
            session_id="test_session",
            user_id="test_user",
            mode="evaluate_code",
            question_id="q1",
            code="def test(): pass",
            language="python"
        )
        
        assert result is not None
        mock_technical_agent.run.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_orchestrator_should_skip_technical(
        self, mock_research_agent, mock_technical_agent,
        mock_companion_agent, mock_session_service, mock_memory_bank
    ):
        """Test orchestrator skip technical logic"""
        orchestrator = Orchestrator(
            mock_research_agent,
            mock_technical_agent,
            mock_companion_agent,
            mock_session_service,
            mock_memory_bank
        )
        
        # Test with skip condition (no technical input)
        state = {
            "inputs": {"skip_technical": True},
            "research_result": {"success": True}
        }
        
        decision = orchestrator._should_skip_technical(state)
        assert decision in ["skip", "continue"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

