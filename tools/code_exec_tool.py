from langchain.tools import Tool
from typing import Dict, Any
import httpx
import json

class CodeExecutionTool:
    def __init__(self, judge0_api_key: str = None, judge0_url: str = "https://judge0-ce.p.rapidapi.com"):
        self.api_key = judge0_api_key
        self.base_url = judge0_url
        
        # Language ID mapping for Judge0
        self.language_map = {
            "python": 71,  # Python 3
            "javascript": 63,  # JavaScript (Node.js)
            "java": 62,  # Java
            "cpp": 54,  # C++
        }
    
    async def execute_code(self, code: str, language: str, test_cases: list) -> Dict[str, Any]:
        """Execute code with test cases"""
        language_id = self.language_map.get(language.lower(), 71)
        
        results = {
            "status": "pending",
            "testsPassed": 0,
            "totalTests": len(test_cases),
            "test_results": [],
            "stdout": "",
            "stderr": "",
            "executionTimeMs": 0
        }
        
        for i, test_case in enumerate(test_cases):
            test_input = test_case.get("input", "")
            expected_output = test_case.get("expected_output", "")
            
            # Submit to Judge0
            result = await self._submit_to_judge0(code, language_id, test_input)
            
            # Check if output matches expected
            passed = result["stdout"].strip() == expected_output.strip()
            if passed:
                results["testsPassed"] += 1
            
            results["test_results"].append({
                "test_case": i + 1,
                "passed": passed,
                "input": test_input,
                "expected": expected_output,
                "actual": result["stdout"],
                "execution_time": result.get("time", 0)
            })
        
        results["status"] = "success" if results["testsPassed"] == results["totalTests"] else "partial"
        return results
    
    async def _submit_to_judge0(self, code: str, language_id: int, stdin: str = "") -> Dict:
        """Submit code to Judge0 API"""
        if not self.api_key:
            # Mock execution for development
            return {
                "stdout": "Mock output",
                "stderr": "",
                "time": "0.01",
                "status": {"description": "Accepted"}
            }
        
        headers = {
            "content-type": "application/json",
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "judge0-ce.p.rapidapi.com"
        }
        
        payload = {
            "language_id": language_id,
            "source_code": code,
            "stdin": stdin
        }
        
        async with httpx.AsyncClient() as client:
            # Submit
            response = await client.post(
                f"{self.base_url}/submissions",
                json=payload,
                headers=headers,
                params={"base64_encoded": "false", "wait": "true"}
            )
            return response.json()

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