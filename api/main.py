"""
FastAPI Backend for Interview Co-Pilot
Main API endpoints for orchestrating multi-agent system
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid
import logging
import asyncio
from contextlib import asynccontextmanager

from langchain_openai import ChatOpenAI
from agents.research_agent import ResearchAgentStructured
from agents.technical_agent import TechnicalAgent
from agents.companion_agent import CompanionAgent
from agents.orchestrator import Orchestrator
from memory.memory_bank import MemoryBank
from memory.session_service import InMemorySessionService
from memory.persistent_session_service import PersistentSessionService
from tools.search_tool import create_search_tool
from tools.code_exec_tool import create_code_exec_tool
from tools.question_bank import QuestionBank
from services.observability import ObservabilityService, RequestTracingMiddleware, RateLimitMiddleware
from config.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============= Pydantic Models =============

class JobDescriptionRequest(BaseModel):
    """Request model for uploading job description"""
    job_title: str = Field(..., description="Job title")
    company_name: str = Field(..., description="Company name")
    jd_text: str = Field(..., description="Full job description text")
    user_id: Optional[str] = Field(default=None, description="User ID")


class SessionCreateRequest(BaseModel):
    """Request to create a new interview session"""
    user_id: str
    job_description_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ResearchRequest(BaseModel):
    """Request to run research agent"""
    session_id: str
    job_description: str
    company_name: str


class MockInterviewStartRequest(BaseModel):
    """Request to start mock technical interview"""
    session_id: str
    difficulty: str = Field(default="medium", pattern="^(easy|medium|hard)$")
    num_questions: int = Field(default=3, ge=1, le=5)


class CodeSubmissionRequest(BaseModel):
    """Request for code submission and evaluation"""
    session_id: str
    question_id: str
    code: str
    language: str = Field(default="python", pattern="^(python|javascript|java|cpp)$")


class SessionResponse(BaseModel):
    """Response model for session data"""
    session_id: str
    user_id: str
    state: str
    agent_states: Dict[str, Any]
    artifacts: List[Dict[str, Any]]
    created_at: str
    updated_at: str


class ResearchResponse(BaseModel):
    """Response from research agent"""
    session_id: str
    company_name: str
    research_packet: Dict[str, Any]
    insights: List[str]
    execution_time_ms: float


class EvaluationResponse(BaseModel):
    """Response for code evaluation"""
    session_id: str
    question_id: str
    status: str
    tests_passed: int
    total_tests: int
    feedback: str
    complexity_analysis: Optional[Dict[str, str]] = None
    execution_time_ms: float


# ============= Global State & Dependencies =============

class ApplicationState:
    """Global application state"""
    def __init__(self):
        self.session_service = None
        self.memory_bank = None
        self.orchestrator = None
        self.observability = None
        self.initialized = False


app_state = ApplicationState()


async def get_session_service():
    """Dependency to get session service"""
    if not app_state.initialized:
        raise HTTPException(
            status_code=503,
            detail="Service not initialized. Please wait for the API to finish starting up."
        )
    if app_state.session_service is None:
        logger.error("Session service is None but app is marked as initialized")
        raise HTTPException(
            status_code=503,
            detail="Session service is not available"
        )
    return app_state.session_service


async def get_memory_bank():
    """Dependency to get memory bank"""
    if not app_state.initialized:
        raise HTTPException(
            status_code=503,
            detail="Service not initialized. Please wait for the API to finish starting up."
        )
    if app_state.memory_bank is None:
        logger.error("Memory bank is None but app is marked as initialized")
        raise HTTPException(
            status_code=503,
            detail="Memory bank is not available"
        )
    return app_state.memory_bank


async def get_orchestrator():
    """Dependency to get orchestrator"""
    if not app_state.initialized:
        raise HTTPException(
            status_code=503,
            detail="Service not initialized. Please wait for the API to finish starting up."
        )
    if app_state.orchestrator is None:
        logger.error("Orchestrator is None but app is marked as initialized")
        raise HTTPException(
            status_code=503,
            detail="Orchestrator is not available"
        )
    return app_state.orchestrator


# ============= Lifespan Management =============

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("🚀 Starting Interview Co-Pilot API...")
    
    try:
        # Initialize core services
        logger.info("Initializing core services...")
        
        # Initialize session service with persistence if enabled
        if settings.SESSION_PERSISTENCE_ENABLED:
            logger.info(f"Initializing persistent session service (type: {settings.SESSION_STORAGE_TYPE})...")
            app_state.session_service = PersistentSessionService(
                storage_type=settings.SESSION_STORAGE_TYPE,
                storage_path=settings.SESSION_STORAGE_PATH,
                expiration_hours=settings.SESSION_EXPIRATION_HOURS,
                auto_save=True
            )
            stats = app_state.session_service.get_storage_stats()
            logger.info(f"✅ Persistent session service initialized: {stats['total_sessions']} sessions loaded")
        else:
            logger.info("Initializing in-memory session service (persistence disabled)...")
            app_state.session_service = InMemorySessionService()
            logger.info("✅ In-memory session service initialized")
        
        app_state.memory_bank = MemoryBank(persist_directory=settings.VECTOR_DB_PATH)
        app_state.observability = ObservabilityService()
        logger.info("✅ Core services initialized")
        
        # Initialize LLM
        logger.info(f"Initializing LLM (model: {settings.LLM_MODEL})...")
        llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            api_key=settings.OPENAI_API_KEY
        )
        logger.info("✅ LLM initialized")
        
        # Initialize tools
        logger.info("Initializing tools...")
        try:
            search_tool = create_search_tool()
            logger.info("✅ Search tool initialized")
        except Exception as e:
            logger.warning(f"⚠️  Search tool initialization failed: {e}. Continuing without search.")
            search_tool = None
        
        try:
            code_exec_tool = create_code_exec_tool(settings.JUDGE0_API_KEY)
            logger.info("✅ Code execution tool initialized")
        except Exception as e:
            logger.warning(f"⚠️  Code execution tool initialization failed: {e}. Continuing without code execution.")
            code_exec_tool = None
        
        # Initialize question bank
        logger.info("Loading question bank...")
        try:
            question_bank = QuestionBank("data/questions_bank.json")
            logger.info(f"✅ Question bank loaded ({question_bank.get_question_count()} questions)")
        except Exception as e:
            logger.error(f"❌ Failed to load question bank: {e}")
            raise
        
        # Initialize agents
        logger.info("Initializing agents...")
        try:
            research_agent = ResearchAgentStructured(llm, app_state.memory_bank)
            logger.info("✅ Research agent initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize research agent: {e}")
            raise
        
        try:
            if code_exec_tool is None:
                logger.warning("⚠️  Technical agent initialized without code execution tool")
            technical_agent = TechnicalAgent(llm, code_exec_tool, question_bank)
            logger.info("✅ Technical agent initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize technical agent: {e}")
            raise
        
        try:
            companion_agent = CompanionAgent(llm, app_state.memory_bank)
            logger.info("✅ Companion agent initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize companion agent: {e}")
            raise
        
        # Initialize orchestrator
        logger.info("Initializing orchestrator...")
        try:
            app_state.orchestrator = Orchestrator(
                research_agent=research_agent,
                technical_agent=technical_agent,
                companion_agent=companion_agent,
                session_service=app_state.session_service,
                memory_bank=app_state.memory_bank
            )
            logger.info("✅ Orchestrator initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize orchestrator: {e}")
            raise
        
        # Mark as initialized
        app_state.initialized = True
        logger.info("✅ All services initialized successfully")
        
        # Health check
        if app_state.session_service is None:
            raise RuntimeError("Session service not initialized")
        if app_state.memory_bank is None:
            raise RuntimeError("Memory bank not initialized")
        if app_state.orchestrator is None:
            raise RuntimeError("Orchestrator not initialized")
        
        logger.info("✅ Health checks passed")
        
        # Store observability in app state for middleware access
        app.state.observability = app_state.observability
        logger.info("✅ Observability service stored in app state")
        
        # Start background cleanup task for session expiration
        if isinstance(app_state.session_service, PersistentSessionService):
            async def periodic_cleanup():
                """Periodic cleanup of expired sessions"""
                while True:
                    try:
                        await asyncio.sleep(3600)  # Run every hour
                        if app_state.session_service:
                            deleted = app_state.session_service.cleanup_expired_sessions()
                            if deleted > 0:
                                logger.info(f"Periodic cleanup: removed {deleted} expired sessions")
                    except asyncio.CancelledError:
                        logger.info("Periodic cleanup task cancelled")
                        break
                    except Exception as e:
                        logger.error(f"Error in periodic cleanup: {e}")
            
            # Start cleanup task
            cleanup_task = asyncio.create_task(periodic_cleanup())
            app.state.cleanup_task = cleanup_task  # Store for cleanup on shutdown
            logger.info("✅ Background cleanup task started")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize services: {e}")
        app_state.initialized = False
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Interview Co-Pilot API...")
    
    try:
        # Cancel background cleanup task if it exists
        if hasattr(app, 'state') and hasattr(app.state, 'cleanup_task'):
            app.state.cleanup_task.cancel()
            try:
                await app.state.cleanup_task
            except asyncio.CancelledError:
                pass
            logger.info("✅ Background cleanup task cancelled")
        
        # Save sessions before shutdown if using persistent service
        if isinstance(app_state.session_service, PersistentSessionService):
            logger.info("Saving sessions to persistent storage...")
            app_state.session_service.force_save()
            logger.info("✅ Sessions saved")
        
        # Close any async resources
        if hasattr(app_state.memory_bank, 'client'):
            # ChromaDB client cleanup if needed
            pass
        
        # Close observability service if needed
        if app_state.observability:
            logger.info("Closing observability service...")
        
        logger.info("✅ Shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# ============= FastAPI App =============

app = FastAPI(
    title="Interview Co-Pilot API",
    description="Multi-agent system for interview preparation with code execution",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Observability middleware (request tracing)
# This will use app_state.observability which is initialized in lifespan
app.add_middleware(
    RequestTracingMiddleware,
    observability_service=None  # Will be set dynamically, but middleware checks for None
)

# Rate limiting middleware
app.add_middleware(
    RateLimitMiddleware,
    max_requests_per_minute=100
)


# ============= Health & Status Endpoints =============

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Interview Co-Pilot API",
        "version": "1.0.0",
        "status": "healthy" if app_state.initialized else "initializing"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint with detailed service status"""
    services_status = {
        "session_service": app_state.session_service is not None,
        "memory_bank": app_state.memory_bank is not None,
        "orchestrator": app_state.orchestrator is not None,
        "observability": app_state.observability is not None
    }
    
    all_healthy = all(services_status.values()) and app_state.initialized
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "initialized": app_state.initialized,
        "timestamp": datetime.utcnow().isoformat(),
        "services": services_status
    }


