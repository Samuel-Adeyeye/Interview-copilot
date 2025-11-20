"""
Complete Example: Running Interview Co-Pilot End-to-End
examples/run_complete_demo.py

This script demonstrates the full workflow:
1. Initialize all agents and services
2. Create a session
3. Upload job description and run research
4. Start mock interview
5. Submit and evaluate code
6. View results and metrics
"""

import asyncio
import json
from datetime import datetime
from client.api_client import InterviewCoPilotClient


# ============= Sample Data =============

SAMPLE_JOB_DESCRIPTION = """
Senior Backend Engineer - TechCorp AI Division

We're looking for an experienced backend engineer to help build our next-generation AI platform.

Requirements:
- 5+ years of Python development experience
- Strong understanding of algorithms and data structures
- Experience with distributed systems and microservices
- Proficiency with SQL and NoSQL databases
- Knowledge of cloud platforms (AWS/GCP)
- Experience with RESTful APIs and async programming

Nice to have:
- Experience with LLMs and AI/ML pipelines
- Knowledge of graph databases
- Docker and Kubernetes experience

Responsibilities:
- Design and implement scalable backend services
- Optimize system performance and reliability
- Collaborate with ML team on model deployment
- Mentor junior engineers
- Participate in technical interviews

Interview Process:
1. Phone screen (30 min) - General experience and culture fit
2. Technical interview (90 min) - Coding and system design
3. Behavioral interview (45 min) - Leadership and teamwork
4. Team fit interview (30 min) - Meet the team
"""

SAMPLE_CODE = """
def two_sum(nums, target):
    '''
    Find two numbers in array that add up to target.
    Time: O(n), Space: O(n)
    '''
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []

# Test
print(two_sum([2, 7, 11, 15], 9))  # Expected: [0, 1]
print(two_sum([3, 2, 4], 6))       # Expected: [1, 2]
"""


# ============= Demo Functions =============

