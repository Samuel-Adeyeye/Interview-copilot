#!/usr/bin/env python3
"""
Full User Flow Test Script
Tests the complete Interview Co-Pilot application flow
"""

import sys
import os
import time
import asyncio
import httpx
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_status(message, status="info"):
    """Print colored status message"""
    if status == "success":
        print(f"{Colors.GREEN}✅ {message}{Colors.RESET}")
    elif status == "error":
        print(f"{Colors.RED}❌ {message}{Colors.RESET}")
    elif status == "warning":
        print(f"{Colors.YELLOW}⚠️  {message}{Colors.RESET}")
    elif status == "info":
        print(f"{Colors.BLUE}ℹ️  {message}{Colors.RESET}")
    else:
        print(f"{message}")

def check_environment():
    """Check if environment is set up correctly"""
    print_status("Checking environment setup...", "info")
    
    issues = []
    
    # Check .env file
    env_file = project_root / ".env"
    if not env_file.exists():
        issues.append("❌ .env file not found")
    else:
        print_status(".env file exists", "success")
    
    # Check required directories
    required_dirs = ["data", "data/sessions"]
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            os.makedirs(full_path, exist_ok=True)
            print_status(f"Created directory: {dir_path}", "info")
        else:
            print_status(f"Directory exists: {dir_path}", "success")
    
    # Check question bank
    qb_file = project_root / "data" / "questions_bank.json"
    if not qb_file.exists():
        issues.append("❌ Question bank file not found")
    else:
        print_status("Question bank file exists", "success")
    
    # Check Python packages
    try:
        import fastapi
        print_status("FastAPI installed", "success")
    except ImportError:
        issues.append("❌ FastAPI not installed")
    
    try:
        import streamlit
        print_status("Streamlit installed", "success")
    except ImportError:
        issues.append("❌ Streamlit not installed")
    
    if issues:
        print_status("\nEnvironment issues found:", "error")
        for issue in issues:
            print(f"  {issue}")
        return False
    
    print_status("Environment check passed!", "success")
    return True

def check_api_server(base_url="http://localhost:8000", timeout=5):
    """Check if API server is running"""
    print_status(f"Checking API server at {base_url}...", "info")
    
    try:
        # Try health endpoint first (more reliable)
        response = httpx.get(f"{base_url}/health", timeout=timeout)
        if response.status_code == 200:
            print_status("API server is running", "success")
            return True
    except httpx.ConnectError:
        print_status("API server is not running", "warning")
        return False
    except Exception as e:
        print_status(f"Error checking API: {e}", "error")
        return False
    
    return False

def test_health_endpoint(base_url="http://localhost:8000"):
    """Test health endpoint"""
    print_status("Testing health endpoint...", "info")
    
    try:
        # Test legacy health
        response = httpx.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print_status("Legacy health endpoint works", "success")
        else:
            print_status(f"Legacy health returned {response.status_code}", "warning")
        
        # Test ADK health
        try:
            response = httpx.get(f"{base_url}/api/v2/adk/health", timeout=5)
            if response.status_code == 200:
                print_status("ADK health endpoint works", "success")
                return True
            else:
                print_status(f"ADK health returned {response.status_code}", "warning")
        except Exception as e:
            print_status(f"ADK health endpoint not available: {e}", "warning")
        
        return True
    except Exception as e:
        print_status(f"Health check failed: {e}", "error")
        return False

