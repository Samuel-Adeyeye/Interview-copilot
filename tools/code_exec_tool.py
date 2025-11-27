from langchain_core.tools import Tool
from exceptions import CodeExecutionError, APIError
from typing import Dict, Any, List
import httpx
import json
import asyncio
import logging
import hashlib
import re

logger = logging.getLogger(__name__)

class CodeExecutionTool:
    def __init__(
        self, 
        judge0_api_key: str = None, 
        judge0_url: str = "https://judge0-ce.p.rapidapi.com",
        timeout_seconds: int = 10,
        max_memory_mb: int = 128
    ):
        self.api_key = judge0_api_key
        self.base_url = judge0_url
        self.timeout_seconds = timeout_seconds
        self.max_memory_mb = max_memory_mb
        self.execution_cache: Dict[str, Dict[str, Any]] = {}  # Simple in-memory cache
        
        # Language ID mapping for Judge0
        self.language_map = {
            "python": 71,  # Python 3
            "javascript": 63,  # JavaScript (Node.js)
            "java": 62,  # Java
            "cpp": 54,  # C++
        }
    
    def _sanitize_code(self, code: str, language: str) -> str:
        """
        Sanitize code to prevent security issues
        """
        # Remove potentially dangerous imports/operations
        dangerous_patterns = [
            (r'import\s+os', 'os module'),
            (r'import\s+subprocess', 'subprocess module'),
            (r'import\s+sys', 'sys module'),
            (r'__import__', '__import__ function'),
            (r'eval\(', 'eval function'),
            (r'exec\(', 'exec function'),
            (r'open\(', 'file operations'),
        ]
        
        sanitized = code
        warnings = []
        
        for pattern, description in dangerous_patterns:
            if re.search(pattern, sanitized):
                warnings.append(f"Warning: {description} detected")
                # Comment out dangerous lines (simple approach)
                sanitized = re.sub(
                    pattern,
                    lambda m: f'# BLOCKED: {m.group(0)}',
                    sanitized,
                    flags=re.IGNORECASE
                )
        
        if warnings:
            logger.warning(f"Code sanitization warnings: {warnings}")
        
        return sanitized
    
    def _get_cache_key(self, code: str, language: str, test_input: str) -> str:
        """Generate cache key for code execution"""
        content = f"{code}:{language}:{test_input}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def execute_code(self, code: str, language: str, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute code with test cases
        
        Args:
            code: Source code to execute
            language: Programming language
            test_cases: List of test case dictionaries with 'input' and 'expected_output'
        
        Returns:
            Dictionary with execution results
        """
        import time
        start_time = time.time()
        
        # Sanitize code
        sanitized_code = self._sanitize_code(code, language)
        language_id = self.language_map.get(language.lower(), 71)
        
        results = {
            "status": "pending",
            "testsPassed": 0,
            "totalTests": len(test_cases),
            "test_results": [],
            "stdout": "",
            "stderr": "",
            "executionTimeMs": 0,
            "errors": []
        }
        
        # Execute test cases with timeout
        for i, test_case in enumerate(test_cases):
            test_input = test_case.get("input", "")
            expected_output = test_case.get("expected_output", "")
            
            # Check cache first
            cache_key = self._get_cache_key(sanitized_code, language, test_input)
            if cache_key in self.execution_cache:
                logger.debug(f"Using cached result for test case {i+1}")
                cached_result = self.execution_cache[cache_key]
                result = cached_result.copy()
            else:
                # Execute with timeout
                try:
                    result = await asyncio.wait_for(
                        self._submit_to_judge0(sanitized_code, language_id, test_input),
                        timeout=self.timeout_seconds
                    )
                    # Cache successful results
                    if result.get("status", {}).get("description") == "Accepted":
                        self.execution_cache[cache_key] = result.copy()
                except asyncio.TimeoutError:
                    result = {
                        "stdout": "",
                        "stderr": f"Execution timeout after {self.timeout_seconds} seconds",
                        "time": "0",
                        "status": {"description": "Time Limit Exceeded"}
                    }
                    results["errors"].append(f"Test case {i+1}: Timeout")
                except Exception as e:
                    result = {
                        "stdout": "",
                        "stderr": f"Execution error: {str(e)}",
                        "time": "0",
                        "status": {"description": "Error"}
                    }
                    results["errors"].append(f"Test case {i+1}: {str(e)}")
                    logger.error(f"Code execution error: {e}")
            
            # Check if output matches expected (normalize whitespace)
            actual_output = str(result.get("stdout") or "").strip()
            expected_output_clean = str(expected_output or "").strip()
            
            # More flexible comparison (handle list/array formatting differences)
            passed = self._compare_outputs(actual_output, expected_output_clean)
            
            if passed:
                results["testsPassed"] += 1
            
            results["test_results"].append({
                "test_case": i + 1,
                "passed": passed,
                "input": test_input,
                "expected": expected_output_clean,
                "actual": actual_output,
                "execution_time": float(result.get("time", 0)),
                "stderr": result.get("stderr", "")
            })
        
        total_time = (time.time() - start_time) * 1000
        results["executionTimeMs"] = total_time
        
        # Determine final status
        if results["testsPassed"] == results["totalTests"]:
            results["status"] = "success"
        elif results["testsPassed"] > 0:
            results["status"] = "partial"
        else:
            results["status"] = "failed"
        
        return results
    
    def _compare_outputs(self, actual: str, expected: str) -> bool:
        """
        Compare actual and expected outputs with flexible matching
        """
        # Exact match
        if actual == expected:
            return True
        
        # Try to parse as JSON and compare
        try:
            import json
            actual_json = json.loads(actual)
            expected_json = json.loads(expected)
            return actual_json == expected_json
        except:
            pass
        
        # Normalize whitespace and compare
        actual_norm = re.sub(r'\s+', ' ', actual.strip())
        expected_norm = re.sub(r'\s+', ' ', expected.strip())
        if actual_norm == expected_norm:
            return True
        
        return False
    
    async def _submit_to_judge0(self, code: str, language_id: int, stdin: str = "") -> Dict:
        """
        Submit code to Judge0 API with improved error handling
        
        Args:
            code: Source code to execute
            language_id: Judge0 language ID
            stdin: Standard input for the program
        
        Returns:
            Execution result dictionary
        """
        if not self.api_key:
            # Mock execution for development
            logger.info("Using mock code execution (Judge0 API key not provided)")
            return {
                "stdout": "Mock output (Judge0 API key not configured)",
                "stderr": "",
                "time": "0.01",
                "status": {"description": "Accepted", "id": 3},
                "memory": "1024"
            }
        
        headers = {
            "content-type": "application/json",
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "judge0-ce.p.rapidapi.com"
        }
        
        payload = {
            "language_id": language_id,
            "source_code": code,
            "stdin": stdin,
            "cpu_time_limit": self.timeout_seconds,
            "memory_limit": self.max_memory_mb * 1024,  # Convert MB to KB
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds + 5) as client:
                # Submit
                response = await client.post(
                    f"{self.base_url}/submissions",
                    json=payload,
                    headers=headers,
                    params={"base64_encoded": "false", "wait": "true"}
                )
                response.raise_for_status()
                result = response.json()
                
                # Check for execution errors
                status_id = result.get("status", {}).get("id", 0)
                if status_id > 3:  # Status IDs > 3 indicate errors
                    error_msg = result.get("status", {}).get("description", "Unknown error")
                    result["stderr"] = f"Execution error: {error_msg}"
                
                return result
        except httpx.TimeoutException:
            logger.error(f"Judge0 API timeout after {self.timeout_seconds} seconds")
            return {
                "stdout": "",
                "stderr": f"API timeout after {self.timeout_seconds} seconds",
                "time": "0",
                "status": {"description": "Time Limit Exceeded", "id": 5}
            }
        except httpx.HTTPStatusError as e:
            logger.error(f"Judge0 API HTTP error: {e.response.status_code}")
            return {
                "stdout": "",
                "stderr": f"API error: {e.response.status_code}",
                "time": "0",
                "status": {"description": "API Error", "id": 13}
            }
        except Exception as e:
            logger.error(f"Judge0 API error: {e}")
            return {
                "stdout": "",
                "stderr": f"Execution error: {str(e)}",
                "time": "0",
                "status": {"description": "Error", "id": 13}
            }

def create_code_exec_tool(judge0_api_key: str = None):
    """Create code execution tool"""
    executor = CodeExecutionTool(judge0_api_key)
    
    async def run_code(input_str: str) -> str:
        """
        Input format: JSON string with 'code', 'language', and 'test_cases'
        """
        try:
            input_data = json.loads(input_str)
            result = await executor.execute_code(
                code=input_data["code"],
                language=input_data["language"],
                test_cases=input_data["test_cases"]
            )
            return json.dumps(result)
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    return Tool(
        name="code_executor",
        description="Execute code with test cases. Input should be JSON with 'code', 'language', and 'test_cases'",
        func=run_code
    )