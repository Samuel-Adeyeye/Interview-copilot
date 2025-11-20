"""
Evaluation Service for Interview Co-Pilot
Calculates scores, tracks progress, and generates recommendations
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class EvaluationService:
    """
    Service for evaluating code submissions and tracking user progress
    """
    
    def __init__(self, memory_bank=None):
        """
        Initialize evaluation service
        
        Args:
            memory_bank: Optional MemoryBank instance for storing evaluations
        """
        self.memory_bank = memory_bank
    
    def evaluate_code_submission(
        self,
        code: str,
        question: Dict[str, Any],
        execution_result: Dict[str, Any],
        language: str = "python"
    ) -> Dict[str, Any]:
        """
        Evaluate a code submission comprehensively
        
        Args:
            code: Submitted code
            question: Question dictionary with test cases, hints, etc.
            execution_result: Result from code execution tool
            language: Programming language
        
        Returns:
            Comprehensive evaluation dictionary
        """
        # Calculate correctness score
        tests_passed = execution_result.get("testsPassed", 0)
        total_tests = execution_result.get("totalTests", 0)
        correctness_score = tests_passed / total_tests if total_tests > 0 else 0.0
        
        # Evaluate code quality
        quality_score = self._evaluate_code_quality(code, language)
        
        # Analyze efficiency
        efficiency_score = self._evaluate_efficiency(code, question, execution_result)
        
        # Calculate overall score (weighted average)
        overall_score = (
            correctness_score * 0.5 +  # 50% correctness
            quality_score * 0.3 +       # 30% code quality
            efficiency_score * 0.2      # 20% efficiency
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            correctness_score,
            quality_score,
            efficiency_score,
            code,
            question
        )
        
        return {
            "correctness": correctness_score,
            "code_quality": quality_score,
            "efficiency": efficiency_score,
            "overall": overall_score,
            "tests_passed": tests_passed,
            "total_tests": total_tests,
            "recommendations": recommendations,
            "evaluated_at": datetime.utcnow().isoformat()
        }
    
    def _evaluate_code_quality(self, code: str, language: str) -> float:
        """
        Evaluate code quality based on various metrics
        
        Returns:
            Score between 0.0 and 1.0
        """
        score = 1.0
        
        # Check for code smells
        issues = []
        
        # Long functions (rough estimate)
        lines = code.split('\n')
        function_lines = 0
        in_function = False
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('def ') or stripped.startswith('async def '):
                if in_function and function_lines > 50:
                    issues.append("Long function detected")
                function_lines = 0
                in_function = True
            elif in_function:
                function_lines += 1
        
        # Check for comments
        comment_count = sum(1 for line in lines if line.strip().startswith('#') or '"""' in line or "'''" in line)
        if comment_count < len(lines) * 0.1:  # Less than 10% comments
            issues.append("Low comment coverage")
        
        # Check for meaningful variable names
        import re
        variable_pattern = r'\b[a-z_][a-z0-9_]*\b'
        variables = re.findall(variable_pattern, code.lower())
        short_vars = [v for v in variables if len(v) < 2]
        if len(short_vars) > len(variables) * 0.3:  # More than 30% very short names
            issues.append("Many short variable names")
        
        # Deduct points for issues
        score -= len(issues) * 0.1
        return max(0.0, min(1.0, score))
    
    def _evaluate_efficiency(
        self,
        code: str,
        question: Dict[str, Any],
        execution_result: Dict[str, Any]
    ) -> float:
        """
        Evaluate code efficiency
        
        Returns:
            Score between 0.0 and 1.0
        """
        # Get expected complexity from question
        expected_time = question.get("time_complexity", "")
        expected_space = question.get("space_complexity", "")
        
        # For now, assume full score if tests pass and execution is fast
        # In a real implementation, you'd analyze the code structure
        avg_execution_time = 0.0
        test_results = execution_result.get("test_results", [])
        if test_results:
            times = [r.get("execution_time", 0) for r in test_results if r.get("execution_time")]
            if times:
                avg_execution_time = sum(times) / len(times)
        
        # Score based on execution time (faster is better, but this is simplified)
        if avg_execution_time < 0.1:
            return 1.0
        elif avg_execution_time < 1.0:
            return 0.8
        elif avg_execution_time < 5.0:
            return 0.6
        else:
            return 0.4
    
    def _generate_recommendations(
        self,
        correctness_score: float,
        quality_score: float,
        efficiency_score: float,
        code: str,
        question: Dict[str, Any]
    ) -> List[str]:
        """
        Generate personalized recommendations based on evaluation
        """
        recommendations = []
        
        if correctness_score < 1.0:
            recommendations.append("Focus on passing all test cases first")
            if correctness_score < 0.5:
                recommendations.append("Review the problem statement and examples carefully")
        
        if quality_score < 0.7:
            recommendations.append("Improve code readability with better variable names")
            recommendations.append("Add comments to explain complex logic")
        
        if efficiency_score < 0.7:
            recommendations.append("Consider optimizing your algorithm for better performance")
            expected_complexity = question.get("time_complexity", "")
            if expected_complexity:
                recommendations.append(f"Target complexity: {expected_complexity}")
        
        if not recommendations:
            recommendations.append("Great work! Your solution is correct and well-written")
            recommendations.append("Consider edge cases and error handling for production code")
        
        return recommendations
    
    def compare_to_baseline(
        self,
        current_evaluation: Dict[str, Any],
        baseline_evaluation: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Compare current evaluation to baseline or previous attempt
        
        Args:
            current_evaluation: Current evaluation results
            baseline_evaluation: Previous/baseline evaluation (optional)
        
        Returns:
            Comparison dictionary
        """
        if not baseline_evaluation:
            # Use default baseline
            baseline_evaluation = {
                "correctness": 0.5,
                "code_quality": 0.5,
                "efficiency": 0.5,
                "overall": 0.5
            }
        
        comparison = {
            "correctness_delta": current_evaluation["correctness"] - baseline_evaluation["correctness"],
            "code_quality_delta": current_evaluation["code_quality"] - baseline_evaluation["code_quality"],
            "efficiency_delta": current_evaluation["efficiency"] - baseline_evaluation["efficiency"],
            "overall_delta": current_evaluation["overall"] - baseline_evaluation["overall"],
            "improvement": current_evaluation["overall"] > baseline_evaluation["overall"]
        }
        
        return comparison
    
    def track_progress_over_time(
        self,
        user_id: str,
        session_evaluations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Track user progress over multiple sessions
        
        Args:
            user_id: User identifier
            session_evaluations: List of evaluation dictionaries from different sessions
        
        Returns:
            Progress tracking dictionary
        """
        if not session_evaluations:
            return {
                "user_id": user_id,
                "total_sessions": 0,
                "trend": "no_data",
                "improvement_rate": 0.0
            }
        
        # Calculate trends
        scores = [e.get("overall", 0) for e in session_evaluations]
        avg_score = sum(scores) / len(scores) if scores else 0.0
        
        # Determine trend
        if len(scores) >= 2:
            recent_avg = sum(scores[-3:]) / min(3, len(scores))
            earlier_avg = sum(scores[:-3]) / max(1, len(scores) - 3) if len(scores) > 3 else scores[0]
            
            if recent_avg > earlier_avg + 0.1:
                trend = "improving"
            elif recent_avg < earlier_avg - 0.1:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"
        
        improvement_rate = (scores[-1] - scores[0]) if len(scores) > 1 else 0.0
        
        return {
            "user_id": user_id,
            "total_sessions": len(session_evaluations),
            "average_score": avg_score,
            "trend": trend,
            "improvement_rate": improvement_rate,
            "scores": scores
        }
    
    def generate_evaluation_report(
        self,
        session_id: str,
        evaluations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive evaluation report for a session
        
        Args:
            session_id: Session identifier
            evaluations: List of code evaluation results
        
        Returns:
            Comprehensive report dictionary
        """
        if not evaluations:
            return {
                "session_id": session_id,
                "total_submissions": 0,
                "message": "No evaluations available"
            }
        
        # Aggregate scores
        avg_correctness = sum(e.get("correctness", 0) for e in evaluations) / len(evaluations)
        avg_quality = sum(e.get("code_quality", 0) for e in evaluations) / len(evaluations)
        avg_efficiency = sum(e.get("efficiency", 0) for e in evaluations) / len(evaluations)
        avg_overall = sum(e.get("overall", 0) for e in evaluations) / len(evaluations)
        
        # Collect all recommendations
        all_recommendations = []
        for eval_result in evaluations:
            all_recommendations.extend(eval_result.get("recommendations", []))
        
        # Get unique recommendations
        unique_recommendations = list(set(all_recommendations))
        
        return {
            "session_id": session_id,
            "total_submissions": len(evaluations),
            "average_scores": {
                "correctness": avg_correctness,
                "code_quality": avg_quality,
                "efficiency": avg_efficiency,
                "overall": avg_overall
            },
            "recommendations": unique_recommendations,
            "generated_at": datetime.utcnow().isoformat()
        }

