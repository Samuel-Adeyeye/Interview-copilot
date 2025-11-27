import asyncio
import httpx
import json
import uuid

async def test_technical_evaluation():
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
    
    print(f"Testing technical evaluation endpoint: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
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
                            print("\n\n[Stream Complete]")
                        elif data["type"] == "error":
                            print(f"\n\n[Stream Error]: {data['text']}")
                    except json.JSONDecodeError:
                        print(f"\n[Invalid JSON]: {line}")
            
if __name__ == "__main__":
    asyncio.run(test_technical_evaluation())