def test_session_creation(base_url="http://localhost:8000"):
    """Test session creation"""
    print_status("Testing session creation...", "info")
    
    try:
        response = httpx.post(
            f"{base_url}/sessions/create",
            json={
                "user_id": "test_user_flow",
                "metadata": {"test": True}
            },
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            session_id = data.get("session_id")
            print_status(f"Session created: {session_id}", "success")
            return session_id
        else:
            print_status(f"Session creation failed: {response.status_code}", "error")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print_status(f"Session creation error: {e}", "error")
        return None

def test_research_endpoint(base_url="http://localhost:8000", session_id=None):
    """Test research endpoint (legacy)"""
    print_status("Testing research endpoint (legacy)...", "info")
    
    if not session_id:
        session_id = test_session_creation(base_url)
        if not session_id:
            return False
    
    try:
        response = httpx.post(
            f"{base_url}/research/run",
            json={
                "session_id": session_id,
                "company_name": "Google",
                "job_description": "Software Engineer position requiring Python and system design skills."
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print_status("Research endpoint works", "success")
            return True
        else:
            print_status(f"Research failed: {response.status_code}", "warning")
            print(f"Response: {response.text[:200]}")
            return False
    except Exception as e:
        print_status(f"Research error: {e}", "error")
        return False

def test_question_selection(base_url="http://localhost:8000", session_id=None):
    """Test question selection"""
    print_status("Testing question selection...", "info")
    
    if not session_id:
        session_id = test_session_creation(base_url)
        if not session_id:
            return False
    
    try:
        response = httpx.post(
            f"{base_url}/interview/start",
            json={
                "session_id": session_id,
                "difficulty": "easy",
                "num_questions": 2
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            questions = data.get("questions", [])
            print_status(f"Question selection works ({len(questions)} questions)", "success")
            return True
        else:
            print_status(f"Question selection failed: {response.status_code}", "warning")
            return False
    except Exception as e:
        print_status(f"Question selection error: {e}", "error")
        return False

def test_adk_endpoints(base_url="http://localhost:8000"):
    """Test ADK endpoints if available"""
    print_status("Testing ADK endpoints...", "info")
    
    session_id = test_session_creation(base_url)
    if not session_id:
        return False
    
    # Test ADK health
    try:
        response = httpx.get(f"{base_url}/api/v2/adk/health", timeout=5)
        if response.status_code == 200:
            print_status("ADK health endpoint works", "success")
        else:
            print_status("ADK health endpoint not available", "warning")
            return False
    except Exception as e:
        print_status(f"ADK endpoints not available: {e}", "warning")
        return False
    
    # Note: ADK endpoints require GOOGLE_API_KEY and may not work without it
    print_status("ADK endpoints available (may require GOOGLE_API_KEY)", "info")
    return True

def main():
    """Run full flow test"""
    print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}Interview Co-Pilot - Full Flow Test{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*60}{Colors.RESET}\n")
    
    # Step 1: Environment check
    print_status("\n[Step 1] Environment Check", "info")
    if not check_environment():
        print_status("\n❌ Environment check failed. Please fix issues above.", "error")
        return 1
    
    # Step 2: Check API server
    print_status("\n[Step 2] API Server Check", "info")
    base_url = "http://localhost:8000"
    
    if not check_api_server(base_url):
        print_status("\n⚠️  API server is not running.", "warning")
        print_status("Please start the API server first:", "info")
        print_status("  uvicorn api.main:app --reload --port 8000", "info")
        print_status("\nWaiting 5 seconds for you to start the server...", "info")
        time.sleep(5)
        
        if not check_api_server(base_url):
            print_status("\n❌ API server still not running. Please start it manually.", "error")
            return 1
    
    # Step 3: Health check
    print_status("\n[Step 3] Health Check", "info")
    if not test_health_endpoint(base_url):
        print_status("Health check had issues, but continuing...", "warning")
    
    # Step 4: Session creation
    print_status("\n[Step 4] Session Management", "info")
    session_id = test_session_creation(base_url)
    if not session_id:
        print_status("Session creation failed, but continuing...", "warning")
    
    # Step 5: Research endpoint
    print_status("\n[Step 5] Research Endpoint", "info")
    research_ok = test_research_endpoint(base_url, session_id)
    
    # Step 6: Question selection
    print_status("\n[Step 6] Question Selection", "info")
    questions_ok = test_question_selection(base_url, session_id)
    
    # Step 7: ADK endpoints (optional)
    print_status("\n[Step 7] ADK Endpoints (Optional)", "info")
    adk_ok = test_adk_endpoints(base_url)
    
    # Summary
    print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}Test Summary{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*60}{Colors.RESET}\n")
    
    results = {
        "Environment": "✅",
        "API Server": "✅" if check_api_server(base_url) else "❌",
        "Health Check": "✅" if test_health_endpoint(base_url) else "⚠️",
        "Session Creation": "✅" if session_id else "⚠️",
        "Research": "✅" if research_ok else "⚠️",
        "Question Selection": "✅" if questions_ok else "⚠️",
        "ADK Endpoints": "✅" if adk_ok else "⚠️"
    }
    
    for test, result in results.items():
        print(f"{result} {test}")
    
    all_critical = all([
        check_api_server(base_url),
        session_id is not None,
        research_ok or questions_ok  # At least one works
    ])
    
    if all_critical:
        print_status("\n✅ All critical tests passed!", "success")
        print_status("The application is ready for use.", "success")
        return 0
    else:
        print_status("\n⚠️  Some tests had issues, but basic functionality may work.", "warning")
        return 1

if __name__ == "__main__":
    sys.exit(main())

