"""
Test static analysis (without Judge0) by temporarily removing API key
"""
import asyncio
import httpx
import json
import uuid
import os

async def test_static_analysis():
    # Temporarily remove Judge0 key to force static analysis
    original_key = os.environ.get('JUDGE0_API_KEY')
    if 'JUDGE0_API_KEY' in os.environ:
        del os.environ['JUDGE0_API_KEY']
    
    url = "http://localhost:8000/api/v2/adk/technical"
    
    session_id = str(uuid.uuid4())
    
    payload = {
        "user_id": "test_user",
        "session_id": session_id,
        "mode": "evaluate_code",
        "code": "def two_sum(nums, target):\n    seen = {}\n    for i, num in enumerate(nums):\n        complement = target - num\n        if complement in seen:\n            return [seen[complement], i]\n        seen[num] = i\n    return []",
        "language": "python",
        "question_id": "q1"
    }
    
    print(f"Testing STATIC ANALYSIS (no Judge0): {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", url, json=payload) as response:
                print(f"Response status: {response.status_code}")
                print("Streaming response:")
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            if data["type"] == "chunk":
                                print(data["text"], end="", flush=True)
                            elif data["type"] == "complete":
                                print("\n\n[Stream Complete - Static Analysis]")
                            elif data["type"] == "error":
                                print(f"\n\n[Stream Error]: {data['text']}")
                        except json.JSONDecodeError:
                            print(f"\n[Invalid JSON]: {line}")
    finally:
        # Restore original key
        if original_key:
            os.environ['JUDGE0_API_KEY'] = original_key
            
if __name__ == "__main__":
    asyncio.run(test_static_analysis())
