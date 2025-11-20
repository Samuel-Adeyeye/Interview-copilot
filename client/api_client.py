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
        self.session = httpx.AsyncClient(timeout=timeout)
    
    async def close(self):
        """Close the client session"""
        await self.session.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    # ===== Session Management =====
    
    async def create_session(self, user_id: str, metadata: Dict = None) -> Dict[str, Any]:
        """Create a new interview session"""
        response = await self.session.post(
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
        response = await self.session.get(
            f"{self.base_url}/sessions/{session_id}"
        )
        response.raise_for_status()
        return response.json()
    
    async def pause_session(self, session_id: str) -> Dict[str, Any]:
        """Pause a running session"""
        response = await self.session.post(
            f"{self.base_url}/sessions/{session_id}/pause"
        )
        response.raise_for_status()
        return response.json()
    
    async def resume_session(self, session_id: str) -> Dict[str, Any]:
        """Resume a paused session"""
        response = await self.session.post(
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
        response = await self.session.post(
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
        response = await self.session.post(
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
        response = await self.session.post(
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
        response = await self.session.post(
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
        response = await self.session.get(
            f"{self.base_url}/users/{user_id}/progress"
        )
        response.raise_for_status()
        return response.json()
    
    async def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive session summary"""
        response = await self.session.get(
            f"{self.base_url}/sessions/{session_id}/summary"
        )
        response.raise_for_status()
        return response.json()
    
    # ===== Observability =====
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get system metrics"""
        response = await self.session.get(
            f"{self.base_url}/metrics"
        )
        response.raise_for_status()
        return response.json()
    
    async def get_session_traces(self, session_id: str) -> Dict[str, Any]:
        """Get session traces for observability"""
        response = await self.session.get(
            f"{self.base_url}/sessions/{session_id}/traces"
        )
        response.raise_for_status()
        return response.json()