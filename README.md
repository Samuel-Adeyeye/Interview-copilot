# Interview Co-Pilot

A multi-agent AI system for interview preparation, powered by Google's Agent Development Kit (ADK).

## 🚀 Features

- **Company Research**: Automated research on companies and their interview processes
- **Technical Interviews**: Coding question selection and code evaluation
- **Personalized Support**: Encouragement, tips, and progress tracking
- **Session Management**: Persistent session storage and history
- **Memory System**: Long-term memory for user progress and preferences

## 🏗️ Architecture

### ADK-Based Architecture (Current)

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Backend                       │
├─────────────────────────────────────────────────────────┤
│  ADK App & Runner                                       │
│    ├── SequentialAgent (Orchestrator)                  │
│    │    ├── ResearchAgent (LlmAgent + google_search)   │
│    │    ├── TechnicalAgent (LlmAgent + code exec)      │
│    │    └── CompanionAgent (LlmAgent)                  │
│    └── Session & Memory Services                        │
├─────────────────────────────────────────────────────────┤
│  ADK Tools                                              │
│    ├── google_search (built-in)                        │
│    ├── BuiltInCodeExecutor / Judge0                    │
│    ├── QuestionBank (FunctionTool)                      │
│    └── JDParser (FunctionTool)                         │
└─────────────────────────────────────────────────────────┘
```

### Key Technologies

- **Google ADK**: Agent Development Kit for building AI agents
- **Gemini**: Google's advanced language models
- **FastAPI**: Modern Python web framework
- **Streamlit**: Interactive UI framework
- **Pydantic**: Data validation and settings

## 📦 Installation

### Prerequisites

- Python 3.11+ (for local development)
- Docker and Docker Compose (for containerized deployment)
- Google API Key (for Gemini/ADK) - [Get one here](https://makersuite.google.com/app/apikey)
- (Optional) Judge0 API Key (for multi-language code execution)

### Quick Start with Docker (Recommended)

```bash
# 1. Clone repository
git clone <repository-url>
cd Interview-copilot

# 2. Create .env file with your API keys
cp .env.example .env
# Edit .env and add: GOOGLE_API_KEY=your_key_here

# 3. Start all services
docker-compose up -d

# 4. Verify installation
curl http://localhost:8000/health
curl http://localhost:8000/api/v2/adk/health
```

See [DOCKER_QUICKSTART.md](DOCKER_QUICKSTART.md) for detailed Docker setup instructions.

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Interview-copilot
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

   Required variables:
   ```bash
   GOOGLE_API_KEY=your-google-api-key
   # Optional:
   JUDGE0_API_KEY=your-judge0-key  # For multi-language code execution
   ```

5. **Initialize data**
   ```bash
   # Ensure data/questions_bank.json exists
   mkdir -p data
   ```

## 🚀 Quick Start

### Start the API Server

```bash
# Development
uvicorn api.main:app --reload --port 8000

# Production
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### Start the UI

```bash
streamlit run ui/streamlit_app.py
```

### Access the Application

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **ADK Endpoints**: http://localhost:8000/api/v2/adk/*
- **UI**: http://localhost:8501

### Using Docker (Alternative)

```bash
# Quick start with Docker
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

See [DOCKER_QUICKSTART.md](DOCKER_QUICKSTART.md) for detailed instructions.

## 📡 API Endpoints

### ADK Endpoints (v2)

- `POST /api/v2/adk/research` - Run research agent
- `POST /api/v2/adk/technical` - Run technical agent
- `POST /api/v2/adk/workflow` - Run full workflow
- `GET /api/v2/adk/health` - Health check

### Legacy Endpoints (v1)

- `POST /api/v1/sessions` - Create session
- `POST /api/v1/research` - Research (legacy)
- `POST /api/v1/technical/select-questions` - Select questions (legacy)
- `POST /api/v1/technical/evaluate-code` - Evaluate code (legacy)

See [API Documentation](http://localhost:8000/docs) for full details.

## 🧪 Testing

### Run All Tests

```bash
pytest tests/ -v
```

### Run ADK Tests Only

```bash
pytest tests/test_adk_*.py -v
```

### Run with Coverage

```bash
pytest tests/ --cov=. --cov-report=html
```

### Test Categories

```bash
# Unit tests
pytest tests/ -m unit -v

