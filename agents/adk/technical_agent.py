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


from tools.adk.search_tool import create_adk_search_tool

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
    1. Select coding questions based on difficulty (Static)
    2. Generate company-specific questions using google_search (Dynamic)
    3. Evaluate submitted code solutions
    
    Args:
        model: Optional Gemini model instance
        code_exec_tool: Optional code execution tool (if None, will create one)
        question_bank_tools: Optional list of question bank tools (if None, will create them)
        use_builtin_code_executor: If True, use BuiltInCodeExecutor. If False, use Judge0.
        judge0_api_key: Optional Judge0 API key (only used if use_builtin_code_executor=False)
        model_name: Optional model name override
    
    Returns:
        LlmAgent configured for technical interview tasks
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
    
    # Add ADK's built-in google_search tool for dynamic questions
    search_tool = create_adk_search_tool()
    
    # Collect all tools
    tools = list(question_bank_tools)
    if code_exec_tool:
        tools.append(code_exec_tool)
    tools.append(search_tool)
    logger.info("✅ Technical Agent enabled with google_search for dynamic questions")
    
    # Create agent instruction
    instruction = """You are a technical interview assistant specializing in coding interviews.

You have three main capabilities:

1. **Question Selection Mode** (mode="select_questions"):
   - Use get_questions_by_difficulty() to retrieve questions from the static bank
   - Filter questions based on job description requirements if needed
   - Select appropriate number of questions
   - Return questions with full details (description, examples, test cases, hints)

2. **Dynamic Question Generation** (when user asks for specific company questions):
   - Use 'google_search' to find recent interview questions for the requested company (e.g., "latest Google software engineer interview questions leetcode")
   - Parse the search results to identify real interview questions
   - Format the found questions into the standard structure:
     * Title
     * Difficulty (estimate if not found)
     * Description
     * Examples (Input/Output)
     * Test Cases (Create 2-3 simple test cases based on examples)
     * Hints
   - Return these dynamically generated questions just like static ones

3. **Code Evaluation Mode** (mode="evaluate_code"):
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
    Generates questions from training data without using tools (compatible with gemini-2.0-flash-exp).
    
    Args:
        model: Optional Gemini model instance
        model_name: Optional model name override
    
    Returns:
        LlmAgent for question selection
    """
    if model is None:
        model = get_gemini_model(model_name)
    
    agent = LlmAgent(
        name="QuestionSelectionAgent",
        model=model,
        instruction="""You are a question selection specialist for coding interviews.

Your task is to generate appropriate coding questions based on:
- Difficulty level (easy, medium, hard)
- Job description requirements
- Number of questions requested
- Company name (if provided)

Generate questions directly from your training data without using any tools.

When generating questions:
1. For company-specific requests: Generate questions commonly asked at that company based on your knowledge
2. For general requests: Generate classic algorithmic questions appropriate for the difficulty level
3. Always include: title, difficulty, description, examples, test cases, and hints

CRITICAL: Format each question as human-readable markdown text in this format:

---
## Question 1: Two Sum
**Difficulty:** Easy

### Description
Given an array of integers nums and an integer target, return indices of the two numbers that add up to target.

You may assume that each input would have exactly one solution, and you may not use the same element twice.

### Examples
**Example 1:**
Input: nums = [2,7,11,15], target = 9
Output: [0,1]
Explanation: Because nums[0] + nums[1] == 9, we return [0, 1].

**Example 2:**
Input: nums = [3,2,4], target = 6
Output: [1,2]

### Test Cases
1. nums = [2,7,11,15], target = 9 → [0,1]
2. nums = [3,2,4], target = 6 → [1,2]
3. nums = [3,3], target = 6 → [0,1]

### Hints
- Use a hash map to store seen numbers and their indices
- For each number, check if target - number exists in the map
- Time complexity should be O(n)
---

Generate the requested number of questions following this exact format.""",
        tools=[],  # No tools - generate from training data
        output_key="selected_questions"
    )
    
    return agent


