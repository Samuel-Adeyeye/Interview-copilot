"""
Tests for ADK Tools
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any


@pytest.mark.unit
@pytest.mark.tools
class TestADKSearchTool:
    """Tests for ADK Search Tool"""
    
    def test_create_adk_search_tool(self):
        """Test creating ADK search tool"""
        from tools.adk.search_tool import create_adk_search_tool
        
        with patch('tools.adk.search_tool.google_search') as mock_search:
            tool = create_adk_search_tool()
            assert tool is not None
            # Tool should be google_search (or a wrapper)
            assert tool == mock_search or hasattr(tool, '__call__')
    
    def test_get_search_tool_alias(self):
        """Test get_search_tool alias"""
        from tools.adk.search_tool import get_search_tool
        
        with patch('tools.adk.search_tool.google_search'):
            tool = get_search_tool()
            assert tool is not None


@pytest.mark.unit
@pytest.mark.tools
class TestADKCodeExecTool:
    """Tests for ADK Code Execution Tool"""
    
    def test_create_builtin_code_executor(self):
        """Test creating built-in code executor"""
        from tools.adk.code_exec_tool import create_builtin_code_executor
        
        with patch('tools.adk.code_exec_tool.BuiltInCodeExecutor') as mock_executor:
            executor = create_builtin_code_executor()
            # Should create BuiltInCodeExecutor instance
            assert executor is not None
    
    @patch('tools.adk.code_exec_tool.CodeExecutionTool')
    @patch('tools.adk.code_exec_tool.FunctionTool')
    def test_create_judge0_code_exec_tool(self, mock_function_tool, mock_code_exec):
        """Test creating Judge0 code execution tool"""
        from tools.adk.code_exec_tool import create_judge0_code_exec_tool
        import os
        
        with patch.dict(os.environ, {'JUDGE0_API_KEY': 'test-key'}):
            tool = create_judge0_code_exec_tool(judge0_api_key='test-key')
            # Should return FunctionTool or None
            assert tool is None or hasattr(tool, 'func')
    
    def test_create_code_exec_tool_factory(self):
        """Test code execution tool factory"""
        from tools.adk.code_exec_tool import create_code_exec_tool
        
        with patch('tools.adk.code_exec_tool.create_builtin_code_executor') as mock_builtin:
            executor = create_code_exec_tool(use_builtin=True)
            assert executor is not None


@pytest.mark.unit
@pytest.mark.tools
class TestADKQuestionBankTool:
    """Tests for ADK Question Bank Tools"""
    
    @patch('tools.adk.question_bank_tool.QuestionBank')
    @patch('tools.adk.question_bank_tool.FunctionTool')
    def test_create_question_bank_tools(self, mock_function_tool, mock_question_bank):
        """Test creating question bank tools"""
        from tools.adk.question_bank_tool import create_question_bank_tools
        
        tools = create_question_bank_tools()
        assert isinstance(tools, list)
        assert len(tools) > 0
    
    @patch('tools.adk.question_bank_tool.QuestionBank')
    @patch('tools.adk.question_bank_tool.FunctionTool')
    def test_get_questions_by_difficulty_tool(self, mock_function_tool, mock_question_bank):
        """Test get_questions_by_difficulty tool"""
        from tools.adk.question_bank_tool import get_question_selection_tool
        
        tool = get_question_selection_tool()
        assert tool is not None


@pytest.mark.unit
@pytest.mark.tools
class TestADKJDParserTool:
    """Tests for ADK JD Parser Tool"""
    
    @patch('tools.adk.jd_parser_tool.FunctionTool')
    def test_create_jd_parser_tools(self, mock_function_tool):
        """Test creating JD parser tools"""
        from tools.adk.jd_parser_tool import create_jd_parser_tools
        
        tools = create_jd_parser_tools()
        assert isinstance(tools, list)
        assert len(tools) > 0
    
    @patch('tools.adk.jd_parser_tool.FunctionTool')
    def test_get_jd_parser_tool(self, mock_function_tool):
        """Test getting JD parser tool"""
        from tools.adk.jd_parser_tool import get_jd_parser_tool
        
        tool = get_jd_parser_tool()
        assert tool is not None


@pytest.mark.integration
@pytest.mark.tools
class TestADKToolsIntegration:
    """Integration tests for ADK tools"""
    
    def test_tool_imports(self):
        """Test that all ADK tools can be imported"""
        from tools.adk import (
            create_adk_search_tool,
            create_code_exec_tool,
            create_question_bank_tools,
            get_jd_parser_tool
        )
        
        # All imports should succeed
        assert create_adk_search_tool is not None
        assert create_code_exec_tool is not None
        assert create_question_bank_tools is not None
        assert get_jd_parser_tool is not None

