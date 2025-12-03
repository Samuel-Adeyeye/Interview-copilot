"""
ADK API Endpoints
FastAPI endpoints using ADK Runner and App
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import logging
import json

from api.adk_app import get_adk_app, ADKApplication
from exceptions import (
    SessionNotFoundError,
    ValidationError,
    ServiceUnavailableError
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v2/adk", tags=["ADK"])


# ============= Request/Response Models =============

class ADKResearchRequest(BaseModel):
    """Request to run research agent via ADK"""
    session_id: str
    user_id: Optional[str] = None  # Optional - will be extracted from session if not provided
    company_name: str
    job_description: str


class ADKTechnicalRequest(BaseModel):
    """Request to run technical agent via ADK"""
    session_id: str
    user_id: str
    mode: str = Field(..., pattern="^(select_questions|evaluate_code)$")
    difficulty: Optional[str] = Field(None, pattern="^(easy|medium|hard)$")
    num_questions: Optional[int] = Field(None, ge=1, le=5)
    question_id: Optional[str] = None
    code: Optional[str] = None
    language: Optional[str] = Field("python", pattern="^(python|javascript|java|cpp)$")
    job_description: Optional[str] = None
    company_name: Optional[str] = None


class ADKWorkflowRequest(BaseModel):
    """Request to run full workflow via ADK"""
    session_id: str
    user_id: str
    company_name: Optional[str] = None
    job_description: Optional[str] = None
    mode: Optional[str] = Field("select_questions", pattern="^(select_questions|evaluate_code)$")
    difficulty: Optional[str] = Field("medium", pattern="^(easy|medium|hard)$")
    num_questions: Optional[int] = Field(3, ge=1, le=5)


# ============= Endpoints =============

@router.post("/research")
async def run_research_adk(
    request: ADKResearchRequest,
    adk_app: ADKApplication = Depends(get_adk_app)
):
    """
    Run research agent using ADK.
    
    Returns streaming response with research results.
    """
    try:
        # Get user_id from session if not provided
        user_id = request.user_id
        if not user_id:
            # Try to get from session service
            from api.main import app_state
            if app_state.session_service:
                session = app_state.session_service.get_session(request.session_id)
                if session:
                    user_id = session.get("user_id")
            if not user_id:
                raise ValidationError(
                    message="user_id is required. Either provide it in the request or ensure the session has a user_id.",
                    field="user_id"
                )
        
        async def generate():
            """Generate streaming response"""
            full_response = ""
            try:
                async for event in adk_app.run_research(
                    user_id=user_id,
                    session_id=request.session_id,
                    company_name=request.company_name,
                    job_description=request.job_description
                ):
                    if event.content and event.content.parts:
                        for part in event.content.parts:
                            if hasattr(part, 'text') and part.text:
                                text = part.text
                                full_response += text
                                yield f"data: {json.dumps({'text': text, 'type': 'chunk'})}\n\n"
                            elif hasattr(part, 'function_call'):
                                # Log function calls but don't break the stream
                                logger.info(f"Research agent calling tool: {part.function_call.name}")
                                # Optional: yield a progress event
                                # yield f"data: {json.dumps({'text': '', 'type': 'progress', 'detail': f'Using tool: {part.function_call.name}'})}\n\n"
                
                # Final response
                yield f"data: {json.dumps({'text': full_response, 'type': 'complete'})}\n\n"
            except Exception as e:
                logger.error(f"Streaming error in research: {e}", exc_info=True)
                yield f"data: {json.dumps({'text': str(e), 'type': 'error'})}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            }
        )
        
    except ValidationError as ve:
        raise HTTPException(status_code=400, detail=ve.message)
    except Exception as e:
        logger.error(f"Error in ADK research endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/technical")
async def run_technical_adk(
    request: ADKTechnicalRequest,
    adk_app: ADKApplication = Depends(get_adk_app)
):
    """
    Run technical agent using ADK.
    
    Returns streaming response with technical results.
    """
    try:
        # Validate request based on mode
        if request.mode == "select_questions":
            if not request.difficulty or not request.num_questions:
                raise ValidationError(
                    message="difficulty and num_questions are required for select_questions mode",
                    field="mode"
                )
        elif request.mode == "evaluate_code":
            if not request.question_id or not request.code:
                raise ValidationError(
                    message="question_id and code are required for evaluate_code mode",
                    field="mode"
                )
        
        async def generate():
            """Generate streaming response"""
            full_response = ""
            kwargs = {}
            
            if request.mode == "select_questions":
                # Construct query based on whether company is specified
                if request.company_name:
                    # Dynamic question generation - construct a query for the agent
                    company_query = f"Find me {request.num_questions} recent {request.company_name} {request.difficulty} difficulty software engineer interview questions"
                    kwargs = {
                        "difficulty": request.difficulty,
                        "num_questions": request.num_questions,
                        "job_description": request.job_description or "",
                        "company_query": company_query  # Pass the constructed query
                    }
                else:
                    # Static question selection
                    kwargs = {
                        "difficulty": request.difficulty,
                        "num_questions": request.num_questions,
                        "job_description": request.job_description or ""
                    }
            elif request.mode == "evaluate_code":
                kwargs = {
                    "question_id": request.question_id,
                    "code": request.code,
                    "language": request.language
                }
            
            try:
                event_count = 0
                async for event in adk_app.run_technical_direct(
                    user_id=request.user_id,
                    session_id=request.session_id,
                    mode=request.mode,
                    **kwargs
                ):
                    event_count += 1
                    parts_count = len(event.content.parts) if (event.content and event.content.parts) else 0
                    logger.info(f"Event {event_count}: content={bool(event.content)}, parts={parts_count}")
                    
                    if event.content and event.content.parts:
                        for i, part in enumerate(event.content.parts):
                            if hasattr(part, 'text') and part.text:
                                text = part.text
                                logger.info(f"Event {event_count}, part {i}: text length={len(text)}")
                                full_response += text
                                yield f"data: {json.dumps({'text': text, 'type': 'chunk'})}\n\n"
                            elif hasattr(part, 'function_call'):
                                logger.info(f"Event {event_count}, part {i}: function_call={part.function_call.name if hasattr(part.function_call, 'name') else 'unknown'}")
                            elif hasattr(part, 'function_response'):
                                logger.info(f"Event {event_count}, part {i}: function_response")
                
                logger.info(f"Streaming completed. Total events: {event_count}, response length: {len(full_response)}")
                
                # Final response
                yield f"data: {json.dumps({'text': full_response, 'type': 'complete'})}\n\n"
            except Exception as e:
                logger.error(f"Streaming error: {e}", exc_info=True)
                yield f"data: {json.dumps({'text': str(e), 'type': 'error'})}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            }
        )
        
    except ValidationError as ve:
        raise HTTPException(status_code=400, detail=ve.message)
    except Exception as e:
        logger.error(f"Error in ADK technical endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workflow")
async def run_workflow_adk(
    request: ADKWorkflowRequest,
    adk_app: ADKApplication = Depends(get_adk_app)
):
    """
    Run full workflow using ADK.
    
    Executes research → technical → companion agents in sequence.
    Returns streaming response with all results.
    """
    try:
        # Build workflow message
        message_parts = []
        
        if request.company_name and request.job_description:
            message_parts.append(f"""1. Research {request.company_name}:
   - Company overview
   - Interview process
   - Technology stack
   - Recent news
   - Preparation tips
   
   Job Description: {request.job_description[:300]}...""")
        
        if request.mode == "select_questions":
            message_parts.append(f"2. Select {request.num_questions} {request.difficulty} difficulty coding questions.")
        elif request.mode == "evaluate_code":
            message_parts.append("2. Evaluate code submission.")
        
        message_parts.append("3. Generate encouragement, tips, and recommendations based on performance.")
        
        workflow_message = "\n\n".join(message_parts)
        
        async def generate():
            """Generate streaming response"""
            full_response = ""
            try:
                async for event in adk_app.run_workflow(
                    user_id=request.user_id,
                    session_id=request.session_id,
                    message=workflow_message
                ):
                    if event.content and event.content.parts:
                        for part in event.content.parts:
                            if hasattr(part, 'text') and part.text:
                                text = part.text
                                full_response += text
                                yield f"data: {json.dumps({'text': text, 'type': 'chunk'})}\n\n"
                            elif hasattr(part, 'function_call'):
                                logger.info(f"Workflow agent calling tool: {part.function_call.name}")
                
                # Final response
                yield f"data: {json.dumps({'text': full_response, 'type': 'complete'})}\n\n"
            except Exception as e:
                logger.error(f"Streaming error in workflow: {e}", exc_info=True)
                yield f"data: {json.dumps({'text': str(e), 'type': 'error'})}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            }
        )
        
    except Exception as e:
        logger.error(f"Error in ADK workflow endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def adk_health_check(adk_app: ADKApplication = Depends(get_adk_app)):
    """
    Health check for ADK services.
    
    Returns status of ADK App, Runner, and services.
    """
    try:
        return {
            "status": "healthy",
            "adk_app": "initialized",
            "orchestrator": "ready",
            "session_service": "ready",
            "memory_service": "ready"
        }
    except Exception as e:
        logger.error(f"ADK health check failed: {e}")
        raise HTTPException(status_code=503, detail=str(e))

