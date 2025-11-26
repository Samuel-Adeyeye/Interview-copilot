"""
ADK App and Runner Setup
Creates and configures ADK App and Runner for Interview Co-Pilot
"""

from google.adk.apps.app import App, EventsCompactionConfig
from google.adk.runners import Runner
from agents.adk.orchestrator import create_adk_orchestrator
from memory.adk.session_service import create_adk_session_service
from memory.adk.memory_service import create_adk_memory_service
from config.settings import settings
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class ADKApplication:
    """
    ADK Application wrapper that manages App and Runner instances.
    """
    
    def __init__(
        self,
        use_database_session: bool = None,
        db_url: Optional[str] = None,
        use_vertex_ai_memory: bool = False,
        project_id: Optional[str] = None,
        location: Optional[str] = None,
        memory_bank_id: Optional[str] = None,
        use_sequential_orchestrator: bool = True,
        use_builtin_code_executor: bool = True,
        judge0_api_key: Optional[str] = None
    ):
        """
        Initialize ADK Application.
        
        Args:
            use_database_session: If True, use DatabaseSessionService. If None, uses settings.
            db_url: Database URL (required if use_database_session=True)
            use_vertex_ai_memory: If True, use VertexAIMemoryBank
            project_id: GCP project ID (required if use_vertex_ai_memory=True)
            location: GCP location (required if use_vertex_ai_memory=True)
            memory_bank_id: Memory bank ID (required if use_vertex_ai_memory=True)
            use_sequential_orchestrator: If True, use SequentialAgent. If False, use LLM orchestrator.
            use_builtin_code_executor: If True, use BuiltInCodeExecutor
            judge0_api_key: Optional Judge0 API key
        """
        # Determine session service configuration
        if use_database_session is None:
            use_database_session = (
                settings.SESSION_PERSISTENCE_ENABLED and
                settings.SESSION_STORAGE_TYPE == "database"
            )
        
        if use_database_session and not db_url:
            db_url = settings.SESSION_STORAGE_PATH if settings.SESSION_PERSISTENCE_ENABLED else None
        
        # Create session service
        self.session_service = create_adk_session_service(
            use_database=use_database_session,
            db_url=db_url,
            app_name="interview_copilot"
        )
        
        # Create memory service
        self.memory_service = create_adk_memory_service(
            use_vertex_ai=use_vertex_ai_memory,
            project_id=project_id or getattr(settings, 'GCP_PROJECT_ID', None),
            location=location or getattr(settings, 'GCP_LOCATION', None),
            memory_bank_id=memory_bank_id or getattr(settings, 'MEMORY_BANK_ID', None)
        )
        
        # Create orchestrator
        self.orchestrator = create_adk_orchestrator(
            session_service=self.session_service,
            memory_bank=self.memory_service,
            use_sequential=use_sequential_orchestrator,
            use_builtin_code_executor=use_builtin_code_executor,
            judge0_api_key=judge0_api_key
        )
        
        # Create ADK App
        self.app = App(
            name="interview_copilot",
            root_agent=self.orchestrator.workflow,
            events_compaction_config=EventsCompactionConfig(
                compaction_interval=5,  # Compact every 5 events
                overlap_size=2  # Keep 2 events of overlap
            )
        )
        
        # Create Runner
        # Note: Runner expects the underlying ADK session service
        # The wrapper provides .service attribute for the actual ADK service
        adk_session_service = self.session_service.service if hasattr(self.session_service, 'service') else self.session_service
        self.runner = Runner(
            app=self.app,
            session_service=adk_session_service
        )
        
        logger.info("✅ ADK Application initialized")
        logger.info(f"   - Session Service: {'Database' if use_database_session else 'In-Memory'}")
        logger.info(f"   - Memory Service: {'Vertex AI' if use_vertex_ai_memory else 'In-Memory'}")
        logger.info(f"   - Orchestrator: {'Sequential' if use_sequential_orchestrator else 'LLM-based'}")
    
    async def run_workflow(
        self,
        user_id: str,
        session_id: str,
        message: str
    ):
        """
        Run the workflow with a user message.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            message: User message text
        
        Yields:
            Event objects from the runner
        """
        from google.genai import types
        
        # Ensure session exists in the runner's session service
        # This is necessary when using InMemorySessionService which has isolated storage
        try:
            session_service = self.runner.session_service
            
            # Try to get the session
            existing_session = await session_service.get_session(
                app_name="interview_copilot",
                user_id=user_id,
                session_id=session_id
            )
            
            # If session doesn't exist, create it
            if not existing_session:
                logger.info(f"Creating session {session_id} in runner's session service")
                await session_service.create_session(
                    app_name="interview_copilot",
                    user_id=user_id,
                    session_id=session_id
                )
        except Exception as e:
            logger.warning(f"Could not ensure session exists: {e}, continuing anyway")
        
        # Create user message
        query = types.Content(
            role="user",
            parts=[types.Part(text=message)]
        )
        
        # Run workflow
        async for event in self.runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=query
        ):
            yield event
    
    async def run_research(
        self,
        user_id: str,
        session_id: str,
        company_name: str,
        job_description: str
    ):
        """
        Run research agent only.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            company_name: Company name
            job_description: Job description text
        
        Yields:
            Event objects from the runner
        """
        message = f"""Research {company_name} and gather information about:
- Company overview and recent news
- Interview process and experience
- Technology stack and engineering practices
- Company culture and values

Job Description context:
{job_description[:500]}{'...' if len(job_description) > 500 else ''}"""
        
        async for event in self.run_workflow(user_id, session_id, message):
            yield event
    
    async def run_technical(
        self,
        user_id: str,
        session_id: str,
        mode: str,
        **kwargs
    ):
        """
        Run technical agent only.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            mode: "select_questions" or "evaluate_code"
            **kwargs: Mode-specific arguments
        
        Yields:
            Event objects from the runner
        """
        if mode == "select_questions":
            difficulty = kwargs.get("difficulty", "medium")
            num_questions = kwargs.get("num_questions", 3)
            job_description = kwargs.get("job_description", "")
            
            message = f"""Select {num_questions} {difficulty} difficulty coding interview questions.

Job Description:
{job_description[:500] if job_description else 'General software engineering'}

Use the question bank tools to get appropriate questions."""
            
        elif mode == "evaluate_code":
            question_id = kwargs.get("question_id")
            code = kwargs.get("code", "")
            language = kwargs.get("language", "python")
            
            if not question_id or not code:
                raise ValueError("question_id and code are required for code evaluation")
            
            message = f"""Evaluate this code submission:

Question ID: {question_id}
Language: {language}
Code:
```{language}
{code}
```

Use get_question_by_id() to get test cases, then execute the code and provide comprehensive feedback."""
        else:
            raise ValueError(f"Invalid mode: {mode}")
        
        async for event in self.run_workflow(user_id, session_id, message):
            yield event