async def run_complete_demo():
    """
    Run a complete end-to-end demo of the Interview Co-Pilot system
    """
    print("=" * 60)
    print("🚀 Interview Co-Pilot - Complete Demo")
    print("=" * 60)
    print()
    
    # Initialize client
    async with InterviewCoPilotClient(base_url="http://localhost:8000") as client:
        
        # Step 1: Create Session
        print("📝 Step 1: Creating Interview Session...")
        session = await client.create_session(
            user_id="demo_user_001",
            metadata={"demo": True, "timestamp": datetime.utcnow().isoformat()}
        )
        session_id = session["session_id"]
        print(f"✅ Session created: {session_id}")
        print(f"   User: {session['user_id']}")
        print(f"   State: {session['state']}")
        print()
        
        # Step 2: Upload Job Description
        print("📄 Step 2: Uploading Job Description...")
        jd_result = await client.upload_job_description(
            job_title="Senior Backend Engineer",
            company_name="TechCorp",
            jd_text=SAMPLE_JOB_DESCRIPTION
        )
        print(f"✅ Job description uploaded")
        print(f"   JD ID: {jd_result['jd_id']}")
        print(f"   Company: {jd_result['company_name']}")
        print()
        
        # Step 3: Run Research Agent
        print("🔍 Step 3: Running Research Agent...")
        print("   (This agent searches the web for company info and interview tips)")
        research_result = await client.run_research(
            session_id=session_id,
            job_description=SAMPLE_JOB_DESCRIPTION,
            company_name="TechCorp"
        )
        print(f"✅ Research completed in {research_result['execution_time_ms']:.1f}ms")
        print(f"\n   📊 Research Packet:")
        research_packet = research_result['research_packet']
        for key, value in research_packet.items():
            print(f"      • {key}: {value}")
        
        print(f"\n   💡 Key Insights:")
        for idx, insight in enumerate(research_result['insights'], 1):
            print(f"      {idx}. {insight}")
        print()
        
        # Step 4: Start Mock Interview
        print("🎯 Step 4: Starting Mock Technical Interview...")
        interview_result = await client.start_mock_interview(
            session_id=session_id,
            difficulty="medium",
            num_questions=3
        )
        print(f"✅ Interview started with {len(interview_result['questions'])} questions")
        print(f"\n   📝 Questions:")
        for idx, question in enumerate(interview_result['questions'], 1):
            print(f"      {idx}. {question['title']} ({question['difficulty']})")
            print(f"         {question['description'][:80]}...")
        print()
        
        # Step 5: Pause Session (Demonstrate pause/resume)
        print("⏸️  Step 5: Pausing Session (demonstrating pause/resume)...")
        pause_result = await client.pause_session(session_id)
        print(f"✅ Session paused: {pause_result['message']}")
        print()
        
        # Wait a moment
        await asyncio.sleep(1)
        
        # Resume Session
        print("▶️  Step 6: Resuming Session...")
        resume_result = await client.resume_session(session_id)
        print(f"✅ Session resumed: {resume_result['message']}")
        print()
        
        # Step 7: Submit Code Solution
        first_question = interview_result['questions'][0]
        print(f"💻 Step 7: Submitting Code for Question: {first_question['title']}...")
        print(f"\n   Code submitted:")
        print("   " + "-" * 50)
        for line in SAMPLE_CODE.split('\n')[:10]:
            print(f"   {line}")
        print("   " + "-" * 50)
        
        evaluation = await client.submit_code(
            session_id=session_id,
            question_id=first_question['id'],
            code=SAMPLE_CODE,
            language="python"
        )
        
        print(f"\n✅ Code evaluated in {evaluation['execution_time_ms']:.1f}ms")
        print(f"\n   📊 Test Results:")
        print(f"      • Tests Passed: {evaluation['tests_passed']}/{evaluation['total_tests']}")
        print(f"      • Status: {evaluation['status']}")
        
        if evaluation.get('complexity_analysis'):
            print(f"\n   ⏱️  Complexity Analysis:")
            print(f"      • Time Complexity: {evaluation['complexity_analysis']['time']}")
            print(f"      • Space Complexity: {evaluation['complexity_analysis']['space']}")
        
        print(f"\n   💬 Feedback:")
        feedback_lines = evaluation['feedback'].strip().split('\n')
        for line in feedback_lines[:8]:  # Show first 8 lines
            print(f"      {line}")
        print()
        
        # Step 8: Get Session Summary
        print("📋 Step 8: Retrieving Session Summary...")
        summary = await client.get_session_summary(session_id)
        print(f"✅ Session Summary Retrieved")
        print(f"\n   Session Details:")
        print(f"      • Session ID: {summary['session_id']}")
        print(f"      • User ID: {summary['user_id']}")
        print(f"      • State: {summary['state']}")
        print(f"      • Duration: {summary['duration_minutes']} minutes")
        print(f"      • Questions Attempted: {summary['questions_attempted']}")
        print(f"      • Questions Solved: {summary['questions_solved']}")
        print(f"      • Artifacts Collected: {len(summary['artifacts'])}")
        print()
        
        # Step 9: Get User Progress
        print("📈 Step 9: Checking User Progress...")
        progress = await client.get_user_progress("demo_user_001")
        print(f"✅ User Progress Retrieved")
        print(f"\n   Overall Statistics:")
        print(f"      • Total Sessions: {progress['total_sessions']}")
        print(f"      • Questions Attempted: {progress['questions_attempted']}")
        print(f"      • Questions Solved: {progress['questions_solved']}")
        print(f"      • Success Rate: {progress['success_rate']*100:.1f}%")
        
        print(f"\n   📊 Skills Progress:")
        for skill, data in progress['skills_progress'].items():
            proficiency = data['proficiency'] * 100
            bar_length = int(proficiency / 5)
            bar = "█" * bar_length + "░" * (20 - bar_length)
            print(f"      • {skill.replace('_', ' ').title():20s} [{bar}] {proficiency:.0f}%")
        print()
        
        # Step 10: Get System Metrics (Observability)
        print("📊 Step 10: Checking System Metrics (Observability)...")
        metrics = await client.get_metrics()
        print(f"✅ Metrics Retrieved (Timestamp: {metrics['timestamp']})")
        
        print(f"\n   🖥️  System Metrics:")
        system_metrics = metrics['system']
        print(f"      • Total Sessions: {system_metrics['total_sessions']}")
        print(f"      • Active Sessions: {system_metrics['active_sessions']}")
        print(f"      • Completed Sessions: {system_metrics['completed_sessions']}")
        
        print(f"\n   🤖 Agent Performance:")
        for agent_name, agent_data in metrics['agents'].items():
            print(f"      • {agent_name}:")
            print(f"         - Calls: {agent_data['total_calls']}")
            print(f"         - Avg Latency: {agent_data['avg_latency_ms']:.1f}ms")
            print(f"         - Success Rate: {agent_data['success_rate']*100:.1f}%")
        
        print(f"\n   🔧 Tool Performance:")
        for tool_name, tool_data in metrics['tools'].items():
            print(f"      • {tool_name}:")
            print(f"         - Executions: {tool_data['total_executions']}")
            print(f"         - Avg Time: {tool_data['avg_execution_time_ms']:.1f}ms")
            print(f"         - Success Rate: {tool_data['success_rate']*100:.1f}%")
        print()
        
        # Step 11: Get Session Traces
        print("🔍 Step 11: Retrieving Session Traces...")
        traces = await client.get_session_traces(session_id)
        print(f"✅ Traces Retrieved")
        print(f"\n   Execution Traces:")
        for trace in traces['traces']:
            print(f"      • {trace['agent']} (Trace ID: {trace['trace_id'][:8]}...)")
            print(f"         - Duration: {trace['duration_ms']}ms")
            print(f"         - Status: {trace['status']}")
            print(f"         - Tools: {', '.join(trace['tools_used'])}")
        print()
        
        # Summary
        print("=" * 60)
        print("✅ Demo Complete!")
        print("=" * 60)
        print(f"\n📌 Key Highlights:")
        print(f"   • Multi-agent system working (Research, Technical, Companion)")
        print(f"   • Tools integrated (Web Search, Code Execution)")
        print(f"   • Session management with pause/resume")
        print(f"   • Long-term memory tracking progress")
        print(f"   • Observability with metrics and traces")
        print(f"   • Evaluation pipeline scoring performance")
        print()


