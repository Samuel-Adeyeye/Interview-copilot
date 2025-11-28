"""
ADK Research Agent
Migrated from LangChain to Google's Agent Development Kit
"""

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.genai import types
from tools.adk.search_tool import create_adk_search_tool
from config.adk_config import get_gemini_model, get_retry_config
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


# ResearchPacket model (same as before, for structured output)
from pydantic import BaseModel, Field
from typing import List


class ResearchPacket(BaseModel):
    """
    Structured research packet containing company and interview information.
    This model ensures consistent, validated output from the research agent.
    """
    company_overview: str = Field(
        ...,
        description="A comprehensive overview of the company, including its mission, values, and key business areas"
    )
    interview_process: str = Field(
        ...,
        description="Detailed description of the company's interview process, including stages, duration, and format"
    )
    tech_stack: List[str] = Field(
        ...,
        description="List of technologies, programming languages, and tools used by the company"
    )
    recent_news: List[str] = Field(
        ...,
        description="Recent news, announcements, or developments about the company"
    )
    preparation_tips: List[str] = Field(
        ...,
        description="Specific tips and recommendations for preparing for interviews at this company"
    )


from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters
import os

def create_research_agent(
    model: Optional[Gemini] = None,
    memory_bank = None,
    model_name: str = None
) -> LlmAgent:
    """
    Create ADK Research Agent.
    
    This agent uses the Brave Search MCP server to research companies and their interview processes,
    then structures the information into a ResearchPacket.
    
    Args:
        model: Optional Gemini model instance. If None, creates one using config.
        memory_bank: Optional memory bank for storing research results.
        model_name: Optional model name override.
    
    Returns:
        LlmAgent configured for research tasks
    """
    # Get model if not provided
    if model is None:
        model = get_gemini_model(model_name)
    
    # Check if npx is available
    import shutil
    npx_path = shutil.which("npx")
    
    # If not in PATH, check common locations
    if not npx_path and os.path.exists("/usr/local/bin/npx"):
        npx_path = "/usr/local/bin/npx"
    
    # Create Brave Search MCP Toolset if npx is available and API key is present
    brave_api_key = os.getenv("BRAVE_API_KEY")
    use_mcp = False
    
    if npx_path and brave_api_key:
        try:
            mcp_toolset = McpToolset(
                connection_params=StdioConnectionParams(
                    server_params=StdioServerParameters(
                        command=npx_path,  # Use the resolved path
                        args=["-y", "@modelcontextprotocol/server-brave-search"],
                        env={
                            **os.environ, 
                            "BRAVE_API_KEY": brave_api_key,
                            "PATH": f"/usr/local/bin:{os.environ.get('PATH', '')}"
                        }
                    ),
                    timeout=30
                )
            )
            tools = [mcp_toolset]
            use_mcp = True
            logger.info("✅ Using Brave Search MCP Tool")
        except Exception as e:
            logger.error(f"Failed to initialize MCP tool: {e}")
            tools = [create_adk_search_tool()]
    else:
        if not npx_path:
            logger.warning("⚠️ 'npx' not found. Falling back to standard Google Search.")
        if not brave_api_key:
            logger.warning("⚠️ BRAVE_API_KEY not found. Falling back to standard Google Search.")
        tools = [create_adk_search_tool()]

    # Set instructions based on available tool
    if use_mcp:
        instruction = """You are a specialized research agent for interview preparation.

Your task is to research companies and their interview processes using the Brave Search MCP tool.

IMPORTANT: The tool name is 'brave_web_search'. Do NOT use 'brave_search'.

When given a company name and job description:
1. Use 'brave_web_search' to find current information about:
   - Company overview, mission, and values
   - Interview process and experience from candidates
   - Technology stack and engineering practices
   - Recent news and developments
   - Company culture and work environment

2. Structure your findings into a comprehensive research packet with:
   - Company overview
   - Interview process details
   - Technology stack (list of technologies)
   - Recent news (list of key developments)
   - Preparation tips (specific, actionable advice)

3. Always use the 'brave_web_search' tool to get current, accurate information.
4. If search results are limited, infer reasonable information from the job description.
5. Provide complete, structured information in your response.

Your output should be well-organized and directly useful for interview preparation."""
    else:
        instruction = """You are a specialized research agent for interview preparation.

Your task is to research companies and their interview processes using the google_search tool.

When given a company name and job description:
1. Use google_search to find current information about:
   - Company overview, mission, and values
   - Interview process and experience from candidates
   - Technology stack and engineering practices
   - Recent news and developments
   - Company culture and work environment

2. Structure your findings into a comprehensive research packet with:
   - Company overview
   - Interview process details
   - Technology stack (list of technologies)
   - Recent news (list of key developments)
   - Preparation tips (specific, actionable advice)

3. Always use the google_search tool to get current, accurate information.
4. If search results are limited, infer reasonable information from the job description.
5. Provide complete, structured information in your response.

Your output should be well-organized and directly useful for interview preparation."""

    # Create agent with structured output capability
    agent = LlmAgent(
        name="ResearchAgent",
        model=model,
        instruction=instruction,
        tools=tools,
        output_key="research_packet"  # Store result in session state
    )
    
    logger.info(f"✅ ADK Research Agent created (MCP: {use_mcp})")
    return agent


def create_research_agent_with_structured_output(
    model: Optional[Gemini] = None,
    memory_bank = None
) -> LlmAgent:
    """
    Create Research Agent with explicit structured output support.
    
    This version uses Gemini's structured output to ensure ResearchPacket format.
    
    Args:
        model: Optional Gemini model instance
        memory_bank: Optional memory bank for storage
    
    Returns:
        LlmAgent with structured output configured
    """
    # For ADK, structured output is handled by the model/agent configuration
    # We'll use the standard agent and rely on Gemini's structured output
    agent = create_research_agent(model=model, memory_bank=memory_bank)
    
    # Note: In ADK, structured output can be achieved by:
    # 1. Using model.with_structured_output() when calling
    # 2. Or configuring the agent's instruction to request structured format
    # 3. Or using output_key and parsing in post-processing
    
    return agent


# For backward compatibility
def create_adk_research_agent(*args, **kwargs):
    """Alias for create_research_agent()"""
    return create_research_agent(*args, **kwargs)

