"""
Centralized error handler middleware for FastAPI
Converts custom exceptions to appropriate HTTP responses
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
import traceback

from exceptions import (
    InterviewCoPilotException,
    AgentExecutionError,
    CodeExecutionError,
    SessionNotFoundError,
    SessionError,
    APIError,
    ValidationError,
    MemoryError,
    ConfigurationError,
    ServiceUnavailableError
)

logger = logging.getLogger(__name__)


async def error_handler_middleware(request: Request, call_next):
    """
    Centralized error handler middleware.
    Catches all exceptions and converts them to appropriate HTTP responses.
    """
    try:
        response = await call_next(request)
        return response
    except InterviewCoPilotException as e:
        # Handle custom exceptions
        status_code = _get_status_code_for_exception(e)
        return JSONResponse(
            status_code=status_code,
            content=e.to_dict()
        )
    except StarletteHTTPException as e:
        # Handle FastAPI HTTP exceptions
        return JSONResponse(
            status_code=e.status_code,
            content={
                "error": e.detail,
                "error_code": "HTTP_ERROR"
            }
        )
    except RequestValidationError as e:
        # Handle Pydantic validation errors
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "Validation error",
                "error_code": "VALIDATION_ERROR",
                "details": e.errors()
            }
        )
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "An unexpected error occurred. Please try again later.",
                "error_code": "INTERNAL_SERVER_ERROR",
                "details": {
                    "message": str(e)
                }
            }
        )


def _get_status_code_for_exception(exception: InterviewCoPilotException) -> int:
    """
    Map custom exceptions to HTTP status codes.
    
    Args:
        exception: Custom exception instance
        
    Returns:
        HTTP status code
    """
    if isinstance(exception, SessionNotFoundError):
        return status.HTTP_404_NOT_FOUND
    elif isinstance(exception, ValidationError):
        return status.HTTP_400_BAD_REQUEST
    elif isinstance(exception, ServiceUnavailableError):
        return status.HTTP_503_SERVICE_UNAVAILABLE
    elif isinstance(exception, ConfigurationError):
        return status.HTTP_500_INTERNAL_SERVER_ERROR
    elif isinstance(exception, (AgentExecutionError, CodeExecutionError, APIError, MemoryError)):
        # These could be client errors (400) or server errors (500)
        # Check if it's a client error based on details
        if exception.details.get("status_code"):
            client_error_codes = [400, 401, 403, 404, 429]
            if exception.details["status_code"] in client_error_codes:
                return status.HTTP_400_BAD_REQUEST
        return status.HTTP_500_INTERNAL_SERVER_ERROR
    elif isinstance(exception, SessionError):
        # Could be 400 (bad request) or 404 (not found)
        if "not found" in exception.message.lower():
            return status.HTTP_404_NOT_FOUND
        return status.HTTP_400_BAD_REQUEST
    else:
        # Default to 500 for unknown custom exceptions
        return status.HTTP_500_INTERNAL_SERVER_ERROR


def create_error_response(
    error: Exception,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    include_traceback: bool = False
) -> JSONResponse:
    """
    Create a standardized error response.
    
    Args:
        error: Exception instance
        status_code: HTTP status code
        include_traceback: Whether to include traceback in response (for debugging)
        
    Returns:
        JSONResponse with error details
    """
    content = {
        "error": str(error),
        "error_code": error.__class__.__name__
    }
    
    if include_traceback:
        content["traceback"] = traceback.format_exc()
    
    if isinstance(error, InterviewCoPilotException):
        content.update(error.to_dict())
    
    return JSONResponse(
        status_code=status_code,
        content=content
    )

