# Google API Migration Guide

## Overview

The Interview Co-Pilot now supports **Google's Gemini API** via ADK (Agent Development Kit) as the **preferred** option, with OpenAI as a fallback. This allows you to use the application with just a `GOOGLE_API_KEY` - no OpenAI API key required!

## Quick Start

### 1. Get a Google API Key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy your API key

### 2. Configure Your Environment

Add to your `.env` file:

```env
# Google API Key (Required for ADK/Gemini)
GOOGLE_API_KEY=your_google_api_key_here

# Optional: OpenAI API Key (only needed if you want to use OpenAI instead)
# OPENAI_API_KEY=your_openai_key_here
```

### 3. Start the Application

```bash
uvicorn api.main:app --reload
```

The application will automatically:
- ✅ Detect `GOOGLE_API_KEY` and use ADK/Gemini agents
- ✅ Use Google's search (no Tavily API key needed)
- ✅ Use built-in code executor (no Judge0 API key needed)
- ✅ Fall back to OpenAI only if `GOOGLE_API_KEY` is not set

## How It Works

### Automatic Detection

The application automatically detects which API keys are available and uses the appropriate agents:

1. **If `GOOGLE_API_KEY` is set** (preferred):
   - Uses ADK/Gemini agents
   - Uses Google Search (no API key needed)
   - Uses BuiltInCodeExecutor (Gemini native, no Judge0 needed)
   - Model: `gemini-2.5-flash-lite` (configurable via `ADK_MODEL`)

2. **If only `OPENAI_API_KEY` is set** (fallback):
   - Uses LangChain/OpenAI agents
   - Requires Tavily API key for search
   - Requires Judge0 API key for code execution
   - Model: `gpt-4o-mini` (configurable via `LLM_MODEL`)

3. **If neither is set**:
   - Application will fail to start with a clear error message

### Configuration

#### Google/Gemini Settings

```env
# Required
GOOGLE_API_KEY=your_key_here

# Optional - ADK/Gemini Configuration
ADK_MODEL=gemini-2.5-flash-lite  # Default model
ADK_TEMPERATURE=0.7              # Model temperature
ADK_RETRY_ATTEMPTS=5             # Retry attempts
ADK_RETRY_BASE=7                 # Retry base delay
ADK_INITIAL_DELAY=1              # Initial retry delay
```

#### OpenAI Settings (Fallback)

```env
# Optional - only needed if GOOGLE_API_KEY is not set
OPENAI_API_KEY=your_key_here
LLM_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.7
TAVILY_API_KEY=your_key_here     # Required for search
JUDGE0_API_KEY=your_key_here     # Required for code execution
```

## Benefits of Using Google API

### 1. **No Additional API Keys Needed**
   - ✅ Google Search is built-in (no Tavily needed)
   - ✅ Code execution is built-in (no Judge0 needed)
   - ✅ Just one API key: `GOOGLE_API_KEY`

### 2. **Cost Effective**
   - Gemini models are generally more cost-effective than OpenAI
   - Free tier available for testing

### 3. **Better Integration**
   - Native ADK integration
   - Better structured output support
   - More reliable code execution

### 4. **Modern Architecture**
   - Uses Google's latest Agent Development Kit
   - Better session management with PostgreSQL
   - Improved error handling and retries

## Verification

### Check Which Agents Are Being Used

When the application starts, you'll see in the logs:

**Using Google/Gemini:**
```
INFO:api.main:🚀 Using ADK/Gemini agents (GOOGLE_API_KEY detected)
INFO:api.main:Using ADK model: gemini-2.5-flash-lite
INFO:api.main:✅ ADK Research agent initialized
INFO:api.main:✅ ADK Technical agent initialized
INFO:api.main:✅ ADK Companion agent initialized
INFO:api.main:✅ ADK Orchestrator initialized
```

**Using OpenAI (Fallback):**
```
INFO:api.main:⚠️  Using LangChain/OpenAI agents (OPENAI_API_KEY detected)
INFO:api.main:Using OpenAI model: gpt-4o-mini
INFO:api.main:✅ Research agent initialized
INFO:api.main:✅ Technical agent initialized
INFO:api.main:✅ Companion agent initialized
```

### Test the API

```bash
# Health check
curl http://localhost:8000/health

# Create a session
curl -X POST http://localhost:8000/sessions/create \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user"}'

# Run research (will use Google/Gemini if GOOGLE_API_KEY is set)
curl -X POST http://localhost:8000/research/run \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "your_session_id",
    "job_description": "Software Engineer",
    "company_name": "Google"
  }'
```

## Migration from OpenAI

If you're currently using OpenAI and want to switch to Google:

1. **Get a Google API Key** (see Quick Start above)

2. **Update your `.env` file:**
   ```env
   # Add Google API key
   GOOGLE_API_KEY=your_google_key_here
   
   # Keep OpenAI key as backup (optional)
   # OPENAI_API_KEY=your_openai_key_here
   ```

3. **Restart the application:**
   ```bash
   uvicorn api.main:app --reload
   ```

4. **Verify it's using Google:**
   - Check logs for "🚀 Using ADK/Gemini agents"
   - Test the research endpoint

5. **Optional: Remove OpenAI key** once you've verified everything works

## Troubleshooting

### Error: "No API key configured"

**Solution**: Make sure `GOOGLE_API_KEY` is set in your `.env` file:
```env
GOOGLE_API_KEY=your_key_here
```

### Error: "ADK agents not available"

**Solution**: Make sure ADK is installed:
```bash
pip install google-adk>=0.1.0 google-genai>=0.2.0
```

### Application Still Using OpenAI

**Cause**: Both `GOOGLE_API_KEY` and `OPENAI_API_KEY` are set, but OpenAI is being used.

**Solution**: The application prefers Google when both are set. If you see OpenAI being used, check:
1. Is `GOOGLE_API_KEY` correctly set?
2. Check application logs for which key was detected
3. Restart the application

### Code Execution Not Working

**Cause**: Using OpenAI agents which require Judge0.

**Solution**: Switch to Google/Gemini agents which have built-in code execution:
```env
GOOGLE_API_KEY=your_key_here
```

## API Endpoints

All API endpoints work the same regardless of which agents are used:

- `POST /sessions/create` - Create a session
- `POST /research/run` - Run research agent
- `POST /technical/select-questions` - Select coding questions
- `POST /technical/evaluate-code` - Evaluate code submission
- `POST /companion/generate` - Generate encouragement/tips
- `GET /health` - Health check

The endpoints automatically use the appropriate agents based on your configuration.

## Next Steps

1. ✅ Get your Google API key
2. ✅ Add it to `.env`
3. ✅ Start the application
4. ✅ Test the research endpoint
5. ✅ Enjoy using Interview Co-Pilot with Google/Gemini!

## Additional Resources

- [Google AI Studio](https://aistudio.google.com/) - Get your API key
- [ADK Documentation](https://google.github.io/adk-docs/) - Learn about ADK
- [Gemini Models](https://ai.google.dev/models/gemini) - Available models

