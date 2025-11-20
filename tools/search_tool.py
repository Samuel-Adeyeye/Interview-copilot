from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.tools import Tool

def create_search_tool():
    """Create web search tool using Tavily"""
    tavily_tool = TavilySearchResults(
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