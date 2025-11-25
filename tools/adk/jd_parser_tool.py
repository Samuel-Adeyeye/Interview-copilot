"""
ADK Job Description Parser Tool
Converts JD parser to ADK FunctionTool
"""

from google.adk.tools import FunctionTool
from tools.jd_parser_tool import extract_basic_info, ParsedJobDescription
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


def parse_job_description_basic(jd_text: str) -> Dict[str, Any]:
    """
    Parse job description using basic regex extraction.
    
    This tool extracts basic information from job descriptions using
    pattern matching. Fast but limited - use parse_job_description_advanced
    for comprehensive extraction.
    
    Args:
        jd_text: The full text of the job description
    
    Returns:
        Dictionary with extracted information:
        {
            "status": "success" | "error",
            "skills": List[str],
            "experience_years": str | None,
            "location": str | None,
            "error_message": str (if error)
        }
    """
    try:
        info = extract_basic_info(jd_text)
        
        return {
            "status": "success",
            "skills": info.get("skills", []),
            "experience_years": info.get("experience_years"),
            "location": info.get("location")
        }
    except Exception as e:
        logger.error(f"Error parsing job description: {e}")
        return {
            "status": "error",
            "error_message": str(e),
            "skills": [],
            "experience_years": None,
            "location": None
        }


def parse_job_description_advanced(
    jd_text: str,
    use_llm: bool = True,
    llm_model=None
) -> Dict[str, Any]:
    """
    Parse job description using advanced LLM-based extraction.
    
    This tool uses an LLM to extract comprehensive structured information
    from job descriptions. More accurate than basic parsing but requires
    an LLM model.
    
    Args:
        jd_text: The full text of the job description
        use_llm: If True, use LLM for extraction. If False, use basic parsing.
        llm_model: Optional LLM model instance (if None, will use Gemini)
    
    Returns:
        Dictionary with parsed job description:
        {
            "status": "success" | "error",
            "parsed_jd": ParsedJobDescription | Dict,
            "error_message": str (if error)
        }
    
    Note:
        For ADK agents, the LLM extraction will be handled by the agent itself
        using structured output. This function provides a fallback.
    """
    try:
        if use_llm and llm_model:
            # Use LLM for advanced parsing
            # Note: In ADK, this is typically done by the agent with structured output
            # This is a compatibility wrapper
            from tools.jd_parser_tool import parse_job_description_llm
            import asyncio
            
            parsed = asyncio.run(parse_job_description_llm(jd_text, llm_model))
            
            return {
                "status": "success",
                "parsed_jd": parsed.dict() if hasattr(parsed, 'dict') else parsed
            }
        else:
            # Fall back to basic parsing
            return parse_job_description_basic(jd_text)
            
    except Exception as e:
        logger.error(f"Error in advanced JD parsing: {e}")
        # Fall back to basic parsing
        return parse_job_description_basic(jd_text)


def create_jd_parser_tools() -> List[FunctionTool]:
    """
    Create job description parser tools as ADK FunctionTools.
    
    Returns:
        List of FunctionTool instances for JD parsing
    """
    tools = [
        FunctionTool(parse_job_description_basic),
        # Advanced parsing is typically handled by agents with structured output
        # but we provide the tool for compatibility
    ]
    
    logger.info(f"✅ Created {len(tools)} JD parser tools")
    return tools


def get_jd_parser_tool() -> FunctionTool:
    """Get basic JD parser tool"""
    return FunctionTool(parse_job_description_basic)

