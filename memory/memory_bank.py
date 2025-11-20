import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

class MemoryBank:
    def __init__(self, persist_directory: str = "./data/vectordb"):
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Collections for different memory types
        self.research_collection = self.client.get_or_create_collection("research_memory")
        self.session_collection = self.client.get_or_create_collection("session_memory")
        self.progress_collection = self.client.get_or_create_collection("user_progress")
    
    async def store_research(self, session_id: str, company: str, research_data: Any):
        """Store research findings"""
        doc_id = f"research_{session_id}"
        self.research_collection.add(
            documents=[json.dumps(research_data)],
            metadatas=[{
                "session_id": session_id,
                "company": company,
                "timestamp": datetime.utcnow().isoformat(),
                "type": "research"
            }],
            ids=[doc_id]
        )
    
    async def store_session(self, session_id: str, user_id: str, session_data: Dict):
        """Store session summary"""
        doc_id = f"session_{session_id}"
        self.session_collection.add(
            documents=[json.dumps(session_data)],
            metadatas=[{
                "session_id": session_id,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "score": session_data.get("score", 0)
            }],
            ids=[doc_id]
        )
    
    async def get_user_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """
        Retrieve user's session history with properly formatted data.
        
        Args:
            user_id: User identifier
            limit: Maximum number of sessions to return
        
        Returns:
            List of formatted session dictionaries
        """
        try:
            results = self.session_collection.get(
                where={"user_id": user_id},
                limit=limit
            )
            
            # Format results
            formatted_sessions = []
            if results and "ids" in results:
                for i, doc_id in enumerate(results["ids"]):
                    session_dict = {}
                    
                    # Get metadata
                    if "metadatas" in results and i < len(results["metadatas"]):
                        session_dict.update(results["metadatas"][i])
                    
                    # Parse document
                    if "documents" in results and i < len(results["documents"]):
                        try:
                            doc_data = json.loads(results["documents"][i])
                            if isinstance(doc_data, dict):
                                session_dict.update(doc_data)
                        except (json.JSONDecodeError, TypeError):
                            pass
                    
                    if session_dict:
                        formatted_sessions.append(session_dict)
            
            # Sort by timestamp (most recent first)
            formatted_sessions.sort(
                key=lambda x: x.get("timestamp", ""),
                reverse=True
            )
            
            return formatted_sessions[:limit]
            
        except Exception as e:
            logger.error(f"Error retrieving user history for {user_id}: {e}")
            return []
    
    async def search_similar_sessions(self, query: str, n_results: int = 5) -> List[Dict]:
        """
        Find similar past sessions with properly formatted results.
        
        Args:
            query: Search query string
            n_results: Maximum number of results to return
        
        Returns:
            List of formatted session dictionaries
        """
        try:
            results = self.session_collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            # Format results
            formatted_sessions = []
            if results and "ids" in results and len(results["ids"]) > 0:
                for i, doc_id_list in enumerate(results["ids"]):
                    for j, doc_id in enumerate(doc_id_list):
                        session_dict = {}
                        
                        # Get metadata
                        if "metadatas" in results and i < len(results["metadatas"]):
                            if j < len(results["metadatas"][i]):
                                session_dict.update(results["metadatas"][i][j])
                        
                        # Parse document
                        if "documents" in results and i < len(results["documents"]):
                            if j < len(results["documents"][i]):
                                try:
                                    doc_data = json.loads(results["documents"][i][j])
                                    if isinstance(doc_data, dict):
                                        session_dict.update(doc_data)
                                except (json.JSONDecodeError, TypeError):
                                    pass
                        
                        # Get distance if available
                        if "distances" in results and i < len(results["distances"]):
                            if j < len(results["distances"][i]):
                                session_dict["similarity_score"] = 1 - results["distances"][i][j]
                        
                        if session_dict:
                            formatted_sessions.append(session_dict)
            
            return formatted_sessions
            
        except Exception as e:
            logger.error(f"Error searching similar sessions: {e}")
            return []
    
    async def get_user_progress(self, user_id: str) -> Dict[str, Any]:
        """
        Get user's progress and session history with aggregated metrics.
        
        Args:
            user_id: User identifier
        
        Returns:
            Dictionary with progress metrics including:
            - total_sessions
            - questions_attempted
            - questions_solved
            - success_rate
            - skills_progress
            - recent_sessions
        """
        try:
            # Get all user sessions
            sessions = await self.get_user_history(user_id, limit=100)
            
            # Initialize metrics
            total_sessions = len(sessions)
            questions_attempted = 0
            questions_solved = 0
            skills_progress: Dict[str, Dict[str, Any]] = {}
            recent_sessions = []
            
            # Aggregate data from sessions
            for session in sessions:
                # Count questions
                q_attempted = session.get("questions_attempted", 0)
                q_solved = session.get("questions_solved", 0)
                
                if isinstance(q_attempted, (int, float)):
                    questions_attempted += int(q_attempted)
                if isinstance(q_solved, (int, float)):
                    questions_solved += int(q_solved)
                
                # Aggregate skills progress
                session_skills = session.get("skills_progress", {})
                if isinstance(session_skills, dict):
                    for skill, skill_data in session_skills.items():
                        if not isinstance(skill_data, dict):
                            continue
                        
                        if skill not in skills_progress:
                            skills_progress[skill] = {
                                "attempted": 0,
                                "solved": 0,
                                "proficiency": 0.0
                            }
                        
                        skills_progress[skill]["attempted"] += skill_data.get("attempted", 0)
                        skills_progress[skill]["solved"] += skill_data.get("solved", 0)
                
                # Collect recent session summary
                recent_sessions.append({
                    "session_id": session.get("session_id"),
                    "date": session.get("timestamp", "").split("T")[0] if session.get("timestamp") else "",
                    "company": session.get("company", ""),
                    "questions_solved": q_solved,
                    "total_questions": q_attempted,
                    "score": (q_solved / q_attempted * 100) if q_attempted > 0 else 0
                })
            
            # Calculate success rate
            success_rate = questions_solved / questions_attempted if questions_attempted > 0 else 0.0
            
            # Calculate skill proficiencies
            for skill, data in skills_progress.items():
                attempted = data["attempted"]
                solved = data["solved"]
                data["proficiency"] = solved / attempted if attempted > 0 else 0.0
            
            # Sort recent sessions by date (most recent first)
            recent_sessions.sort(key=lambda x: x.get("date", ""), reverse=True)
            
            return {
                "user_id": user_id,
                "total_sessions": total_sessions,
                "questions_attempted": questions_attempted,
                "questions_solved": questions_solved,
                "success_rate": success_rate,
                "avg_execution_time": 0.0,  # Could be calculated from session data
                "recent_sessions": recent_sessions[:10],  # Last 10 sessions
                "skills_progress": skills_progress
            }
            
        except Exception as e:
            logger.error(f"Error getting user progress for {user_id}: {e}")
            return {
                "user_id": user_id,
                "total_sessions": 0,
                "questions_attempted": 0,
                "questions_solved": 0,
                "success_rate": 0.0,
                "avg_execution_time": 0.0,
                "recent_sessions": [],
                "skills_progress": {}
            }
    
    async def store_user_progress(
        self,
        user_id: str,
        progress_data: Dict[str, Any]
    ):
        """
        Store user progress updates.
        
        Args:
            user_id: User identifier
            progress_data: Dictionary with progress information
        """
        try:
            doc_id = f"progress_{user_id}_{datetime.utcnow().isoformat()}"
            
            # Store in progress collection
            self.progress_collection.add(
                documents=[json.dumps(progress_data)],
                metadatas=[{
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "type": "progress_update"
                }],
                ids=[doc_id]
            )
            
            logger.info(f"Stored progress update for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error storing user progress: {e}")
            raise
    
    async def get_research_by_company(self, company: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve most recent research for a company.
        
        Args:
            company: Company name
        
        Returns:
            Most recent research dictionary or None
        """
        try:
            results = self.research_collection.get(
                where={"company": company},
                limit=1
            )
            
            if results and "ids" in results and len(results["ids"]) > 0:
                # Get most recent
                metadata = results["metadatas"][0] if "metadatas" in results else {}
                document = results["documents"][0] if "documents" in results else "{}"
                
                try:
                    research_data = json.loads(document) if isinstance(document, str) else document
                    return {
                        **metadata,
                        **research_data
                    }
                except (json.JSONDecodeError, TypeError):
                    return metadata
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving research for company {company}: {e}")
            return None
    
    async def update_session_score(
        self,
        session_id: str,
        score: float,
        additional_data: Optional[Dict[str, Any]] = None
    ):
        """
        Update session score in the database.
        
        Args:
            session_id: Session identifier
            score: Score value (0-100)
            additional_data: Optional additional data to update
        """
        try:
            # Get existing session
            results = self.session_collection.get(
                ids=[f"session_{session_id}"]
            )
            
            if results and "ids" in results and len(results["ids"]) > 0:
                # Update metadata
                metadata = results["metadatas"][0] if "metadatas" in results else {}
                document = results["documents"][0] if "documents" in results else "{}"
                
                # Parse and update
                try:
                    session_data = json.loads(document) if isinstance(document, str) else {}
                except (json.JSONDecodeError, TypeError):
                    session_data = {}
                
                # Update score and additional data
                session_data["score"] = score
                if additional_data:
                    session_data.update(additional_data)
                
                metadata["score"] = score
                metadata["updated_at"] = datetime.utcnow().isoformat()
                
                # Update in collection
                self.session_collection.update(
                    ids=[f"session_{session_id}"],
                    metadatas=[metadata],
                    documents=[json.dumps(session_data)]
                )
                
                logger.info(f"Updated score for session {session_id}: {score}")
            else:
                logger.warning(f"Session {session_id} not found for score update")
                
        except Exception as e:
            logger.error(f"Error updating session score: {e}")
            raise