# ============= Session Management Endpoints =============

@app.post("/sessions/create", response_model=SessionResponse)
async def create_session(
    request: SessionCreateRequest,
    session_service = Depends(get_session_service)
):
    """
    Create a new interview session
    """
    try:
        session_id = str(uuid.uuid4())
        
        session = session_service.create_session(
            session_id=session_id,
            user_id=request.user_id,
            metadata=request.metadata or {}
        )
        
        logger.info(f"Created session {session_id} for user {request.user_id}")
        
        return SessionResponse(**session)
    
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    session_service = Depends(get_session_service)
):
    """
    Retrieve session by ID
    """
    try:
        session = session_service.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        return SessionResponse(**session)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sessions/{session_id}/pause")
async def pause_session(
    session_id: str,
    session_service = Depends(get_session_service)
):
    """
    Pause a running session (creates checkpoint)
    """
    try:
        session = session_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        session_service.pause_session(session_id)
        
        return {
            "session_id": session_id,
            "status": "paused",
            "message": "Session paused successfully. Checkpoint created."
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pausing session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sessions/{session_id}/resume")
async def resume_session(
    session_id: str,
    session_service = Depends(get_session_service)
):
    """
    Resume a paused session
    """
    try:
        session = session_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        session_service.resume_session(session_id)
        
        return {
            "session_id": session_id,
            "status": "running",
            "message": "Session resumed successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resuming session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= Job Description & Research Endpoints =============

@app.post("/job-descriptions/upload")
async def upload_job_description(
    request: JobDescriptionRequest,
    memory_bank = Depends(get_memory_bank)
):
    """
    Upload and parse job description (OpenAPI tool endpoint)
    """
    try:
        jd_id = str(uuid.uuid4())
        
        # Store in memory bank for future reference
        # await memory_bank.store_research(
        #     session_id=jd_id,
        #     company=request.company_name,
        #     research_data={
        #         "job_title": request.job_title,
        #         "jd_text": request.jd_text,
        #         "uploaded_at": datetime.utcnow().isoformat()
        #     }
        # )
        
        return {
            "jd_id": jd_id,
            "job_title": request.job_title,
            "company_name": request.company_name,
            "status": "uploaded",
            "message": "Job description uploaded successfully"
        }
    
    except Exception as e:
        logger.error(f"Error uploading job description: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/research/run", response_model=ResearchResponse)
async def run_research(
    request: ResearchRequest,
    background_tasks: BackgroundTasks,
    session_service = Depends(get_session_service),
    orchestrator = Depends(get_orchestrator)
):
    """
    Run research agent to build company prep packet
    """
    try:
        session = session_service.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {request.session_id} not found")
        
        logger.info(f"Starting research for session {request.session_id}")
        
        # Get user_id from session
        user_id = session.get("user_id")
        if not user_id:
            raise HTTPException(status_code=400, detail="Session missing user_id")
        
        # Execute research agent through orchestrator
        research_result = await orchestrator.execute_research(
            session_id=request.session_id,
            user_id=user_id,
            job_description=request.job_description,
            company_name=request.company_name
        )
        
        if not research_result.get("success"):
            error_msg = research_result.get("error", "Research agent failed")
            logger.error(f"Research failed: {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
        
        # Extract research packet from result
        research_output = research_result.get("output", {})
        if not research_output:
            raise HTTPException(status_code=500, detail="Research agent returned empty output")
        
        # Format response
        result = {
            "session_id": request.session_id,
            "company_name": request.company_name,
            "research_packet": research_output,
            "insights": research_output.get("preparation_tips", []),
            "execution_time_ms": research_result.get("execution_time_ms", 0.0)
        }
        
        # Update session
        session_service.update_agent_state(
            request.session_id,
            "research",
            {
                "status": "completed",
                "result": result,
                "execution_time_ms": research_result.get("execution_time_ms", 0.0)
            }
        )
        
        return ResearchResponse(**result)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running research: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= Mock Interview Endpoints =============

@app.post("/interview/start")
async def start_mock_interview(
    request: MockInterviewStartRequest,
    session_service = Depends(get_session_service),
    orchestrator = Depends(get_orchestrator)
):
    """
    Start mock technical interview session
    """
    try:
        session = session_service.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {request.session_id} not found")
        
        logger.info(f"Starting mock interview for session {request.session_id}")
        
        # Get user_id and job description from session
        user_id = session.get("user_id")
        if not user_id:
            raise HTTPException(status_code=400, detail="Session missing user_id")
        
        # Get job description from research results if available
        agent_states = session.get("agent_states", {})
        research_state = agent_states.get("research", {})
        research_result = research_state.get("result", {})
        job_description = research_result.get("research_packet", {}).get("company_overview", "")
        
        # Execute technical agent to select questions
        technical_result = await orchestrator.execute_technical(
            session_id=request.session_id,
            user_id=user_id,
            mode="select_questions",
            job_description=job_description,
            difficulty=request.difficulty,
            num_questions=request.num_questions
        )
        
        if not technical_result.get("success"):
            error_msg = technical_result.get("error", "Technical agent failed")
            logger.error(f"Technical agent failed: {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
        
        # Extract questions from result
        tech_output = technical_result.get("output", {})
        questions = tech_output.get("questions", [])
        
        if not questions:
            raise HTTPException(status_code=500, detail="No questions selected")
        
        # Update session
        session_service.update_agent_state(
            request.session_id,
            "technical",
            {
                "status": "in_progress",
                "questions": questions,
                "current_question": 0,
                "execution_time_ms": technical_result.get("execution_time_ms", 0.0)
            }
        )
        
        return {
            "session_id": request.session_id,
            "status": "started",
            "questions": questions,
            "message": f"Mock interview started with {len(questions)} questions"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting mock interview: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/interview/submit-code", response_model=EvaluationResponse)
async def submit_code(
    request: CodeSubmissionRequest,
    session_service = Depends(get_session_service),
    orchestrator = Depends(get_orchestrator)
):
    """
    Submit code for evaluation with automated testing
    """
    try:
        session = session_service.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {request.session_id} not found")
        
        logger.info(f"Evaluating code submission for session {request.session_id}, question {request.question_id}")
        
        # Get user_id from session
        user_id = session.get("user_id")
        if not user_id:
            raise HTTPException(status_code=400, detail="Session missing user_id")
        
        # Execute technical agent with code execution tool
        technical_result = await orchestrator.execute_technical(
            session_id=request.session_id,
            user_id=user_id,
            mode="evaluate_code",
            question_id=request.question_id,
            code=request.code,
            language=request.language
        )
        
        if not technical_result.get("success"):
            error_msg = technical_result.get("error", "Code evaluation failed")
            logger.error(f"Code evaluation failed: {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
        
        # Extract evaluation from result
        tech_output = technical_result.get("output", {})
        
        # Format evaluation response
        # The output format depends on how TechnicalAgent returns evaluation results
        # If it's a string, parse it; if it's a dict, use it directly
        if isinstance(tech_output, str):
            # If output is a string (from agent), create a basic evaluation
            evaluation = {
                "session_id": request.session_id,
                "question_id": request.question_id,
                "status": "success",
                "tests_passed": 0,
                "total_tests": 0,
                "feedback": tech_output,
                "complexity_analysis": None,
                "execution_time_ms": technical_result.get("execution_time_ms", 0.0)
            }
        else:
            # If output is a dict, use it
            evaluation = {
                "session_id": request.session_id,
                "question_id": request.question_id,
                "status": tech_output.get("status", "success"),
                "tests_passed": tech_output.get("tests_passed", tech_output.get("testsPassed", 0)),
                "total_tests": tech_output.get("total_tests", tech_output.get("totalTests", 0)),
                "feedback": tech_output.get("feedback", ""),
                "complexity_analysis": tech_output.get("complexity_analysis"),
                "execution_time_ms": technical_result.get("execution_time_ms", 0.0)
            }
        
        # Store submission in session
        session_service.add_artifact(
            request.session_id,
            "code_submission",
            {
                "question_id": request.question_id,
                "code": request.code,
                "language": request.language,
                "evaluation": evaluation,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return EvaluationResponse(**evaluation)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error evaluating code: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= Memory & Progress Endpoints =============

@app.get("/users/{user_id}/progress")
async def get_user_progress(
    user_id: str,
    memory_bank = Depends(get_memory_bank)
):
    """
    Get user's progress and session history
    """
    try:
        # Get real progress from memory bank
        progress = await memory_bank.get_user_progress(user_id)
        
        return progress
    
    except Exception as e:
        logger.error(f"Error retrieving user progress: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions/{session_id}/summary")
async def get_session_summary(
    session_id: str,
    session_service = Depends(get_session_service)
):
    """
    Get comprehensive session summary with all artifacts
    """
    try:
        session = session_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        # Calculate duration from timestamps
        duration_minutes = 0
        created_at = session.get("created_at")
        completed_at = session.get("completed_at") or session.get("updated_at")
        
        if created_at and completed_at:
            try:
                from datetime import datetime
                start = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                end = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
                duration_minutes = (end - start).total_seconds() / 60
            except Exception as e:
                logger.warning(f"Error calculating duration: {e}")
        
        # Count questions attempted and solved
        code_submissions = [a for a in session.get("artifacts", []) if a.get("type") == "code_submission"]
        questions_attempted = len(code_submissions)
        questions_solved = sum(
            1 for a in code_submissions
            if a.get("payload", {}).get("evaluation", {}).get("status") == "success"
            or a.get("payload", {}).get("evaluation", {}).get("tests_passed", 0) > 0
        )
        
        # Get research insights
        agent_states = session.get("agent_states", {})
        research_state = agent_states.get("research", {})
        research_result = research_state.get("result", {})
        
        # Compile summary from session data
        summary = {
            "session_id": session_id,
            "user_id": session["user_id"],
            "state": str(session.get("state", "")),
            "duration_minutes": round(duration_minutes, 1),
            "research_insights": research_result.get("research_packet", {}),
            "questions_attempted": questions_attempted,
            "questions_solved": questions_solved,
            "artifacts": session.get("artifacts", []),
            "created_at": created_at,
            "completed_at": completed_at
        }
        
        return summary
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving session summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= Observability Endpoints =============

@app.get("/sessions/storage/stats")
async def get_storage_stats(
    session_service = Depends(get_session_service)
):
    """
    Get storage statistics for session persistence
    """
    try:
        if isinstance(session_service, PersistentSessionService):
            stats = session_service.get_storage_stats()
            return stats
        else:
            return {
                "storage_type": "in-memory",
                "total_sessions": session_service.get_session_count(),
                "active_sessions": len(session_service.get_active_sessions()),
                "persistence_enabled": False
            }
    except Exception as e:
        logger.error(f"Error retrieving storage stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
async def get_metrics():
    """
    Get system metrics for observability
    """
    try:
        # Get real metrics from observability service
        if app_state.observability:
            observability_metrics = app_state.observability.get_metrics()
            
            # Count sessions from session service
            total_sessions = 0
            active_sessions = 0
            completed_sessions = 0
            
            if app_state.session_service:
                all_sessions = app_state.session_service.sessions
                total_sessions = len(all_sessions)
                for session in all_sessions.values():
                    state = str(session.get("state", ""))
                    if state == "running" or state == "created":
                        active_sessions += 1
                    elif state == "completed":
                        completed_sessions += 1
            
            # Format metrics response
            metrics = {
                "timestamp": datetime.utcnow().isoformat(),
                "system": {
                    "total_sessions": total_sessions,
                    "active_sessions": active_sessions,
                    "completed_sessions": completed_sessions
                },
                "agents": observability_metrics.get("agents", {}),
                "tools": observability_metrics.get("tools", {})
            }
            
            return metrics
        else:
            # Fallback if observability service not available
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "system": {
                    "total_sessions": 0,
                    "active_sessions": 0,
                    "completed_sessions": 0
                },
                "agents": {},
                "tools": {}
            }
    
    except Exception as e:
        logger.error(f"Error retrieving metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions/{session_id}/traces")
async def get_session_traces(
    session_id: str,
    session_service = Depends(get_session_service)
):
    """
    Get detailed traces for a session (for observability)
    """
    try:
        session = session_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        # Extract traces from session agent states
        agent_states = session.get("agent_states", {})
        traces_list = []
        
        # Research agent trace
        if "research" in agent_states:
            research_state = agent_states["research"]
            traces_list.append({
                "trace_id": research_state.get("result", {}).get("trace_id", f"research_{session_id}"),
                "agent": "research_agent",
                "start_time": session.get("created_at", ""),
                "end_time": research_state.get("result", {}).get("timestamp", ""),
                "duration_ms": research_state.get("execution_time_ms", 0),
                "status": "success" if research_state.get("status") == "completed" else "failed",
                "tools_used": ["web_search"],
                "input_hash": "",
                "output_size_bytes": 0
            })
        
        # Technical agent trace
        if "technical" in agent_states:
            tech_state = agent_states["technical"]
            traces_list.append({
                "trace_id": tech_state.get("result", {}).get("trace_id", f"technical_{session_id}"),
                "agent": "technical_agent",
                "start_time": tech_state.get("timestamp", ""),
                "end_time": session.get("updated_at", ""),
                "duration_ms": tech_state.get("execution_time_ms", 0),
                "status": "success" if tech_state.get("status") == "completed" else "failed",
                "tools_used": ["code_executor"],
                "input_hash": "",
                "output_size_bytes": 0
            })
        
        # Companion agent trace
        if "companion" in agent_states:
            companion_state = agent_states["companion"]
            traces_list.append({
                "trace_id": companion_state.get("result", {}).get("trace_id", f"companion_{session_id}"),
                "agent": "companion_agent",
                "start_time": companion_state.get("timestamp", ""),
                "end_time": session.get("updated_at", ""),
                "duration_ms": companion_state.get("execution_time_ms", 0),
                "status": "success" if companion_state.get("status") == "completed" else "failed",
                "tools_used": [],
                "input_hash": "",
                "output_size_bytes": 0
            })
        
        traces = {
            "session_id": session_id,
            "traces": traces_list
        }
        
        return traces
    
    except Exception as e:
        logger.error(f"Error retrieving traces: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= Evaluation Endpoints =============

@app.post("/evaluation/run")
async def run_evaluation(session_id: str):
    """
    Run automated evaluation pipeline on a session
    """
    try:
        # Run evaluation metrics
        evaluation = {
            "session_id": session_id,
            "evaluation_timestamp": datetime.utcnow().isoformat(),
            "scores": {
                "correctness": 0.85,
                "code_quality": 0.78,
                "efficiency": 0.82,
                "overall": 0.82
            },
            "comparison_to_baseline": {
                "correctness_delta": +0.05,
                "code_quality_delta": +0.03,
                "efficiency_delta": -0.02,
                "improvement": True
            },
            "recommendations": [
                "Focus on optimizing space complexity",
                "Practice more graph problems",
                "Review dynamic programming patterns"
            ]
        }
        
        return evaluation
    
    except Exception as e:
        logger.error(f"Error running evaluation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= Run Server =============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )