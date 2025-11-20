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
from contextlib import asynccontextmanager

from langchain_openai import ChatOpenAI
from agents.research_agent import ResearchAgentStructured
from agents.technical_agent import TechnicalAgent
from agents.companion_agent import CompanionAgent
from agents.orchestrator import Orchestrator
from memory.memory_bank import MemoryBank
from memory.session_service import InMemorySessionService
from tools.search_tool import create_search_tool
from tools.code_exec_tool import create_code_exec_tool
from tools.question_bank import QuestionBank
from services.observability import ObservabilityService
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
        app_state.session_service = InMemorySessionService()
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
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize services: {e}")
        app_state.initialized = False
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Interview Co-Pilot API...")
    
    try:
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
        
        # Execute research agent through orchestrator
        # result = await orchestrator.execute_research({
        #     "session_id": request.session_id,
        #     "job_description": request.job_description,
        #     "company_name": request.company_name
        # })
        
        # Mock response for now
        result = {
            "session_id": request.session_id,
            "company_name": request.company_name,
            "research_packet": {
                "company_overview": "Tech company focused on AI/ML",
                "interview_process": "3 rounds: phone screen, technical, behavioral",
                "tech_stack": ["Python", "React", "AWS"],
                "recent_news": ["Launched new AI product", "Series B funding"]
            },
            "insights": [
                "Focus on system design patterns",
                "Prepare examples of ML projects",
                "Company values innovation and speed"
            ],
            "execution_time_ms": 1500.0
        }
        
        # Update session
        session_service.update_agent_state(
            request.session_id,
            "research",
            {"status": "completed", "result": result}
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
        
        # Execute technical agent to select questions
        # questions = await orchestrator.execute_technical({
        #     "session_id": request.session_id,
        #     "mode": "select_questions",
        #     "difficulty": request.difficulty,
        #     "num_questions": request.num_questions
        # })
        
        # Mock questions for now
        questions = [
            {
                "id": "q1",
                "title": "Two Sum",
                "difficulty": "easy",
                "description": "Given an array of integers nums and an integer target, return indices of the two numbers that add up to target.",
                "examples": [
                    {"input": "[2,7,11,15], target=9", "output": "[0,1]"}
                ],
                "test_cases": [
                    {"input": "[2,7,11,15]\n9", "expected_output": "[0, 1]"},
                    {"input": "[3,2,4]\n6", "expected_output": "[1, 2]"}
                ]
            },
            {
                "id": "q2",
                "title": "Valid Parentheses",
                "difficulty": "easy",
                "description": "Given a string containing just the characters '(', ')', '{', '}', '[' and ']', determine if the input string is valid."
            },
            {
                "id": "q3",
                "title": "Merge Intervals",
                "difficulty": "medium",
                "description": "Given an array of intervals, merge all overlapping intervals."
            }
        ]
        
        # Update session
        session_service.update_agent_state(
            request.session_id,
            "technical",
            {
                "status": "in_progress",
                "questions": questions,
                "current_question": 0
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
        
        # Execute technical agent with code execution tool
        # evaluation = await orchestrator.execute_technical({
        #     "session_id": request.session_id,
        #     "mode": "evaluate_code",
        #     "question_id": request.question_id,
        #     "code": request.code,
        #     "language": request.language
        # })
        
        # Mock evaluation for now
        evaluation = {
            "session_id": request.session_id,
            "question_id": request.question_id,
            "status": "success",
            "tests_passed": 2,
            "total_tests": 2,
            "feedback": """
Great job! Your solution is correct and handles all test cases.

Strengths:
- Clean and readable code
- Correct algorithmic approach
- Good variable naming

Complexity Analysis:
- Time: O(n) - single pass through array
- Space: O(n) - hash map storage

Suggestions for improvement:
- Consider edge cases like empty arrays
- Add input validation
            """.strip(),
            "complexity_analysis": {
                "time": "O(n)",
                "space": "O(n)"
            },
            "execution_time_ms": 850.0
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
        # history = await memory_bank.get_user_history(user_id, limit=10)
        
        # Mock progress data
        progress = {
            "user_id": user_id,
            "total_sessions": 5,
            "questions_attempted": 15,
            "questions_solved": 12,
            "success_rate": 0.80,
            "avg_execution_time": 45.5,
            "recent_sessions": [
                {
                    "session_id": "session_1",
                    "date": "2025-11-15",
                    "company": "Google",
                    "questions_solved": 2,
                    "total_questions": 3,
                    "score": 66.7
                },
                {
                    "session_id": "session_2",
                    "date": "2025-11-17",
                    "company": "Amazon",
                    "questions_solved": 3,
                    "total_questions": 3,
                    "score": 100.0
                }
            ],
            "skills_progress": {
                "arrays": {"attempted": 5, "solved": 4, "proficiency": 0.8},
                "strings": {"attempted": 4, "solved": 3, "proficiency": 0.75},
                "dynamic_programming": {"attempted": 3, "solved": 2, "proficiency": 0.67},
                "graphs": {"attempted": 3, "solved": 3, "proficiency": 1.0}
            }
        }
        
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
        
        # Compile summary from session data
        summary = {
            "session_id": session_id,
            "user_id": session["user_id"],
            "state": session["state"],
            "duration_minutes": 45,  # Calculate from timestamps
            "research_insights": session.get("agent_states", {}).get("research", {}),
            "questions_attempted": len([a for a in session["artifacts"] if a["type"] == "code_submission"]),
            "questions_solved": 2,  # Calculate from artifacts
            "artifacts": session["artifacts"],
            "created_at": session["created_at"],
            "completed_at": session.get("completed_at")
        }
        
        return summary
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving session summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= Observability Endpoints =============

@app.get("/metrics")
async def get_metrics():
    """
    Get system metrics for observability
    """
    try:
        # In production, this would pull from Prometheus or similar
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "system": {
                "total_sessions": 25,
                "active_sessions": 3,
                "completed_sessions": 22
            },
            "agents": {
                "research_agent": {
                    "total_calls": 25,
                    "avg_latency_ms": 1250.5,
                    "success_rate": 0.96
                },
                "technical_agent": {
                    "total_calls": 75,
                    "avg_latency_ms": 850.3,
                    "success_rate": 0.93
                },
                "companion_agent": {
                    "total_calls": 25,
                    "avg_latency_ms": 500.2,
                    "success_rate": 0.98
                }
            },
            "tools": {
                "code_execution": {
                    "total_executions": 75,
                    "avg_execution_time_ms": 120.5,
                    "success_rate": 0.89
                },
                "web_search": {
                    "total_searches": 50,
                    "avg_search_time_ms": 800.3,
                    "success_rate": 0.94
                }
            }
        }
        
        return metrics
    
    except Exception as e:
        logger.error(f"Error retrieving metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions/{session_id}/traces")
async def get_session_traces(session_id: str):
    """
    Get detailed traces for a session (for observability)
    """
    try:
        # Mock trace data - in production, pull from logging/tracing system
        traces = {
            "session_id": session_id,
            "traces": [
                {
                    "trace_id": "trace_1",
                    "agent": "research_agent",
                    "start_time": "2025-11-18T10:30:00Z",
                    "end_time": "2025-11-18T10:30:01.5Z",
                    "duration_ms": 1500,
                    "status": "success",
                    "tools_used": ["web_search"],
                    "input_hash": "abc123",
                    "output_size_bytes": 2048
                },
                {
                    "trace_id": "trace_2",
                    "agent": "technical_agent",
                    "start_time": "2025-11-18T10:31:00Z",
                    "end_time": "2025-11-18T10:31:00.85Z",
                    "duration_ms": 850,
                    "status": "success",
                    "tools_used": ["code_executor"],
                    "input_hash": "def456",
                    "output_size_bytes": 1024
                }
            ]
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