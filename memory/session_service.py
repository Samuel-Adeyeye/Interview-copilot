from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum
import json

class SessionState(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"

class InMemorySessionService:
    def __init__(self):
        self.sessions: Dict[str, Dict] = {}
    
    def create_session(self, session_id: str, user_id: str, metadata: Dict = None) -> Dict:
        """Create a new session"""
        session = {
            "session_id": session_id,
            "user_id": user_id,
            "state": SessionState.CREATED,
            "agent_states": {},
            "artifacts": [],
            "checkpoints": [],
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        self.sessions[session_id] = session
        return session
    
    def update_agent_state(self, session_id: str, agent_name: str, state: Dict):
        """Update state for a specific agent"""
        if session_id in self.sessions:
            self.sessions[session_id]["agent_states"][agent_name] = state
            self.sessions[session_id]["updated_at"] = datetime.utcnow().isoformat()
    
    def add_artifact(self, session_id: str, artifact_type: str, payload: Any):
        """Add an artifact to the session"""
        if session_id in self.sessions:
            artifact = {
                "type": artifact_type,
                "payload": payload,
                "timestamp": datetime.utcnow().isoformat()
            }
            self.sessions[session_id]["artifacts"].append(artifact)
    
    def create_checkpoint(self, session_id: str) -> str:
        """Create a checkpoint for pause/resume"""
        if session_id in self.sessions:
            checkpoint = {
                "checkpoint_id": f"{session_id}_{len(self.sessions[session_id]['checkpoints'])}",
                "state_snapshot": json.dumps(self.sessions[session_id]),
                "timestamp": datetime.utcnow().isoformat()
            }
            self.sessions[session_id]["checkpoints"].append(checkpoint)
            return checkpoint["checkpoint_id"]
        return None
    
    def pause_session(self, session_id: str):
        """Pause a session"""
        if session_id in self.sessions:
            self.sessions[session_id]["state"] = SessionState.PAUSED
            self.create_checkpoint(session_id)
    
    def resume_session(self, session_id: str):
        """Resume a paused session"""
        if session_id in self.sessions:
            self.sessions[session_id]["state"] = SessionState.RUNNING
    
    def complete_session(self, session_id: str):
        """Mark session as completed"""
        if session_id in self.sessions:
            self.sessions[session_id]["state"] = SessionState.COMPLETED
            self.sessions[session_id]["completed_at"] = datetime.utcnow().isoformat()
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Retrieve session"""
        return self.sessions.get(session_id)