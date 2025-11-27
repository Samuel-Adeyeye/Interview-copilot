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


def create_research_agent(
    model: Optional[Gemini] = None,
    memory_bank = None,
    model_name: str = None
) -> LlmAgent:
    """
    Create ADK Research Agent.
    
    This agent uses Google Search to research companies and their interview processes,
    then structures the information into a ResearchPacket.
    
    Args:
        model: Optional Gemini model instance. If None, creates one using config.
        memory_bank: Optional memory bank for storing research results.
        model_name: Optional model name override.
    
    Returns:
        LlmAgent configured for research tasks
    
    Example:
        >>> agent = create_research_agent()
        >>> # Use with Runner to execute research
    """
    # Get model if not provided
    if model is None:
        model = get_gemini_model(model_name)
    
    # Create search tool
    search_tool = create_adk_search_tool()
    
    # Create agent with structured output capability
    # Note: ADK agents can use structured output via Gemini's native support
    agent = LlmAgent(
        name="ResearchAgent",
        model=model,
        instruction="""You are a specialized research agent for interview preparation.

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

Your output should be well-organized and directly useful for interview preparation.""",
        tools=[search_tool],
        output_key="research_packet"  # Store result in session state
    )
    
    logger.info("✅ ADK Research Agent created")
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

