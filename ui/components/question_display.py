"""
Question Display Component for Streamlit
"""

import streamlit as st
from typing import Dict, Any, Optional

def question_display_component(question: Dict[str, Any], question_number: int = 1):
    """
    Display a coding question with all details
    
    Args:
        question: Question dictionary with title, description, examples, etc.
        question_number: Question number in the interview
    """
    st.subheader(f"Question {question_number}: {question.get('title', 'Untitled')}")
    
    # Difficulty badge
    difficulty = question.get('difficulty', 'medium').lower()
    difficulty_colors = {
        'easy': '🟢',
        'medium': '🟡',
        'hard': '🔴'
    }
    st.markdown(f"**Difficulty:** {difficulty_colors.get(difficulty, '⚪')} {difficulty.upper()}")
    
    # Description
    st.markdown("### Description")
    st.markdown(question.get('description', 'No description provided'))
    
    # Examples
    examples = question.get('examples', [])
    if examples:
        with st.expander("📝 Examples", expanded=True):
            for i, example in enumerate(examples, 1):
                st.markdown(f"**Example {i}:**")
                if isinstance(example, dict):
                    input_val = example.get('input', '')
                    output_val = example.get('output', '')
                    st.code(f"Input: {input_val}\nOutput: {output_val}", language="text")
                else:
                    st.code(str(example), language="text")
    
    # Constraints
    constraints = question.get('constraints', [])
    if constraints:
        with st.expander("⚠️ Constraints"):
            for constraint in constraints:
                st.markdown(f"- {constraint}")
    
    # Hints (collapsible)
    hints = question.get('hints', [])
    if hints:
        with st.expander("💡 Hints"):
            for i, hint in enumerate(hints, 1):
                st.markdown(f"{i}. {hint}")
    
    # Tags
    tags = question.get('tags', [])
    if tags:
        st.markdown("**Tags:** " + ", ".join([f"`{tag}`" for tag in tags]))

