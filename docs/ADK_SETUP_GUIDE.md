# ADK Setup Guide

## Prerequisites

Before starting the ADK migration, ensure you have:

1. **Google API Key** - Get one from [Google AI Studio](https://aistudio.google.com/app/api-keys)
2. **Python 3.11+** - ADK requires Python 3.11 or higher
3. **Git Branch** - You're on the `migrating-to-adk` branch ✅

## Environment Variables

Add the following to your `.env` file:

```bash
# Google ADK API Key (REQUIRED for ADK)
GOOGLE_API_KEY=your_google_api_key_here

# Legacy API Keys (still needed during migration)
OPENAI_API_KEY=your_openai_key_here
TAVILY_API_KEY=your_tavily_key_here  # Optional - ADK uses google_search
JUDGE0_API_KEY=your_judge0_key_here  # Optional - can use BuiltInCodeExecutor

# ADK Configuration (optional - defaults provided)
ADK_MODEL=gemini-2.5-flash-lite
ADK_TEMPERATURE=0.7
ADK_RETRY_ATTEMPTS=5
ADK_RETRY_BASE=7
ADK_INITIAL_DELAY=1
```

## Installation Steps

1. **Install ADK Dependencies**
   ```bash
   pip install google-adk google-genai
   ```

   Or install all requirements:
   ```bash
   pip install -r requirements.txt
   ```

2. **Verify Installation**
   ```python
   from config.adk_config import validate_adk_setup
   validate_adk_setup()  # Should return True
   ```

3. **Test Google API Key**
   ```python
   import os
   from google.adk.models.google_llm import Gemini
   
   os.environ["GOOGLE_API_KEY"] = "your_key_here"
   model = Gemini(model="gemini-2.5-flash-lite")
   # If no error, key is valid
   ```

## Project Structure

After Phase 1 setup, you'll have:

```
agents/
  ├── adk/              # New ADK agents (Phase 3)
  │   └── __init__.py
  ├── base_agent.py     # Legacy (to be deprecated)
  ├── research_agent.py # Legacy (to be migrated)
  └── ...

tools/
  ├── adk/              # New ADK tools (Phase 2)
  │   └── __init__.py
  ├── search_tool.py    # Legacy (to be migrated)
  └── ...

config/
  ├── adk_config.py     # ADK configuration helpers
  └── settings.py       # Updated with ADK settings
```

## Next Steps

1. ✅ **Phase 1 Complete**: Foundation setup done
2. **Phase 2**: Migrate tools to ADK
3. **Phase 3**: Migrate agents to ADK
4. Continue with remaining phases...

## Troubleshooting

### Issue: `google-adk` not found
**Solution**: `pip install google-adk google-genai`

### Issue: `GOOGLE_API_KEY` not set
**Solution**: Add to `.env` file and ensure it's loaded

### Issue: Import errors
**Solution**: Ensure you're using Python 3.11+ and all dependencies are installed

## Resources

- [ADK Documentation](https://google.github.io/adk-docs/)
- [Google AI Studio](https://aistudio.google.com/app/api-keys)
- [Migration Plan](./ADK_MIGRATION_PLAN.md)
- [Quick Reference](./ADK_QUICK_REFERENCE.md)

