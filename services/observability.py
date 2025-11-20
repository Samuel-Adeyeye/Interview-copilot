"""
Observability Service & Middleware for Request Tracing
services/observability.py
"""

import time
import uuid
from typing import Callable, Dict, Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger
from datetime import datetime
import json

# ============= Observability Service =============

class ObservabilityService:
    """Service for logging, tracing, and metrics collection"""
    
    def __init__(self):
        self.metrics_store = {
            "requests_total": 0,
            "requests_by_endpoint": {},
            "agent_calls": {},
            "tool_calls": {},
            "errors": []
        }
        
        # Configure loguru
        logger.add(
            "logs/api_{time}.log",
            rotation="500 MB",
            retention="10 days",
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
        )
    
    def log_request(self, request_id: str, method: str, path: str, 
                   duration_ms: float, status_code: int, user_id: str = None):
        """Log HTTP request"""
        log_data = {
            "request_id": request_id,
            "method": method,
            "path": path,
            "duration_ms": duration_ms,
            "status_code": status_code,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"REQUEST | {json.dumps(log_data)}")
        
        # Update metrics
        self.metrics_store["requests_total"] += 1
        
        if path not in self.metrics_store["requests_by_endpoint"]:
            self.metrics_store["requests_by_endpoint"][path] = {
                "count": 0,
                "total_duration_ms": 0,
                "errors": 0
            }
        
        endpoint_metrics = self.metrics_store["requests_by_endpoint"][path]
        endpoint_metrics["count"] += 1
        endpoint_metrics["total_duration_ms"] += duration_ms
        
        if status_code >= 400:
            endpoint_metrics["errors"] += 1
    
    def log_agent_call(self, agent_name: str, session_id: str, 
                      duration_ms: float, success: bool, 
                      tools_used: list = None, trace_id: str = None):
        """Log agent execution"""
        log_data = {
            "trace_id": trace_id or str(uuid.uuid4()),
            "agent_name": agent_name,
            "session_id": session_id,
            "duration_ms": duration_ms,
            "success": success,
            "tools_used": tools_used or [],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"AGENT | {json.dumps(log_data)}")
        
        # Update metrics
        if agent_name not in self.metrics_store["agent_calls"]:
            self.metrics_store["agent_calls"][agent_name] = {
                "total_calls": 0,
                "total_duration_ms": 0,
                "success_count": 0,
                "failure_count": 0
            }
        
        agent_metrics = self.metrics_store["agent_calls"][agent_name]
        agent_metrics["total_calls"] += 1
        agent_metrics["total_duration_ms"] += duration_ms
        
        if success:
            agent_metrics["success_count"] += 1
        else:
            agent_metrics["failure_count"] += 1
    
    def log_tool_call(self, tool_name: str, duration_ms: float, 
                     success: bool, error: str = None):
        """Log tool execution"""
        log_data = {
            "tool_name": tool_name,
            "duration_ms": duration_ms,
            "success": success,
            "error": error,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"TOOL | {json.dumps(log_data)}")
        
        # Update metrics
        if tool_name not in self.metrics_store["tool_calls"]:
            self.metrics_store["tool_calls"][tool_name] = {
                "total_calls": 0,
                "total_duration_ms": 0,
                "success_count": 0,
                "failure_count": 0
            }
        
        tool_metrics = self.metrics_store["tool_calls"][tool_name]
        tool_metrics["total_calls"] += 1
        tool_metrics["total_duration_ms"] += duration_ms
        
        if success:
            tool_metrics["success_count"] += 1
        else:
            tool_metrics["failure_count"] += 1
    
    def log_error(self, error_type: str, error_message: str, 
                 context: Dict[str, Any] = None):
        """Log error"""
        error_data = {
            "error_type": error_type,
            "error_message": error_message,
            "context": context or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.error(f"ERROR | {json.dumps(error_data)}")
        
        # Store in metrics (keep last 100 errors)
        self.metrics_store["errors"].append(error_data)
        if len(self.metrics_store["errors"]) > 100:
            self.metrics_store["errors"].pop(0)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics snapshot"""
        # Calculate averages
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "requests": {
                "total": self.metrics_store["requests_total"],
                "by_endpoint": {}
            },
            "agents": {},
            "tools": {},
            "errors": self.metrics_store["errors"][-10:]  # Last 10 errors
        }
        
        # Process endpoint metrics
        for endpoint, data in self.metrics_store["requests_by_endpoint"].items():
            if data["count"] > 0:
                metrics["requests"]["by_endpoint"][endpoint] = {
                    "count": data["count"],
                    "avg_duration_ms": data["total_duration_ms"] / data["count"],
                    "error_rate": data["errors"] / data["count"]
                }
        
        # Process agent metrics
        for agent_name, data in self.metrics_store["agent_calls"].items():
            if data["total_calls"] > 0:
                metrics["agents"][agent_name] = {
                    "total_calls": data["total_calls"],
                    "avg_duration_ms": data["total_duration_ms"] / data["total_calls"],
                    "success_rate": data["success_count"] / data["total_calls"]
                }
        
        # Process tool metrics
        for tool_name, data in self.metrics_store["tool_calls"].items():
            if data["total_calls"] > 0:
                metrics["tools"][tool_name] = {
                    "total_calls": data["total_calls"],
                    "avg_duration_ms": data["total_duration_ms"] / data["total_calls"],
                    "success_rate": data["success_count"] / data["total_calls"]
                }
        
        return metrics


# ============= Request Tracing Middleware =============

class RequestTracingMiddleware(BaseHTTPMiddleware):
    """Middleware for tracing and timing all requests"""
    
    def __init__(self, app, observability_service: ObservabilityService):
        super().__init__(app)
        self.observability = observability_service
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Add request ID to headers
        start_time = time.time()
        
        # Log request start
        logger.debug(f"Request {request_id} started: {request.method} {request.url.path}")
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Extract user_id if available (from headers or auth)
            user_id = request.headers.get("X-User-ID")
            
            # Log request completion
            self.observability.log_request(
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                duration_ms=duration_ms,
                status_code=response.status_code,
                user_id=user_id
            )
            
            # Add tracing headers to response
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
            
            return response
        
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            # Log error
            self.observability.log_error(
                error_type=type(e).__name__,
                error_message=str(e),
                context={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms
                }
            )
            
            # Re-raise to let FastAPI handle it
            raise


# ============= Rate Limiting Middleware (Optional) =============

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware"""
    
    def __init__(self, app, max_requests_per_minute: int = 60):
        super().__init__(app)
        self.max_requests = max_requests_per_minute
        self.request_counts = {}  # user_id -> [(timestamp, count)]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get user identifier (from header, auth, or IP)
        user_id = request.headers.get("X-User-ID") or request.client.host
        
        # Check rate limit
        current_time = time.time()
        
        if user_id not in self.request_counts:
            self.request_counts[user_id] = []
        
        # Remove old entries (older than 1 minute)
        self.request_counts[user_id] = [
            (ts, count) for ts, count in self.request_counts[user_id]
            if current_time - ts < 60
        ]
        
        # Count requests in last minute
        total_requests = sum(count for _, count in self.request_counts[user_id])
        
        if total_requests >= self.max_requests:
            return Response(
                content=json.dumps({
                    "error": "Rate limit exceeded",
                    "message": f"Maximum {self.max_requests} requests per minute"
                }),
                status_code=429,
                media_type="application/json"
            )
        
        # Add current request
        self.request_counts[user_id].append((current_time, 1))
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(self.max_requests - total_requests - 1)
        
        return response
    
    
    """
To use these in your FastAPI app (main.py):

from services.observability import ObservabilityService, RequestTracingMiddleware, RateLimitMiddleware

# Initialize observability service
observability_service = ObservabilityService()

# Add middleware
app.add_middleware(RequestTracingMiddleware, observability_service=observability_service)
app.add_middleware(RateLimitMiddleware, max_requests_per_minute=100)

# Use in endpoints
@app.post("/some-endpoint")
async def some_endpoint(request: Request):
    request_id = request.state.request_id
    logger.info(f"Processing request {request_id}")
    
    # Log agent calls
    observability_service.log_agent_call(
        agent_name="research_agent",
        session_id="session_123",
        duration_ms=1500.0,
        success=True,
        tools_used=["web_search"],
        trace_id=request_id
    )
    
    return {"status": "success"}
"""