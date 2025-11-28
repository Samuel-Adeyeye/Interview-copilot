# User Migration Guide: LangChain to ADK

This guide helps users migrate from the legacy LangChain-based API to the new ADK-based API.

---

## Quick Migration

### For API Users

**Before (Legacy)**:
```python
POST /api/v1/research
{
    "session_id": "...",
    "job_description": "...",
    "company_name": "..."
}
```

**After (ADK)**:
```python
POST /api/v2/adk/research
{
    "session_id": "...",
    "user_id": "...",  # NEW: Required
    "company_name": "...",
    "job_description": "..."
}
```

### Key Changes

1. **New Endpoint Path**: `/api/v2/adk/*` instead of `/api/v1/*`
2. **Required `user_id`**: All requests now require `user_id`
3. **Streaming Responses**: Responses use Server-Sent Events (SSE)
4. **Event Format**: Responses are streamed as events

---

## Detailed Migration

### 1. Research Endpoint

#### Legacy
```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/research",
    json={
        "session_id": "session_123",
        "job_description": "Software Engineer...",
        "company_name": "Google"
    }
)

data = response.json()
research_packet = data["research_packet"]
```

#### ADK (New)
```python
import httpx
import json

response = httpx.post(
    "http://localhost:8000/api/v2/adk/research",
    json={
        "session_id": "session_123",
        "user_id": "user_456",  # NEW: Required
        "company_name": "Google",
        "job_description": "Software Engineer..."
    }
)

# Stream results
full_response = ""
for line in response.iter_lines():
    if line.startswith("data: "):
        event = json.loads(line[6:])
        if event["type"] == "chunk":
            full_response += event["text"]
        elif event["type"] == "complete":
            # Final response
            break
```

### 2. Technical Endpoint

#### Legacy: Question Selection
```python
POST /api/v1/technical/select-questions
{
    "session_id": "...",
    "difficulty": "medium",
    "num_questions": 3
}
```

#### ADK: Question Selection
```python
POST /api/v2/adk/technical
{
    "session_id": "...",
    "user_id": "...",  # NEW: Required
    "mode": "select_questions",  # NEW: Mode parameter
    "difficulty": "medium",
    "num_questions": 3
}
```

#### Legacy: Code Evaluation
```python
POST /api/v1/technical/evaluate-code
{
    "session_id": "...",
    "question_id": "q1",
    "code": "...",
    "language": "python"
}
```

#### ADK: Code Evaluation
```python
POST /api/v2/adk/technical
{
    "session_id": "...",
    "user_id": "...",  # NEW: Required
    "mode": "evaluate_code",  # NEW: Mode parameter
    "question_id": "q1",
    "code": "...",
    "language": "python"
}
```

### 3. Full Workflow

#### Legacy
```python
# Multiple separate calls
research = requests.post("/api/v1/research", ...)
questions = requests.post("/api/v1/technical/select-questions", ...)
```

#### ADK
```python
# Single workflow call
response = httpx.post(
    "http://localhost:8000/api/v2/adk/workflow",
    json={
        "session_id": "session_123",
        "user_id": "user_456",
        "company_name": "Google",
        "job_description": "...",
        "mode": "select_questions",
        "difficulty": "medium",
        "num_questions": 3
    }
)

# Stream all results
for line in response.iter_lines():
    if line.startswith("data: "):
        event = json.loads(line[6:])
        print(event["text"])
```

---

## Client Library Examples

### Python Client

