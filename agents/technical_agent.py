from agents.base_agent import BaseAgent, AgentContext, AgentResult
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate
import json
import time

class TechnicalAgent(BaseAgent):
    def __init__(self, llm, code_exec_tool, question_bank):
        super().__init__("TechnicalAgent", llm, tools=[code_exec_tool])
        self.code_exec_tool = code_exec_tool
        self.question_bank = question_bank
        self.agent = self._create_agent()
    
    def _create_agent(self):
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a technical interviewer conducting coding interviews.
            
            Your role:
            1. Select appropriate coding questions based on the job requirements
            2. Present questions clearly with examples
            3. Execute user's code using the code execution tool
            4. Provide detailed feedback on correctness, time/space complexity, and code quality
            5. Suggest improvements
            
            Be encouraging but thorough in your evaluation."""),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])
        
        agent = create_openai_tools_agent(self.llm, self.tools, prompt)
        return AgentExecutor(agent=agent, tools=self.tools, verbose=True)
    
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
                
                # Use agent to evaluate
                result = await self.agent.ainvoke({
                    "input": f"""Evaluate this code submission:
                    
                    Question ID: {question_id}
                    Language: {language}
                    Code:
```{language}
                    {user_code}
```
                    
                    1. Execute the code using the code execution tool
                    2. Check if it passes test cases
                    3. Analyze time and space complexity
                    4. Provide constructive feedback"""
                })
                
                output = result["output"]
            
            execution_time = (time.time() - start_time) * 1000
            return self._create_result(True, output, execution_time=execution_time)
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return self._create_result(False, None, error=str(e), execution_time=execution_time)