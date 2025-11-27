import asyncio
import httpx
import json
import uuid

async def test_technical_streaming():
    session_id = str(uuid.uuid4())
    user_id = "test_user"
    
    url = "http://localhost:8000/api/v2/adk/technical"
    
    payload = {
        "user_id": user_id,
        "session_id": session_id,
        "mode": "select_questions",
        "difficulty": "easy",
        "num_questions": 1,
        "job_description": "Python Developer"
    }
    
    print(f"Testing technical streaming endpoint: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", url, json=payload) as response:
                print(f"Response status: {response.status_code}")
                
                if response.status_code != 200:
                    print(f"Error: {response.status_code}")
                    content = await response.read()
                    print(content.decode())
                    return
                
                print("Streaming response:")
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = json.loads(line[6:])
                        if data["type"] == "chunk":
                            print(data["text"], end="", flush=True)
                        elif data["type"] == "complete":
                            print("\n\n[Stream Complete]")
                        elif data["type"] == "error":
                            print(f"\n\n[Stream Error]: {data['text']}")
                            
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_technical_streaming())
