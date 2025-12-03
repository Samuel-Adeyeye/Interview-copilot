from typing import Dict, Any, Optional, List
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
    
    async def create_session(self, session_id: str, user_id: str, app_name: str = None, metadata: Dict = None) -> Dict:
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
    
    async def get_session(self, session_id: str, app_name: str = None, user_id: str = None) -> Optional[Dict]:
        """Retrieve session"""
        return self.sessions.get(session_id)
    
    def get_all_user_sessions(self, user_id: str) -> List[Dict]:
        """
        Get all sessions for a specific user
        
        Args:
            user_id: User identifier
        
        Returns:
            List of session dictionaries
        """
        user_sessions = [
            session for session in self.sessions.values()
            if session.get("user_id") == user_id
        ]
        # Sort by created_at (most recent first)
        user_sessions.sort(
            key=lambda x: x.get("created_at", ""),
            reverse=True
        )
        return user_sessions
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session
        
        Args:
            session_id: Session identifier
        
        Returns:
            True if session was deleted, False if not found
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    def update_session_metadata(self, session_id: str, metadata: Dict):
        """
        Update session metadata
        
        Args:
            session_id: Session identifier
            metadata: Dictionary of metadata to update (will be merged with existing)
        """
        if session_id in self.sessions:
            existing_metadata = self.sessions[session_id].get("metadata", {})
            existing_metadata.update(metadata)
            self.sessions[session_id]["metadata"] = existing_metadata
            self.sessions[session_id]["updated_at"] = datetime.utcnow().isoformat()
    
    def get_session_count(self) -> int:
        """Get total number of sessions"""
        return len(self.sessions)
    
    def get_active_sessions(self) -> List[Dict]:
        """Get all active (running) sessions"""
        return [
            session for session in self.sessions.values()
            if session.get("state") == SessionState.RUNNING
        ]
    
    def cleanup_expired_sessions(self, max_age_hours: int = 24):
        """
        Remove sessions older than max_age_hours
        
        Args:
            max_age_hours: Maximum age in hours before session is considered expired
        """
        from datetime import datetime, timedelta
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        expired_sessions = []
        for session_id, session in list(self.sessions.items()):
            created_at_str = session.get("created_at", "")
            try:
                created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                if created_at < cutoff_time:
                    expired_sessions.append(session_id)
            except:
                pass
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
        
        return len(expired_sessions)