# Global ADK application instance
_adk_app: Optional[ADKApplication] = None


def get_adk_app() -> ADKApplication:
    """
    Get or create the global ADK application instance.
    
    Uses the shared orchestrator from app_state to ensure session consistency.
    
    Returns:
        ADKApplication instance
    """
    global _adk_app
    
    if _adk_app is None:
        # Import here to avoid circular dependency
        from api.main import app_state
        
        # Use the shared orchestrator from app_state if available
        if app_state.orchestrator and app_state.session_service:
            logger.info("Using shared orchestrator and session service from app_state")
            
            # Create a minimal ADKApplication that uses the shared services
            _adk_app = ADKApplication.__new__(ADKApplication)
            _adk_app.session_service = app_state.session_service
            _adk_app.memory_service = app_state.memory_bank
            _adk_app.orchestrator = app_state.orchestrator
            
            # Create ADK App from the shared orchestrator
            _adk_app.app = App(
                name="interview_copilot",
                root_agent=app_state.orchestrator.workflow,
                events_compaction_config=EventsCompactionConfig(
                    compaction_interval=5,
                    overlap_size=2
                )
            )
            
            # Create Runner with the shared session service
            adk_session_service = app_state.session_service.service if hasattr(app_state.session_service, 'service') else app_state.session_service
            _adk_app.runner = Runner(
                app=_adk_app.app,
                session_service=adk_session_service
            )
            
            logger.info("✅ ADK Application initialized with shared services")
        else:
            # Fallback: create standalone instance
            logger.warning("app_state not available, creating standalone ADK application")
            _adk_app = ADKApplication(
                use_sequential_orchestrator=True,
                use_builtin_code_executor=True
            )
    
    return _adk_app



def initialize_adk_app(
    use_database_session: bool = None,
    db_url: Optional[str] = None,
    use_vertex_ai_memory: bool = False,
    project_id: Optional[str] = None,
    location: Optional[str] = None,
    memory_bank_id: Optional[str] = None,
    use_sequential_orchestrator: bool = True,
    use_builtin_code_executor: bool = True,
    judge0_api_key: Optional[str] = None
) -> ADKApplication:
    """
    Initialize the global ADK application instance.
    
    Args:
        use_database_session: If True, use DatabaseSessionService
        db_url: Database URL
        use_vertex_ai_memory: If True, use VertexAIMemoryBank
        project_id: GCP project ID
        location: GCP location
        memory_bank_id: Memory bank ID
        use_sequential_orchestrator: If True, use SequentialAgent
        use_builtin_code_executor: If True, use BuiltInCodeExecutor
        judge0_api_key: Optional Judge0 API key
    
    Returns:
        ADKApplication instance
    """
    global _adk_app
    
    _adk_app = ADKApplication(
        use_database_session=use_database_session,
        db_url=db_url,
        use_vertex_ai_memory=use_vertex_ai_memory,
        project_id=project_id,
        location=location,
        memory_bank_id=memory_bank_id,
        use_sequential_orchestrator=use_sequential_orchestrator,
        use_builtin_code_executor=use_builtin_code_executor,
        judge0_api_key=judge0_api_key
    )
    
    return _adk_app

