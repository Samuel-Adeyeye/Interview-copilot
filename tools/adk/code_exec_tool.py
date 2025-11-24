"""
ADK Code Execution Tool
Provides code execution capabilities using Judge0 or BuiltInCodeExecutor
"""

from google.adk.tools import FunctionTool
from google.adk.code_executors import BuiltInCodeExecutor
from typing import Dict, Any, List, Optional
import logging
import os

logger = logging.getLogger(__name__)


# Option 1: Use ADK's BuiltInCodeExecutor (Gemini's built-in code execution)
def create_builtin_code_executor():
    """
    Create ADK's built-in code executor.
    
    This uses Gemini's native code execution capability.
    No external API needed, but limited to Python code.
    
    Returns:
        BuiltInCodeExecutor instance
    
    Example:
        >>> code_executor = create_builtin_code_executor()
        >>> agent = LlmAgent(..., code_executor=code_executor)
    """
    logger.info("✅ ADK BuiltInCodeExecutor created (Gemini native)")
    return BuiltInCodeExecutor()


# Option 2: Keep Judge0 as FunctionTool (for multi-language support)
def create_judge0_code_exec_tool(judge0_api_key: Optional[str] = None):
    """
    Create Judge0 code execution tool as ADK FunctionTool.
    
    This wraps the existing Judge0 integration as an ADK FunctionTool
    to support multiple programming languages.
    
    Args:
        judge0_api_key: Optional Judge0 API key. If not provided, uses env var.
    
    Returns:
        FunctionTool for code execution, or None if Judge0 not available
    """
    from tools.code_exec_tool import CodeExecutionTool
    from exceptions import CodeExecutionError
    
    # Get API key
    api_key = judge0_api_key or os.getenv("JUDGE0_API_KEY")
    
    if not api_key:
        logger.warning("⚠️  JUDGE0_API_KEY not set. Code execution tool will not be available.")
        return None
    
    # Create the Judge0 tool instance
    code_exec_tool = CodeExecutionTool(judge0_api_key=api_key)
    
    def execute_code(
        code: str,
        language: str = "python",
        test_cases: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute code with test cases using Judge0.
        
        This tool executes code in a sandboxed environment and runs test cases
        to verify correctness. Supports multiple programming languages.
        
        Args:
            code: Source code to execute
            language: Programming language (python, javascript, java, cpp)
            test_cases: List of test case dictionaries with 'input' and 'expected_output'
        
        Returns:
            Dictionary with execution results:
            {
                "status": "success" | "error",
                "testsPassed": int,
                "totalTests": int,
                "test_results": [...],
                "executionTimeMs": float,
                "error_message": str (if error)
            }
        """
        import asyncio
        
        if test_cases is None:
            test_cases = []
        
        try:
            # Run async execution
            result = asyncio.run(
                code_exec_tool.execute_code(code, language, test_cases)
            )
            
            return {
                "status": "success",
                "testsPassed": result.get("testsPassed", 0),
                "totalTests": result.get("totalTests", 0),
                "test_results": result.get("test_results", []),
                "executionTimeMs": result.get("executionTimeMs", 0),
                "stdout": result.get("stdout", ""),
                "stderr": result.get("stderr", "")
            }
        except Exception as e:
            logger.error(f"Code execution error: {e}")
            return {
                "status": "error",
                "error_message": str(e),
                "testsPassed": 0,
                "totalTests": len(test_cases) if test_cases else 0
            }
    
    # Create ADK FunctionTool
    tool = FunctionTool(execute_code)
    logger.info("✅ Judge0 code execution tool created as ADK FunctionTool")
    return tool


def create_code_exec_tool(use_builtin: bool = True, judge0_api_key: Optional[str] = None):
    """
    Create code execution tool (factory function).
    
    Args:
        use_builtin: If True, use BuiltInCodeExecutor. If False, use Judge0.
        judge0_api_key: Optional Judge0 API key (only used if use_builtin=False)
    
    Returns:
        BuiltInCodeExecutor or FunctionTool, depending on use_builtin flag
    
    Example:
        >>> # Use Gemini's built-in executor
        >>> executor = create_code_exec_tool(use_builtin=True)
        >>> agent = LlmAgent(..., code_executor=executor)
        
        >>> # Use Judge0 for multi-language support
        >>> tool = create_code_exec_tool(use_builtin=False)
        >>> agent = LlmAgent(..., tools=[tool])
    """
    if use_builtin:
        return create_builtin_code_executor()
    else:
        return create_judge0_code_exec_tool(judge0_api_key)

