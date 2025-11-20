"""
Job Description Parser Tool
Extracts structured information from job descriptions
"""

from langchain_core.tools import Tool
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import re
import logging

logger = logging.getLogger(__name__)


class ParsedJobDescription(BaseModel):
    """
    Structured representation of a job description
    """
    job_title: str = Field(..., description="The job title/position")
    company_name: Optional[str] = Field(None, description="Company name if mentioned")
    requirements: List[str] = Field(default_factory=list, description="List of job requirements")
    skills: List[str] = Field(default_factory=list, description="Technical skills and technologies mentioned")
    experience_years: Optional[str] = Field(None, description="Required years of experience")
    responsibilities: List[str] = Field(default_factory=list, description="Job responsibilities")
    interview_process: Optional[str] = Field(None, description="Interview process steps if mentioned")
    location: Optional[str] = Field(None, description="Job location if mentioned")
    salary_range: Optional[str] = Field(None, description="Salary range if mentioned")
    benefits: List[str] = Field(default_factory=list, description="Benefits mentioned")


def extract_basic_info(jd_text: str) -> Dict[str, Any]:
    """
    Extract basic information using regex patterns
    """
    info = {
        "skills": [],
        "experience_years": None,
        "location": None
    }
    
    # Extract years of experience
    experience_patterns = [
        r'(\d+)\+?\s*years?\s*(?:of\s*)?experience',
        r'(\d+)\+?\s*years?\s*in',
        r'minimum\s*(\d+)\s*years?'
    ]
    for pattern in experience_patterns:
        match = re.search(pattern, jd_text, re.IGNORECASE)
        if match:
            info["experience_years"] = match.group(1)
            break
    
    # Extract common technologies/skills
    common_skills = [
        "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "Go", "Rust",
        "React", "Vue", "Angular", "Node.js", "Django", "Flask", "FastAPI",
        "AWS", "GCP", "Azure", "Docker", "Kubernetes", "Kafka", "Redis",
        "PostgreSQL", "MySQL", "MongoDB", "Elasticsearch", "GraphQL",
        "Machine Learning", "AI", "TensorFlow", "PyTorch", "Data Science"
    ]
    
    for skill in common_skills:
        if re.search(rf'\b{re.escape(skill)}\b', jd_text, re.IGNORECASE):
            info["skills"].append(skill)
    
    # Extract location
    location_patterns = [
        r'(?:location|based in|located in|office in):\s*([A-Za-z\s,]+)',
        r'(remote|onsite|hybrid)',
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*[A-Z]{2}'  # City, State format
    ]
    for pattern in location_patterns:
        match = re.search(pattern, jd_text, re.IGNORECASE)
        if match:
            info["location"] = match.group(1) if match.groups() else match.group(0)
            break
    
    return info


async def parse_job_description_llm(jd_text: str, llm: ChatOpenAI) -> ParsedJobDescription:
    """
    Parse job description using LLM for structured extraction
    """
    # First, extract basic info with regex
    basic_info = extract_basic_info(jd_text)
    
    # Use LLM to extract structured information
    prompt = f"""Parse the following job description and extract structured information:

Job Description:
{jd_text}

Extract:
1. Job title
2. Company name (if mentioned)
3. Requirements (list each requirement separately)
4. Technical skills and technologies
5. Years of experience required
6. Responsibilities (list each responsibility)
7. Interview process (if mentioned)
8. Location (if mentioned)
9. Salary range (if mentioned)
10. Benefits (if mentioned)

Return the information in a structured format."""

    try:
        # Use structured output if available
        if hasattr(llm, 'with_structured_output'):
            structured_llm = llm.with_structured_output(ParsedJobDescription)
            result = await structured_llm.ainvoke([
                SystemMessage(content="You are an expert at parsing job descriptions and extracting structured information."),
                HumanMessage(content=prompt)
            ])
            return result
        else:
            # Fallback: parse from text response
            response = await llm.ainvoke([
                SystemMessage(content="You are an expert at parsing job descriptions. Return a JSON object with the extracted information."),
                HumanMessage(content=prompt)
            ])
            
            # Try to extract JSON from response
            content = response.content if hasattr(response, 'content') else str(response)
            # Simple fallback - create from basic info
            return ParsedJobDescription(
                job_title=basic_info.get("job_title", "Software Engineer"),
                skills=basic_info.get("skills", []),
                experience_years=basic_info.get("experience_years"),
                location=basic_info.get("location")
            )
    except Exception as e:
        logger.error(f"Error parsing JD with LLM: {e}")
        # Fallback to basic extraction
        return ParsedJobDescription(
            job_title="Software Engineer",
            skills=basic_info.get("skills", []),
            experience_years=basic_info.get("experience_years"),
            location=basic_info.get("location")
        )


def create_jd_parser_tool(llm: ChatOpenAI = None) -> Tool:
    """
    Create a LangChain tool for parsing job descriptions
    
    Args:
        llm: Optional LLM instance for advanced parsing
    
    Returns:
        Tool instance for job description parsing
    """
    
    async def parse_jd(jd_text: str) -> str:
        """
        Parse job description and return structured information
        
        Args:
            jd_text: Job description text
        
        Returns:
            JSON string with parsed information
        """
        try:
            if llm:
                # Use LLM for advanced parsing
                parsed = await parse_job_description_llm(jd_text, llm)
                return parsed.model_dump_json(indent=2)
            else:
                # Use basic regex extraction
                basic_info = extract_basic_info(jd_text)
                # Try to extract job title (first line or after "Position:" etc.)
                title_match = re.search(r'(?:position|title|role):\s*([^\n]+)', jd_text, re.IGNORECASE)
                job_title = title_match.group(1).strip() if title_match else "Software Engineer"
                
                parsed = ParsedJobDescription(
                    job_title=job_title,
                    skills=basic_info.get("skills", []),
                    experience_years=basic_info.get("experience_years"),
                    location=basic_info.get("location")
                )
                return parsed.model_dump_json(indent=2)
        except Exception as e:
            logger.error(f"Error parsing job description: {e}")
            return f'{{"error": "Failed to parse job description: {str(e)}"}}'
    
    return Tool(
        name="parse_job_description",
        description="Parse a job description and extract structured information including job title, requirements, skills, experience, responsibilities, and other details",
        func=parse_jd
    )

