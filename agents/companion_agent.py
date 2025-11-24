"""
Companion Agent for Interview Co-Pilot
Provides personalized encouragement, tips, and progress tracking
"""

from agents.base_agent import BaseAgent, AgentContext, AgentResult
from exceptions import AgentExecutionError, ValidationError, MemoryError
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from typing import Dict, Any, List, Optional
import time
import logging
import json

logger = logging.getLogger(__name__)


class CompanionAgent(BaseAgent):
    """
    Companion Agent that provides personalized support, encouragement,
    and progress tracking for interview preparation.
    """
    
    def __init__(self, llm: ChatOpenAI, memory_bank):
        """
        Initialize Companion Agent.
        
        Args:
            llm: Language model instance
            memory_bank: MemoryBank instance for retrieving user history
        """
        super().__init__("CompanionAgent", llm, tools=[])
        self.memory_bank = memory_bank
    
    async def _get_user_history(self, user_id: str, limit: int = 5) -> List[Dict]:
        """Retrieve user's recent session history"""
        try:
            if not self.memory_bank:
                return []
            
            results = await self.memory_bank.get_user_history(user_id, limit=limit)
            
            # Format results for easier processing
            formatted_history = []
            if results and isinstance(results, dict):
                # ChromaDB returns results in a specific format
                if 'ids' in results and 'metadatas' in results and 'documents' in results:
                    for i, doc_id in enumerate(results.get('ids', [[]])[0]):
                        if i < len(results.get('metadatas', [[]])[0]):
                            metadata = results['metadatas'][0][i]
                            document = results['documents'][0][i] if i < len(results.get('documents', [[]])[0]) else "{}"
                            try:
                                session_data = json.loads(document) if isinstance(document, str) else document
                                formatted_history.append({
                                    **metadata,
                                    **session_data
                                })
                            except json.JSONDecodeError:
                                formatted_history.append(metadata)
            
            return formatted_history
        except Exception as e:
            logger.warning(f"Error retrieving user history: {e}")
            return []
    
    async def _generate_encouragement(
        self, 
        user_id: str, 
        session_data: Dict[str, Any],
        user_history: List[Dict]
    ) -> str:
        """Generate personalized encouragement message"""
        
        # Analyze performance
        questions_attempted = session_data.get("questions_attempted", 0)
        questions_solved = session_data.get("questions_solved", 0)
        success_rate = questions_solved / questions_attempted if questions_attempted > 0 else 0
        
        # Compare with history
        improvement = ""
        if user_history:
            prev_success_rate = user_history[0].get("success_rate", 0)
            if success_rate > prev_success_rate:
                improvement = f"Great improvement! Your success rate increased from {prev_success_rate*100:.1f}% to {success_rate*100:.1f}%."
            elif success_rate == prev_success_rate and success_rate > 0:
                improvement = "You're maintaining consistent performance. Keep it up!"
        
        # Build context for LLM
        history_summary = ""
        if user_history:
            total_sessions = len(user_history)
            history_summary = f"You've completed {total_sessions} previous practice sessions. "
        
        prompt = f"""You are a supportive and encouraging interview preparation coach. Generate a personalized encouragement message.

User Performance:
- Questions Attempted: {questions_attempted}
- Questions Solved: {questions_solved}
- Success Rate: {success_rate*100:.1f}%
{improvement}

{history_summary}

Generate a brief (2-3 sentences), warm, and motivating message that:
1. Acknowledges their effort and progress
2. Provides specific positive feedback
3. Offers constructive encouragement
4. Is personalized and genuine

Keep it concise and uplifting."""

        try:
            messages = [
                SystemMessage(content="You are a supportive interview coach who provides personalized encouragement and motivation."),
                HumanMessage(content=prompt)
            ]
            response = await self.llm.ainvoke(messages)
            encouragement = response.content if hasattr(response, 'content') else str(response)
            return encouragement.strip()
        except Exception as e:
            logger.error(f"Error generating encouragement: {e}")
            # Fallback encouragement
            if success_rate >= 0.8:
                return "Excellent work! You're performing very well. Keep practicing to maintain this level!"
            elif success_rate >= 0.5:
                return "Good progress! You're on the right track. Continue practicing to improve further!"
            else:
                return "Keep going! Every practice session helps you improve. Review the solutions and try again!"
    
    async def _generate_tips(
        self,
        user_id: str,
        session_data: Dict[str, Any],
        user_history: List[Dict]
    ) -> List[str]:
        """Generate personalized tips based on performance"""
        
        # Analyze weak areas
        questions_attempted = session_data.get("questions_attempted", 0)
        questions_solved = session_data.get("questions_solved", 0)
        success_rate = questions_solved / questions_attempted if questions_attempted > 0 else 0
        
        # Get skill breakdown if available
        skills_progress = session_data.get("skills_progress", {})
        weak_skills = [
            skill for skill, data in skills_progress.items()
            if isinstance(data, dict) and data.get("proficiency", 1.0) < 0.7
        ]
        
        prompt = f"""You are an expert interview coach. Generate 3-5 specific, actionable tips for improvement.

Performance Analysis:
- Success Rate: {success_rate*100:.1f}%
- Questions Solved: {questions_solved}/{questions_attempted}
- Areas needing improvement: {', '.join(weak_skills) if weak_skills else 'General practice'}

Generate tips that are:
1. Specific and actionable
2. Relevant to their current performance level
3. Focused on areas that need improvement
4. Encouraging and constructive

Return only the tips as a numbered list, one per line."""

        try:
            messages = [
                SystemMessage(content="You are an expert interview coach providing actionable improvement tips."),
                HumanMessage(content=prompt)
            ]
            response = await self.llm.ainvoke(messages)
            tips_text = response.content if hasattr(response, 'content') else str(response)
            
            # Parse tips from response
            tips = []
            for line in tips_text.split('\n'):
                line = line.strip()
                # Remove numbering (1., 2., etc.)
                if line and (line[0].isdigit() or line.startswith('-') or line.startswith('*')):
                    tip = line.split('.', 1)[-1].strip() if '.' in line else line.lstrip('-* ').strip()
                    if tip:
                        tips.append(tip)
            
            # Fallback tips if parsing fails
            if not tips:
                tips = [
                    "Practice more problems in your weak areas",
                    "Review solutions and understand different approaches",
                    "Focus on time and space complexity analysis",
                    "Practice explaining your thought process out loud"
                ]
            
            return tips[:5]  # Limit to 5 tips
            
        except Exception as e:
            logger.error(f"Error generating tips: {e}")
            # Fallback tips
            return [
                "Continue practicing regularly to build confidence",
                "Review solutions after attempting problems",
                "Focus on understanding patterns and approaches",
                "Practice explaining your solutions clearly"
            ]
    
    async def _generate_session_summary(
        self,
        session_id: str,
        user_id: str,
        session_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate comprehensive session summary"""
        
        questions_attempted = session_data.get("questions_attempted", 0)
        questions_solved = session_data.get("questions_solved", 0)
        success_rate = questions_solved / questions_attempted if questions_attempted > 0 else 0
        
        # Calculate duration if available
        created_at = session_data.get("created_at")
        completed_at = session_data.get("completed_at")
        duration_minutes = 0
        if created_at and completed_at:
            try:
                from datetime import datetime
                start = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                end = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
                duration_minutes = (end - start).total_seconds() / 60
            except:
                pass
        
        summary = {
            "session_id": session_id,
            "user_id": user_id,
            "questions_attempted": questions_attempted,
            "questions_solved": questions_solved,
            "success_rate": success_rate,
            "duration_minutes": round(duration_minutes, 1),
            "score": success_rate * 100,
            "timestamp": session_data.get("completed_at") or session_data.get("updated_at"),
            "skills_practiced": list(session_data.get("skills_progress", {}).keys()),
            "highlights": []
        }
        
        # Add highlights
        if success_rate >= 0.9:
            summary["highlights"].append("Outstanding performance!")
        elif success_rate >= 0.7:
            summary["highlights"].append("Strong performance")
        elif questions_attempted > 0:
            summary["highlights"].append("Good effort, keep practicing")
        
        return summary
    
    async def _generate_recommendations(
        self,
        user_id: str,
        session_data: Dict[str, Any],
        user_history: List[Dict]
    ) -> List[str]:
        """Generate personalized recommendations for next steps"""
        
        questions_attempted = session_data.get("questions_attempted", 0)
        questions_solved = session_data.get("questions_solved", 0)
        success_rate = questions_solved / questions_attempted if questions_attempted > 0 else 0
        
        # Analyze trends
        trend = "stable"
        if len(user_history) >= 2:
            recent_rate = success_rate
            previous_rate = user_history[0].get("success_rate", 0)
            if recent_rate > previous_rate + 0.1:
                trend = "improving"
            elif recent_rate < previous_rate - 0.1:
                trend = "declining"
        
        prompt = f"""You are an interview coach. Generate 3-4 specific recommendations for the user's next practice session.

Current Performance:
- Success Rate: {success_rate*100:.1f}%
- Questions Solved: {questions_solved}/{questions_attempted}
- Performance Trend: {trend}

Generate recommendations that:
1. Are specific and actionable
2. Build on current progress
3. Address areas for improvement
4. Are encouraging and realistic

Return only the recommendations as a numbered list."""

        try:
            messages = [
                SystemMessage(content="You are an expert interview coach providing personalized recommendations."),
                HumanMessage(content=prompt)
            ]
            response = await self.llm.ainvoke(messages)
            recs_text = response.content if hasattr(response, 'content') else str(response)
            
            # Parse recommendations
            recommendations = []
            for line in recs_text.split('\n'):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-') or line.startswith('*')):
                    rec = line.split('.', 1)[-1].strip() if '.' in line else line.lstrip('-* ').strip()
                    if rec:
                        recommendations.append(rec)
            
            # Fallback recommendations
            if not recommendations:
                if success_rate >= 0.8:
                    recommendations = [
                        "Try more challenging problems to push your limits",
                        "Practice system design questions",
                        "Focus on optimizing your solutions"
                    ]
                elif success_rate >= 0.5:
                    recommendations = [
                        "Continue practicing similar difficulty problems",
                        "Review solutions and understand different approaches",
                        "Focus on time complexity optimization"
                    ]
                else:
                    recommendations = [
                        "Start with easier problems to build confidence",
                        "Review fundamental data structures and algorithms",
                        "Practice explaining your approach step by step"
                    ]
            
            return recommendations[:4]  # Limit to 4 recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return [
                "Continue practicing regularly",
                "Review solutions and understand patterns",
                "Focus on your weak areas"
            ]
    
    async def run(self, context: AgentContext) -> AgentResult:
        """
        Execute companion agent to provide support and generate summary.
        
        Args:
            context: AgentContext containing:
                - session_id: Current session ID
                - user_id: User ID
                - inputs: Dict with optional keys:
                    - session_data: Current session data
                    - mode: "summary" (default), "encouragement", "tips", "recommendations", or "all"
        
        Returns:
            AgentResult with companion output
        """
        start_time = time.time()
        
        try:
            # Input validation
            if not context.session_id:
                raise ValueError("session_id is required in context")
            if not context.user_id:
                raise ValueError("user_id is required in context")
            
            mode = context.inputs.get("mode", "all")
            session_data = context.inputs.get("session_data", {})
            
            # Retrieve user history for context
            user_history = await self._get_user_history(context.user_id, limit=5)
            
            output = {
                "session_id": context.session_id,
                "user_id": context.user_id,
                "mode": mode
            }
            
            # Generate requested outputs
            if mode in ["encouragement", "all"]:
                encouragement = await self._generate_encouragement(
                    context.user_id,
                    session_data,
                    user_history
                )
                output["encouragement"] = encouragement
            
            if mode in ["tips", "all"]:
                tips = await self._generate_tips(
                    context.user_id,
                    session_data,
                    user_history
                )
                output["tips"] = tips
            
            if mode in ["summary", "all"]:
                summary = await self._generate_session_summary(
                    context.session_id,
                    context.user_id,
                    session_data
                )
                output["summary"] = summary
            
            if mode in ["recommendations", "all"]:
                recommendations = await self._generate_recommendations(
                    context.user_id,
                    session_data,
                    user_history
                )
                output["recommendations"] = recommendations
            
            # Store session summary in memory bank
            if mode in ["summary", "all"] and self.memory_bank:
                try:
                    summary_data = output.get("summary", {})
                    await self.memory_bank.store_session(
                        context.session_id,
                        context.user_id,
                        summary_data
                    )
                except Exception as memory_error:
                    logger.warning(f"Failed to store session summary: {memory_error}")
            
            execution_time = (time.time() - start_time) * 1000
            
            return self._create_result(
                success=True,
                output=output,
                execution_time=execution_time
            )
            
        except ValueError as ve:
            execution_time = (time.time() - start_time) * 1000
            validation_error = ValidationError(
                message=str(ve),
                field="inputs",
                details={"session_id": context.session_id}
            )
            return self._create_result(
                success=False,
                output=None,
                error=validation_error.message,
                execution_time=execution_time
            )
        except MemoryError as mem_error:
            execution_time = (time.time() - start_time) * 1000
            return self._create_result(
                success=False,
                output=None,
                error=mem_error.message,
                execution_time=execution_time
            )
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            agent_error = AgentExecutionError(
                agent_name="companion",
                message=str(e),
                details={"session_id": context.session_id},
                original_error=e
            )
            return self._create_result(
                success=False,
                output=None,
                error=agent_error.message,
                execution_time=execution_time
            )

