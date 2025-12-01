"""
ADK MCP Tools Utility
Shared utilities for creating MCP tools.
"""

import os
import logging
import shutil
from typing import Optional, List
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters
from google.adk.tools import FunctionTool

logger = logging.getLogger(__name__)

def create_brave_search_mcp_tool() -> Optional[McpToolset]:
    """
    Create the Brave Search MCP Toolset.
    
    Returns:
        McpToolset if successful, None otherwise.
    """
    # Check if npx is available
    npx_path = shutil.which("npx")
    
    # If not in PATH, check common locations
    if not npx_path and os.path.exists("/usr/local/bin/npx"):
        npx_path = "/usr/local/bin/npx"
    
    # Get API key
    brave_api_key = os.getenv("BRAVE_API_KEY")
    
    if not npx_path:
        logger.warning("⚠️ 'npx' not found. Cannot create Brave Search MCP tool.")
        return None
        
    if not brave_api_key:
        logger.warning("⚠️ BRAVE_API_KEY not found. Cannot create Brave Search MCP tool.")
        return None
    
    try:
        mcp_toolset = McpToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command=npx_path,
                    args=["-y", "@modelcontextprotocol/server-brave-search"],
                    env={
                        **os.environ, 
                        "BRAVE_API_KEY": brave_api_key,
                        "PATH": f"/usr/local/bin:{os.environ.get('PATH', '')}"
                    }
                ),
                timeout=30
            )
        )
        logger.info("✅ Brave Search MCP Tool created")
        return mcp_toolset
    except Exception as e:
        logger.error(f"Failed to initialize Brave Search MCP tool: {e}")
        return None
