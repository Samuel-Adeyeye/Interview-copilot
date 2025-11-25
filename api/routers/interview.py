from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
import logging
from pydantic import BaseModel
from api.main import (
    get_session_service,
    get_orchestrator,
    MockInterviewStartRequest,
    CodeSubmissionRequest,
    EvaluationResponse,
    SessionNotFoundError,
    SessionError,
    AgentExecutionError
)

router = APIRouter(tags=["interview"])
logger = logging.getLogger(__name__)

@router.post("/interview/start")
async def start_mock_interview(
    request: MockInterviewStartRequest,
    session_service = Depends(get_session_service),
    orchestrator = Depends(get_orchestrator)
):
    """
    Start a mock technical interview session
    """
    session = session_service.get_session(request.session_id)
    if not session:
        raise SessionNotFoundError(session_id=request.session_id)
    
    logger.info(f"Starting mock interview for session {request.session_id}")
    
    # Get user_id from session
    user_id = session.get("user_id")
    if not user_id:
        raise SessionError(
            message="Session missing user_id",
            session_id=request.session_id
        )
    
    # Execute technical agent to select questions
    try:
        # Get job description from session metadata if available
        # In a real app, this would be retrieved from session state or memory
        job_description = session.get("metadata", {}).get("job_description", "Software Engineer")
        
        technical_result = await orchestrator.execute_technical(
            session_id=request.session_id,
            user_id=user_id,
            mode="select_questions",
            difficulty=request.difficulty,
            num_questions=request.num_questions,
            job_description=job_description
        )
    except Exception as e:
        logger.error(f"Error starting interview: {e}")
        raise AgentExecutionError(
            agent_name="technical",
            message=f"Failed to start interview: {str(e)}",
            details={"session_id": request.session_id}
        )
    
    if not technical_result.get("success"):
        raise AgentExecutionError(
            agent_name="technical",
            message=technical_result.get("error", "Technical agent failed"),
            details={"session_id": request.session_id}
        )
    
    # Parse questions from result
    # This assumes the agent returns a list of questions in the output
    # For now, we'll mock the response structure if the agent returns raw text
    output = technical_result.get("output", {})
    questions = output.get("result", [])
    
    # If result is a string (raw LLM output), we might need to parse it
    # For this implementation, we'll assume the agent (or tool) returns structured data
    # If not, we'd need a parser here
    
    # Update session
    session_service.update_agent_state(
        request.session_id,
        "technical",
        {
            "status": "in_progress",
            "current_phase": "interview",
            "questions": questions
        }
    )
    
    return {
        "session_id": request.session_id,
        "status": "started",
        "questions": questions,
        "message": f"Interview started with {len(questions)} questions"
    }


@router.post("/technical/submit-code", response_model=EvaluationResponse)
async def submit_code(
    request: CodeSubmissionRequest,
    session_service = Depends(get_session_service),
    orchestrator = Depends(get_orchestrator)
):
    """
    Submit code for evaluation
    """
    session = session_service.get_session(request.session_id)
    if not session:
        raise SessionNotFoundError(session_id=request.session_id)
    
    logger.info(f"Evaluating code for session {request.session_id}, question {request.question_id}")
    
    user_id = session.get("user_id")
    
    # Execute technical agent to evaluate code
    try:
        evaluation_result = await orchestrator.execute_technical(
            session_id=request.session_id,
            user_id=user_id,
            mode="evaluate_code",
            question_id=request.question_id,
            code=request.code,
            language=request.language
        )
    except Exception as e:
        logger.error(f"Error evaluating code: {e}")
        raise AgentExecutionError(
            agent_name="technical",
            message=f"Code evaluation failed: {str(e)}",
            details={"session_id": request.session_id}
        )
    
    if not evaluation_result.get("success"):
        raise AgentExecutionError(
            agent_name="technical",
            message=evaluation_result.get("error", "Evaluation failed"),
            details={"session_id": request.session_id}
        )
    
    # Process result
    output = evaluation_result.get("output", {})
    result_data = output.get("result", {})
    
    # If result is string, create structured response
    if isinstance(result_data, str):
        feedback = result_data
        tests_passed = 0  # Unknown
        total_tests = 0   # Unknown
        status = "completed"
    else:
        feedback = result_data.get("feedback", "No feedback provided")
        tests_passed = result_data.get("tests_passed", 0)
        total_tests = result_data.get("total_tests", 0)
        status = result_data.get("status", "completed")
    
    response = {
        "session_id": request.session_id,
        "question_id": request.question_id,
        "status": status,
        "tests_passed": tests_passed,
        "total_tests": total_tests,
        "feedback": feedback,
        "execution_time_ms": evaluation_result.get("execution_time_ms", 0.0)
    }
    
    # Update session
    # We might want to store this submission in the session history
    
    return EvaluationResponse(**response)
