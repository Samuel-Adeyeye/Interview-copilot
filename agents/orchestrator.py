"""
Orchestrator for Interview Co-Pilot
Coordinates the execution of research, technical, and companion agents
"""

from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, Sequence, Optional, Dict, Any
import operator
from langchain_core.messages import BaseMessage, HumanMessage
import logging

from agents.base_agent import AgentContext

logger = logging.getLogger(__name__)


class OrchestratorState(TypedDict):
    """State for the orchestrator workflow"""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    session_id: str
    user_id: str
    current_agent: str
    research_result: Optional[Dict[str, Any]]
    technical_result: Optional[Dict[str, Any]]
    companion_result: Optional[Dict[str, Any]]
    next_action: str
    error: Optional[str]
    inputs: Dict[str, Any]  # Input data for agents


class Orchestrator:
    """
    Orchestrator that coordinates the execution of multiple agents
    in a workflow for interview preparation.
    """
    
    def __init__(self, research_agent, technical_agent, companion_agent, session_service=None, memory_bank=None):
        """
        Initialize Orchestrator.
        
        Args:
            research_agent: ResearchAgent instance
            technical_agent: TechnicalAgent instance
            companion_agent: CompanionAgent instance
            session_service: Optional session service for state management
            memory_bank: Optional memory bank for persistence
        """
        self.research_agent = research_agent
        self.technical_agent = technical_agent
        self.companion_agent = companion_agent
        self.session_service = session_service
        self.memory_bank = memory_bank
        self.workflow = self._build_workflow()
    
    def _build_workflow(self):
        """Build the LangGraph workflow"""
        workflow = StateGraph(OrchestratorState)
        
        # Add nodes
        workflow.add_node("research", self._run_research)
        workflow.add_node("technical", self._run_technical)
        workflow.add_node("companion", self._run_companion)
        
        # Add conditional edges for routing
        workflow.add_conditional_edges(
            "research",
            self._should_skip_technical,
            {
                "skip": "companion",
                "continue": "technical"
            }
        )
        
        workflow.add_edge("technical", "companion")
        workflow.add_edge("companion", END)
        
        # Set entry point
        workflow.set_entry_point("research")
        
        return workflow.compile()
    
    def _should_skip_technical(self, state: OrchestratorState) -> str:
        """
        Determine if technical agent should be skipped.
        
        Returns:
            "skip" if technical should be skipped, "continue" otherwise
        """
        # Skip if research failed or if explicitly requested
        if state.get("error"):
            return "skip"
        
        # Check if technical is already completed
        if state.get("technical_result") and state.get("technical_result", {}).get("success"):
            return "skip"
        
        # Check session state if available
        if self.session_service:
            session = self.session_service.get_session(state["session_id"])
            if session:
                agent_states = session.get("agent_states", {})
                if agent_states.get("technical", {}).get("status") == "completed":
                    return "skip"
        
        return "continue"
    
    async def _run_research(self, state: OrchestratorState) -> OrchestratorState:
        """
        Execute research agent.
        
        Args:
            state: Current orchestrator state
        
        Returns:
            Updated state with research results
        """
        logger.info(f"Running research agent for session {state['session_id']}")
        
        try:
            # Check if research already completed
            if state.get("research_result") and state.get("research_result", {}).get("success"):
                logger.info("Research already completed, skipping")
                return state
            
            # Check session state
            if self.session_service:
                session = self.session_service.get_session(state["session_id"])
                if session:
                    agent_states = session.get("agent_states", {})
                    research_state = agent_states.get("research", {})
                    if research_state.get("status") == "completed":
                        logger.info("Research already completed in session, skipping")
                        return state
            
            # Prepare inputs for research agent
            inputs = state.get("inputs", {})
            job_description = inputs.get("job_description", "")
            company_name = inputs.get("company_name", "")
            
            if not job_description or not company_name:
                raise ValueError("job_description and company_name are required for research")
            
            # Create AgentContext
            context = AgentContext(
                session_id=state["session_id"],
                user_id=state["user_id"],
                inputs={
                    "job_description": job_description,
                    "company_name": company_name
                },
                metadata=state.get("inputs", {}).get("metadata", {})
            )
            
            # Execute research agent
            result = await self.research_agent.run(context)
            
            # Update state
            state["research_result"] = {
                "success": result.success,
                "output": result.output,
                "error": result.error,
                "execution_time_ms": result.execution_time_ms,
                "trace_id": result.trace_id
            }
            state["current_agent"] = "research"
            
            # Update session service if available
            if self.session_service:
                self.session_service.update_agent_state(
                    state["session_id"],
                    "research",
                    {
                        "status": "completed" if result.success else "failed",
                        "result": result.output,
                        "error": result.error,
                        "execution_time_ms": result.execution_time_ms
                    }
                )
            
            if not result.success:
                state["error"] = f"Research agent failed: {result.error}"
                logger.error(f"Research agent failed: {result.error}")
            
            return state
            
        except Exception as e:
            logger.error(f"Error in research agent execution: {e}")
            state["research_result"] = {
                "success": False,
                "output": None,
                "error": str(e),
                "execution_time_ms": 0,
                "trace_id": None
            }
            state["error"] = f"Research agent error: {str(e)}"
            return state
    
    async def _run_technical(self, state: OrchestratorState) -> OrchestratorState:
        """
        Execute technical agent.
        
        Args:
            state: Current orchestrator state
        
        Returns:
            Updated state with technical results
        """
        logger.info(f"Running technical agent for session {state['session_id']}")
        
        try:
            # Check if technical already completed
            if state.get("technical_result") and state.get("technical_result", {}).get("success"):
                logger.info("Technical already completed, skipping")
                return state
            
            # Prepare inputs for technical agent
            inputs = state.get("inputs", {})
            mode = inputs.get("mode", "select_questions")
            
            # Create AgentContext based on mode
            context_inputs = {
                "mode": mode
            }
            
            if mode == "select_questions":
                # For question selection
                job_description = inputs.get("job_description", "")
                difficulty = inputs.get("difficulty", "medium")
                num_questions = inputs.get("num_questions", 3)
                
                context_inputs.update({
                    "job_description": job_description,
                    "difficulty": difficulty,
                    "num_questions": num_questions
                })
                
            elif mode == "evaluate_code":
                # For code evaluation
                question_id = inputs.get("question_id")
                code = inputs.get("code", "")
                language = inputs.get("language", "python")
                
                if not question_id or not code:
                    raise ValueError("question_id and code are required for code evaluation")
                
                context_inputs.update({
                    "question_id": question_id,
                    "code": code,
                    "language": language
                })
            
            # Create AgentContext
            context = AgentContext(
                session_id=state["session_id"],
                user_id=state["user_id"],
                inputs=context_inputs,
                metadata=inputs.get("metadata", {})
            )
            
            # Execute technical agent
            result = await self.technical_agent.run(context)
            
            # Update state
            state["technical_result"] = {
                "success": result.success,
                "output": result.output,
                "error": result.error,
                "execution_time_ms": result.execution_time_ms,
                "trace_id": result.trace_id
            }
            state["current_agent"] = "technical"
            
            # Update session service if available
            if self.session_service:
                self.session_service.update_agent_state(
                    state["session_id"],
                    "technical",
                    {
                        "status": "completed" if result.success else "failed",
                        "mode": mode,
                        "result": result.output,
                        "error": result.error,
                        "execution_time_ms": result.execution_time_ms
                    }
                )
                
                # Add artifacts for code submissions
                if mode == "evaluate_code" and result.success:
                    self.session_service.add_artifact(
                        state["session_id"],
                        "code_evaluation",
                        {
                            "question_id": inputs.get("question_id"),
                            "evaluation": result.output,
                            "language": inputs.get("language", "python")
                        }
                    )
            
            if not result.success:
                state["error"] = f"Technical agent failed: {result.error}"
                logger.error(f"Technical agent failed: {result.error}")
            
            return state
            
        except Exception as e:
            logger.error(f"Error in technical agent execution: {e}")
            state["technical_result"] = {
                "success": False,
                "output": None,
                "error": str(e),
                "execution_time_ms": 0,
                "trace_id": None
            }
            state["error"] = f"Technical agent error: {str(e)}"
            return state
    
    async def _run_companion(self, state: OrchestratorState) -> OrchestratorState:
        """
        Execute companion agent.
        
        Args:
            state: Current orchestrator state
        
        Returns:
            Updated state with companion results
        """
        logger.info(f"Running companion agent for session {state['session_id']}")
        
        try:
            # Prepare session data for companion agent
            session_data = {
                "questions_attempted": 0,
                "questions_solved": 0,
                "skills_progress": {}
            }
            
            # Aggregate data from technical results
            if state.get("technical_result") and state.get("technical_result", {}).get("success"):
                tech_output = state.get("technical_result", {}).get("output", {})
                if isinstance(tech_output, dict):
                    questions = tech_output.get("questions", [])
                    if questions:
                        session_data["questions_attempted"] = len(questions)
                        # Count solved questions (would need to check evaluations)
                        session_data["questions_solved"] = 0
            
            # Get session data from session service if available
            if self.session_service:
                session = self.session_service.get_session(state["session_id"])
                if session:
                    artifacts = session.get("artifacts", [])
                    code_evaluations = [a for a in artifacts if a.get("type") == "code_evaluation"]
                    session_data["questions_attempted"] = len(code_evaluations)
                    session_data["questions_solved"] = sum(
                        1 for a in code_evaluations
                        if a.get("payload", {}).get("evaluation", {}).get("status") == "success"
                    )
                    
                    # Extract skills progress if available
                    agent_states = session.get("agent_states", {})
                    tech_state = agent_states.get("technical", {})
                    if tech_state:
                        session_data.update(tech_state.get("result", {}))
            
            # Create AgentContext
            context = AgentContext(
                session_id=state["session_id"],
                user_id=state["user_id"],
                inputs={
                    "mode": state.get("inputs", {}).get("companion_mode", "all"),
                    "session_data": session_data
                },
                metadata=state.get("inputs", {}).get("metadata", {})
            )
            
            # Execute companion agent
            result = await self.companion_agent.run(context)
            
            # Update state
            state["companion_result"] = {
                "success": result.success,
                "output": result.output,
                "error": result.error,
                "execution_time_ms": result.execution_time_ms,
                "trace_id": result.trace_id
            }
            state["current_agent"] = "companion"
            
            # Update session service if available
            if self.session_service:
                self.session_service.update_agent_state(
                    state["session_id"],
                    "companion",
                    {
                        "status": "completed" if result.success else "failed",
                        "result": result.output,
                        "error": result.error,
                        "execution_time_ms": result.execution_time_ms
                    }
                )
            
            if not result.success:
                state["error"] = f"Companion agent failed: {result.error}"
                logger.error(f"Companion agent failed: {result.error}")
            
            return state
            
        except Exception as e:
            logger.error(f"Error in companion agent execution: {e}")
            state["companion_result"] = {
                "success": False,
                "output": None,
                "error": str(e),
                "execution_time_ms": 0,
                "trace_id": None
            }
            state["error"] = f"Companion agent error: {str(e)}"
            return state
    
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
        initial_state: OrchestratorState = {
            "messages": [],
            "session_id": session_id,
            "user_id": user_id,
            "current_agent": "",
            "research_result": None,
            "technical_result": None,
            "companion_result": None,
            "next_action": "research",
            "error": None,
            "inputs": {
                "job_description": job_description,
                "company_name": company_name,
                "metadata": metadata or {}
            }
        }
        
        # Execute only research
        state = await self._run_research(initial_state)
        
        return state.get("research_result", {})
    
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
        initial_state: OrchestratorState = {
            "messages": [],
            "session_id": session_id,
            "user_id": user_id,
            "current_agent": "",
            "research_result": None,
            "technical_result": None,
            "companion_result": None,
            "next_action": "technical",
            "error": None,
            "inputs": {
                "mode": mode,
                **kwargs
            }
        }
        
        # Execute only technical
        state = await self._run_technical(initial_state)
        
        return state.get("technical_result", {})
    
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
        initial_state: OrchestratorState = {
            "messages": [HumanMessage(content=f"Starting interview preparation workflow for session {session_id}")],
            "session_id": session_id,
            "user_id": user_id,
            "current_agent": "",
            "research_result": None,
            "technical_result": None,
            "companion_result": None,
            "next_action": "start",
            "error": None,
            "inputs": inputs
        }
        
        try:
            result = await self.workflow.ainvoke(initial_state)
            return {
                "success": not bool(result.get("error")),
                "research": result.get("research_result"),
                "technical": result.get("technical_result"),
                "companion": result.get("companion_result"),
                "error": result.get("error"),
                "session_id": session_id
            }
        except Exception as e:
            logger.error(f"Error executing workflow: {e}")
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id
            }