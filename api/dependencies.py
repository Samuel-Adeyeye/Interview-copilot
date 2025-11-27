from fastapi import Request
import logging
from exceptions import ServiceUnavailableError

logger = logging.getLogger(__name__)

async def get_session_service(request: Request):
    """Dependency to get session service"""
    app_state = request.app.state
    if not hasattr(app_state, 'session_service') or app_state.session_service is None:
        logger.error("Session service is None")
        raise ServiceUnavailableError(
            service_name="session_service",
            message="Session service is not available"
        )
    return app_state.session_service

async def get_memory_bank(request: Request):
    """Dependency to get memory bank"""
    app_state = request.app.state
    if not hasattr(app_state, 'memory_bank') or app_state.memory_bank is None:
        logger.error("Memory bank is None")
        raise ServiceUnavailableError(
            service_name="memory_bank",
            message="Memory bank is not available"
        )
    return app_state.memory_bank

async def get_orchestrator(request: Request):
    """Dependency to get orchestrator"""
    app_state = request.app.state
    if not hasattr(app_state, 'orchestrator') or app_state.orchestrator is None:
        logger.error("Orchestrator is None")
        raise ServiceUnavailableError(
            service_name="orchestrator",
            message="Orchestrator is not available"
        )
    return app_state.orchestrator