```python
import httpx
import json

class InterviewCoPilotClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.Client()
    
    def research(self, session_id: str, user_id: str, company_name: str, job_description: str):
        """Run research agent"""
        response = self.client.post(
            f"{self.base_url}/api/v2/adk/research",
            json={
                "session_id": session_id,
                "user_id": user_id,
                "company_name": company_name,
                "job_description": job_description
            },
            timeout=60.0
        )
        
        # Stream results
        full_response = ""
        for line in response.iter_lines():
            if line.startswith("data: "):
                event = json.loads(line[6:])
                if event["type"] == "chunk":
                    full_response += event["text"]
                elif event["type"] == "complete":
                    break
        
        return full_response
    
    def select_questions(self, session_id: str, user_id: str, difficulty: str = "medium", num_questions: int = 3):
        """Select coding questions"""
        response = self.client.post(
            f"{self.base_url}/api/v2/adk/technical",
            json={
                "session_id": session_id,
                "user_id": user_id,
                "mode": "select_questions",
                "difficulty": difficulty,
                "num_questions": num_questions
            },
            timeout=60.0
        )
        
        # Process streaming response
        # ... (similar to research)
    
    def evaluate_code(self, session_id: str, user_id: str, question_id: str, code: str, language: str = "python"):
        """Evaluate code submission"""
        response = self.client.post(
            f"{self.base_url}/api/v2/adk/technical",
            json={
                "session_id": session_id,
                "user_id": user_id,
                "mode": "evaluate_code",
                "question_id": question_id,
                "code": code,
                "language": language
            },
            timeout=60.0
        )
        
        # Process streaming response
        # ... (similar to research)

# Usage
client = InterviewCoPilotClient()
research = client.research(
    session_id="session_123",
    user_id="user_456",
    company_name="Google",
    job_description="Software Engineer..."
)
```

### JavaScript/TypeScript Client

```typescript
class InterviewCoPilotClient {
    constructor(private baseUrl: string = "http://localhost:8000") {}
    
    async research(
        sessionId: string,
        userId: string,
        companyName: string,
        jobDescription: string
    ): Promise<string> {
        const response = await fetch(`${this.baseUrl}/api/v2/adk/research`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                session_id: sessionId,
                user_id: userId,
                company_name: companyName,
                job_description: jobDescription
            })
        });
        
        const reader = response.body?.getReader();
        const decoder = new TextDecoder();
        let fullResponse = "";
        
        while (true) {
            const { done, value } = await reader!.read();
            if (done) break;
            
            const chunk = decoder.decode(value);
            const lines = chunk.split("\n");
            
            for (const line of lines) {
                if (line.startsWith("data: ")) {
                    const event = JSON.parse(line.slice(6));
                    if (event.type === "chunk") {
                        fullResponse += event.text;
                    } else if (event.type === "complete") {
                        return fullResponse;
                    }
                }
            }
        }
        
        return fullResponse;
    }
}
```

---

## Migration Checklist

- [ ] Update API endpoint URLs (`/api/v1/*` → `/api/v2/adk/*`)
- [ ] Add `user_id` to all requests
- [ ] Update request formats (add `mode` for technical endpoint)
- [ ] Implement streaming response handling (SSE)
- [ ] Update error handling for new response format
- [ ] Test all endpoints
- [ ] Update documentation
- [ ] Deploy updated client code

---

## Breaking Changes

### 1. Endpoint URLs
- **Before**: `/api/v1/research`
- **After**: `/api/v2/adk/research`

### 2. Required Fields
- **Before**: `session_id` only
- **After**: `session_id` + `user_id` required

### 3. Response Format
- **Before**: JSON response
- **After**: Streaming SSE events

### 4. Technical Endpoint
- **Before**: Separate endpoints (`/select-questions`, `/evaluate-code`)
- **After**: Single endpoint with `mode` parameter

---

## Backward Compatibility

Legacy endpoints (`/api/v1/*`) remain available but are **deprecated**:

- They will be removed in a future release
- No new features will be added
- Bug fixes will be limited
- **Recommendation**: Migrate to ADK endpoints as soon as possible

---

## Support

For migration assistance:

1. Review [ADK Migration Summary](ADK_MIGRATION_SUMMARY.md)
2. Check [ADK API Documentation](http://localhost:8000/docs)
3. Review [Phase 6: Runner & App](PHASE6_RUNNER_APP_MIGRATION.md)
4. Open an issue in the repository

---

**Last Updated**: 2025-01-20

