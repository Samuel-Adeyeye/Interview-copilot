"""
ADK Agents Module
Agent implementations using Google's Agent Development Kit

This module provides ADK-compatible versions of all Interview Co-Pilot agents.
"""

from agents.adk.research_agent import (
    create_research_agent,
    create_research_agent_with_structured_output,
    create_adk_research_agent,
    ResearchPacket
)
from agents.adk.technical_agent import (
    create_technical_agent,
    create_question_selection_agent,
    create_code_evaluation_agent,
    create_adk_technical_agent
)
from agents.adk.companion_agent import (
    create_companion_agent,
    create_encouragement_agent,
    create_tips_agent,
    create_summary_agent,
    create_adk_companion_agent
)
from agents.adk.orchestrator import (
    ADKOrchestrator,
    create_adk_orchestrator
)

__all__ = [
    # Research Agent
    "create_research_agent",
    "create_research_agent_with_structured_output",
    "create_adk_research_agent",
    "ResearchPacket",
    
    # Technical Agent
    "create_technical_agent",
    "create_question_selection_agent",
    "create_code_evaluation_agent",
    "create_adk_technical_agent",
    
    # Companion Agent
    "create_companion_agent",
    "create_encouragement_agent",
    "create_tips_agent",
    "create_summary_agent",
    "create_adk_companion_agent",
    
    # Orchestrator
    "ADKOrchestrator",
    "create_adk_orchestrator",
]
