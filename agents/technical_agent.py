from agents.base_agent import BaseAgent, AgentContext, AgentResult
from exceptions import AgentExecutionError, CodeExecutionError, ValidationError
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
import json
import time
import logging

logger = logging.getLogger(__name__)

class TechnicalAgent(BaseAgent):
    def __init__(self, llm, code_exec_tool, question_bank):
        super().__init__("TechnicalAgent", llm, tools=[code_exec_tool] if code_exec_tool else [])
        self.code_exec_tool = code_exec_tool
        self.question_bank = question_bank
    
    def select_questions(self, jd_text: str, difficulty: str = "medium", count: int = 3):
        """Select questions from bank based on JD requirements"""
        # Simple implementation - can be enhanced with embeddings
        questions = self.question_bank.get_questions_by_difficulty(difficulty)
        return questions[:count]
    
    async def run(self, context: AgentContext) -> AgentResult:
        """Execute technical agent for question selection or code evaluation"""
        start_time = time.time()
        
        try:
            mode = context.inputs.get("mode", "select_questions")
            
            if mode == "select_questions":
                jd_text = context.inputs.get("job_description", "")
                questions = self.select_questions(jd_text)
                output = {"questions": questions}
                
            elif mode == "evaluate_code":
                question_id = context.inputs.get("question_id")
                user_code = context.inputs.get("code")
                language = context.inputs.get("language", "python")
                
                # Get question details
                question = self.question_bank.get_question_by_id(question_id)
                test_cases = question.get("test_cases", []) if question else []
                
                # Execute code if tool is available
                test_results = []
                tests_passed = 0
                total_tests = len(test_cases)
                
                if self.code_exec_tool and test_cases:
                    try:
                        # Check if it's a CodeExecutionTool instance
                        if hasattr(self.code_exec_tool, 'execute_code'):
                            exec_result = await self.code_exec_tool.execute_code(
                                code=user_code,
                                language=language,
                                test_cases=test_cases
                            )
                            tests_passed = exec_result.get("testsPassed", 0)
                            test_results = exec_result.get("test_results", [])
                        else:
                            # If it's a LangChain tool, call it differently
                            logger.warning("Code execution tool not directly callable, skipping execution")
                            test_results = []
                    except Exception as e:
                        logger.warning(f"Code execution failed: {e}")
                        code_error = CodeExecutionError(
                            message=str(e),
                            language=language,
                            code=user_code,
                            original_error=e
                        )
                        test_results = [{"error": code_error.message}]
                
                # Generate feedback using LLM
                feedback_prompt = f"""Evaluate this code submission:

Question ID: {question_id}
Language: {language}
Code:
```{language}
{user_code}
```

Test Results: {tests_passed}/{total_tests} tests passed

Provide:
1. Feedback on code correctness
2. Time and space complexity analysis
3. Code quality assessment
4. Suggestions for improvement

Be constructive and encouraging."""
                
                try:
                    feedback_response = await self.llm.ainvoke([HumanMessage(content=feedback_prompt)])
                    feedback = feedback_response.content if hasattr(feedback_response, 'content') else str(feedback_response)
                except Exception as e:
                    feedback = f"Evaluation completed. {tests_passed}/{total_tests} tests passed. Error generating detailed feedback: {e}"
                
                output = {
                    "status": "success" if tests_passed == total_tests else "partial",
                    "tests_passed": tests_passed,
                    "total_tests": total_tests,
                    "test_results": test_results,
                    "feedback": feedback,
                    "complexity_analysis": {
                        "time": question.get("time_complexity", "Unknown") if question else "Unknown",
                        "space": question.get("space_complexity", "Unknown") if question else "Unknown"
                    }
                }
            
            execution_time = (time.time() - start_time) * 1000
            return self._create_result(True, output, execution_time=execution_time)
            
        except ValueError as ve:
            execution_time = (time.time() - start_time) * 1000
            validation_error = ValidationError(
                message=str(ve),
                field="inputs",
                details={"session_id": context.session_id}
            )
            return self._create_result(False, None, error=validation_error.message, execution_time=execution_time)
        except CodeExecutionError as code_error:
            execution_time = (time.time() - start_time) * 1000
            return self._create_result(False, None, error=code_error.message, execution_time=execution_time)
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            agent_error = AgentExecutionError(
                agent_name="technical",
                message=str(e),
                details={"session_id": context.session_id},
                original_error=e
            )
            return self._create_result(False, None, error=agent_error.message, execution_time=execution_time)