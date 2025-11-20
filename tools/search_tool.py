from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import Tool
import os

def create_search_tool():
    """Create web search tool using Tavily"""
    try:
        tavily_api_key = os.getenv("TAVILY_API_KEY")
        if not tavily_api_key:
            raise ValueError("TAVILY_API_KEY not found in environment")
        
        tavily_tool = TavilySearchResults(
            api_key=tavily_api_key,
            max_results=5,
            search_depth="advanced",
            include_answer=True,
            include_raw_content=False
        )
        
        return Tool(
            name="web_search",
            description="Search the web for information about companies, interview processes, and technical topics",
            func=tavily_tool.run
        )
    except Exception as e:
        # Return a mock tool if Tavily is not available
        def mock_search(query: str) -> str:
            return f"Mock search result for: {query}. Tavily API key not configured."
        
        return Tool(
            name="web_search",
            description="Mock web search (Tavily API key not configured)",
            func=mock_search
        )