# Integration tests
pytest tests/ -m integration -v

# API tests
pytest tests/ -m api -v
```

## 📚 Documentation

### ADK Migration Documentation

- [ADK Migration Plan](docs/ADK_MIGRATION_PLAN.md) - Complete migration strategy
- [ADK Quick Reference](docs/ADK_QUICK_REFERENCE.md) - Quick reference guide
- [ADK Setup Guide](docs/ADK_SETUP_GUIDE.md) - Setup instructions
- [ADK Installation Troubleshooting](docs/ADK_INSTALLATION_TROUBLESHOOTING.md) - Troubleshooting guide

### Phase Documentation

- [Phase 1: Foundation](docs/ADK_SETUP_GUIDE.md) - Foundation setup
- [Phase 2: Tool Migration](docs/PHASE2_TOOL_MIGRATION.md) - Tools migration
- [Phase 3: Agent Migration](docs/PHASE3_AGENT_MIGRATION.md) - Agents migration
- [Phase 4: Orchestrator Migration](docs/PHASE4_ORCHESTRATOR_MIGRATION.md) - Orchestrator migration
- [Phase 5: Session & Memory](docs/PHASE5_SESSION_MEMORY_MIGRATION.md) - Services migration
- [Phase 6: Runner & App](docs/PHASE6_RUNNER_APP_MIGRATION.md) - Integration
- [Phase 7: Testing](docs/PHASE7_TESTING.md) - Testing strategy

### Comparison Guides

- [Tool Migration Comparison](docs/TOOL_MIGRATION_COMPARISON.md)
- [Agent Migration Comparison](docs/AGENT_MIGRATION_COMPARISON.md)
- [Orchestrator Migration Comparison](docs/ORCHESTRATOR_MIGRATION_COMPARISON.md)

### Other Documentation

- [Testing Guide](docs/TESTING.md) - Testing strategy
- [Docker Quick Start](DOCKER_QUICKSTART.md) - Quick Docker setup guide
- [Docker Setup](docs/DOCKER_SETUP.md) - Complete Docker configuration
- [Error Handling](docs/ERROR_HANDLING.md) - Error handling patterns

## 🏃 Usage Examples

### Using ADK API

```python
import httpx

# Research a company
response = httpx.post(
    "http://localhost:8000/api/v2/adk/research",
    json={
        "session_id": "session_123",
        "user_id": "user_456",
        "company_name": "Google",
        "job_description": "Software Engineer position..."
    }
)

# Stream results
for line in response.iter_lines():
    if line.startswith("data: "):
        data = json.loads(line[6:])
        print(data["text"])
```

### Using ADK Agents Directly

```python
from agents.adk import create_research_agent
from google.adk.runners import InMemoryRunner
from google.genai import types

# Create agent
agent = create_research_agent()

# Create runner
runner = InMemoryRunner(agent=agent)

# Run agent
query = types.Content(
    role="user",
    parts=[types.Part(text="Research Google's interview process")]
)

async for event in runner.run_async(
    user_id="user_123",
    session_id="session_456",
    new_message=query
):
    if event.content and event.content.parts:
        print(event.content.parts[0].text)
```

## 🔧 Configuration

### Environment Variables

```bash
# Required
GOOGLE_API_KEY=your-api-key

# ADK Configuration
ADK_LLM_MODEL=gemini-2.5-flash-lite
ADK_LLM_TEMPERATURE=0.7
ADK_RETRY_ATTEMPTS=5

# Session Configuration
SESSION_PERSISTENCE_ENABLED=true
SESSION_STORAGE_TYPE=database  # or "file"
SESSION_STORAGE_PATH=sqlite:///sessions.db

