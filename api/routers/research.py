from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict, Any, List
import uuid
import logging
from pydantic import BaseModel
from api.main import (
    get_session_service,
    get_memory_bank,
    get_orchestrator,
    JobDescriptionRequest,
    ResearchRequest,
    ResearchResponse,
    SessionNotFoundError,
    SessionError,
    AgentExecutionError
)

router = APIRouter(tags=["research"])
logger = logging.getLogger(__name__)

@router.post("/job-descriptions/upload")
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


@router.post("/research/run", response_model=ResearchResponse)
async def run_research(
    request: ResearchRequest,
    background_tasks: BackgroundTasks,
    session_service = Depends(get_session_service),
    orchestrator = Depends(get_orchestrator)
):
    """
    Run research agent to build company prep packet
    """
    session = session_service.get_session(request.session_id)
    if not session:
        raise SessionNotFoundError(session_id=request.session_id)
    
    logger.info(f"Starting research for session {request.session_id}")
    
    # Get user_id from session
    user_id = session.get("user_id")
    if not user_id:
        raise SessionError(
            message="Session missing user_id",
            session_id=request.session_id
        )
    
    # Execute research agent through orchestrator
    try:
        research_result = await orchestrator.execute_research(
            session_id=request.session_id,
            user_id=user_id,
            job_description=request.job_description,
            company_name=request.company_name
        )
    except Exception as e:
        logger.error(f"Error executing research: {e}", exc_info=True)
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Full traceback: {error_details}")
        raise AgentExecutionError(
            agent_name="research",
            message=f"Research execution failed: {str(e)}",
            details={"session_id": request.session_id, "error_type": type(e).__name__}
        )
    
    # Ensure research_result is not None
    if research_result is None:
        logger.error(f"Research result is None for session {request.session_id}")
        raise AgentExecutionError(
            agent_name="research",
            message="Research agent returned no result",
            details={"session_id": request.session_id}
        )
    
    if not research_result.get("success"):
        error_msg = research_result.get("error", "Research agent failed")
        logger.error(f"Research agent returned error: {error_msg}")
        raise AgentExecutionError(
            agent_name="research",
            message=error_msg,
            details={"session_id": request.session_id}
        )
    
    # Extract research packet from result
    research_output = research_result.get("output", {})
    if not research_output:
        raise AgentExecutionError(
            agent_name="research",
            message="Research agent returned empty output",
            details={"session_id": request.session_id}
        )
    
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
