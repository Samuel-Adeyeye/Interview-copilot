"""
Session List Component for Streamlit
"""

import streamlit as st
from typing import Dict, Any, List
from datetime import datetime

def session_list_component(
    sessions: List[Dict[str, Any]],
    on_select: callable = None,
    on_delete: callable = None
):
    """
    Display and manage session list
    
    Args:
        sessions: List of session dictionaries
        on_select: Callback function when session is selected
        on_delete: Callback function when session is deleted
    """
    if not sessions:
        st.info("No sessions found. Create a new session to get started!")
        return
    
    st.markdown(f"### Your Sessions ({len(sessions)})")
    
    for session in sessions:
        session_id = session.get('session_id', 'unknown')
        state = session.get('state', 'unknown')
        created_at = session.get('created_at', '')
        
        # Format date
        try:
            if created_at:
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                date_str = dt.strftime("%Y-%m-%d %H:%M")
            else:
                date_str = "Unknown"
        except:
            date_str = created_at
        
        # State badge
        state_colors = {
            'created': '🔵',
            'running': '🟢',
            'paused': '🟡',
            'completed': '✅',
            'failed': '❌'
        }
        state_icon = state_colors.get(state.lower(), '⚪')
        
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
        
        with col1:
            st.markdown(f"**{state_icon} {session_id[:8]}...**")
        
        with col2:
            st.caption(f"State: {state}")
        
        with col3:
            st.caption(f"Created: {date_str}")
        
        with col4:
            if on_select:
                if st.button("Select", key=f"select_{session_id}"):
                    on_select(session_id)
            if on_delete:
                if st.button("🗑️", key=f"delete_{session_id}", help="Delete session"):
                    on_delete(session_id)
        
        st.divider()

