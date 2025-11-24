"""
Comprehensive unit tests for Interview Co-Pilot tools
"""
import pytest
import json
import tempfile
import os
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from tools.question_bank import QuestionBank
from tools.code_exec_tool import CodeExecutionTool, create_code_exec_tool
from tools.search_tool import create_search_tool
from tools.jd_parser_tool import create_jd_parser_tool, extract_basic_info, ParsedJobDescription
from exceptions import CodeExecutionError, APIError


class TestQuestionBank:
    """Tests for QuestionBank"""
    
    def test_question_bank_initialization(self):
        """Test QuestionBank initialization with default questions"""
        qb = QuestionBank()
        assert qb.get_question_count() > 0
        assert len(qb.questions) > 0
    
    def test_question_bank_load_from_file(self):
        """Test loading questions from JSON file"""
        # Create temporary questions file
        questions_data = {
            "questions": [
                {
                    "id": "test_q1",
                    "title": "Test Question 1",
                    "difficulty": "easy",
                    "description": "Test description",
                    "tags": ["test"],
                    "test_cases": []
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(questions_data, f)
            temp_path = f.name
        
        try:
            qb = QuestionBank(temp_path)
            assert qb.get_question_count() == 1
            assert qb.get_question_by_id("test_q1") is not None
        finally:
            os.unlink(temp_path)
    
    def test_question_bank_get_by_difficulty(self):
        """Test filtering questions by difficulty"""
        qb = QuestionBank()
        
        easy_questions = qb.get_questions_by_difficulty("easy")
        medium_questions = qb.get_questions_by_difficulty("medium")
        hard_questions = qb.get_questions_by_difficulty("hard")
        
        assert all(q["difficulty"] == "easy" for q in easy_questions)
        assert all(q["difficulty"] == "medium" for q in medium_questions)
        assert all(q["difficulty"] == "hard" for q in hard_questions)
    
    def test_question_bank_get_by_id(self):
        """Test getting question by ID"""
        qb = QuestionBank()
        
        # Get first question
        if qb.questions:
            first_q = qb.questions[0]
            question_id = first_q["id"]
            
            found = qb.get_question_by_id(question_id)
            assert found is not None
            assert found["id"] == question_id
    
    def test_question_bank_get_by_id_not_found(self):
        """Test getting non-existent question"""
        qb = QuestionBank()
        result = qb.get_question_by_id("nonexistent_id")
        assert result is None
    
    def test_question_bank_filter_by_tags(self):
        """Test filtering questions by tags"""
        qb = QuestionBank()
        
        # Filter by a common tag
        array_questions = qb.filter_by_tags(["arrays"])
        assert isinstance(array_questions, list)
        
        # All returned questions should have the tag
        for q in array_questions:
            assert "arrays" in [tag.lower() for tag in q.get("tags", [])]
    
    def test_question_bank_search_questions(self):
        """Test searching questions"""
        qb = QuestionBank()
        
        # Search for a common term
        results = qb.search_questions("sum")
        assert isinstance(results, list)
        
        # Results should contain the search term
        for q in results:
            title = q.get("title", "").lower()
            desc = q.get("description", "").lower()
            assert "sum" in title or "sum" in desc
    
    def test_question_bank_invalid_difficulty(self):
        """Test handling invalid difficulty"""
        qb = QuestionBank()
        
        # Invalid difficulty should default to medium
        results = qb.get_questions_by_difficulty("invalid")
        # Should return empty or default to medium
        assert isinstance(results, list)
    
    def test_question_bank_reload(self):
        """Test reloading questions"""
        qb = QuestionBank()
        initial_count = qb.get_question_count()
        
        qb.reload()
        assert qb.get_question_count() == initial_count


class TestCodeExecutionTool:
    """Tests for CodeExecutionTool"""
    
    @pytest.fixture
    def code_exec_tool(self):
        """Create CodeExecutionTool instance"""
        return CodeExecutionTool(judge0_api_key="test_key")
    
    def test_code_exec_tool_initialization(self):
        """Test CodeExecutionTool initialization"""
        tool = CodeExecutionTool(judge0_api_key="test_key")
        assert tool.api_key == "test_key"
        assert tool.timeout_seconds == 10
        assert "python" in tool.language_map
    
    def test_code_sanitization(self, code_exec_tool):
        """Test code sanitization"""
        dangerous_code = """
import os
import subprocess
def test():
    eval("malicious code")
    exec("bad code")
    open("/etc/passwd")
"""
        sanitized = code_exec_tool._sanitize_code(dangerous_code, "python")
        
        assert "BLOCKED" in sanitized or "#" in sanitized
        assert "import os" not in sanitized or "BLOCKED" in sanitized
    
    def test_cache_key_generation(self, code_exec_tool):
        """Test cache key generation"""
        key1 = code_exec_tool._get_cache_key("code1", "python", "input1")
        key2 = code_exec_tool._get_cache_key("code1", "python", "input1")
        key3 = code_exec_tool._get_cache_key("code2", "python", "input1")
        
        assert key1 == key2  # Same inputs should generate same key
        assert key1 != key3  # Different code should generate different key
    
    @pytest.mark.asyncio
    async def test_execute_code_success(self, code_exec_tool):
        """Test successful code execution"""
        # Mock httpx client
        mock_response = Mock()
        mock_response.json.return_value = {
            "token": "test_token"
        }
        mock_response.status_code = 201
        
        mock_result_response = Mock()
        mock_result_response.json.return_value = {
            "status": {"id": 3, "description": "Accepted"},
            "stdout": "[0, 1]",
            "stderr": "",
            "time": "0.1"
        }
        mock_result_response.status_code = 200
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            
            # Mock POST (submission)
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            # Mock GET (result)
            mock_client_instance.get = AsyncMock(return_value=mock_result_response)
            
            test_cases = [
                {"input": "[2,7,11,15]\n9", "expected_output": "[0, 1]"}
            ]
            
            result = await code_exec_tool.execute_code(
                code="def two_sum(nums, target): return [0, 1]",
                language="python",
                test_cases=test_cases
            )
            
            assert result["status"] == "success"
            assert result["testsPassed"] == 1
            assert result["totalTests"] == 1
    
    @pytest.mark.asyncio
    async def test_execute_code_timeout(self, code_exec_tool):
        """Test code execution timeout"""
        code_exec_tool.timeout_seconds = 0.1  # Very short timeout
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            
            # Mock slow response
            async def slow_post(*args, **kwargs):
                await asyncio.sleep(1)  # Longer than timeout
                return Mock(json=lambda: {"token": "test"})
            
            mock_client_instance.post = slow_post
            
            test_cases = [{"input": "test", "expected_output": "test"}]
            
            with pytest.raises(CodeExecutionError, match="timed out"):
                await code_exec_tool.execute_code(
                    code="print('test')",
                    language="python",
                    test_cases=test_cases
                )
    
    @pytest.mark.asyncio
    async def test_execute_code_api_error(self, code_exec_tool):
        """Test handling API errors"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            
            # Mock API error
            from httpx import HTTPStatusError
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            
            error = HTTPStatusError("API Error", request=Mock(), response=mock_response)
            mock_client_instance.post = AsyncMock(side_effect=error)
            
            test_cases = [{"input": "test", "expected_output": "test"}]
            
            with pytest.raises((CodeExecutionError, APIError)):
                await code_exec_tool.execute_code(
                    code="print('test')",
                    language="python",
                    test_cases=test_cases
                )
    
    def test_create_code_exec_tool(self):
        """Test create_code_exec_tool factory function"""
        tool = create_code_exec_tool("test_key")
        assert tool is not None
        assert isinstance(tool, CodeExecutionTool)


class TestSearchTool:
    """Tests for SearchTool"""
    
    def test_create_search_tool_with_key(self):
        """Test creating search tool with API key"""
        with patch.dict(os.environ, {"TAVILY_API_KEY": "test_key"}):
            tool = create_search_tool()
            assert tool is not None
            assert tool.name == "web_search"
    
    def test_create_search_tool_without_key(self):
        """Test creating search tool without API key"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(APIError, match="TAVILY_API_KEY not set"):
                create_search_tool()


class TestJDParserTool:
    """Tests for JDParserTool"""
    
    def test_extract_basic_info(self):
        """Test basic info extraction from JD text"""
        jd_text = """
        We are looking for a Senior Python Developer with 5+ years of experience.
        Required skills: Python, FastAPI, PostgreSQL, AWS.
        Location: San Francisco, CA (Remote available)
        """
        
        info = extract_basic_info(jd_text)
        
        assert "Python" in info["skills"]
        assert info["experience_years"] == "5"
        assert info["location"] is not None
    
    def test_extract_basic_info_no_match(self):
        """Test extraction with no matches"""
        jd_text = "Generic job description without specific details."
        info = extract_basic_info(jd_text)
        
        assert isinstance(info, dict)
        assert "skills" in info
    
    @pytest.mark.asyncio
    async def test_create_jd_parser_tool(self, mock_llm):
        """Test creating JD parser tool"""
        tool = create_jd_parser_tool(mock_llm)
        assert tool is not None
        assert tool.name == "parse_job_description"
    
    @pytest.mark.asyncio
    async def test_jd_parser_tool_execution(self, mock_llm):
        """Test JD parser tool execution"""
        # Mock structured LLM output
        mock_structured_llm = Mock()
        mock_parsed = ParsedJobDescription(
            job_title="Senior Software Engineer",
            company_name="TestCorp",
            requirements=["5+ years Python"],
            skills=["Python", "FastAPI"],
            experience_years="5",
            responsibilities=["Develop APIs"]
        )
        mock_structured_llm.ainvoke = AsyncMock(return_value=mock_parsed)
        mock_llm.with_structured_output = Mock(return_value=mock_structured_llm)
        
        tool = create_jd_parser_tool(mock_llm)
        
        jd_text = "We need a Senior Software Engineer with Python experience."
        result = await tool.ainvoke({"jd_text": jd_text})
        
        assert result is not None
        assert "job_title" in result or hasattr(result, "job_title")
    
    def test_parsed_job_description_model(self):
        """Test ParsedJobDescription Pydantic model"""
        parsed = ParsedJobDescription(
            job_title="Software Engineer",
            company_name="TestCorp",
            requirements=["Python"],
            skills=["Python", "FastAPI"]
        )
        
        assert parsed.job_title == "Software Engineer"
        assert parsed.company_name == "TestCorp"
        assert len(parsed.requirements) == 1
        assert len(parsed.skills) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

