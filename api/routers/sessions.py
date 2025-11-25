from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
import uuid
import logging
from pydantic import BaseModel
from api.main import (
    get_session_service,
    SessionCreateRequest,
    SessionResponse,
    SessionNotFoundError
)

router = APIRouter(prefix="/sessions", tags=["sessions"])
logger = logging.getLogger(__name__)

@router.post("/create", response_model=SessionResponse)
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


@router.get("/{session_id}", response_model=SessionResponse)
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
            raise SessionNotFoundError(session_id=session_id)
        
        return SessionResponse(**session)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{session_id}/pause")
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


@router.post("/{session_id}/resume")
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
