"""
Test script for Interview Co-Pilot API
Tests all critical endpoints to ensure they work correctly
"""

import asyncio
import httpx
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

async def test_health_check():
    """Test health check endpoint"""
    print("\n🔍 Testing Health Check...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/health")
            print(f"✅ Status: {response.status_code}")
            print(f"   Response: {json.dumps(response.json(), indent=2)}")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

async def test_create_session():
    """Test session creation"""
    print("\n🔍 Testing Session Creation...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/sessions/create",
                json={"user_id": "test_user_001", "metadata": {"test": True}}
            )
            print(f"✅ Status: {response.status_code}")
            data = response.json()
            print(f"   Session ID: {data.get('session_id')}")
            print(f"   User ID: {data.get('user_id')}")
            print(f"   State: {data.get('state')}")
            return data.get('session_id')
        except Exception as e:
            print(f"❌ Error: {e}")
            return None

async def test_upload_job_description():
    """Test job description upload"""
    print("\n🔍 Testing Job Description Upload...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/job-descriptions/upload",
                json={
                    "job_title": "Senior Software Engineer",
                    "company_name": "TechCorp",
                    "jd_text": "We are looking for a Senior Software Engineer with 5+ years of Python experience."
                }
            )
            print(f"✅ Status: {response.status_code}")
            data = response.json()
            print(f"   JD ID: {data.get('jd_id')}")
            return True
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

async def test_research(session_id: str):
    """Test research endpoint"""
    print("\n🔍 Testing Research Endpoint...")
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{BASE_URL}/research/run",
                json={
                    "session_id": session_id,
                    "job_description": "Senior Software Engineer position requiring Python, algorithms, and system design.",
                    "company_name": "TechCorp"
                }
            )
            print(f"✅ Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Company: {data.get('company_name')}")
                print(f"   Research Packet Keys: {list(data.get('research_packet', {}).keys())}")
                print(f"   Execution Time: {data.get('execution_time_ms', 0):.1f}ms")
                return True
            else:
                print(f"   Error: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

async def test_start_interview(session_id: str):
    """Test interview start endpoint"""
    print("\n🔍 Testing Interview Start...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{BASE_URL}/interview/start",
                json={
                    "session_id": session_id,
                    "difficulty": "easy",
                    "num_questions": 2
                }
            )
            print(f"✅ Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                questions = data.get('questions', [])
                print(f"   Questions Returned: {len(questions)}")
                if questions:
                    print(f"   First Question: {questions[0].get('title')}")
                return questions[0].get('id') if questions else None
            else:
                print(f"   Error: {response.text}")
                return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None

async def test_submit_code(session_id: str, question_id: str):
    """Test code submission"""
    print("\n🔍 Testing Code Submission...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            code = """
def two_sum(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []
"""
            response = await client.post(
                f"{BASE_URL}/interview/submit-code",
                json={
                    "session_id": session_id,
                    "question_id": question_id or "q1",
                    "code": code,
                    "language": "python"
                }
            )
            print(f"✅ Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Status: {data.get('status')}")
                print(f"   Tests Passed: {data.get('tests_passed', 0)}/{data.get('total_tests', 0)}")
                return True
            else:
                print(f"   Error: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

async def test_user_progress():
    """Test user progress endpoint"""
    print("\n🔍 Testing User Progress...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/users/test_user_001/progress")
            print(f"✅ Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Total Sessions: {data.get('total_sessions', 0)}")
                print(f"   Questions Attempted: {data.get('questions_attempted', 0)}")
                print(f"   Success Rate: {data.get('success_rate', 0)*100:.1f}%")
                return True
            else:
                print(f"   Error: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

async def test_session_summary(session_id: str):
    """Test session summary endpoint"""
    print("\n🔍 Testing Session Summary...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/sessions/{session_id}/summary")
            print(f"✅ Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Questions Attempted: {data.get('questions_attempted', 0)}")
                print(f"   Questions Solved: {data.get('questions_solved', 0)}")
                print(f"   Duration: {data.get('duration_minutes', 0):.1f} minutes")
                return True
            else:
                print(f"   Error: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

async def test_metrics():
    """Test metrics endpoint"""
    print("\n🔍 Testing Metrics...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/metrics")
            print(f"✅ Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Total Sessions: {data.get('system', {}).get('total_sessions', 0)}")
                print(f"   Agents: {list(data.get('agents', {}).keys())}")
                return True
            else:
                print(f"   Error: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

async def run_all_tests():
    """Run all tests in sequence"""
    print("=" * 60)
    print("🧪 Interview Co-Pilot API Test Suite")
    print("=" * 60)
    
    results = {}
    
    # Test 1: Health Check
    results['health'] = await test_health_check()
    if not results['health']:
        print("\n❌ Health check failed. Is the API server running?")
        print("   Start the server with: uvicorn api.main:app --reload")
        return
    
    # Test 2: Create Session
    session_id = await test_create_session()
    results['session'] = session_id is not None
    
    if not session_id:
        print("\n❌ Session creation failed. Cannot continue tests.")
        return
    
    # Test 3: Upload Job Description
    results['jd_upload'] = await test_upload_job_description()
    
    # Test 4: Research (may take time)
    results['research'] = await test_research(session_id)
    
    # Test 5: Start Interview
    question_id = await test_start_interview(session_id)
    results['interview'] = question_id is not None
    
    # Test 6: Submit Code
    if question_id:
        results['code_submit'] = await test_submit_code(session_id, question_id)
    else:
        results['code_submit'] = False
    
    # Test 7: User Progress
    results['progress'] = await test_user_progress()
    
    # Test 8: Session Summary
    results['summary'] = await test_session_summary(session_id)
    
    # Test 9: Metrics
    results['metrics'] = await test_metrics()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {test_name:20s} {status}")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    print(f"\n   Total: {passed}/{total} tests passed")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_all_tests())