# Memory Configuration
MEMORY_SERVICE_TYPE=in_memory  # or "vertex_ai"
GCP_PROJECT_ID=your-project-id  # For Vertex AI
GCP_LOCATION=us-central1
MEMORY_BANK_ID=interview-copilot-memory

# Optional
JUDGE0_API_KEY=your-judge0-key  # For multi-language code execution
```

See `config/settings.py` for all configuration options.

## 🗂️ Project Structure

```
Interview-copilot/
├── agents/
│   ├── adk/              # ADK agents (new)
│   │   ├── research_agent.py
│   │   ├── technical_agent.py
│   │   ├── companion_agent.py
│   │   └── orchestrator.py
│   ├── research_agent.py    # Legacy (LangChain)
│   ├── technical_agent.py   # Legacy (LangChain)
│   └── companion_agent.py    # Legacy (LangChain)
├── api/
│   ├── adk_app.py        # ADK App setup
│   ├── adk_endpoints.py  # ADK API endpoints
│   └── main.py           # Main API (legacy + ADK)
├── tools/
│   ├── adk/              # ADK tools (new)
│   │   ├── search_tool.py
│   │   ├── code_exec_tool.py
│   │   ├── question_bank_tool.py
│   │   └── jd_parser_tool.py
│   └── ...               # Legacy tools
├── memory/
│   ├── adk/              # ADK services (new)
│   │   ├── session_service.py
│   │   └── memory_service.py
│   └── ...               # Legacy services
├── config/
│   ├── adk_config.py     # ADK configuration
│   └── settings.py       # Application settings
├── tests/
│   ├── test_adk_*.py     # ADK tests
│   └── ...               # Legacy tests
├── docs/                 # Documentation
└── ui/                   # Streamlit UI
```

## 🔄 Migration Status

### ✅ Completed Phases

- ✅ **Phase 1**: Foundation setup
- ✅ **Phase 2**: Tool migration
- ✅ **Phase 3**: Agent migration
- ✅ **Phase 4**: Orchestrator migration
- ✅ **Phase 5**: Session & Memory migration
- ✅ **Phase 6**: Runner & App integration
- ✅ **Phase 7**: Testing
- ✅ **Phase 8**: Documentation

### Current Status

The ADK migration is **complete**. Both legacy (LangChain) and new (ADK) implementations coexist:

- **ADK Endpoints**: `/api/v2/adk/*` (recommended)
- **Legacy Endpoints**: `/api/v1/*` (deprecated, will be removed)

## 🛠️ Development

### Adding New Agents

```python
from agents.adk import create_research_agent
from google.adk.agents import LlmAgent
from config.adk_config import get_gemini_model

def create_custom_agent():
    return LlmAgent(
        name="CustomAgent",
        model=get_gemini_model(),
        instruction="Your agent instructions...",
        tools=[...],
        output_key="custom_output"
    )
```

### Adding New Tools

```python
from google.adk.tools import FunctionTool

def my_tool_function(param: str) -> dict:
    """Tool description for LLM."""
    return {"status": "success", "result": ...}

my_tool = FunctionTool(my_tool_function)
```

## 🐛 Troubleshooting

### ADK Installation Issues

See [ADK Installation Troubleshooting](docs/ADK_INSTALLATION_TROUBLESHOOTING.md)

### Common Issues

1. **Import Errors**: Ensure ADK is installed: `pip install google-adk google-genai`
2. **API Key Errors**: Check `GOOGLE_API_KEY` is set in `.env`
3. **Session Errors**: Verify session service is initialized
4. **Memory Errors**: Check memory service configuration

## 📝 License

[Your License Here]

## 🤝 Contributing

[Contributing Guidelines]

## 📧 Contact

[Contact Information]

---

**Last Updated**: 2025-11-27  
**Version**: 2.0 (ADK Migration Complete)

