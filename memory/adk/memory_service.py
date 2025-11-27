"""
ADK Memory Service Wrapper
Provides compatibility layer between custom MemoryBank and ADK memory services
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

# Try to import ADK memory services
try:
    from google.adk.memory import InMemoryMemoryService, VertexAIMemoryBank
    ADK_AVAILABLE = True
except ImportError:
    ADK_AVAILABLE = False
    logger.warning("ADK memory services not available - using fallback")


class ADKMemoryService:
    """
    ADK Memory Service wrapper that provides compatibility with custom MemoryBank API.
    
    This wraps ADK's memory services and provides the same interface as MemoryBank
    for backward compatibility.
    """
    
    def __init__(
        self,
        use_vertex_ai: bool = False,
        project_id: Optional[str] = None,
        location: Optional[str] = None,
        memory_bank_id: Optional[str] = None
    ):
        """
        Initialize ADK Memory Service.
        
        Args:
            use_vertex_ai: If True, use VertexAIMemoryBank. If False, use InMemoryMemoryService.
            project_id: GCP project ID (required if use_vertex_ai=True)
            location: GCP location (required if use_vertex_ai=True)
            memory_bank_id: Memory bank ID (required if use_vertex_ai=True)
        """
        if not ADK_AVAILABLE:
            logger.warning("ADK memory services not available - using fallback in-memory storage")
            self.service = None
            self._fallback_storage = {
                "research": {},
                "sessions": {},
                "progress": {}
            }
            return
        
        if use_vertex_ai:
            if not project_id or not location or not memory_bank_id:
                raise ValueError("project_id, location, and memory_bank_id are required when use_vertex_ai=True")
            
            try:
                self.service = VertexAIMemoryBank(
                    project_id=project_id,
                    location=location,
                    memory_bank_id=memory_bank_id
                )
                logger.info(f"✅ Using ADK VertexAIMemoryBank: {memory_bank_id}")
            except Exception as e:
                logger.error(f"Failed to create VertexAIMemoryBank: {e}")
                logger.warning("Falling back to in-memory storage")
                self.service = None
                self._fallback_storage = {
                    "research": {},
                    "sessions": {},
                    "progress": {}
                }
        else:
            try:
                self.service = InMemoryMemoryService()
                logger.info("✅ Using ADK InMemoryMemoryService")
                self._fallback_storage = None
            except Exception as e:
                logger.error(f"Failed to create InMemoryMemoryService: {e}")
                self.service = None
                self._fallback_storage = {
                    "research": {},
                    "sessions": {},
                    "progress": {}
                }
    
    async def store_research(self, session_id: str, company: str, research_data: Any):
        """
        Store research findings.
        
        Args:
            session_id: Session identifier
            company: Company name
            research_data: Research data to store
        """
        try:
            if self.service:
                # Use ADK memory service
                # Note: ADK memory service API may differ - this is a placeholder
                # Actual implementation depends on ADK memory service API
                logger.info(f"Storing research for {company} (session: {session_id})")
                # await self.service.store(...)  # Would use actual ADK API
            else:
                # Fallback storage
                doc_id = f"research_{session_id}"
                self._fallback_storage["research"][doc_id] = {
                    "session_id": session_id,
                    "company": company,
                    "data": research_data,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error storing research: {e}")
    
    async def store_session(self, session_id: str, user_id: str, session_data: Dict):
        """
        Store session summary.
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            session_data: Session data to store
        """
        try:
            if self.service:
                # Use ADK memory service
                logger.info(f"Storing session {session_id} for user {user_id}")
                # await self.service.store(...)  # Would use actual ADK API
            else:
                # Fallback storage
                doc_id = f"session_{session_id}"
                self._fallback_storage["sessions"][doc_id] = {
                    "session_id": session_id,
                    "user_id": user_id,
                    "data": session_data,
                    "timestamp": datetime.utcnow().isoformat(),
                    "score": session_data.get("score", 0)
                }
                
        except Exception as e:
            logger.error(f"Error storing session: {e}")
    
    async def get_user_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """
        Retrieve user's session history.
        
        Args:
            user_id: User identifier
            limit: Maximum number of sessions to return
        
        Returns:
            List of formatted session dictionaries
        """
        try:
            if self.service:
                # Use ADK memory service
                # Would query ADK memory service
                logger.info(f"Getting user history for {user_id}")
                # results = await self.service.query(...)  # Would use actual ADK API
                return []
            else:
                # Fallback: search in-memory storage
                user_sessions = [
                    {
                        **value["data"],
                        "session_id": value["session_id"],
                        "user_id": value["user_id"],
                        "timestamp": value["timestamp"],
                        "score": value.get("score", 0)
                    }
                    for value in self._fallback_storage["sessions"].values()
                    if value.get("user_id") == user_id
                ]
                
                # Sort by timestamp (most recent first)
                user_sessions.sort(
                    key=lambda x: x.get("timestamp", ""),
                    reverse=True
                )
                
                return user_sessions[:limit]
                
        except Exception as e:
            logger.error(f"Error getting user history: {e}")
            return []
    
    async def search_similar_sessions(self, query: str, n_results: int = 5) -> List[Dict]:
        """
        Find similar past sessions.
        
        Args:
            query: Search query string
            n_results: Maximum number of results to return
        
        Returns:
            List of formatted session dictionaries
        """
        try:
            if self.service:
                # Use ADK memory service for semantic search
                logger.info(f"Searching similar sessions: {query}")
                # results = await self.service.search(...)  # Would use actual ADK API
                return []
            else:
                # Fallback: simple text matching
                matching_sessions = []
                query_lower = query.lower()
                
                for value in self._fallback_storage["sessions"].values():
                    session_str = json.dumps(value["data"]).lower()
                    if query_lower in session_str:
                        matching_sessions.append({
                            **value["data"],
                            "session_id": value["session_id"],
                            "user_id": value["user_id"],
                            "timestamp": value["timestamp"],
                            "similarity_score": 0.5  # Placeholder
                        })
                
                return matching_sessions[:n_results]
                
        except Exception as e:
            logger.error(f"Error searching similar sessions: {e}")
            return []
    
    async def get_research_by_company(self, company: str) -> Optional[Dict]:
        """
        Get research data for a specific company.
        
        Args:
            company: Company name
        
        Returns:
            Research data dictionary or None
        """
        try:
            if self.service:
                # Use ADK memory service
                logger.info(f"Getting research for {company}")
                # result = await self.service.get(...)  # Would use actual ADK API
                return None
            else:
                # Fallback: search in-memory storage
                for value in self._fallback_storage["research"].values():
                    if value.get("company", "").lower() == company.lower():
                        return {
                            **value["data"],
                            "company": value["company"],
                            "timestamp": value["timestamp"]
                        }
                
                return None
                
        except Exception as e:
            logger.error(f"Error getting research by company: {e}")
            return None
    
    async def get_user_progress(self, user_id: str) -> Dict[str, Any]:
        """
        Get user progress data.
        
        Args:
            user_id: User identifier
        
        Returns:
            Progress data dictionary
        """
        try:
            if self.service:
                # Use ADK memory service
                logger.info(f"Getting user progress for {user_id}")
                # result = await self.service.get(...)  # Would use actual ADK API
                return {}
            else:
                # Fallback: aggregate from sessions
                user_sessions = [
                    value for value in self._fallback_storage["sessions"].values()
                    if value.get("user_id") == user_id
                ]
                
                total_sessions = len(user_sessions)
                total_score = sum(s.get("score", 0) for s in user_sessions)
                avg_score = total_score / total_sessions if total_sessions > 0 else 0
                
                return {
                    "user_id": user_id,
                    "total_sessions": total_sessions,
                    "average_score": avg_score,
                    "last_session": user_sessions[0]["timestamp"] if user_sessions else None
                }
                
        except Exception as e:
            logger.error(f"Error getting user progress: {e}")
            return {}
    
    async def store_user_progress(self, user_id: str, progress_data: Dict):
        """
        Store user progress data.
        
        Args:
            user_id: User identifier
            progress_data: Progress data to store
        """
        try:
            if self.service:
                # Use ADK memory service
                logger.info(f"Storing user progress for {user_id}")
                # await self.service.store(...)  # Would use actual ADK API
            else:
                # Fallback storage
                self._fallback_storage["progress"][user_id] = {
                    **progress_data,
                    "user_id": user_id,
                    "updated_at": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error storing user progress: {e}")
    
    async def update_session_score(self, session_id: str, score: float):
        """
        Update session score.
        
        Args:
            session_id: Session identifier
            score: Score value
        """
        try:
            if self.service:
                # Use ADK memory service
                logger.info(f"Updating session score for {session_id}: {score}")
                # await self.service.update(...)  # Would use actual ADK API
            else:
                # Fallback: update in-memory storage
                doc_id = f"session_{session_id}"
                if doc_id in self._fallback_storage["sessions"]:
                    self._fallback_storage["sessions"][doc_id]["score"] = score
                    if "data" in self._fallback_storage["sessions"][doc_id]:
                        self._fallback_storage["sessions"][doc_id]["data"]["score"] = score
                
        except Exception as e:
            logger.error(f"Error updating session score: {e}")


# Factory functions
def create_adk_memory_service(
    use_vertex_ai: bool = False,
    project_id: Optional[str] = None,
    location: Optional[str] = None,
    memory_bank_id: Optional[str] = None
) -> ADKMemoryService:
    """
    Create an ADK Memory Service instance.
    
    Args:
        use_vertex_ai: If True, use VertexAIMemoryBank
        project_id: GCP project ID (required if use_vertex_ai=True)
        location: GCP location (required if use_vertex_ai=True)
        memory_bank_id: Memory bank ID (required if use_vertex_ai=True)
    
    Returns:
        ADKMemoryService instance
    """
    return ADKMemoryService(
        use_vertex_ai=use_vertex_ai,
        project_id=project_id,
        location=location,
        memory_bank_id=memory_bank_id
    )

