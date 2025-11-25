"""
ADK Orchestrator for Interview Co-Pilot
Coordinates the execution of research, technical, and companion agents using ADK patterns
"""

from google.adk.agents import SequentialAgent, LlmAgent
from google.adk.tools import AgentTool
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.genai import types
from agents.adk.research_agent import create_research_agent
from agents.adk.technical_agent import create_technical_agent
from agents.adk.companion_agent import create_companion_agent
from config.adk_config import get_gemini_model
from typing import Dict, Any, Optional, List
import logging
import asyncio

logger = logging.getLogger(__name__)


class ADKOrchestrator:
    """
    ADK-based Orchestrator that coordinates the execution of multiple agents
    in a workflow for interview preparation.
    
    Uses ADK SequentialAgent for fixed workflow or custom orchestrator agent
    for dynamic routing.
    """
    
    def __init__(
        self,
        research_agent: Optional[LlmAgent] = None,
        technical_agent: Optional[LlmAgent] = None,
        companion_agent: Optional[LlmAgent] = None,
        session_service = None,
        memory_bank = None,
        use_sequential: bool = True,
        use_builtin_code_executor: bool = True,
        judge0_api_key: Optional[str] = None
    ):
        """
        Initialize ADK Orchestrator.
        
        Args:
            research_agent: Optional ResearchAgent instance (creates if None)
            technical_agent: Optional TechnicalAgent instance (creates if None)
            companion_agent: Optional CompanionAgent instance (creates if None)
            session_service: Optional session service for state management
            memory_bank: Optional memory bank for persistence
            use_sequential: If True, use SequentialAgent. If False, use LLM-based orchestrator.
            use_builtin_code_executor: If True, use BuiltInCodeExecutor for technical agent
            judge0_api_key: Optional Judge0 API key (only used if use_builtin_code_executor=False)
        """
        # Create agents if not provided
        if research_agent is None:
            research_agent = create_research_agent()
        if technical_agent is None:
            technical_agent = create_technical_agent(
                use_builtin_code_executor=use_builtin_code_executor,
                judge0_api_key=judge0_api_key
            )
        if companion_agent is None:
            companion_agent = create_companion_agent()
        
        self.research_agent = research_agent
        self.technical_agent = technical_agent
        self.companion_agent = companion_agent
        self.session_service = session_service
        self.memory_bank = memory_bank
        
        # Create workflow based on strategy
        if use_sequential:
            self.workflow = self._create_sequential_workflow()
        else:
            self.workflow = self._create_llm_orchestrator()
        
        # Create runner for execution
        self.runner = InMemoryRunner(agent=self.workflow)
        
        logger.info("✅ ADK Orchestrator created")
    
    def _create_sequential_workflow(self) -> SequentialAgent:
        """
        Create a SequentialAgent workflow.
        
        This executes agents in fixed order: research → technical → companion
        """
        workflow = SequentialAgent(
            name="InterviewOrchestrator",
            sub_agents=[
                self.research_agent,
                self.technical_agent,
                self.companion_agent
            ]
        )
        
        logger.info("✅ Created SequentialAgent workflow")
        return workflow
    
    def _create_llm_orchestrator(self) -> LlmAgent:
        """
        Create an LLM-based orchestrator agent.
        
        This uses an LLM to decide which agents to call and in what order.
        More flexible but may be slower.
        """
        # Wrap agents as tools
        research_tool = AgentTool(self.research_agent)
        technical_tool = AgentTool(self.technical_agent)
        companion_tool = AgentTool(self.companion_agent)
        
        orchestrator = LlmAgent(
            name="Orchestrator",
            model=get_gemini_model(),
            instruction="""You are an orchestrator for interview preparation workflow.

Your task is to coordinate the execution of three specialized agents:

1. **ResearchAgent**: Researches companies and their interview processes
   - Use when you need company information, interview process details, tech stack
   - Input: company_name, job_description
   - Output: ResearchPacket with company overview, interview process, tech stack, etc.

2. **TechnicalAgent**: Handles coding interview questions and code evaluation
   - Use when you need to select questions or evaluate code submissions
   - Input: mode ("select_questions" or "evaluate_code"), plus mode-specific inputs
   - Output: Questions or evaluation results

3. **CompanionAgent**: Provides encouragement, tips, summaries, and recommendations
   - Use at the end to provide support and feedback
   - Input: session_data (performance metrics)
   - Output: Encouragement, tips, summary, recommendations

Workflow:
1. Always start with ResearchAgent if company_name and job_description are provided
2. Use TechnicalAgent if questions need to be selected or code needs evaluation
3. Always end with CompanionAgent to provide support

Coordinate the workflow intelligently based on the user's request.""",
            tools=[research_tool, technical_tool, companion_tool],
            output_key="orchestrator_result"
        )
        
        logger.info("✅ Created LLM-based orchestrator")
        return orchestrator
    
    async def execute_research(
        self,
        session_id: str,
        user_id: str,
        job_description: str,
        company_name: str,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Execute only the research agent.
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            job_description: Job description text
            company_name: Company name
            metadata: Optional metadata
        
        Returns:
            Research result dictionary
        """
        logger.info(f"Executing research agent for session {session_id}")
        
        try:
            # Create query for research agent
            query_text = f"""Research {company_name} and gather information about:
- Company overview and recent news
- Interview process and experience
- Technology stack and engineering practices
- Company culture and values

Job Description context:
{job_description[:500]}{'...' if len(job_description) > 500 else ''}"""
            
            query = types.Content(
                role="user",
                parts=[types.Part(text=query_text)]
            )
            
            # Run research agent directly
            runner = InMemoryRunner(agent=self.research_agent)
            
            result = None
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=query
            ):
                if event.content and event.content.parts:
                    result = event.content.parts[0].text
            
            # Get structured output from session state
            # Note: In ADK, structured output would be in session.state[output_key]
            # For now, we'll parse the text response
            
            return {
                "success": True,
                "output": {
                    "company_name": company_name,
                    "research_text": result or "Research completed",
                    "job_description": job_description
                },
                "error": None,
                "execution_time_ms": 0,
                "trace_id": None
            }
            
        except Exception as e:
            logger.error(f"Error executing research: {e}")
            return {
                "success": False,
                "output": None,
                "error": str(e),
                "execution_time_ms": 0,
                "trace_id": None
            }
    
    async def execute_technical(
        self,
        session_id: str,
        user_id: str,
        mode: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute only the technical agent.
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            mode: "select_questions" or "evaluate_code"
            **kwargs: Additional inputs based on mode
        
        Returns:
            Technical result dictionary
        """
        logger.info(f"Executing technical agent for session {session_id}, mode: {mode}")
        
        try:
            # Build query based on mode
            if mode == "select_questions":
                job_description = kwargs.get("job_description", "")
                difficulty = kwargs.get("difficulty", "medium")
                num_questions = kwargs.get("num_questions", 3)
                
                query_text = f"""Select {num_questions} {difficulty} difficulty coding interview questions.

Job Description:
{job_description[:500] if job_description else 'General software engineering'}

Use the question bank tools to get appropriate questions."""
                
            elif mode == "evaluate_code":
                question_id = kwargs.get("question_id")
                code = kwargs.get("code", "")
                language = kwargs.get("language", "python")
                
                if not question_id or not code:
                    raise ValueError("question_id and code are required for code evaluation")
                
                query_text = f"""Evaluate this code submission:

Question ID: {question_id}
Language: {language}
Code:
```{language}
{code}
```

Use get_question_by_id() to get test cases, then execute the code and provide comprehensive feedback."""
                
            else:
                raise ValueError(f"Invalid mode: {mode}. Must be 'select_questions' or 'evaluate_code'")
            
            query = types.Content(
                role="user",
                parts=[types.Part(text=query_text)]
            )
            
            # Run technical agent directly
            runner = InMemoryRunner(agent=self.technical_agent)
            
            result = None
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=query
            ):
                if event.content and event.content.parts:
                    result = event.content.parts[0].text
            
            return {
                "success": True,
                "output": {
                    "mode": mode,
                    "result": result or "Technical task completed",
                    **kwargs
                },
                "error": None,
                "execution_time_ms": 0,
                "trace_id": None
            }
            
        except Exception as e:
            logger.error(f"Error executing technical agent: {e}")
            return {
                "success": False,
                "output": None,
                "error": str(e),
                "execution_time_ms": 0,
                "trace_id": None
            }
    
    async def execute(
        self,
        session_id: str,
        user_id: str,
        inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute the full workflow.
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            inputs: Input dictionary with:
                - job_description: str (required for research)
                - company_name: str (required for research)
                - mode: str (for technical agent)
                - Other mode-specific inputs
        
        Returns:
            Complete workflow result
        """
        logger.info(f"Executing full workflow for session {session_id}")
        
        try:
            # Build workflow query
            query_parts = []
            
            # Research phase
            if inputs.get("company_name") and inputs.get("job_description"):
                query_parts.append(f"""1. Research {inputs['company_name']}:
   - Company overview
   - Interview process
   - Technology stack
   - Recent news
   - Preparation tips
   
   Job Description: {inputs['job_description'][:300]}...""")
            
            # Technical phase
            mode = inputs.get("mode", "select_questions")
            if mode == "select_questions":
                difficulty = inputs.get("difficulty", "medium")
                num_questions = inputs.get("num_questions", 3)
                query_parts.append(f"""2. Select {num_questions} {difficulty} difficulty coding questions.""")
            elif mode == "evaluate_code":
                query_parts.append(f"""2. Evaluate code submission for question {inputs.get('question_id')}.""")
            
            # Companion phase
            query_parts.append("""3. Generate encouragement, tips, and recommendations based on performance.""")

            query_text = "\n\n".join(query_parts)
            
            query = types.Content(
                role="user",
                parts=[types.Part(text=query_text)]
            )
            
            # Execute workflow
            research_result = None
            technical_result = None
            companion_result = None
            
            async for event in self.runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=query
            ):
                # Collect results from session state
                # Note: In a real implementation, we'd access session.state
                if event.content and event.content.parts:
                    # For now, we'll need to parse the response
                    pass
            
            # Get results from session state
            # This is a simplified version - in production, access session.state directly
            return {
                "success": True,
                "research": research_result or {"status": "completed"},
                "technical": technical_result or {"status": "completed"},
                "companion": companion_result or {"status": "completed"},
                "error": None,
                "session_id": session_id
            }
            
        except Exception as e:
            logger.error(f"Error executing workflow: {e}")
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id
            }


# Factory function for easy creation
def create_adk_orchestrator(
    research_agent: Optional[LlmAgent] = None,
    technical_agent: Optional[LlmAgent] = None,
    companion_agent: Optional[LlmAgent] = None,
    session_service = None,
    memory_bank = None,
    use_sequential: bool = True,
    use_builtin_code_executor: bool = True,
    judge0_api_key: Optional[str] = None
) -> ADKOrchestrator:
    """
    Create an ADK Orchestrator instance.
    
    Args:
        research_agent: Optional ResearchAgent instance
        technical_agent: Optional TechnicalAgent instance
        companion_agent: Optional CompanionAgent instance
        session_service: Optional session service
        memory_bank: Optional memory bank
        use_sequential: If True, use SequentialAgent. If False, use LLM orchestrator.
        use_builtin_code_executor: If True, use BuiltInCodeExecutor
        judge0_api_key: Optional Judge0 API key
    
    Returns:
        ADKOrchestrator instance
    """
    return ADKOrchestrator(
        research_agent=research_agent,
        technical_agent=technical_agent,
        companion_agent=companion_agent,
        session_service=session_service,
        memory_bank=memory_bank,
        use_sequential=use_sequential,
        use_builtin_code_executor=use_builtin_code_executor,
        judge0_api_key=judge0_api_key
    )

