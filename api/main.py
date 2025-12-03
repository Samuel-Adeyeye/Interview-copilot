"""
FastAPI Backend for Interview Co-Pilot
Main API endpoints for orchestrating multi-agent system
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import logging
import asyncio
from contextlib import asynccontextmanager

# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import settings
from config.settings import settings

# Import ADK agents
try:
    from agents.adk.research_agent import create_research_agent
    from agents.adk.technical_agent import create_technical_agent
    from agents.adk.companion_agent import create_companion_agent
    from agents.adk.orchestrator import ADKOrchestrator
except ImportError as e:
    logger.error(f"Failed to import ADK agents: {e}")
    raise

from memory.memory_bank import MemoryBank
from memory.adk.session_service import create_adk_session_service, ADKSessionService
# Legacy tools removed - have LangChain dependencies
# from tools.search_tool import create_search_tool
# from tools.code_exec_tool import create_code_exec_tool
from tools.question_bank import QuestionBank
from services.observability import ObservabilityService, RequestTracingMiddleware, RateLimitMiddleware
from middleware.error_handler import error_handler_middleware
from exceptions import ServiceUnavailableError

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


# ============= Lifespan Management =============


# ============= Lifespan Management =============

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("🚀 Starting Interview Co-Pilot API...")
    
    try:
        # Initialize core services
        logger.info("Initializing core services...")
        
        # Initialize session service - always use ADK-compatible service
        if settings.SESSION_PERSISTENCE_ENABLED and settings.SESSION_STORAGE_TYPE == "database":
            # Use ADK DatabaseSessionService for PostgreSQL
            db_url = settings.DATABASE_URL
            if not db_url:
                raise ValueError("DATABASE_URL is required when SESSION_STORAGE_TYPE=database")
            
            logger.info(f"Using ADK DatabaseSessionService with PostgreSQL: {db_url.split('@')[1] if '@' in db_url else 'configured'}")
            app_state.session_service = create_adk_session_service(
                use_database=True,
                db_url=db_url,
                app_name="interview_copilot"
            )
            logger.info("✅ ADK DatabaseSessionService initialized (PostgreSQL)")
        else:
            # Use ADK InMemorySessionService for all other cases
            logger.info("Initializing ADK in-memory session service...")
            app_state.session_service = create_adk_session_service(
                use_database=False,
                db_url=None,
                app_name="interview_copilot"
            )
            logger.info("✅ ADK InMemorySessionService initialized")
        
        app_state.memory_bank = MemoryBank(persist_directory=settings.VECTOR_DB_PATH)
        app_state.observability = ObservabilityService()
        logger.info("✅ Core services initialized")
        
        # Initialize ADK agents
        logger.info("Initializing ADK agents...")
        try:
            research_agent = create_research_agent()
            logger.info("✅ ADK Research agent initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize ADK research agent: {e}")
            raise
        
        try:
            technical_agent = create_technical_agent(
                use_builtin_code_executor=True,  # Use built-in executor (no Judge0 needed)
                judge0_api_key=settings.JUDGE0_API_KEY  # Optional, for multi-language support
            )
            logger.info("✅ ADK Technical agent initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize ADK technical agent: {e}")
            raise
        
        try:
            companion_agent = create_companion_agent(memory_bank=app_state.memory_bank)
            logger.info("✅ ADK Companion agent initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize ADK companion agent: {e}")
            raise
        
        # Initialize ADK orchestrator
        logger.info("Initializing ADK orchestrator...")
        try:
            app_state.orchestrator = ADKOrchestrator(
                research_agent=research_agent,
                technical_agent=technical_agent,
                companion_agent=companion_agent,
                session_service=app_state.session_service,
                memory_bank=app_state.memory_bank,
                use_sequential=True,
                use_builtin_code_executor=True,
                judge0_api_key=settings.JUDGE0_API_KEY
            )
            logger.info("✅ ADK Orchestrator initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize ADK orchestrator: {e}")
            raise
        
        # Store agent type for reference
        app_state.agent_type = "adk"
        
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
        
        # Store services in app state for dependencies
        app.state.session_service = app_state.session_service
        app.state.memory_bank = app_state.memory_bank
        app.state.orchestrator = app_state.orchestrator
        app.state.observability = app_state.observability
        logger.info("✅ Services stored in app state")
        
        # Start background cleanup task for session expiration
        if isinstance(app_state.session_service, ADKSessionService):
            async def periodic_cleanup():
                """Periodic cleanup of expired sessions"""
                while True:
                    try:
                        await asyncio.sleep(3600)  # Run every hour
                        if app_state.session_service:
                            # ADK session service cleanup is async
                            if isinstance(app_state.session_service, ADKSessionService):
                                await app_state.session_service.cleanup_expired_sessions()
                            else:
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
        
        # ADK session service handles persistence automatically
        if isinstance(app_state.session_service, ADKSessionService):
            logger.info("ADK session service uses automatic persistence")
        
        # Close any async resources
        if hasattr(app_state.memory_bank, 'client'):
            # ChromaDB client cleanup if needed
            pass
        
        # Close observability service if needed
        if app_state.observability:
            logger.info("Closing observability service...")
        
        logger.info("✅ Shutdown complete")
    except Exception as e:
        logger.error(f"❌ Failed to initialize services: {e}")
        app_state.initialized = False
        raise


from api.routers import sessions, research, interview, users

# ============= App Initialization =============

app = FastAPI(
    title="Interview Co-Pilot API",
    description="Backend API for the Multi-Agent Interview Co-Pilot",
    version="2.0.0",
    lifespan=lifespan
)

# Include routers
app.include_router(sessions.router)
app.include_router(research.router)
app.include_router(interview.router)
app.include_router(users.router)

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

# Include ADK router if available
try:
    from api.adk_endpoints import router as adk_router
    app.include_router(adk_router)
    logger.info("✅ ADK endpoints included")
except ImportError as e:
    logger.warning(f"⚠️  ADK endpoints not available: {e}")

# Error handler middleware (should be last to catch all errors)
@app.middleware("http")
async def error_handler(request: Request, call_next):
    """Centralized error handler middleware"""
    return await error_handler_middleware(request, call_next)


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