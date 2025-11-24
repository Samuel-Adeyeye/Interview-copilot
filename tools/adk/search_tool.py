"""
ADK Search Tool
Uses Google's built-in google_search tool from ADK
"""

from google.adk.tools import google_search
import logging

logger = logging.getLogger(__name__)


def create_adk_search_tool():
    """
    Create web search tool using ADK's built-in google_search.
    
    This replaces the Tavily-based search tool with Google's native search.
    No API key required - uses Google's search capabilities.
    
    Returns:
        google_search tool instance (ready to use in agents)
    
    Example:
        >>> search_tool = create_adk_search_tool()
        >>> agent = LlmAgent(..., tools=[search_tool])
    """
    logger.info("✅ ADK google_search tool created (no API key needed)")
    return google_search


# For backward compatibility and easier migration
def get_search_tool():
    """Alias for create_adk_search_tool()"""
    return create_adk_search_tool()

