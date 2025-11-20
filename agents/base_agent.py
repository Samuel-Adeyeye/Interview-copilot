from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid

class AgentContext(BaseModel):
    session_id: str
    user_id: str
    inputs: Dict[str, Any]
    metadata: Dict[str, Any] = {}
    timestamp: datetime = datetime.utcnow()

class AgentResult(BaseModel):
    agent_name: str
    success: bool
    output: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}
    execution_time_ms: float
    trace_id: str

class BaseAgent(ABC):
    def __init__(self, name: str, llm, tools: list = None):
        self.name = name
        self.llm = llm
        self.tools = tools or []
        
    @abstractmethod
    async def run(self, context: AgentContext) -> AgentResult:
        """Execute the agent's main logic"""
        pass
    
    def _create_result(self, success: bool, output: Any, 
                       error: Optional[str] = None, 
                       execution_time: float = 0.0) -> AgentResult:
        return AgentResult(
            agent_name=self.name,
            success=success,
            output=output,
            error=error,
            execution_time_ms=execution_time,
            trace_id=str(uuid.uuid4()),
            metadata={"tools_used": [tool.name for tool in self.tools]}
        )