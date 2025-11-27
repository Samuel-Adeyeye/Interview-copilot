"""
Custom exception classes for Interview Co-Pilot
Provides structured error handling with user-friendly messages
"""

from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class InterviewCoPilotException(Exception):
    """
    Base exception class for all Interview Co-Pilot errors.
    All custom exceptions should inherit from this.
    """
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        """
        Initialize exception
        
        Args:
            message: User-friendly error message
            error_code: Optional error code for programmatic handling
            details: Optional dictionary with additional error details
            original_error: Optional original exception that caused this error
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.original_error = original_error
        
        # Log the error
        if original_error:
            logger.error(f"{self.__class__.__name__}: {message}", exc_info=original_error)
        else:
            logger.error(f"{self.__class__.__name__}: {message}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses"""
        result = {
            "error": self.message,
            "error_code": self.error_code
        }
        if self.details:
            result["details"] = self.details
        return result


class AgentExecutionError(InterviewCoPilotException):
    """
    Raised when an agent fails to execute properly.
    """
    
    def __init__(
        self,
        agent_name: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(
            message=f"Agent '{agent_name}' execution failed: {message}",
            error_code=f"AGENT_ERROR_{agent_name.upper()}",
            details=details,
            original_error=original_error
        )
        self.agent_name = agent_name


class CodeExecutionError(InterviewCoPilotException):
    """
    Raised when code execution fails (e.g., Judge0 API errors, syntax errors).
    """
    
    def __init__(
        self,
        message: str,
        language: Optional[str] = None,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        error_details = details or {}
        if language:
            error_details["language"] = language
        if code:
            error_details["code_length"] = len(code) if code else 0
        
        super().__init__(
            message=f"Code execution failed: {message}",
            error_code="CODE_EXECUTION_ERROR",
            details=error_details,
            original_error=original_error
        )
        self.language = language
        self.code = code


class SessionNotFoundError(InterviewCoPilotException):
    """
    Raised when a requested session is not found.
    """
    
    def __init__(
        self,
        session_id: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=f"Session '{session_id}' not found",
            error_code="SESSION_NOT_FOUND",
            details=details or {}
        )
        self.session_id = session_id


class SessionError(InterviewCoPilotException):
    """
    Raised for general session-related errors (not found, invalid state, etc.).
    """
    
    def __init__(
        self,
        message: str,
        session_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        error_details = details or {}
        if session_id:
            error_details["session_id"] = session_id
        
        super().__init__(
            message=f"Session error: {message}",
            error_code="SESSION_ERROR",
            details=error_details,
            original_error=original_error
        )
        self.session_id = session_id


class APIError(InterviewCoPilotException):
    """
    Raised when external API calls fail (OpenAI, Tavily, Judge0, etc.).
    """
    
    def __init__(
        self,
        service_name: str,
        message: str,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        error_details = details or {}
        if status_code:
            error_details["status_code"] = status_code
        
        super().__init__(
            message=f"{service_name} API error: {message}",
            error_code=f"API_ERROR_{service_name.upper()}",
            details=error_details,
            original_error=original_error
        )
        self.service_name = service_name
        self.status_code = status_code


class ValidationError(InterviewCoPilotException):
    """
    Raised when input validation fails.
    """
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        if field:
            error_details["field"] = field
        if value is not None:
            error_details["value"] = str(value)
        
        super().__init__(
            message=f"Validation error: {message}",
            error_code="VALIDATION_ERROR",
            details=error_details
        )
        self.field = field
        self.value = value


class MemoryError(InterviewCoPilotException):
    """
    Raised when memory bank operations fail.
    """
    
    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        error_details = details or {}
        if operation:
            error_details["operation"] = operation
        
        super().__init__(
            message=f"Memory operation failed: {message}",
            error_code="MEMORY_ERROR",
            details=error_details,
            original_error=original_error
        )
        self.operation = operation


class ConfigurationError(InterviewCoPilotException):
    """
    Raised when configuration is invalid or missing.
    """
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        if config_key:
            error_details["config_key"] = config_key
        
        super().__init__(
            message=f"Configuration error: {message}",
            error_code="CONFIGURATION_ERROR",
            details=error_details
        )
        self.config_key = config_key


class ServiceUnavailableError(InterviewCoPilotException):
    """
    Raised when a required service is not available or not initialized.
    """
    
    def __init__(
        self,
        service_name: str,
        message: Optional[str] = None
    ):
        super().__init__(
            message=message or f"Service '{service_name}' is not available",
            error_code="SERVICE_UNAVAILABLE",
            details={"service_name": service_name}
        )
        self.service_name = service_name

