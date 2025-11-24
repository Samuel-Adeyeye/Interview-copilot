"""
ADK Session Service Wrapper
Provides compatibility layer between custom session service and ADK session service
"""

from google.adk.sessions import InMemorySessionService, DatabaseSessionService
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class SessionState(str, Enum):
    """Session state enumeration"""
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class ADKSessionService:
    """
    ADK Session Service wrapper that provides compatibility with custom session service API.
    
    This wraps ADK's InMemorySessionService or DatabaseSessionService and provides
    the same interface as the custom session service for backward compatibility.
    """
    
    def __init__(
        self,
        use_database: bool = False,
        db_url: Optional[str] = None,
        app_name: str = "interview_copilot"
    ):
        """
        Initialize ADK Session Service.
        
        Args:
            use_database: If True, use DatabaseSessionService. If False, use InMemorySessionService.
            db_url: Database URL (required if use_database=True)
            app_name: Application name for session management
        """
        self.app_name = app_name
        
        if use_database:
            if not db_url:
                raise ValueError("db_url is required when use_database=True")
            self.service = DatabaseSessionService(db_url=db_url)
            logger.info(f"✅ Using ADK DatabaseSessionService: {db_url}")
        else:
            self.service = InMemorySessionService()
            logger.info("✅ Using ADK InMemorySessionService")
    
    async def create_session(
        self,
        session_id: str,
        user_id: str,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Create a new session.
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            metadata: Optional metadata dictionary
        
        Returns:
            Session dictionary
        """
        try:
            # Create session using ADK service
            session = await self.service.create_session(
                app_name=self.app_name,
                user_id=user_id,
                session_id=session_id
            )
            
            # Add custom metadata
            if metadata:
                # Store metadata in session state
                if not hasattr(session, 'state'):
                    session.state = {}
                session.state['metadata'] = metadata
                session.state['custom_state'] = SessionState.CREATED
                session.state['agent_states'] = {}
                session.state['artifacts'] = []
            
            # Convert to dict format for compatibility
            return self._session_to_dict(session, user_id, session_id, metadata)
            
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            raise
    
    def _session_to_dict(
        self,
        session,
        user_id: str,
        session_id: str,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """Convert ADK session to dictionary format"""
        return {
            "session_id": session_id,
            "user_id": user_id,
            "state": session.state.get('custom_state', SessionState.CREATED) if hasattr(session, 'state') else SessionState.CREATED,
            "agent_states": session.state.get('agent_states', {}) if hasattr(session, 'state') else {},
            "artifacts": session.state.get('artifacts', []) if hasattr(session, 'state') else [],
            "checkpoints": session.state.get('checkpoints', []) if hasattr(session, 'state') else [],
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
    
    async def update_agent_state(self, session_id: str, agent_name: str, state: Dict):
        """
        Update state for a specific agent.
        
        Args:
            session_id: Session identifier
            agent_name: Agent name
            state: State dictionary to update
        """
        try:
            session = await self.service.get_session(
                app_name=self.app_name,
                session_id=session_id
            )
            
            if session:
                if not hasattr(session, 'state'):
                    session.state = {}
                if 'agent_states' not in session.state:
                    session.state['agent_states'] = {}
                
                session.state['agent_states'][agent_name] = state
                session.state['updated_at'] = datetime.utcnow().isoformat()
                
                # Save session
                await self.service.save_session(session)
                
        except Exception as e:
            logger.error(f"Error updating agent state: {e}")
    
    async def add_artifact(self, session_id: str, artifact_type: str, payload: Any):
        """
        Add an artifact to the session.
        
        Args:
            session_id: Session identifier
            artifact_type: Type of artifact
            payload: Artifact payload
        """
        try:
            session = await self.service.get_session(
                app_name=self.app_name,
                session_id=session_id
            )
            
            if session:
                if not hasattr(session, 'state'):
                    session.state = {}
                if 'artifacts' not in session.state:
                    session.state['artifacts'] = []
                
                artifact = {
                    "type": artifact_type,
                    "payload": payload,
                    "timestamp": datetime.utcnow().isoformat()
                }
                session.state['artifacts'].append(artifact)
                
                # Save session
                await self.service.save_session(session)
                
        except Exception as e:
            logger.error(f"Error adding artifact: {e}")
    
    async def create_checkpoint(self, session_id: str) -> Optional[str]:
        """
        Create a checkpoint for pause/resume.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Checkpoint ID or None
        """
        try:
            session = await self.service.get_session(
                app_name=self.app_name,
                session_id=session_id
            )
            
            if session:
                if not hasattr(session, 'state'):
                    session.state = {}
                if 'checkpoints' not in session.state:
                    session.state['checkpoints'] = []
                
                checkpoint_id = f"{session_id}_{len(session.state['checkpoints'])}"
                checkpoint = {
                    "checkpoint_id": checkpoint_id,
                    "state_snapshot": str(session.state),  # Simplified - full snapshot would be more complex
                    "timestamp": datetime.utcnow().isoformat()
                }
                session.state['checkpoints'].append(checkpoint)
                
                # Save session
                await self.service.save_session(session)
                
                return checkpoint_id
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating checkpoint: {e}")
            return None
    
    async def pause_session(self, session_id: str):
        """Pause a session"""
        await self._update_session_state(session_id, SessionState.PAUSED)
        await self.create_checkpoint(session_id)
    
    async def resume_session(self, session_id: str):
        """Resume a paused session"""
        await self._update_session_state(session_id, SessionState.RUNNING)
    
    async def complete_session(self, session_id: str):
        """Mark session as completed"""
        await self._update_session_state(session_id, SessionState.COMPLETED)
    
    async def _update_session_state(self, session_id: str, state: SessionState):
        """Internal helper to update session state"""
        try:
            session = await self.service.get_session(
                app_name=self.app_name,
                session_id=session_id
            )
            
            if session:
                if not hasattr(session, 'state'):
                    session.state = {}
                session.state['custom_state'] = state
                session.state['updated_at'] = datetime.utcnow().isoformat()
                
                if state == SessionState.COMPLETED:
                    session.state['completed_at'] = datetime.utcnow().isoformat()
                
                await self.service.save_session(session)
                
        except Exception as e:
            logger.error(f"Error updating session state: {e}")
    
    async def get_session(self, session_id: str) -> Optional[Dict]:
        """
        Retrieve session.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Session dictionary or None
        """
        try:
            session = await self.service.get_session(
                app_name=self.app_name,
                session_id=session_id
            )
            
            if session:
                # Extract user_id from session (ADK stores it)
                user_id = getattr(session, 'user_id', 'unknown')
                metadata = session.state.get('metadata', {}) if hasattr(session, 'state') else {}
                
                return self._session_to_dict(session, user_id, session_id, metadata)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting session: {e}")
            return None
    
    async def get_all_user_sessions(self, user_id: str) -> List[Dict]:
        """
        Get all sessions for a specific user.
        
        Args:
            user_id: User identifier
        
        Returns:
            List of session dictionaries
        """
        try:
            # ADK doesn't have direct method for this, so we'll need to implement
            # a workaround or use a different approach
            # For now, return empty list (would need to implement based on ADK API)
            logger.warning("get_all_user_sessions not fully implemented for ADK - returning empty list")
            return []
            
        except Exception as e:
            logger.error(f"Error getting user sessions: {e}")
            return []
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.
        
        Args:
            session_id: Session identifier
        
        Returns:
            True if session was deleted, False if not found
        """
        try:
            await self.service.delete_session(
                app_name=self.app_name,
                session_id=session_id
            )
            return True
            
        except Exception as e:
            logger.error(f"Error deleting session: {e}")
            return False
    
    async def update_session_metadata(self, session_id: str, metadata: Dict):
        """
        Update session metadata.
        
        Args:
            session_id: Session identifier
            metadata: Dictionary of metadata to update
        """
        try:
            session = await self.service.get_session(
                app_name=self.app_name,
                session_id=session_id
            )
            
            if session:
                if not hasattr(session, 'state'):
                    session.state = {}
                if 'metadata' not in session.state:
                    session.state['metadata'] = {}
                
                session.state['metadata'].update(metadata)
                session.state['updated_at'] = datetime.utcnow().isoformat()
                
                await self.service.save_session(session)
                
        except Exception as e:
            logger.error(f"Error updating session metadata: {e}")
    
    async def get_session_count(self) -> int:
        """Get total number of sessions"""
        # ADK doesn't provide direct count, would need custom implementation
        logger.warning("get_session_count not fully implemented for ADK - returning 0")
        return 0
    
    async def get_active_sessions(self) -> List[Dict]:
        """Get all active (running) sessions"""
        # Would need to implement based on ADK API
        logger.warning("get_active_sessions not fully implemented for ADK - returning empty list")
        return []
    
    async def cleanup_expired_sessions(self, max_age_hours: int = 24):
        """
        Remove sessions older than max_age_hours.
        
        Args:
            max_age_hours: Maximum age in hours before session is considered expired
        """
        # Would need to implement based on ADK API
        logger.warning("cleanup_expired_sessions not fully implemented for ADK")


# Factory functions
def create_adk_session_service(
    use_database: bool = False,
    db_url: Optional[str] = None,
    app_name: str = "interview_copilot"
) -> ADKSessionService:
    """
    Create an ADK Session Service instance.
    
    Args:
        use_database: If True, use DatabaseSessionService
        db_url: Database URL (required if use_database=True)
        app_name: Application name
    
    Returns:
        ADKSessionService instance
    """
    return ADKSessionService(
        use_database=use_database,
        db_url=db_url,
        app_name=app_name
    )

