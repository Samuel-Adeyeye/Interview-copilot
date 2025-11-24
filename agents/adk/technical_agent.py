"""
ADK Technical Agent
Migrated from LangChain to Google's Agent Development Kit
"""

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.code_executors import BuiltInCodeExecutor
from tools.adk.question_bank_tool import create_question_bank_tools, get_question_selection_tool, get_question_lookup_tool
from tools.adk.code_exec_tool import create_code_exec_tool, create_builtin_code_executor, create_judge0_code_exec_tool
from config.adk_config import get_gemini_model, get_retry_config
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


def create_technical_agent(
    model: Optional[Gemini] = None,
    code_exec_tool = None,
    question_bank_tools: Optional[List] = None,
    use_builtin_code_executor: bool = True,
    judge0_api_key: Optional[str] = None,
    model_name: str = None
) -> LlmAgent:
    """
    Create ADK Technical Agent for coding interviews.
    
    This agent can:
    1. Select coding questions based on difficulty
    2. Evaluate submitted code solutions
    
    Args:
        model: Optional Gemini model instance
        code_exec_tool: Optional code execution tool (if None, will create one)
        question_bank_tools: Optional list of question bank tools (if None, will create them)
        use_builtin_code_executor: If True, use BuiltInCodeExecutor. If False, use Judge0.
        judge0_api_key: Optional Judge0 API key (only used if use_builtin_code_executor=False)
        model_name: Optional model name override
    
    Returns:
        LlmAgent configured for technical interview tasks
    
    Example:
        >>> # Use built-in code executor (Python only)
        >>> agent = create_technical_agent(use_builtin_code_executor=True)
        
        >>> # Use Judge0 for multi-language support
        >>> agent = create_technical_agent(
        ...     use_builtin_code_executor=False,
        ...     judge0_api_key="your_key"
        ... )
    """
    # Get model if not provided
    if model is None:
        model = get_gemini_model(model_name)
    
    # Create question bank tools if not provided
    if question_bank_tools is None:
        question_bank_tools = create_question_bank_tools()
    
    # Create code execution tool if not provided
    if code_exec_tool is None:
        if use_builtin_code_executor:
            # Use BuiltInCodeExecutor (set as code_executor parameter)
            code_executor = create_builtin_code_executor()
            code_exec_tool = None  # Will be set as code_executor
        else:
            # Use Judge0 as FunctionTool
            code_exec_tool = create_judge0_code_exec_tool(judge0_api_key)
            code_executor = None
    
    # Collect all tools
    tools = list(question_bank_tools)
    if code_exec_tool:
        tools.append(code_exec_tool)
    
    # Create agent instruction
    instruction = """You are a technical interview assistant specializing in coding interviews.

You have two main capabilities:

1. **Question Selection Mode** (mode="select_questions"):
   - Use get_questions_by_difficulty() to retrieve questions
   - Filter questions based on job description requirements if needed
   - Select appropriate number of questions
   - Return questions with full details (description, examples, test cases, hints)

2. **Code Evaluation Mode** (mode="evaluate_code"):
   - Use get_question_by_id() to get question details and test cases
   - Use code execution tools to run the submitted code
   - Analyze test results
   - Provide comprehensive feedback on:
     * Code correctness
     * Time and space complexity
     * Code quality and style
     * Suggestions for improvement
   - Be constructive and encouraging in your feedback

When evaluating code:
- Check if all test cases pass
- Analyze the algorithm's efficiency
- Provide specific, actionable feedback
- Acknowledge what the candidate did well
- Suggest improvements where appropriate

Always be supportive and help candidates learn and improve."""

    # Create agent
    agent = LlmAgent(
        name="TechnicalAgent",
        model=model,
        instruction=instruction,
        tools=tools,
        code_executor=code_executor if use_builtin_code_executor else None,
        output_key="technical_result"
    )
    
    logger.info("✅ ADK Technical Agent created")
    if use_builtin_code_executor:
        logger.info("   - Using BuiltInCodeExecutor (Python only)")
    else:
        logger.info("   - Using Judge0 (multi-language support)")
    
    return agent


def create_question_selection_agent(
    model: Optional[Gemini] = None,
    model_name: str = None
) -> LlmAgent:
    """
    Create a specialized agent for question selection only.
    
    This is a lighter version focused only on selecting questions.
    
    Args:
        model: Optional Gemini model instance
        model_name: Optional model name override
    
    Returns:
        LlmAgent for question selection
    """
    if model is None:
        model = get_gemini_model(model_name)
    
    question_tools = create_question_bank_tools()
    
    agent = LlmAgent(
        name="QuestionSelectionAgent",
        model=model,
        instruction="""You are a question selection specialist for coding interviews.

Your task is to select appropriate coding questions based on:
- Difficulty level (easy, medium, hard)
- Job description requirements
- Number of questions requested

Use the available question bank tools to:
1. Get questions by difficulty
2. Filter by tags if needed
3. Search for specific topics if needed

Return selected questions with all their details.""",
        tools=question_tools,
        output_key="selected_questions"
    )
    
    return agent


def create_code_evaluation_agent(
    model: Optional[Gemini] = None,
    use_builtin_code_executor: bool = True,
    judge0_api_key: Optional[str] = None,
    model_name: str = None
) -> LlmAgent:
    """
    Create a specialized agent for code evaluation only.
    
    This is a focused version for evaluating code submissions.
    
    Args:
        model: Optional Gemini model instance
        use_builtin_code_executor: If True, use BuiltInCodeExecutor
        judge0_api_key: Optional Judge0 API key
        model_name: Optional model name override
    
    Returns:
        LlmAgent for code evaluation
    """
    if model is None:
        model = get_gemini_model(model_name)
    
    # Get question lookup tool
    question_tool = get_question_lookup_tool()
    tools = [question_tool]
    
    # Get code execution
    code_executor = None
    code_exec_tool = None
    
    if use_builtin_code_executor:
        code_executor = create_builtin_code_executor()
    else:
        code_exec_tool = create_judge0_code_exec_tool(judge0_api_key)
        if code_exec_tool:
            tools.append(code_exec_tool)
    
    agent = LlmAgent(
        name="CodeEvaluationAgent",
        model=model,
        instruction="""You are a code evaluation specialist for technical interviews.

Your task is to evaluate submitted code solutions:

1. Use get_question_by_id() to retrieve question details and test cases
2. Execute the code using code execution tools
3. Analyze the results:
   - Check if all test cases pass
   - Evaluate time and space complexity
   - Assess code quality and style
   - Identify strengths and areas for improvement
4. Provide comprehensive, constructive feedback

Your feedback should:
- Be specific and actionable
- Acknowledge what was done well
- Suggest concrete improvements
- Help the candidate learn and grow
- Be encouraging and supportive""",
        tools=tools,
        code_executor=code_executor,
        output_key="evaluation_result"
    )
    
    return agent


# For backward compatibility
def create_adk_technical_agent(*args, **kwargs):
    """Alias for create_technical_agent()"""
    return create_technical_agent(*args, **kwargs)

