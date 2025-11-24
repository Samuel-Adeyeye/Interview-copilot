"""
Integration tests for end-to-end workflows
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
import os

# Set test environment variables
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("TAVILY_API_KEY", "test-tavily-key")
os.environ.setdefault("JUDGE0_API_KEY", "test-judge0-key")
os.environ.setdefault("SESSION_PERSISTENCE_ENABLED", "false")
os.environ.setdefault("VECTOR_DB_PATH", "./data/vectordb_test")


class TestEndToEndWorkflows:
    """End-to-end workflow integration tests"""
    
    @pytest.mark.asyncio
    async def test_complete_interview_preparation_flow(self):
        """Test complete interview preparation workflow"""
        from memory.session_service import InMemorySessionService
        from memory.memory_bank import MemoryBank
        from agents.base_agent import AgentContext
        
        # Initialize services
        session_service = InMemorySessionService()
        memory_bank = MemoryBank(persist_directory="./data/vectordb_test")
        
        # Create session
        session_id = session_service.create_session("test_user")
        assert session_id is not None
        
        # Get session
        session = session_service.get_session(session_id)
        assert session is not None
        assert session["user_id"] == "test_user"
        
        # Pause and resume
        session_service.pause_session(session_id)
        paused_session = session_service.get_session(session_id)
        assert paused_session["state"] == "paused"
        
        session_service.resume_session(session_id)
        resumed_session = session_service.get_session(session_id)
        assert resumed_session["state"] == "running"
    
    @pytest.mark.asyncio
    async def test_question_bank_integration(self):
        """Test QuestionBank integration with agents"""
        from tools.question_bank import QuestionBank
        from agents.base_agent import AgentContext
        
        qb = QuestionBank()
        
        # Get questions by difficulty
        easy_questions = qb.get_questions_by_difficulty("easy")
        assert len(easy_questions) > 0
        
        # Get specific question
        if easy_questions:
            question_id = easy_questions[0]["id"]
            question = qb.get_question_by_id(question_id)
            assert question is not None
            assert question["id"] == question_id
    
    @pytest.mark.asyncio
    async def test_memory_bank_integration(self):
        """Test MemoryBank integration"""
        from memory.memory_bank import MemoryBank
        import tempfile
        import shutil
        
        # Use temporary directory
        temp_dir = tempfile.mkdtemp()
        try:
            memory_bank = MemoryBank(persist_directory=temp_dir)
            
            # Store research
            research_data = {
                "company_name": "TestCorp",
                "overview": "Test company",
                "tech_stack": ["Python", "FastAPI"]
            }
            
            # Note: store_research might need to be implemented or mocked
            # This is a placeholder test structure
            
            # Get user progress
            progress = await memory_bank.get_user_progress("test_user")
            assert progress is not None
            assert "total_sessions" in progress
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.mark.asyncio
    async def test_orchestrator_workflow(self):
        """Test orchestrator workflow integration"""
        from agents.orchestrator import Orchestrator
        from memory.session_service import InMemorySessionService
        from memory.memory_bank import MemoryBank
        from unittest.mock import Mock, AsyncMock
        
        # Create mock agents
        mock_research = Mock()
        mock_research.name = "ResearchAgent"
        
        async def mock_research_run(context):
            from agents.base_agent import AgentResult
            return AgentResult(
                agent_name="ResearchAgent",
                success=True,
                output={"research_packet": {"company_overview": "Test"}},
                execution_time_ms=100.0,
                trace_id="trace_123"
            )
        mock_research.run = AsyncMock(side_effect=mock_research_run)
        
        mock_technical = Mock()
        mock_technical.name = "TechnicalAgent"
        
        async def mock_technical_run(context):
            from agents.base_agent import AgentResult
            return AgentResult(
                agent_name="TechnicalAgent",
                success=True,
                output={"questions": [{"id": "q1"}]},
                execution_time_ms=50.0,
                trace_id="trace_456"
            )
        mock_technical.run = AsyncMock(side_effect=mock_technical_run)
        
        mock_companion = Mock()
        mock_companion.name = "CompanionAgent"
        
        async def mock_companion_run(context):
            from agents.base_agent import AgentResult
            return AgentResult(
                agent_name="CompanionAgent",
                success=True,
                output={"encouragement": "Great job!"},
                execution_time_ms=30.0,
                trace_id="trace_789"
            )
        mock_companion.run = AsyncMock(side_effect=mock_companion_run)
        
        # Initialize orchestrator
        session_service = InMemorySessionService()
        memory_bank = MemoryBank(persist_directory="./data/vectordb_test")
        
        orchestrator = Orchestrator(
            mock_research,
            mock_technical,
            mock_companion,
            session_service,
            memory_bank
        )
        
        # Test research execution
        result = await orchestrator.execute_research(
            session_id="test_session",
            user_id="test_user",
            job_description="Test JD",
            company_name="TestCorp"
        )
        
        assert result is not None
        mock_research.run.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_session_persistence_integration(self):
        """Test session persistence integration"""
        from memory.persistent_session_service import PersistentSessionService
        import tempfile
        import shutil
        
        temp_dir = tempfile.mkdtemp()
        try:
            # Create persistent session service
            session_service = PersistentSessionService(
                storage_type="file",
                storage_path=temp_dir,
                expiration_hours=24,
                auto_save=True
            )
            
            # Create session
            session_id = session_service.create_session("test_user")
            assert session_id is not None
            
            # Get session
            session = session_service.get_session(session_id)
            assert session is not None
            
            # Update metadata
            session_service.update_session_metadata(session_id, {"test": "value"})
            
            # Get storage stats
            stats = session_service.get_storage_stats()
            assert stats["total_sessions"] > 0
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


class TestErrorHandlingIntegration:
    """Integration tests for error handling"""
    
    @pytest.mark.asyncio
    async def test_error_propagation(self):
        """Test error propagation through the system"""
        from exceptions import SessionNotFoundError, ValidationError
        
        # Test SessionNotFoundError
        with pytest.raises(SessionNotFoundError):
            from memory.session_service import InMemorySessionService
            service = InMemorySessionService()
            service.get_session("nonexistent_session")
        
        # Test ValidationError
        with pytest.raises(ValidationError):
            from agents.base_agent import AgentContext
            # Create context with invalid inputs
            context = AgentContext(
                session_id="",  # Empty session_id should fail validation
                user_id="test",
                inputs={}
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

