# Note: AgentExecutor and create_openai_tools_agent are not used in this implementation
# We use langgraph.prebuilt.create_react_agent instead
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from agents.base_agent import BaseAgent, AgentContext, AgentResult
from pydantic import BaseModel, Field
from typing import List
import time
import logging

logger = logging.getLogger(__name__)


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


class ResearchAgentStructured(BaseAgent):
    """
    Research Agent with structured output using Pydantic.
    
    This is the BEST approach for production because:
    - Guaranteed structured output
    - Type safety
    - Easy to parse and use downstream
    - Validation built-in
    """
    
    def __init__(self, llm: ChatOpenAI, memory_bank):
        from langgraph.prebuilt import create_react_agent
        import os
        
        # Create search tool with proper API key handling
        try:
            tavily_api_key = os.getenv("TAVILY_API_KEY")
            if tavily_api_key:
                search_tool = TavilySearchResults(
                    api_key=tavily_api_key,
                    max_results=5,
                    search_depth="advanced"
                )
            else:
                # Create a mock tool if API key is missing
                from langchain_core.tools import Tool
                def mock_search(query: str) -> str:
                    return f"Mock search: {query}. Tavily API key not configured."
                search_tool = Tool(name="web_search", description="Mock search", func=mock_search)
        except Exception as e:
            logger.warning(f"Failed to create Tavily search tool: {e}")
            from langchain_core.tools import Tool
            def mock_search(query: str) -> str:
                return f"Mock search: {query}. Search tool unavailable."
            search_tool = Tool(name="web_search", description="Mock search", func=mock_search)
        
        super().__init__("ResearchAgent", llm, tools=[search_tool])
        self.memory_bank = memory_bank
        
        # Create LLM with structured output
        self.structured_llm = llm.with_structured_output(ResearchPacket)
        
        # Create ReAct agent for research
        # Use prompt parameter for system instructions
        self.research_agent = create_react_agent(
            llm,
            [search_tool],
            prompt="You are a research assistant. Search the web to gather information about companies and their interview processes."
        )
    
    async def run(self, context: AgentContext) -> AgentResult:
        """
        Execute research with structured output.
        
        Args:
            context: AgentContext containing session_id, user_id, and inputs
                Required inputs:
                - job_description: str - The job description text
                - company_name: str - The company name to research
        
        Returns:
            AgentResult with structured research packet or error information
        """
        start_time = time.time()
        
        try:
            # Input validation
            if not context.inputs:
                raise ValueError("Context inputs cannot be empty")
            
            jd_text = context.inputs.get("job_description", "").strip()
            company_name = context.inputs.get("company_name", "").strip()
            
            # Validate required inputs
            if not company_name:
                raise ValueError("company_name is required in context inputs")
            if not jd_text:
                raise ValueError("job_description is required in context inputs")
            
            if not context.session_id:
                raise ValueError("session_id is required in context")
            if not context.user_id:
                raise ValueError("user_id is required in context")
            
            # Step 1: Gather raw research using ReAct agent
            search_query = f"""Research {company_name} and gather information about:
- Company overview and recent news
- Interview process and experience
- Technology stack and engineering practices
- Company culture and values

Job Description context:
{jd_text[:500]}{'...' if len(jd_text) > 500 else ''}"""

            try:
                research_result = await self.research_agent.ainvoke({
                    "messages": [HumanMessage(content=search_query)]
                })
                
                if not research_result or "messages" not in research_result:
                    raise ValueError("Invalid response from research agent")
                
                raw_research = research_result["messages"][-1].content
                
                if not raw_research or not raw_research.strip():
                    raise ValueError("Empty research results from search agent")
                    
            except Exception as search_error:
                # If search fails, create a basic research packet with available info
                raw_research = f"Limited information available for {company_name}. Job description: {jd_text[:200]}..."
                # Log the error but continue with limited data
                logger.warning(f"Search failed for {company_name}: {str(search_error)}")
            
            # Step 2: Structure the research using LLM with structured output
            structure_prompt = f"""Based on this research about {company_name}, create a structured research packet:

Raw Research:
{raw_research}

Job Description:
{jd_text}

Extract and organize the information into the required format. If information is not available, provide reasonable defaults based on the job description and company name."""

            try:
                structured_packet = await self.structured_llm.ainvoke([
                    SystemMessage(content="You are an expert at structuring interview research. Always provide complete information in the required format, even if some details need to be inferred from available context."),
                    HumanMessage(content=structure_prompt)
                ])
                
                # Validate structured output
                if not isinstance(structured_packet, ResearchPacket):
                    raise ValueError("Structured output is not a ResearchPacket instance")
                
                # Convert Pydantic model to dict
                research_packet = structured_packet.model_dump()
                
                # Validate research packet has required fields
                required_fields = ["company_overview", "interview_process", "tech_stack", "recent_news", "preparation_tips"]
                for field in required_fields:
                    if field not in research_packet:
                        raise ValueError(f"Missing required field in research packet: {field}")
                
            except Exception as struct_error:
                # Fallback: create a basic research packet
                logger.warning(f"Structure parsing failed for {company_name}: {str(struct_error)}")
                research_packet = {
                    "company_overview": f"Information about {company_name} based on job description",
                    "interview_process": "Standard technical interview process (details to be researched)",
                    "tech_stack": [],
                    "recent_news": [],
                    "preparation_tips": ["Review the job description requirements", "Practice relevant technical skills"]
                }
            
            # Store in memory (with error handling)
            try:
                if self.memory_bank:
                    await self.memory_bank.store_research(
                        session_id=context.session_id,
                        company=company_name,
                        research_data=research_packet
                    )
            except Exception as memory_error:
                # Log but don't fail - memory storage is not critical for execution
                logger.warning(f"Failed to store research in memory for session {context.session_id}: {str(memory_error)}")
            
            execution_time = (time.time() - start_time) * 1000
            
            return self._create_result(
                success=True,
                output=research_packet,
                execution_time=execution_time
            )
            
        except ValueError as ve:
            # Input validation errors
            execution_time = (time.time() - start_time) * 1000
            return self._create_result(
                success=False,
                output=None,
                error=f"Validation error: {str(ve)}",
                execution_time=execution_time
            )
        except Exception as e:
            # General errors
            execution_time = (time.time() - start_time) * 1000
            return self._create_result(
                success=False,
                output=None,
                error=f"Research agent error: {str(e)}",
                execution_time=execution_time
            )