"""
ADK Companion Agent
Migrated from LangChain to Google's Agent Development Kit
"""

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from config.adk_config import get_gemini_model
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


def create_companion_agent(
    model: Optional[Gemini] = None,
    memory_bank = None,
    model_name: str = None
) -> LlmAgent:
    """
    Create ADK Companion Agent for personalized support.
    
    This agent provides:
    - Encouragement based on performance
    - Personalized tips for improvement
    - Session summaries
    - Recommendations for next steps
    
    Args:
        model: Optional Gemini model instance
        memory_bank: Optional memory bank for accessing user history
        model_name: Optional model name override
    
    Returns:
        LlmAgent configured for companion/support tasks
    
    Example:
        >>> agent = create_companion_agent()
        >>> # Use with Runner to generate encouragement, tips, summaries
    """
    # Get model if not provided
    if model is None:
        model = get_gemini_model(model_name)
    
    # Create agent instruction
    instruction = """You are a supportive and encouraging interview preparation companion.

Your role is to help users prepare for technical interviews by providing:

1. **Encouragement**: Generate personalized, motivating messages based on user performance
   - Acknowledge their effort and progress
   - Highlight specific achievements
   - Provide positive reinforcement
   - Be warm and genuine

2. **Tips**: Generate 3-5 specific, actionable tips for improvement
   - Focus on areas that need work
   - Be specific and practical
   - Tailor to their current performance level
   - Encourage continued practice

3. **Session Summaries**: Create comprehensive summaries of practice sessions
   - Include questions attempted and solved
   - Calculate success rate
   - Highlight key achievements
   - Note areas for improvement

4. **Recommendations**: Suggest next steps for continued improvement
   - Build on current progress
   - Address weak areas
   - Set realistic goals
   - Provide actionable next steps

When generating content:
- Be supportive and encouraging
- Be specific and actionable
- Personalize based on performance data
- Maintain a positive, motivating tone
- Help users build confidence

Always focus on growth and improvement rather than just pointing out mistakes."""

    # Note: Memory bank access would be through tools or session state
    # For now, we'll rely on the agent's instruction and context from session state
    
    agent = LlmAgent(
        name="CompanionAgent",
        model=model,
        instruction=instruction,
        tools=[],  # No tools needed - uses LLM for generation
        output_key="companion_output"
    )
    
    logger.info("✅ ADK Companion Agent created")
    return agent


def create_encouragement_agent(
    model: Optional[Gemini] = None,
    model_name: str = None
) -> LlmAgent:
    """
    Create a specialized agent for generating encouragement only.
    
    Args:
        model: Optional Gemini model instance
        model_name: Optional model name override
    
    Returns:
        LlmAgent for encouragement generation
    """
    if model is None:
        model = get_gemini_model(model_name)
    
    agent = LlmAgent(
        name="EncouragementAgent",
        model=model,
        instruction="""You are a supportive interview coach who provides personalized encouragement.

Generate brief (2-3 sentences), warm, and motivating messages that:
- Acknowledge the user's effort and progress
- Provide specific positive feedback
- Offer constructive encouragement
- Are personalized and genuine

Base your encouragement on:
- Questions attempted and solved
- Success rate
- Improvement trends
- Overall progress

Keep it concise, uplifting, and focused on growth.""",
        output_key="encouragement"
    )
    
    return agent


def create_tips_agent(
    model: Optional[Gemini] = None,
    model_name: str = None
) -> LlmAgent:
    """
    Create a specialized agent for generating tips only.
    
    Args:
        model: Optional Gemini model instance
        model_name: Optional model name override
    
    Returns:
        LlmAgent for tips generation
    """
    if model is None:
        model = get_gemini_model(model_name)
    
    agent = LlmAgent(
        name="TipsAgent",
        model=model,
        instruction="""You are an expert interview coach providing actionable improvement tips.

Generate 3-5 specific, actionable tips that are:
- Relevant to the user's current performance level
- Focused on areas that need improvement
- Specific and practical (not generic)
- Encouraging and constructive

Return tips as a numbered list, one per line.
Each tip should be clear, actionable, and directly helpful.""",
        output_key="tips"
    )
    
    return agent


def create_summary_agent(
    model: Optional[Gemini] = None,
    model_name: str = None
) -> LlmAgent:
    """
    Create a specialized agent for generating session summaries.
    
    Args:
        model: Optional Gemini model instance
        model_name: Optional model name override
    
    Returns:
        LlmAgent for summary generation
    """
    if model is None:
        model = get_gemini_model(model_name)
    
    agent = LlmAgent(
        name="SummaryAgent",
        model=model,
        instruction="""You are a session summary generator for interview practice.

Create comprehensive summaries that include:
- Questions attempted and solved
- Success rate calculation
- Duration and time spent
- Skills practiced
- Key highlights and achievements
- Areas for improvement

Format the summary as a structured, easy-to-read report.
Be concise but comprehensive.""",
        output_key="session_summary"
    )
    
    return agent


# For backward compatibility
def create_adk_companion_agent(*args, **kwargs):
    """Alias for create_companion_agent()"""
    return create_companion_agent(*args, **kwargs)