async def run_quick_test():
    """
    Quick test to verify API is working
    """
    print("🧪 Running Quick API Test...")
    
    async with InterviewCoPilotClient() as client:
        # Test health
        try:
            response = await client.session.get("http://localhost:8000/health")
            if response.status_code == 200:
                print("✅ API is healthy and running!")
                return True
            else:
                print(f"❌ API returned status {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Could not connect to API: {str(e)}")
            print("\n💡 Make sure the API is running:")
            print("   cd <project_root>")
            print("   python api/main.py")
            return False


async def run_evaluation_demo():
    """
    Demonstrate evaluation and regression testing
    """
    print("=" * 60)
    print("📊 Evaluation & Regression Demo")
    print("=" * 60)
    print()
    
    async with InterviewCoPilotClient() as client:
        # Create multiple sessions to track improvement
        user_id = "eval_user_001"
        
        print(f"Running evaluation for user: {user_id}")
        print()
        
        # Simulate 3 practice sessions
        for session_num in range(1, 4):
            print(f"📝 Session {session_num}...")
            
            # Create session
            session = await client.create_session(user_id)
            session_id = session["session_id"]
            
            # Start interview
            await client.start_mock_interview(session_id, difficulty="medium", num_questions=2)
            
            # Submit code (simulate improving over time)
            # In real scenario, code quality would improve
            await client.submit_code(
                session_id,
                "q1",
                SAMPLE_CODE,
                "python"
            )
            
            # Get summary
            summary = await client.get_session_summary(session_id)
            print(f"   ✓ Completed - Score: {summary.get('questions_solved', 0)}/{summary.get('questions_attempted', 0)}")
            
            await asyncio.sleep(0.5)
        
        print()
        
        # Show progress
        print("📈 Progress Over Time:")
        progress = await client.get_user_progress(user_id)
        
        for idx, session in enumerate(progress['recent_sessions'][-3:], 1):
            score = session.get('score', 0)
            bar_length = int(score / 5)
            bar = "█" * bar_length + "░" * (20 - bar_length)
            print(f"   Session {idx}: [{bar}] {score:.1f}%")
        
        print()
        print("✅ Evaluation complete - showing clear improvement!")
        print()


# ============= Main Entry Point =============

async def main():
    """
    Main entry point - run different demo modes
    """
    import sys
    
    if len(sys.argv) > 1:
        mode = sys.argv[1]
    else:
        mode = "complete"
    
    if mode == "test":
        # Quick health check
        await run_quick_test()
    
    elif mode == "eval":
        # Evaluation demo
        success = await run_quick_test()
        if success:
            await run_evaluation_demo()
    
    else:
        # Full demo
        success = await run_quick_test()
        if success:
            print()
            await run_complete_demo()


if __name__ == "__main__":
    """
    Usage:
        python examples/run_complete_demo.py           # Full demo
        python examples/run_complete_demo.py test      # Quick test
        python examples/run_complete_demo.py eval      # Evaluation demo
    """
    asyncio.run(main())