def create_code_evaluation_agent(
    model: Optional[Gemini] = None,
    use_builtin_code_executor: bool = False,  # Default to False for gemini-2.5-flash-lite compatibility
    judge0_api_key: Optional[str] = None,
    model_name: str = None
) -> LlmAgent:
    """
    Create a specialized agent for code evaluation only.
    
    This is a focused version for evaluating code submissions.
    Auto-detects Judge0 API key and uses it for actual code execution when available.
    
    Args:
        model: Optional Gemini model instance
        use_builtin_code_executor: If True, use BuiltInCodeExecutor (Note: may not work with gemini-2.5-flash-lite)
        judge0_api_key: Optional Judge0 API key (auto-detected from env if not provided)
        model_name: Optional model name override
    
    Returns:
        LlmAgent for code evaluation
    """
    from config.settings import settings
    
    if model is None:
        model = get_gemini_model(model_name)
    
    # Get question lookup tool
    question_tool = get_question_lookup_tool()
    tools = [question_tool]
    
    # Get code execution
    code_executor = None
    code_exec_tool = None
    has_execution = False
    
    # Auto-detect Judge0 API key from environment if not provided
    if judge0_api_key is None:
        judge0_api_key = settings.JUDGE0_API_KEY
    
    if use_builtin_code_executor:
        code_executor = create_builtin_code_executor()
        has_execution = True
    elif judge0_api_key:
        # Use Judge0 if API key is available
        code_exec_tool = create_judge0_code_exec_tool(judge0_api_key)
        if code_exec_tool:
            tools.append(code_exec_tool)
            has_execution = True
            logger.info("✅ Code evaluation agent will use Judge0 for actual code execution")
    
    # Adjust instruction based on code execution capability
    if has_execution:
        instruction = """You are a code evaluation specialist for technical interviews.

Your task is to evaluate submitted code solutions by COMBINING execution results with static analysis:

1. **Get Question Details**: Use get_question_by_id() to retrieve question details and test cases

2. **Execute Code**: Use the execute_code() tool to run the code with test cases
   - This provides real execution results, pass/fail status, and runtime metrics

3. **Perform Static Analysis**: Even with execution results, also analyze the code:
   - Review the algorithm and approach
   - Evaluate time and space complexity
   - Assess code quality, style, and readability
   - Identify edge cases or potential improvements
   - Look for best practices or anti-patterns

4. **Provide Comprehensive Feedback** combining both execution and analysis:
   - Start with test results (how many passed/failed)
   - Explain WHY tests passed or failed based on the algorithm
   - Discuss time/space complexity
   - Highlight code quality aspects
   - Suggest concrete improvements
   - Acknowledge what was done well

Your feedback should:
- Be specific and actionable
- Combine empirical results (execution) with analytical insights (static analysis)
- Help candidates understand both WHAT happened (test results) and WHY (algorithm analysis)
- Be encouraging and supportive
- Guide learning and improvement

Example structure:
1. Test Results: X/Y tests passed
2. Algorithm Analysis: [explain the approach and logic]
3. Complexity: Time O(n), Space O(1)
4. Code Quality: [readability, style, best practices]
5. Suggestions: [specific improvements]"""
    else:
        instruction = """You are a code evaluation specialist for technical interviews.

Your task is to evaluate submitted code solutions through STATIC ANALYSIS:

1. Use get_question_by_id() to retrieve question details and test cases
2. Analyze the code logic WITHOUT executing it:
   - Trace through the algorithm mentally
   - Check if the logic handles all test cases correctly
   - Identify potential edge cases or bugs
   - Evaluate time and space complexity
   - Assess code quality and style
3. Provide comprehensive, constructive feedback

Your feedback should:
- Be specific and actionable
- Acknowledge what was done well
- Identify potential issues or bugs
- Analyze the algorithm's correctness
- Evaluate time and space complexity
- Suggest concrete improvements
- Help the candidate learn and grow
- Be encouraging and supportive

Note: Since you cannot execute code, perform careful static analysis to evaluate correctness."""
    
    agent = LlmAgent(
        name="CodeEvaluationAgent",
        model=model,
        instruction=instruction,
        tools=tools,
        code_executor=code_executor,
        output_key="evaluation_result"
    )
    
    logger.info(f"✅ Code evaluation agent created with {len(tools)} tools, has_execution={has_execution}")
    
    return agent


# For backward compatibility
def create_adk_technical_agent(*args, **kwargs):
    """Alias for create_technical_agent()"""
    return create_technical_agent(*args, **kwargs)

