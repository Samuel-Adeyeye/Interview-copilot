import httpx
from typing import Dict, Any, Optional, List
from pydantic import BaseModel

class InterviewCoPilotClient:
    """
    Python client for Interview Co-Pilot API
    """
    
    def __init__(self, base_url: str = "http://localhost:8000", timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session = None  # Lazy initialization
    
    def _get_session(self):
        """Get or create async client session (lazy initialization per event loop)"""
        # Always create a new client to avoid event loop binding issues
        # This ensures the client is bound to the current event loop
        return httpx.AsyncClient(timeout=self.timeout)
    
    @property
    def session(self):
        """Get async client session (creates new one each time to avoid event loop issues)"""
        # Create a new session each time to avoid event loop binding issues
        # This is necessary when using nest_asyncio with Streamlit
        return self._get_session()
    
    async def close(self):
        """Close the client session"""
        if self._session is not None:
            await self._session.aclose()
            self._session = None
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    # ===== Session Management =====
    
    async def create_session(self, user_id: str, metadata: Dict = None) -> Dict[str, Any]:
        """Create a new interview session"""
        # Create a new client for this request to avoid event loop issues
        async with self._get_session() as session:
            response = await session.post(
                f"{self.base_url}/sessions/create",
                json={
                    "user_id": user_id,
                    "metadata": metadata or {}
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def get_session(self, session_id: str) -> Dict[str, Any]:
        """Get session details"""
        async with self._get_session() as session:
            response = await session.get(
                f"{self.base_url}/sessions/{session_id}"
            )
            response.raise_for_status()
            return response.json()
    
    async def pause_session(self, session_id: str) -> Dict[str, Any]:
        """Pause a running session"""
        async with self._get_session() as session:
            response = await session.post(
                f"{self.base_url}/sessions/{session_id}/pause"
            )
            response.raise_for_status()
            return response.json()
    
    async def resume_session(self, session_id: str) -> Dict[str, Any]:
        """Resume a paused session"""
        async with self._get_session() as session:
            response = await session.post(
                f"{self.base_url}/sessions/{session_id}/resume"
            )
            response.raise_for_status()
            return response.json()
    
    # ===== Job Description & Research =====
    
    async def upload_job_description(
        self, 
        job_title: str, 
        company_name: str, 
        jd_text: str
    ) -> Dict[str, Any]:
        """Upload a job description"""
        async with self._get_session() as session:
            response = await session.post(
                f"{self.base_url}/job-descriptions/upload",
                json={
                    "job_title": job_title,
                    "company_name": company_name,
                    "jd_text": jd_text
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def run_research(
        self, 
        session_id: str, 
        job_description: str, 
        company_name: str
    ) -> Dict[str, Any]:
        """Run research agent"""
        # Create a new client for this request to avoid event loop issues
        async with self._get_session() as session:
            response = await session.post(
                f"{self.base_url}/research/run",
                json={
                    "session_id": session_id,
                    "job_description": job_description,
                    "company_name": company_name
                }
            )
            response.raise_for_status()
            return response.json()
    
    # ===== Mock Interview =====
    
    async def start_mock_interview(
        self, 
        session_id: str, 
        difficulty: str = "medium", 
        num_questions: int = 3
    ) -> Dict[str, Any]:
        """Start mock technical interview"""
        async with self._get_session() as session:
            response = await session.post(
                f"{self.base_url}/interview/start",
                json={
                    "session_id": session_id,
                    "difficulty": difficulty,
                    "num_questions": num_questions
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def submit_code(
        self, 
        session_id: str, 
        question_id: str, 
        code: str, 
        language: str = "python"
    ) -> Dict[str, Any]:
        """Submit code for evaluation"""
        async with self._get_session() as session:
            response = await session.post(
                f"{self.base_url}/interview/submit-code",
                json={
                    "session_id": session_id,
                    "question_id": question_id,
                    "code": code,
                    "language": language
                }
            )
            response.raise_for_status()
            return response.json()
    
    # ===== Progress & Memory =====
    
    async def get_user_progress(self, user_id: str) -> Dict[str, Any]:
        """Get user's progress and history"""
        async with self._get_session() as session:
            response = await session.get(
                f"{self.base_url}/users/{user_id}/progress"
            )
            response.raise_for_status()
            return response.json()
    
    async def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive session summary"""
        async with self._get_session() as session:
            response = await session.get(
                f"{self.base_url}/sessions/{session_id}/summary"
            )
            response.raise_for_status()
            return response.json()
    
    # ===== Observability =====
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get system metrics"""
        async with self._get_session() as session:
            response = await session.get(
                f"{self.base_url}/metrics"
            )
            response.raise_for_status()
            return response.json()
    
    async def get_session_traces(self, session_id: str) -> Dict[str, Any]:
        """Get session traces for observability"""
        async with self._get_session() as session:
            response = await session.get(
                f"{self.base_url}/sessions/{session_id}/traces"
            )
            response.raise_for_status()
            return response.json()


class InterviewCoPilotSyncClient:
    """
    Synchronous Python client for Interview Co-Pilot API
    Designed for use with Streamlit and other synchronous environments
    """
    
    def __init__(self, base_url: str = "http://localhost:8000", timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session = None
    
    def _get_session(self):
        """Get or create sync client session"""
        if self._session is None:
            self._session = httpx.Client(timeout=self.timeout)
        return self._session
    
    def close(self):
        """Close the client session"""
        if self._session is not None:
            self._session.close()
            self._session = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    # ===== Session Management =====
    
    def create_session(self, user_id: str, metadata: Dict = None) -> Dict[str, Any]:
        """Create a new interview session"""
        response = self._get_session().post(
            f"{self.base_url}/sessions/create",
            json={
                "user_id": user_id,
                "metadata": metadata or {}
            }
        )
        response.raise_for_status()
        return response.json()
    
    def get_session(self, session_id: str) -> Dict[str, Any]:
        """Get session details"""
        response = self._get_session().get(
            f"{self.base_url}/sessions/{session_id}"
        )
        response.raise_for_status()
        return response.json()
    
    def pause_session(self, session_id: str) -> Dict[str, Any]:
        """Pause a running session"""
        response = self._get_session().post(
            f"{self.base_url}/sessions/{session_id}/pause"
        )
        response.raise_for_status()
        return response.json()
    
    def resume_session(self, session_id: str) -> Dict[str, Any]:
        """Resume a paused session"""
        response = self._get_session().post(
            f"{self.base_url}/sessions/{session_id}/resume"
        )
        response.raise_for_status()
        return response.json()
    
    # ===== Job Description & Research =====
    
    def upload_job_description(
        self, 
        job_title: str, 
        company_name: str, 
        jd_text: str
    ) -> Dict[str, Any]:
        """Upload a job description"""
        response = self._get_session().post(
            f"{self.base_url}/job-descriptions/upload",
            json={
                "job_title": job_title,
                "company_name": company_name,
                "jd_text": jd_text
            }
        )
        response.raise_for_status()
        return response.json()
    
    def run_research(
        self, 
        session_id: str, 
        job_description: str, 
        company_name: str
    ) -> Dict[str, Any]:
        """Run research agent"""
        response = self._get_session().post(
            f"{self.base_url}/research/run",
            json={
                "session_id": session_id,
                "job_description": job_description,
                "company_name": company_name
            }
        )
        response.raise_for_status()
        return response.json()
    
    # ===== Mock Interview =====
    
    def start_mock_interview(
        self, 
        session_id: str, 
        difficulty: str = "medium", 
        num_questions: int = 3
    ) -> Dict[str, Any]:
        """Start mock technical interview"""
        response = self._get_session().post(
            f"{self.base_url}/interview/start",
            json={
                "session_id": session_id,
                "difficulty": difficulty,
                "num_questions": num_questions
            }
        )
        response.raise_for_status()
        return response.json()
    
    def submit_code(
        self, 
        session_id: str, 
        question_id: str, 
        code: str, 
        language: str = "python"
    ) -> Dict[str, Any]:
        """Submit code for evaluation"""
        response = self._get_session().post(
            f"{self.base_url}/interview/submit-code",
            json={
                "session_id": session_id,
                "question_id": question_id,
                "code": code,
                "language": language
            }
        )
        response.raise_for_status()
        return response.json()
    
    # ===== Progress & Memory =====
    
    def get_user_progress(self, user_id: str) -> Dict[str, Any]:
        """Get user's progress and history"""
        response = self._get_session().get(
            f"{self.base_url}/users/{user_id}/progress"
        )
        response.raise_for_status()
        return response.json()
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive session summary"""
        response = self._get_session().get(
            f"{self.base_url}/sessions/{session_id}/summary"
        )
        response.raise_for_status()
        return response.json()
    
    # ===== Observability =====
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get system metrics"""
        response = self._get_session().get(
            f"{self.base_url}/metrics"
        )
        response.raise_for_status()
        return response.json()
    
    def get_session_traces(self, session_id: str) -> Dict[str, Any]:
        """Get session traces for observability"""
        response = self._get_session().get(
            f"{self.base_url}/sessions/{session_id}/traces"
        )
        response.raise_for_status()
        return response.json()