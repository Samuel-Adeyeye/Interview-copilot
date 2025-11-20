"""
Code Editor Component for Streamlit
"""

import streamlit as st
from typing import Dict, Any, Optional

def code_editor_component(
    default_code: str = "",
    language: str = "python",
    height: int = 400,
    key: str = "code_editor"
) -> Dict[str, Any]:
    """
    Code editor component with syntax highlighting
    
    Args:
        default_code: Default code to display
        language: Programming language (python, javascript, java, cpp)
        height: Editor height in pixels
        key: Streamlit component key
    
    Returns:
        Dictionary with 'code' and 'language' keys
    """
    # Language selection
    languages = {
        "python": "Python",
        "javascript": "JavaScript",
        "java": "Java",
        "cpp": "C++"
    }
    
    selected_lang = st.selectbox(
        "Language",
        options=list(languages.keys()),
        format_func=lambda x: languages[x],
        index=list(languages.keys()).index(language) if language in languages else 0,
        key=f"{key}_lang"
    )
    
    # Code editor using text_area (Streamlit doesn't have built-in code editor)
    # For better experience, we can use streamlit-ace if available
    try:
        from streamlit_ace import st_ace
        code = st_ace(
            value=default_code,
            language=selected_lang,
            theme="monokai",
            key=key,
            height=height,
            font_size=14,
            auto_update=True
        )
    except ImportError:
        # Fallback to text_area if streamlit-ace not available
        st.info("💡 Install `streamlit-ace` for better code editing: `pip install streamlit-ace`")
        code = st.text_area(
            "Code",
            value=default_code,
            height=height,
            key=key,
            help="Enter your code here"
        )
    
    return {
        "code": code,
        "language": selected_lang
    }

