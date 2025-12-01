"""
ADK Configuration Module
Configuration and helper functions for Google's Agent Development Kit
"""

from google.genai import types
from config.settings import settings
import logging
import os

logger = logging.getLogger(__name__)

# Ensure GOOGLE_API_KEY is in environment for ADK/GenAI libraries
if settings.GOOGLE_API_KEY and "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_API_KEY



def get_retry_config() -> types.HttpRetryOptions:
    """
    Get HTTP retry configuration for ADK/Gemini API calls.
    
    Returns:
        HttpRetryOptions configured with settings
    """
    return types.HttpRetryOptions(
        attempts=settings.ADK_RETRY_ATTEMPTS,
        exp_base=settings.ADK_RETRY_BASE,
        initial_delay=settings.ADK_INITIAL_DELAY,
        http_status_codes=[429, 500, 503, 504]  # Rate limit and server errors
    )


def get_gemini_model(model_name: str = None, temperature: float = None):
    """
    Get configured Gemini model instance.
    
    Args:
        model_name: Optional model name override
        temperature: Optional temperature override
    
    Returns:
        Gemini model instance configured with retry options
    """
    from google.adk.models.google_llm import Gemini
    
    model = model_name or settings.ADK_MODEL
    temp = temperature if temperature is not None else settings.ADK_TEMPERATURE
    
    return Gemini(
        model=model,
        temperature=temp,
        retry_options=get_retry_config()
    )


def validate_adk_setup() -> bool:
    """
    Validate that ADK is properly configured.
    
    Returns:
        True if configuration is valid, False otherwise
    """
    if not settings.GOOGLE_API_KEY:
        logger.warning("GOOGLE_API_KEY not set. ADK features will not work.")
        return False
    
    try:
        import google.adk
        import google.genai
        logger.info("✅ ADK dependencies are installed")
        return True
    except ImportError as e:
        logger.error(f"❌ ADK dependencies not installed: {e}")
        logger.info("Install with: pip install google-adk google-genai")
        return False

