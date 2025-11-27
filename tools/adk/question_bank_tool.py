"""
ADK Question Bank Tool
Wraps QuestionBank as ADK FunctionTools
"""

from google.adk.tools import FunctionTool
from tools.question_bank import QuestionBank
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

# Global question bank instance (lazy loaded)
_question_bank: Optional[QuestionBank] = None


def get_question_bank() -> QuestionBank:
    """Get or create question bank instance"""
    global _question_bank
    if _question_bank is None:
        _question_bank = QuestionBank("data/questions_bank.json")
    return _question_bank


def get_questions_by_difficulty(difficulty: str) -> Dict[str, Any]:
    """
    Get coding interview questions filtered by difficulty level.
    
    This tool retrieves questions from the question bank based on their
    difficulty level. Useful for selecting appropriate questions for
    technical interviews.
    
    Args:
        difficulty: One of 'easy', 'medium', 'hard'
    
    Returns:
        Dictionary with status and questions list:
        {
            "status": "success" | "error",
            "questions": [...],
            "count": int,
            "error_message": str (if error)
        }
    """
    try:
        qb = get_question_bank()
        questions = qb.get_questions_by_difficulty(difficulty)
        
        return {
            "status": "success",
            "questions": questions,
            "count": len(questions),
            "difficulty": difficulty
        }
    except Exception as e:
        logger.error(f"Error getting questions by difficulty: {e}")
        return {
            "status": "error",
            "error_message": str(e),
            "questions": [],
            "count": 0
        }


def get_question_by_id(question_id: str) -> Dict[str, Any]:
    """
    Get a specific coding interview question by its ID.
    
    This tool retrieves a single question from the question bank using
    its unique identifier. Useful for getting full question details
    including test cases, hints, and examples.
    
    Args:
        question_id: The unique identifier of the question (e.g., "q1", "q2")
    
    Returns:
        Dictionary with status and question data:
        {
            "status": "success" | "error",
            "question": {...} | None,
            "error_message": str (if error)
        }
    """
    try:
        qb = get_question_bank()
        question = qb.get_question_by_id(question_id)
        
        if question is None:
            return {
                "status": "error",
                "error_message": f"Question with ID '{question_id}' not found",
                "question": None
            }
        
        return {
            "status": "success",
            "question": question
        }
    except Exception as e:
        logger.error(f"Error getting question by ID: {e}")
        return {
            "status": "error",
            "error_message": str(e),
            "question": None
        }


def filter_questions_by_tags(tags: List[str]) -> Dict[str, Any]:
    """
    Filter coding interview questions by tags.
    
    This tool retrieves questions that match any of the provided tags.
    Useful for finding questions related to specific topics like
    "arrays", "dynamic-programming", "trees", etc.
    
    Args:
        tags: List of tag strings to filter by (e.g., ["arrays", "hash-table"])
    
    Returns:
        Dictionary with status and filtered questions:
        {
            "status": "success" | "error",
            "questions": [...],
            "count": int,
            "tags": List[str],
            "error_message": str (if error)
        }
    """
    try:
        qb = get_question_bank()
        questions = qb.filter_by_tags(tags)
        
        return {
            "status": "success",
            "questions": questions,
            "count": len(questions),
            "tags": tags
        }
    except Exception as e:
        logger.error(f"Error filtering questions by tags: {e}")
        return {
            "status": "error",
            "error_message": str(e),
            "questions": [],
            "count": 0
        }


def search_questions(query: str) -> Dict[str, Any]:
    """
    Search coding interview questions by title or description.
    
    This tool performs a text search across question titles and descriptions
    to find relevant questions. Useful for finding questions on specific topics.
    
    Args:
        query: Search query string (e.g., "two sum", "binary tree")
    
    Returns:
        Dictionary with status and matching questions:
        {
            "status": "success" | "error",
            "questions": [...],
            "count": int,
            "query": str,
            "error_message": str (if error)
        }
    """
    try:
        qb = get_question_bank()
        questions = qb.search_questions(query)
        
        return {
            "status": "success",
            "questions": questions,
            "count": len(questions),
            "query": query
        }
    except Exception as e:
        logger.error(f"Error searching questions: {e}")
        return {
            "status": "error",
            "error_message": str(e),
            "questions": [],
            "count": 0
        }


def get_question_count() -> Dict[str, Any]:
    """
    Get the total number of questions in the question bank.
    
    Returns:
        Dictionary with status and count:
        {
            "status": "success",
            "count": int
        }
    """
    try:
        qb = get_question_bank()
        count = qb.get_question_count()
        
        return {
            "status": "success",
            "count": count
        }
    except Exception as e:
        logger.error(f"Error getting question count: {e}")
        return {
            "status": "error",
            "error_message": str(e),
            "count": 0
        }


# Create ADK FunctionTools
def create_question_bank_tools() -> List[FunctionTool]:
    """
    Create all question bank tools as ADK FunctionTools.
    
    Returns:
        List of FunctionTool instances for question bank operations
    """
    tools = [
        FunctionTool(get_questions_by_difficulty),
        FunctionTool(get_question_by_id),
        FunctionTool(filter_questions_by_tags),
        FunctionTool(search_questions),
        FunctionTool(get_question_count)
    ]
    
    logger.info(f"✅ Created {len(tools)} question bank tools")
    return tools


# Convenience function to get specific tools
def get_question_selection_tool() -> FunctionTool:
    """Get tool for selecting questions by difficulty"""
    return FunctionTool(get_questions_by_difficulty)


def get_question_lookup_tool() -> FunctionTool:
    """Get tool for looking up specific questions by ID"""
    return FunctionTool(get_question_by_id)

