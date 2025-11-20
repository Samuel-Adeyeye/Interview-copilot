"""
Question Bank for Interview Co-Pilot
Loads and manages coding interview questions from JSON file
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Set
from functools import lru_cache

logger = logging.getLogger(__name__)


class QuestionBank:
    """
    Manages a bank of coding interview questions.
    Supports filtering by difficulty, tags, and other criteria.
    """
    
    def __init__(self, questions_file: str = "data/questions_bank.json"):
        """
        Initialize QuestionBank with questions from JSON file.
        
        Args:
            questions_file: Path to JSON file containing questions
        """
        self.questions_file = Path(questions_file)
        self.questions: List[Dict] = []
        self.questions_by_id: Dict[str, Dict] = {}
        self._load_questions()
    
    def _load_questions(self):
        """Load questions from JSON file"""
        try:
            if not self.questions_file.exists():
                logger.warning(f"Questions file not found: {self.questions_file}. Creating default questions.")
                self._create_default_questions()
                return
            
            with open(self.questions_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Support both list format and object with 'questions' key
            if isinstance(data, list):
                self.questions = data
            elif isinstance(data, dict) and 'questions' in data:
                self.questions = data['questions']
            else:
                raise ValueError(f"Invalid JSON format in {self.questions_file}")
            
            # Validate and index questions
            self._validate_and_index()
            
            logger.info(f"Loaded {len(self.questions)} questions from {self.questions_file}")
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in questions file: {e}")
            self._create_default_questions()
        except Exception as e:
            logger.error(f"Error loading questions: {e}")
            self._create_default_questions()
    
    def _validate_and_index(self):
        """Validate questions and create index by ID"""
        valid_questions = []
        self.questions_by_id = {}
        
        for idx, question in enumerate(self.questions):
            try:
                # Validate required fields
                if not isinstance(question, dict):
                    logger.warning(f"Question at index {idx} is not a dict, skipping")
                    continue
                
                required_fields = ['id', 'title', 'difficulty', 'description']
                missing_fields = [field for field in required_fields if field not in question]
                
                if missing_fields:
                    logger.warning(f"Question at index {idx} missing fields: {missing_fields}, skipping")
                    continue
                
                # Validate difficulty
                if question['difficulty'] not in ['easy', 'medium', 'hard']:
                    logger.warning(f"Question {question.get('id')} has invalid difficulty: {question['difficulty']}")
                    question['difficulty'] = 'medium'  # Default to medium
                
                # Ensure optional fields exist
                question.setdefault('tags', [])
                question.setdefault('examples', [])
                question.setdefault('test_cases', [])
                question.setdefault('hints', [])
                question.setdefault('constraints', '')
                question.setdefault('time_complexity', '')
                question.setdefault('space_complexity', '')
                
                # Index by ID
                question_id = question['id']
                if question_id in self.questions_by_id:
                    logger.warning(f"Duplicate question ID: {question_id}, overwriting")
                
                self.questions_by_id[question_id] = question
                valid_questions.append(question)
                
            except Exception as e:
                logger.error(f"Error validating question at index {idx}: {e}")
                continue
        
        self.questions = valid_questions
        logger.info(f"Validated {len(self.questions)} questions")
    
    def _create_default_questions(self):
        """Create default questions if file doesn't exist"""
        logger.info("Creating default questions bank")
        default_questions = [
            {
                "id": "q1",
                "title": "Two Sum",
                "difficulty": "easy",
                "description": "Given an array of integers nums and an integer target, return indices of the two numbers that add up to target. You may assume that each input would have exactly one solution, and you may not use the same element twice.",
                "tags": ["arrays", "hash-table"],
                "examples": [
                    {"input": "nums = [2,7,11,15], target = 9", "output": "[0,1]", "explanation": "Because nums[0] + nums[1] == 9, we return [0, 1]."}
                ],
                "test_cases": [
                    {"input": "[2,7,11,15]\n9", "expected_output": "[0, 1]"},
                    {"input": "[3,2,4]\n6", "expected_output": "[1, 2]"},
                    {"input": "[3,3]\n6", "expected_output": "[0, 1]"}
                ],
                "hints": [
                    "Use a hash map to store numbers and their indices",
                    "For each number, check if target - number exists in the map"
                ],
                "constraints": "2 <= nums.length <= 10^4\n-10^9 <= nums[i] <= 10^9\n-10^9 <= target <= 10^9",
                "time_complexity": "O(n)",
                "space_complexity": "O(n)"
            },
            {
                "id": "q2",
                "title": "Valid Parentheses",
                "difficulty": "easy",
                "description": "Given a string s containing just the characters '(', ')', '{', '}', '[' and ']', determine if the input string is valid. An input string is valid if: 1) Open brackets must be closed by the same type of brackets. 2) Open brackets must be closed in the correct order. 3) Every close bracket has a corresponding open bracket of the same type.",
                "tags": ["string", "stack"],
                "examples": [
                    {"input": "s = \"()\"", "output": "true"},
                    {"input": "s = \"()[]{}\"", "output": "true"},
                    {"input": "s = \"(]\"", "output": "false"}
                ],
                "test_cases": [
                    {"input": "\"()\"", "expected_output": "True"},
                    {"input": "\"()[]{}\"", "expected_output": "True"},
                    {"input": "\"(]\"", "expected_output": "False"}
                ],
                "hints": [
                    "Use a stack to keep track of opening brackets",
                    "When you see a closing bracket, check if it matches the top of the stack"
                ],
                "constraints": "1 <= s.length <= 10^4\ns consists of parentheses only '()[]{}'",
                "time_complexity": "O(n)",
                "space_complexity": "O(n)"
            },
            {
                "id": "q3",
                "title": "Merge Intervals",
                "difficulty": "medium",
                "description": "Given an array of intervals where intervals[i] = [start_i, end_i], merge all overlapping intervals, and return an array of the non-overlapping intervals that cover all the intervals in the input.",
                "tags": ["arrays", "sorting"],
                "examples": [
                    {"input": "intervals = [[1,3],[2,6],[8,10],[15,18]]", "output": "[[1,6],[8,10],[15,18]]", "explanation": "Since intervals [1,3] and [2,6] overlap, merge them into [1,6]."}
                ],
                "test_cases": [
                    {"input": "[[1,3],[2,6],[8,10],[15,18]]", "expected_output": "[[1, 6], [8, 10], [15, 18]]"},
                    {"input": "[[1,4],[4,5]]", "expected_output": "[[1, 5]]"}
                ],
                "hints": [
                    "Sort intervals by start time",
                    "Iterate and merge overlapping intervals"
                ],
                "constraints": "1 <= intervals.length <= 10^4\nintervals[i].length == 2\n0 <= start_i <= end_i <= 10^4",
                "time_complexity": "O(n log n)",
                "space_complexity": "O(n)"
            },
            {
                "id": "q4",
                "title": "Longest Substring Without Repeating Characters",
                "difficulty": "medium",
                "description": "Given a string s, find the length of the longest substring without repeating characters.",
                "tags": ["string", "sliding-window", "hash-table"],
                "examples": [
                    {"input": "s = \"abcabcbb\"", "output": "3", "explanation": "The answer is \"abc\", with the length of 3."}
                ],
                "test_cases": [
                    {"input": "\"abcabcbb\"", "expected_output": "3"},
                    {"input": "\"bbbbb\"", "expected_output": "1"},
                    {"input": "\"pwwkew\"", "expected_output": "3"}
                ],
                "hints": [
                    "Use sliding window technique",
                    "Keep track of characters in current window using a set or map"
                ],
                "constraints": "0 <= s.length <= 5 * 10^4\ns consists of English letters, digits, symbols and spaces",
                "time_complexity": "O(n)",
                "space_complexity": "O(min(n, m)) where m is the size of charset"
            },
            {
                "id": "q5",
                "title": "Binary Tree Level Order Traversal",
                "difficulty": "medium",
                "description": "Given the root of a binary tree, return the level order traversal of its nodes' values. (i.e., from left to right, level by level).",
                "tags": ["tree", "breadth-first-search"],
                "examples": [
                    {"input": "root = [3,9,20,null,null,15,7]", "output": "[[3],[9,20],[15,7]]"}
                ],
                "test_cases": [
                    {"input": "[3,9,20,null,null,15,7]", "expected_output": "[[3], [9, 20], [15, 7]]"}
                ],
                "hints": [
                    "Use BFS (Breadth-First Search)",
                    "Process nodes level by level using a queue"
                ],
                "constraints": "The number of nodes in the tree is in the range [0, 2000]\n-1000 <= Node.val <= 1000",
                "time_complexity": "O(n)",
                "space_complexity": "O(n)"
            }
        ]
        
        self.questions = default_questions
        self._validate_and_index()
        
        # Save to file for future use
        try:
            self.questions_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.questions_file, 'w', encoding='utf-8') as f:
                json.dump({"questions": self.questions}, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved default questions to {self.questions_file}")
        except Exception as e:
            logger.warning(f"Could not save default questions to file: {e}")
    
    def get_questions_by_difficulty(self, difficulty: str) -> List[Dict]:
        """
        Get all questions of a specific difficulty level.
        
        Args:
            difficulty: One of 'easy', 'medium', 'hard'
        
        Returns:
            List of question dictionaries
        """
        if difficulty not in ['easy', 'medium', 'hard']:
            logger.warning(f"Invalid difficulty: {difficulty}, defaulting to 'medium'")
            difficulty = 'medium'
        
        filtered = [q for q in self.questions if q.get('difficulty') == difficulty]
        logger.debug(f"Found {len(filtered)} questions with difficulty '{difficulty}'")
        return filtered
    
    def get_question_by_id(self, question_id: str) -> Optional[Dict]:
        """
        Get a specific question by its ID.
        
        Args:
            question_id: The unique identifier of the question
        
        Returns:
            Question dictionary or None if not found
        """
        question = self.questions_by_id.get(question_id)
        if question is None:
            logger.warning(f"Question with ID '{question_id}' not found")
        return question
    
    def filter_by_tags(self, tags: List[str]) -> List[Dict]:
        """
        Filter questions by tags.
        
        Args:
            tags: List of tag strings to filter by
        
        Returns:
            List of questions that have at least one of the specified tags
        """
        if not tags:
            return self.questions
        
        tag_set = set(tag.lower() for tag in tags)
        filtered = [
            q for q in self.questions
            if tag_set.intersection(set(tag.lower() for tag in q.get('tags', [])))
        ]
        logger.debug(f"Found {len(filtered)} questions matching tags: {tags}")
        return filtered
    
    def get_all_questions(self) -> List[Dict]:
        """
        Get all questions in the bank.
        
        Returns:
            List of all question dictionaries
        """
        return self.questions.copy()
    
    def get_question_count(self) -> int:
        """Get total number of questions"""
        return len(self.questions)
    
    def get_questions_by_difficulty_and_tags(
        self, 
        difficulty: str, 
        tags: List[str] = None
    ) -> List[Dict]:
        """
        Get questions filtered by both difficulty and tags.
        
        Args:
            difficulty: One of 'easy', 'medium', 'hard'
            tags: Optional list of tags to filter by
        
        Returns:
            List of matching question dictionaries
        """
        questions = self.get_questions_by_difficulty(difficulty)
        
        if tags:
            questions = self.filter_by_tags(tags)
            # Re-filter by difficulty
            questions = [q for q in questions if q.get('difficulty') == difficulty]
        
        return questions
    
    def search_questions(self, query: str) -> List[Dict]:
        """
        Search questions by title or description (simple text matching).
        
        Args:
            query: Search query string
        
        Returns:
            List of questions matching the query
        """
        if not query:
            return []
        
        query_lower = query.lower()
        matching = [
            q for q in self.questions
            if query_lower in q.get('title', '').lower()
            or query_lower in q.get('description', '').lower()
        ]
        logger.debug(f"Found {len(matching)} questions matching query: '{query}'")
        return matching
    
    def reload(self):
        """Reload questions from file"""
        logger.info("Reloading questions from file")
        self.questions = []
        self.questions_by_id = {}
        self._load_questions()

